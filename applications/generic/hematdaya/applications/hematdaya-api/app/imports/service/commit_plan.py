"""The pure rules of a commit: which streams count, what a row becomes, and what its bindings must cover."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo

from app.assets.model.models import BindingModel
from app.core.errors.base import AppError
from app.imports.model.models import ImportModel, ValueKind
from app.measurements.model.models import IngestResult, ReadingInput
from app.sites.model.models import SiteModel

_MICROSECOND = timedelta(microseconds=1)

EXPIRED = "expired"
REVISION_CHANGED = "revision_changed"
TIMEZONE_CHANGED = "timezone_changed"


@dataclass(frozen=True, slots=True)
class CommitStream:
    """A stream a preview resolved, with at least one staged row.

    Attributes:
        stream_key (str): The stream.
        label (str): The label its source carries.
        asset_name (str): The name as written.
        asset_id (UUID | None): Its target asset; None for a new one.
        source_id (UUID | None): The stored source it feeds; None for a new one.
        kind (ValueKind): What its values mean.
        cadence_seconds (int | None): The cadence a new source should declare.
        interval_basis (str | None): Where its interval ends came from.
    """

    stream_key: str
    label: str
    asset_name: str
    asset_id: UUID | None
    source_id: UUID | None
    kind: ValueKind
    cadence_seconds: int | None
    interval_basis: str | None


def _uuid(value: str | None) -> UUID | None:
    return None if value is None else UUID(value)


def committable_streams(mapping: dict[str, Any]) -> list[CommitStream]:
    """Read a stored mapping's streams. One whose rows were all invalid has no period, and it creates nothing.

    Args:
        mapping (dict[str, Any]): ``imports.mapping``.

    Returns:
        list[CommitStream]: The streams, in first-seen order.
    """
    return [
        CommitStream(
            stream_key=stream["stream_key"],
            label=stream["label"],
            asset_name=stream["asset_name"],
            asset_id=_uuid(stream["asset_id"]),
            source_id=_uuid(stream["source_id"]),
            kind=ValueKind(stream["kind"]),
            cadence_seconds=stream["cadence_seconds"],
            interval_basis=stream["interval_basis"],
        )
        for stream in mapping["streams"]
        if stream["period_start"] is not None
    ]


def _moment(value: str | None) -> datetime | None:
    return None if value is None else datetime.fromisoformat(value)


def reading_from_parsed(parsed: dict[str, Any]) -> ReadingInput:
    """Rebuild a staged row's reading from its canonical ``value``, never ``raw_value``.

    The preview compared stored rows against the canonical value, so the raw cell would turn a reimport into a revision.

    Args:
        parsed (dict[str, Any]): ``import_rows.parsed``.

    Returns:
        ReadingInput: The reading.
    """
    return ReadingInput(
        value=Decimal(parsed["value"]),
        unit=parsed["unit"],
        interval_start=_moment(parsed["interval_start"]),
        interval_end=_moment(parsed["interval_end"]),
        measured_at=_moment(parsed["measured_at"]),
    )


def row_bounds(parsed: dict[str, Any]) -> tuple[datetime, datetime]:
    """Return the half-open range a binding must cover for a row to count.

    Args:
        parsed (dict[str, Any]): ``import_rows.parsed``.

    Returns:
        tuple[datetime, datetime]: An interval's bounds, or a point and the next microsecond.
    """
    if parsed["measured_at"] is not None:
        moment = datetime.fromisoformat(parsed["measured_at"])
        return moment, moment + _MICROSECOND
    return datetime.fromisoformat(parsed["interval_start"]), datetime.fromisoformat(parsed["interval_end"])


def uncovered_ranges(
    start: datetime, end: datetime, bindings: Sequence[BindingModel]
) -> list[tuple[datetime, datetime | None]]:
    """List the parts of a span no binding of the asset covers, each ready to become one binding.

    Every binding counts, authoritative or not: an open authoritative range must end at any later binding's start, or
    it would collide with one or silently overrule the other.

    Args:
        start (datetime): The accepted rows' earliest instant.
        end (datetime): Their latest instant, exclusive.
        bindings (Sequence[BindingModel]): All of the asset's bindings, of any source.

    Returns:
        list[tuple[datetime, datetime | None]]: Each start and end. An end of None stays open.
    """
    ranges: list[tuple[datetime, datetime | None]] = []
    cursor = start
    for binding in sorted(bindings, key=lambda item: item.effective_from):
        if binding.effective_to is not None and binding.effective_to <= cursor:
            continue
        if binding.effective_from > cursor:
            ranges.append((cursor, binding.effective_from))
        if binding.effective_to is None or binding.effective_to >= end or binding.effective_from >= end:
            return ranges
        cursor = binding.effective_to
    ranges.append((cursor, None))
    return ranges


def stale_reason(model: ImportModel, site: SiteModel, now: datetime) -> str | None:
    """Tell why a preview no longer describes its locked site. Rows are not classified again.

    Every write that could change a classification advances a revision, so equal revisions mean the stored data is what
    the preview read. Changing a site's timezone advances neither, and naive rows were read in the old one.

    Args:
        model (ImportModel): The stored preview.
        site (SiteModel): Its site, read under the lock.
        now (datetime): Wall-clock now.

    Returns:
        str | None: ``expired``, ``revision_changed`` or ``timezone_changed``; None when it is still valid.
    """
    if model.expires_at <= now:
        return EXPIRED
    if model.measurement_revision != site.measurement_revision or model.binding_revision != site.binding_revision:
        return REVISION_CHANGED
    if model.mapping["timezone"] != site.timezone:
        return TIMEZONE_CHANGED
    return None


def affected_period(start: datetime | None, end: datetime | None, timezone: str) -> dict[str, str] | None:
    """Name the local dates a change touched.

    Args:
        start (datetime | None): Start of the changed data.
        end (datetime | None): Its end, exclusive unless it equals ``start``.
        timezone (str): The site's IANA timezone.

    Returns:
        dict[str, str] | None: ``start_date``, ``end_date`` and ``timezone``, or None when nothing changed.
    """
    if start is None or end is None:
        return None
    zone = ZoneInfo(timezone)
    last = end if end == start else end - _MICROSECOND
    return {
        "start_date": start.astimezone(zone).date().isoformat(),
        "end_date": last.astimezone(zone).date().isoformat(),
        "timezone": timezone,
    }


@dataclass(slots=True)
class CommitTotals:
    """What a commit's batches changed so far.

    Attributes:
        added (int): Identities stored.
        affected_from (datetime | None): Start of the changed data.
        affected_to (datetime | None): End of the changed data.
    """

    added: int = 0
    affected_from: datetime | None = None
    affected_to: datetime | None = None

    def add(self, result: IngestResult) -> None:
        """Merge one batch, refusing anything the preview said could not happen.

        Equal revisions make such a result a bug in 024, 025 or 006. Left alone, ``ingest`` would silently revise a
        changed value, which is what the preview exists to prevent.

        Args:
            result (IngestResult): One ``ingest`` result.

        Raises:
            AppError: When a row was rejected, revised or repeated.
        """
        if result.rejected or result.revised or result.repeated:
            raise AppError(error=RuntimeError("Ingestion disagrees with the preview it was given."))
        self.added += result.added
        if result.affected_from is not None:
            self.affected_from = min(self.affected_from or result.affected_from, result.affected_from)
        if result.affected_to is not None:
            self.affected_to = max(self.affected_to or result.affected_to, result.affected_to)
