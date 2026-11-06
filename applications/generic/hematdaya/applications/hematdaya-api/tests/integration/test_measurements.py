"""Ingestion over real Postgres: identity, revisions, counters and concurrency."""

import asyncio
import time
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

import pytest

from app.assets.model.models import MeasurementKind, SourceModel, SourceOrigin, TransportStatus
from app.core.database import get_session_factory
from app.measurements.dependencies import build_ingest_service
from app.measurements.model.models import IngestResult, ReadingInput
from app.sites.repository.sqlalchemy.repository import SqlAlchemySiteRepository
from tests.integration.conftest import execute, make_principal, make_site

pytestmark = pytest.mark.integration

T0 = datetime(2026, 10, 18, 17, tzinfo=UTC)
RECEIVED = datetime(2026, 11, 1, tzinfo=UTC)


async def _source(kind: MeasurementKind = MeasurementKind.INTERVAL_ENERGY) -> SourceModel:
    site = await make_site(await make_principal())
    rows = await execute(
        "INSERT INTO sources (id, site_id, label, origin, measurement_kind, cadence_seconds)"
        " VALUES (gen_random_uuid(), :site, 'Sumber', 'simulated', :kind, 3600) RETURNING id",
        site=site,
        kind=kind.value,
    )
    return SourceModel(
        id=rows[0][0],
        site_id=site,
        label="Sumber",
        origin=SourceOrigin.SIMULATED,
        measurement_kind=kind,
        cadence_seconds=3600,
        resolution_mwh=None,
        transport_status=TransportStatus.NONE,
    )


async def _ingest(source: SourceModel, readings: list[ReadingInput], *, commit: bool = True) -> IngestResult:
    async with get_session_factory()() as session:
        site = await SqlAlchemySiteRepository(session).lock(source.site_id)
        assert site is not None
        result = await build_ingest_service(session).ingest(site, source, readings, received_at=RECEIVED)
        if commit:
            await session.commit()
        return result


def _hourly(count: int, wh: str = "50", start: int = 0) -> list[ReadingInput]:
    return [
        ReadingInput(
            value=Decimal(wh),
            unit="Wh",
            interval_start=T0 + timedelta(hours=i),
            interval_end=T0 + timedelta(hours=i + 1),
        )
        for i in range(start, start + count)
    ]


def _counter(*readings: tuple[int, str]) -> list[ReadingInput]:
    return [ReadingInput(value=Decimal(wh), unit="Wh", measured_at=T0 + timedelta(hours=hour)) for hour, wh in readings]


async def _current(source: UUID, kind: str) -> list[tuple]:
    return await execute(
        "SELECT interval_start, energy_mwh, revision FROM current_measurements"
        " WHERE source_id = :id AND kind = :kind ORDER BY interval_start",
        id=source,
        kind=kind,
    )


async def _measurement_revision(site: UUID) -> int:
    return (await execute("SELECT measurement_revision FROM sites WHERE id = :id", id=site))[0][0]


async def test_replaying_a_batch_changes_nothing() -> None:
    """
    Condition:
    - A day of hourly readings ingested twice.

    Expected:
    - The replay is all repeats: no row, no total and no revision changes.
    """
    source = await _source()

    first = await _ingest(source, _hourly(24))
    revision = await _measurement_revision(source.site_id)
    second = await _ingest(source, _hourly(24))

    assert (first.added, second.added, second.repeated) == (24, 0, 24)
    assert (await execute("SELECT count(*), sum(energy_mwh) FROM measurements WHERE source_id = :id", id=source.id))[
        0
    ] == (24, 1_200_000)
    assert await _measurement_revision(source.site_id) == revision


