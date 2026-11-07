"""The one ingestion path. CSV (026), demo (008) and adapters (046) all call it."""

from datetime import datetime
from typing import Any
from uuid import UUID

from app.assets.model.models import SourceModel
from app.measurements.model.models import IngestResult, MeasurementRow, ReadingInput, Rejection, StoredKind
from app.measurements.repository.base_repository import MeasurementRepository
from app.measurements.service.normalize import CounterPoint, ReadingRejectedError, counter_deltas, normalize
from app.sites.model.models import SiteModel
from app.sites.service.service import SiteService


def _span(row: MeasurementRow) -> tuple[datetime, datetime]:
    if row.interval_start is not None and row.interval_end is not None:
        return row.interval_start, row.interval_end
    assert row.measured_at is not None
    return row.measured_at, row.measured_at


class IngestService:
    """Stores readings once: repeats are no-ops, corrections are revisions, and nothing invalid becomes zero."""

    def __init__(self, repository: MeasurementRepository, sites: SiteService) -> None:
        """Bind to storage and the site lock.

        Args:
            repository (MeasurementRepository): Measurement storage.
            sites (SiteService): Site lock and revisions.
        """
        self.repository = repository
        self.sites = sites

    async def ingest(
        self,
        site: SiteModel,
        source: SourceModel,
        readings: list[ReadingInput],
        *,
        received_at: datetime,
        provenance: dict[str, Any] | None = None,
    ) -> IngestResult:
        """Normalize and store a batch for one source of a resolved site, in the caller's transaction.

        Args:
            site (SiteModel): The source's site, already resolved through its owner.
            source (SourceModel): The source; it declares what values mean.
            readings (list[ReadingInput]): Raw observations.
            received_at (datetime): Wall-clock arrival time.
            provenance (dict[str, Any] | None, optional): How the batch arrived, such as the import's timezone
                assumption. Defaults to None.

        Returns:
            IngestResult: Counts, rejections and the affected interval.
        """
        assert source.site_id == site.id
        locked = await self.sites.lock(site.id)
        result = IngestResult()
        normalized: list[MeasurementRow] = []
        for index, reading in enumerate(readings):
            try:
                row = normalize(reading, source.measurement_kind)
            except ReadingRejectedError as rejection:
                result.rejected.append(Rejection(index=index, reason=rejection.reason))
                continue
            normalized.append(row.model_copy(update={"provenance": provenance or {}}))

        current = await self.repository.current_rows(source.id, sorted({row.identity_key for row in normalized}))
        changed: list[MeasurementRow] = []
        spans: list[tuple[datetime, datetime]] = []
        for row in normalized:
            stored = current.get(row.identity_key)
            if stored is not None and row.same_observation(stored):
                result.repeated += 1
                continue
            if stored is not None:
                row = row.model_copy(update={"revision": stored.revision + 1})
                spans.append(_span(stored))
                result.revised += 1
            else:
                result.added += 1
            current[row.identity_key] = row
            changed.append(row)
            spans.append(_span(row))
        await self.repository.insert(source.id, changed, received_at)

        if any(row.kind is StoredKind.COUNTER_POINT for row in changed):
            spans.extend(await self._rederive_counter(source, received_at))
        if changed:
            await self.sites.advance_measurement_revision(locked)
            result.affected_from = min(start for start, _ in spans)
            result.affected_to = max(end for _, end in spans)
        return result

    async def current_rows(self, source_id: UUID, identity_keys: list[str]) -> dict[str, MeasurementRow]:
        """Read the current revision of known identities. Takes no lock, so a concurrent write may land after it.

        Args:
            source_id (UUID): The source.
            identity_keys (list[str]): Identities to look up.

        Returns:
            dict[str, MeasurementRow]: Current rows by identity; unknown identities are absent.
        """
        return await self.repository.current_rows(source_id, identity_keys)

    async def stored_intervals(self, source_id: UUID, start: datetime, end: datetime) -> list[MeasurementRow]:
        """Read current rows with energy overlapping a half-open window. Takes no lock.

        Args:
            source_id (UUID): The source.
            start (datetime): Window start, inclusive.
            end (datetime): Window end, exclusive.

        Returns:
            list[MeasurementRow]: Rows by interval start. Adjacent intervals are not included.
        """
        return await self.repository.stored_intervals(source_id, start, end)

    async def _rederive_counter(self, source: SourceModel, received_at: datetime) -> list[tuple[datetime, datetime]]:
        # ponytail: re-derives all of one source's deltas per counter batch; window it by neighbouring readings
        # if counter sources grow beyond a few hundred thousand readings.
        points = [CounterPoint.from_row(row) for row in await self.repository.counter_points(source.id)]
        fresh = counter_deltas(points, source.cadence_seconds)
        old = await self.repository.counter_deltas(source.id)
        old_keys = {(row.identity_key, row.energy_mwh, row.quality) for row in old}
        new_keys = {(row.identity_key, row.energy_mwh, row.quality) for row in fresh}
        if old_keys == new_keys:
            return []
        await self.repository.replace_counter_deltas(source.id, fresh, received_at)
        displaced = [row for row in old if (row.identity_key, row.energy_mwh, row.quality) not in new_keys]
        added = [row for row in fresh if (row.identity_key, row.energy_mwh, row.quality) not in old_keys]
        return [_span(row) for row in [*displaced, *added]]
