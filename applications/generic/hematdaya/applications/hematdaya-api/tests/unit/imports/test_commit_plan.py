"""The commit's pure rules: streams, readings, ranges, staleness and totals."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from app.assets.model.models import BindingModel, MeasurementKind
from app.core.errors.base import AppError
from app.imports.model.models import ImportModel, ImportStatus, ValueKind
from app.imports.service.commit_plan import (
    CommitStream,
    CommitTotals,
    affected_period,
    committable_streams,
    reading_from_parsed,
    row_bounds,
    stale_reason,
    uncovered_ranges,
)
from app.measurements.model.models import IngestResult, Rejection
from app.measurements.service.normalize import normalize
from app.sites.model.models import SiteContext, SiteKind, SiteModel

NOW = datetime(2026, 11, 7, 12, tzinfo=UTC)
DAY_1, DAY_2, DAY_3, DAY_4, DAY_5, DAY_6 = (datetime(2026, 10, day, tzinfo=UTC) for day in range(1, 7))
MICROSECOND = timedelta(microseconds=1)


def _stream(**overrides: object) -> dict:
    values = {
        "stream_key": "router",
        "label": "Impor CSV · router",
        "asset_name": "Router",
        "asset_id": None,
        "source_id": None,
        "kind": "interval_energy",
        "unit": "Wh",
        "cadence_seconds": 3600,
        "period_start": "2026-10-20T00:00:00Z",
        "period_end": "2026-10-20T01:00:00Z",
        "interval_basis": "explicit",
    }
    return values | overrides


def _binding(start: datetime, end: datetime | None = None) -> BindingModel:
    return BindingModel(
        id=uuid4(),
        site_id=uuid4(),
        source_id=uuid4(),
        asset_id=uuid4(),
        effective_from=start,
        effective_to=end,
        authoritative=True,
    )


def _import(**overrides: object) -> ImportModel:
    values = {
        "id": uuid4(),
        "site_id": uuid4(),
        "status": ImportStatus.PREVIEWED,
        "file_name": "a.csv",
        "content_sha256": "0" * 64,
        "mapping": {"timezone": "Asia/Jakarta"},
        "total_rows": 1,
        "accepted_rows": 1,
        "invalid_rows": 0,
        "duplicate_rows": 0,
        "conflict_rows": 0,
        "pending_rows": 0,
        "blocked": False,
        "block_reasons": [],
        "needs_acknowledgment": False,
        "questions": [],
        "assumptions": [],
        "period_start": None,
        "period_end": None,
        "measurement_revision": 3,
        "binding_revision": 4,
        "idempotency_key": None,
        "expires_at": NOW + timedelta(hours=1),
    }
    return ImportModel(**(values | overrides))


def _site(**overrides: object) -> SiteModel:
    values = {
        "id": uuid4(),
        "owner_principal_id": uuid4(),
        "kind": SiteKind.DEMO,
        "name": "Rumah",
        "context": SiteContext.UNSPECIFIED,
        "timezone": "Asia/Jakarta",
        "currency": "IDR",
        "virtual_now": NOW,
        "measurement_revision": 3,
        "binding_revision": 4,
    }
    return SiteModel(**(values | overrides))


def test_committable_streams_drops_a_stream_with_no_period() -> None:
    """
    Condition:
    - ``mapping`` holds a stream whose rows are all invalid, so it has no period.

    Expected:
    - That stream is gone, so it can never create anything (D11).
    """
    mapping = {"streams": [_stream(stream_key="kosong", period_start=None, period_end=None), _stream()]}

    assert [stream.stream_key for stream in committable_streams(mapping)] == ["router"]


def test_committable_streams_types_the_fields() -> None:
    """
    Condition:
    - A stream stored as JSON, resolved to an asset and a source.

    Expected:
    - IDs and the kind are typed, and the plain fields carry over.
    """
    asset, source = uuid4(), uuid4()
    mapping = {"streams": [_stream(asset_id=str(asset), source_id=str(source))]}

    assert committable_streams(mapping) == [
        CommitStream(
            stream_key="router",
            label="Impor CSV · router",
            asset_name="Router",
            asset_id=asset,
            source_id=source,
            kind=ValueKind.INTERVAL_ENERGY,
            cadence_seconds=3600,
            interval_basis="explicit",
        )
    ]


def test_committable_streams_keeps_unknown_targets_empty() -> None:
    """
    Condition:
    - A stream targeting a new asset with no source.

    Expected:
    - Both stay None.
    """
    stream = committable_streams({"streams": [_stream()]})[0]

    assert (stream.asset_id, stream.source_id) == (None, None)


def test_reading_from_parsed_uses_the_canonical_value() -> None:
    """
    Condition:
    - A row written ``10,5`` in the file, staged as the canonical ``10.500``.

    Expected:
    - ``normalize`` gives the preview's identity and raw value ``10.500``, so a reimport is a repeat, not a revision.
    """
    parsed = {
        "kind": "interval_energy",
        "unit": "Wh",
        "value": "10.500",
        "raw_value": "10,5",
        "identity_key": "i:interval_energy:1792454400.000000:1792458000.000000",
        "interval_start": "2026-10-20T00:00:00Z",
        "interval_end": "2026-10-20T01:00:00Z",
        "measured_at": None,
    }

    reading = reading_from_parsed(parsed)
    row = normalize(reading, MeasurementKind.INTERVAL_ENERGY)

    assert reading.value == Decimal("10.500")
    assert row.identity_key == parsed["identity_key"]
    assert row.raw_value == "10.500"
    assert reading.interval_start == datetime(2026, 10, 20, tzinfo=UTC)
    assert reading.interval_start.utcoffset() == timedelta(0)


def test_reading_from_parsed_gives_a_counter_only_its_capture_time() -> None:
    """
    Condition:
    - A counter row.

    Expected:
    - It has ``measured_at`` in UTC and no interval, which 006 requires of a point.
    """
    parsed = {
        "kind": "counter",
        "unit": "Wh",
        "value": "100.000",
        "raw_value": "100",
        "interval_start": None,
        "interval_end": None,
        "measured_at": "2026-10-20T00:00:00Z",
    }

    reading = reading_from_parsed(parsed)

    assert (reading.interval_start, reading.interval_end) == (None, None)
    assert reading.measured_at == datetime(2026, 10, 20, tzinfo=UTC)
    assert normalize(reading, MeasurementKind.COUNTER).raw_value == "100.000"


def test_row_bounds_of_an_interval_are_its_bounds() -> None:
    """
    Condition:
    - An interval row.

    Expected:
    - Its start and its exclusive end.
    """
    parsed = {"interval_start": "2026-10-20T00:00:00Z", "interval_end": "2026-10-20T01:00:00Z", "measured_at": None}

    assert row_bounds(parsed) == (datetime(2026, 10, 20, tzinfo=UTC), datetime(2026, 10, 20, 1, tzinfo=UTC))


def test_row_bounds_of_a_point_cover_it() -> None:
    """
    Condition:
    - A counter point, which a half-open binding must still cover.

    Expected:
    - Itself and itself plus one microsecond (D13).
    """
    parsed = {"interval_start": None, "interval_end": None, "measured_at": "2026-10-20T00:00:00Z"}

    moment = datetime(2026, 10, 20, tzinfo=UTC)
    assert row_bounds(parsed) == (moment, moment + MICROSECOND)


@pytest.mark.parametrize(
    ("start", "end", "bindings", "expected"),
    [
        (DAY_2, DAY_3, [], [(DAY_2, None)]),
        (DAY_2, DAY_3, [(DAY_1, None)], []),
        (DAY_1, DAY_3, [(DAY_3, None)], [(DAY_1, DAY_3)]),
        (DAY_1, DAY_2, [(DAY_5, None)], [(DAY_1, DAY_5)]),
        (DAY_3, DAY_4, [(DAY_1, DAY_2)], [(DAY_3, None)]),
        (DAY_2, DAY_5, [(DAY_1, DAY_3)], [(DAY_3, None)]),
        (DAY_2, DAY_5, [(DAY_1, DAY_3), (DAY_4, None)], [(DAY_3, DAY_4)]),
        (DAY_2, DAY_3, [(DAY_1, DAY_4)], []),
        (DAY_3, DAY_3 + MICROSECOND, [(DAY_1, DAY_3)], [(DAY_3, None)]),
        (DAY_1, DAY_6, [(DAY_2, DAY_3), (DAY_4, DAY_5)], [(DAY_1, DAY_2), (DAY_3, DAY_4), (DAY_5, None)]),
    ],
    ids=[
        "no_bindings",
        "open_covers",
        "earlier_rows",
        "later_binding",
        "after_a_closed_binding",
        "straddle",
        "hole",
        "inside_a_closed_binding",
        "counter_point_at_the_end_of_a_binding",
        "several_gaps",
    ],
)
def test_uncovered_ranges(
    start: datetime,
    end: datetime,
    bindings: list[tuple[datetime, datetime | None]],
    expected: list[tuple[datetime, datetime | None]],
) -> None:
    """
    Condition:
    - The accepted rows' span and the asset's bindings of any source, given out of order.

    Expected:
    - Each uncovered part, ending at the next binding's start, or open when none follows (D13).
    """
    models = [_binding(*binding) for binding in reversed(bindings)]

    assert uncovered_ranges(start, end, models) == expected


def test_stale_reason_is_none_when_everything_matches() -> None:
    """
    Condition:
    - A live preview, with both revisions and the timezone as the site has them.

    Expected:
    - None.
    """
    assert stale_reason(_import(), _site(), NOW) is None


@pytest.mark.parametrize(
    ("model", "site", "expected"),
    [
        ({"expires_at": NOW}, {}, "expired"),
        ({"expires_at": NOW, "measurement_revision": 1}, {"timezone": "Asia/Makassar"}, "expired"),
        ({"measurement_revision": 2}, {}, "revision_changed"),
        ({"binding_revision": 2}, {}, "revision_changed"),
        ({"binding_revision": 2}, {"timezone": "Asia/Makassar"}, "revision_changed"),
        ({}, {"timezone": "Asia/Makassar"}, "timezone_changed"),
    ],
    ids=["expired_at_now", "expired_first", "measurement", "binding", "revision_before_timezone", "timezone"],
)
def test_stale_reason_names_the_first_failure(model: dict, site: dict, expected: str) -> None:
    """
    Condition:
    - A preview past its expiry, or one whose revision or timezone no longer matches (D6, D7).

    Expected:
    - The reason, with ``expired`` ahead of the others.
    """
    assert stale_reason(_import(**model), _site(**site), NOW) == expected


def test_affected_period_is_none_without_a_range() -> None:
    """
    Condition:
    - Nothing changed.

    Expected:
    - None.
    """
    assert affected_period(None, None, "Asia/Jakarta") is None


def test_affected_period_gives_an_end_at_local_midnight_to_the_previous_date() -> None:
    """
    Condition:
    - An exclusive end exactly at local midnight in Jakarta.

    Expected:
    - That date is not touched, so the period ends the day before.
    """
    start, end = datetime(2026, 10, 19, 17, tzinfo=UTC), datetime(2026, 10, 20, 17, tzinfo=UTC)

    assert affected_period(start, end, "Asia/Jakarta") == {
        "start_date": "2026-10-20",
        "end_date": "2026-10-20",
        "timezone": "Asia/Jakarta",
    }


def test_affected_period_of_one_instant_is_its_date() -> None:
    """
    Condition:
    - A counter anchor, whose affected range starts and ends at one instant.

    Expected:
    - That one local date, not the day before.
    """
    moment = datetime(2026, 10, 19, 17, tzinfo=UTC)

    period = affected_period(moment, moment, "Asia/Jakarta")

    assert period == {"start_date": "2026-10-20", "end_date": "2026-10-20", "timezone": "Asia/Jakarta"}


def test_commit_totals_sum_and_widen() -> None:
    """
    Condition:
    - Three batches, one of which changed nothing.

    Expected:
    - ``added`` sums, the range takes the minimum and maximum, and a batch with no range leaves it alone.
    """
    totals = CommitTotals()

    totals.add(IngestResult(added=2, affected_from=DAY_2, affected_to=DAY_3))
    totals.add(IngestResult(added=1, affected_from=DAY_1, affected_to=DAY_2))
    totals.add(IngestResult())

    assert (totals.added, totals.affected_from, totals.affected_to) == (3, DAY_1, DAY_3)


def test_commit_totals_start_empty() -> None:
    """
    Condition:
    - No batch.

    Expected:
    - Zero rows and no range, as a duplicate-only commit reports.
    """
    totals = CommitTotals()

    assert (totals.added, totals.affected_from, totals.affected_to) == (0, None, None)


@pytest.mark.parametrize(
    "result",
    [
        IngestResult(rejected=[Rejection(index=0, reason="negative")]),
        IngestResult(revised=1),
        IngestResult(repeated=1),
    ],
    ids=["rejected", "revised", "repeated"],
)
def test_commit_totals_refuse_what_the_preview_said_could_not_happen(result: IngestResult) -> None:
    """
    Condition:
    - ``ingest`` disagrees with the preview, which equal revisions make a bug (D22).

    Expected:
    - ``AppError`` with the fallback code, so the transaction rolls back and a value is never silently revised.
    """
    with pytest.raises(AppError) as raised:
        CommitTotals().add(result)

    assert raised.value.code == "APP-UNKNOWN"
    assert raised.value.recovery["retryable"] is False