async def test_a_correction_is_a_revision_with_its_affected_range() -> None:
    """
    Condition:
    - One hour is re-sent with a different value.

    Expected:
    - It becomes revision 2, the current view shows only the new value, and the affected range is that hour.
    """
    source = await _source()
    await _ingest(source, _hourly(3))
    revision = await _measurement_revision(source.site_id)

    result = await _ingest(source, _hourly(1, wh="80", start=1))

    assert (result.revised, result.affected_from, result.affected_to) == (
        1,
        T0 + timedelta(hours=1),
        T0 + timedelta(hours=2),
    )
    assert [row[1:] for row in await _current(source.id, "interval_energy")] == [(50_000, 1), (80_000, 2), (50_000, 1)]
    assert await _measurement_revision(source.site_id) == revision + 1


async def test_points_without_capture_id_dedupe_by_time() -> None:
    """
    Condition:
    - Instantaneous samples without capture IDs: one repeated, one at another time.

    Expected:
    - The repeat is idempotent; a different time is a distinct point.
    """
    source = await _source(MeasurementKind.INSTANTANEOUS_POWER)
    sample = [ReadingInput(value=Decimal(100), unit="W", measured_at=T0)]

    await _ingest(source, sample)
    repeat = await _ingest(source, sample)
    later = await _ingest(source, [ReadingInput(value=Decimal(100), unit="W", measured_at=T0 + timedelta(minutes=1))])

    assert (repeat.repeated, later.added) == (1, 1)
    assert (await execute("SELECT count(*) FROM measurements WHERE source_id = :id", id=source.id))[0][0] == 2


async def test_corrected_middle_counter_reading_replaces_both_deltas() -> None:
    """
    Condition:
    - Counter 100 → 130 → 160 Wh, then the middle reading is corrected to 140 Wh, then replayed.

    Expected:
    - Deltas become 40 and 20 Wh, replacing 30 and 30 rather than adding to them, and the replay changes nothing.
    """
    source = await _source(MeasurementKind.COUNTER)
    await _ingest(source, _counter((0, "100"), (1, "130"), (2, "160")))
    before = await _current(source.id, "counter_delta")

    corrected = await _ingest(source, _counter((1, "140")))
    after = await _current(source.id, "counter_delta")
    replay = await _ingest(source, _counter((0, "100"), (1, "140"), (2, "160")))

    assert [row[1] for row in before] == [30_000, 30_000]
    assert [row[1] for row in after] == [40_000, 20_000]
    assert (corrected.affected_from, corrected.affected_to) == (T0, T0 + timedelta(hours=2))
    assert (replay.added, replay.revised, replay.repeated) == (0, 0, 3)
    assert await _current(source.id, "counter_delta") == after


async def test_concurrent_delivery_stores_once() -> None:
    """
    Condition:
    - The same batch arrives twice at the same time.

    Expected:
    - The site lock serializes them: one adds, the other repeats.
    """
    source = await _source()

    results = await asyncio.gather(_ingest(source, _hourly(48)), _ingest(source, _hourly(48)))

    assert sorted((result.added, result.repeated) for result in results) == [(0, 48), (48, 0)]
    assert (await execute("SELECT count(*) FROM measurements WHERE source_id = :id", id=source.id))[0][0] == 48


async def test_rollback_leaves_revision_and_rows_unchanged() -> None:
    """
    Condition:
    - A batch is ingested but its transaction rolls back.

    Expected:
    - No row stays and the measurement revision does not move.
    """
    source = await _source()
    revision = await _measurement_revision(source.site_id)

    await _ingest(source, _hourly(5), commit=False)

    assert (await execute("SELECT count(*) FROM measurements WHERE source_id = :id", id=source.id))[0][0] == 0
    assert await _measurement_revision(source.site_id) == revision


async def test_ten_thousand_rows_ingest_in_one_batch() -> None:
    """
    Condition:
    - A 10,000-row batch, then its replay.

    Expected:
    - Everything is stored once; the timing is printed for the record.
    """
    source = await _source()

    started = time.perf_counter()
    first = await _ingest(source, _hourly(10_000))
    took = time.perf_counter() - started
    replay = await _ingest(source, _hourly(10_000))

    print(f"10,000-row ingest took {took:.2f}s")
    assert (first.added, replay.repeated) == (10_000, 10_000)
