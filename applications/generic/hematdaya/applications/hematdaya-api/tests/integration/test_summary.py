"""Energy summary oracles over seeded demo workspaces (PRD §19, AT-05, AT-06, AT-19, AT-21, AT-35, AT-36)."""

import json
import os
import re
import time
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import UUID

import pytest
from httpx import AsyncClient

from app.assets.model.models import MeasurementKind, SourceModel, SourceOrigin, TransportStatus
from app.core.database import get_session_factory
from app.demo.dependencies import build_demo_service
from app.energy.repository.sqlalchemy.repository import SqlAlchemyEnergyRepository
from app.energy.service.periods import resolve_window
from app.energy.service.summary import EnergyService
from app.measurements.dependencies import build_ingest_service
from app.measurements.model.models import ReadingInput
from app.sites.repository.sqlalchemy.repository import SqlAlchemySiteRepository
from tests.integration.conftest import execute, make_asset, start_demo, summary

pytestmark = pytest.mark.integration

GOLDEN = Path(__file__).resolve().parents[4] / "contracts" / "golden"
WEEK = {"start_date": "2026-10-19", "end_date": "2026-10-25"}


def _by_name(body: dict) -> dict[str, dict]:
    return {row["name"]: row for row in body["assets"]}


async def _selection(site_id: str, names: list[str], start: date, end: date) -> dict:
    """Summarize an explicit selection through the service, the way 028 will persist one."""
    async with get_session_factory()() as session:
        demo = build_demo_service(session)
        site = await SqlAlchemySiteRepository(session).lock(UUID(site_id))
        assert site is not None
        service = EnergyService(SqlAlchemyEnergyRepository(session), demo.sites, demo.assets)
        snapshot = await demo.assets.snapshot(site)
        ids = [asset.id for asset in snapshot.assets if asset.name in names]
        window = resolve_window(site.timezone, site.virtual_now, start_date=start, end_date=end)
        return (await service.summarize(site, window, ids)).model_dump(mode="json")


def _normalize(body: dict) -> str:
    """Replace generated IDs with stable placeholders, so a golden file is byte for byte."""
    text = json.dumps(body, indent=2, sort_keys=True, ensure_ascii=False)
    ids = dict.fromkeys(re.findall(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", text))
    for index, value in enumerate(ids):
        text = text.replace(value, f"id-{index}")
    body = json.loads(text)
    body["revision"] = "revision"
    return json.dumps(body, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _golden(name: str, body: dict) -> None:
    path = GOLDEN / name
    text = _normalize(body)
    if os.environ.get("UPDATE_GOLDEN") == "1":
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    assert text == path.read_text(), f"{name} drifted; rerun with UPDATE_GOLDEN=1 after review"


async def test_household_week_day_and_four_weeks(client: AsyncClient) -> None:
    """
    Condition:
    - AT-05 on h-base: 19–25 Oktober, 19 Oktober, and 28 September to 25 Oktober.

    Expected:
    - 14.700 kWh with complete coverage and Kulkas 8.400 kWh (57.14%) first of four; 2.100 and 58.800 kWh.
    """
    session = await start_demo(client)

    started = time.perf_counter()
    four_weeks = await summary(client, session, start_date="2026-09-28", end_date="2026-10-25")
    print(f"four-week summary over 2,688 rows took {time.perf_counter() - started:.3f}s")
    week = await summary(client, session, preset="last_7_days")
    day = await summary(client, session, start_date="2026-10-19", end_date="2026-10-19")

    assert (week["energy_kwh"], day["energy_kwh"], four_weeks["energy_kwh"]) == ("14.700", "2.100", "58.800")
    assert week["window"]["start"] == "2026-10-18T17:00:00Z" and week["window"]["is_current"] is False
    assert week["coverage"] == {"minimum": "1.000", "concurrent": "1.000", "allocated_estimate": False}
    assert [(row["name"], row["energy_kwh"], row["share_percent"]) for row in week["assets"]] == [
        ("Kulkas", "8.400", "57.14"),
        ("TV", "2.520", "17.14"),
        ("Pompa Air", "2.100", "14.29"),
        ("Router", "1.680", "11.43"),
    ]
    assert week["scope"]["valid"] and week["origins"] == ["simulated"]
    assert week["latest_measurement_at"] == "2026-10-25T17:00:00Z"
    _golden("summary-h-week.json", week)


async def test_industry_week_and_measured_zero_sunday(client: AsyncClient) -> None:
    """
    Condition:
    - AT-06 on i-base: 19–25 Oktober, then Sunday 25 Oktober.

    Expected:
    - 144.000 kWh with Oven 72.000 (50.00%); Sunday is 0.000 kWh with full coverage and no percentages.
    """
    session = await start_demo(client, "i-base")

    week = await summary(client, session, **WEEK)
    sunday = await summary(client, session, start_date="2026-10-25", end_date="2026-10-25")

    assert week["energy_kwh"] == "144.000"
    assert (week["assets"][0]["name"], week["assets"][0]["energy_kwh"], week["assets"][0]["share_percent"]) == (
        "Oven",
        "72.000",
        "50.00",
    )
    assert (sunday["energy_kwh"], sunday["coverage"]["minimum"]) == ("0.000", "1.000")
    assert {row["share_percent"] for row in sunday["assets"]} == {None}
    _golden("summary-i-week.json", week)


async def test_today_on_the_virtual_monday_is_empty_not_zero(client: AsyncClient) -> None:
    """
    Condition:
    - FX-NOW: h-base today at virtual Monday 00.00.

    Expected:
    - Energy is null with reason no_data, and nothing has elapsed.
    """
    body = await summary(client, await start_demo(client), preset="today")

    assert (body["energy_kwh"], body["energy_unavailable_reason"]) == (None, "no_data")
    assert body["window"]["effective_end"] == body["window"]["start"]
    assert body["coverage"]["minimum"] is None


async def test_current_period_excludes_later_rows(client: AsyncClient) -> None:
    """
    Condition:
    - FX-CUR at 21 Oktober 12.00: today and this week for h-current and i-current.

    Expected:
    - H 0.870 and 5.070 kWh; I 13.000 and 61.000 kWh; the window is current.
    """
    household, industry = await start_demo(client, "h-current"), await start_demo(client, "i-current")

    h_today = await summary(client, household, preset="today")
    h_week = await summary(client, household, preset="this_week")
    i_today = await summary(client, industry, preset="today")
    i_week = await summary(client, industry, preset="this_week")

    assert (h_today["energy_kwh"], h_week["energy_kwh"]) == ("0.870", "5.070")
    assert (i_today["energy_kwh"], i_week["energy_kwh"]) == ("13.000", "61.000")
    assert h_today["window"]["is_current"] and h_today["coverage"]["minimum"] == "1.000"


async def test_scope_refuses_double_counting(client: AsyncClient) -> None:
    """
    Condition:
    - h-scope: Meter utama contains Kulkas, Router and TV; Kulkas has two unresolved sources; Pompa Air's
      overlap with the meter is unknown.

    Expected:
    - The default total is refused with every reason; Kulkas shows each source's 2.000 kWh, never 4; the meter
      alone reads 10.000 kWh; meter plus Pompa refuses only the total and keeps Pompa's 0.300 kWh.
    """
    session = await start_demo(client, "h-scope")

    default = await summary(client, session, start_date="2026-10-24", end_date="2026-10-25")
    meter_id = _by_name(default)["Meter utama"]["asset_id"]
    meter = await summary(
        client, session, f"/api/v1/assets/{meter_id}/summary", start_date="2026-10-25", end_date="2026-10-25"
    )
    parent_child = await _selection(session["site_id"], ["Meter utama", "TV"], date(2026, 10, 25), date(2026, 10, 25))
    unknown = await _selection(session["site_id"], ["Meter utama", "Pompa Air"], date(2026, 10, 25), date(2026, 10, 25))

    assert (default["energy_kwh"], default["energy_unavailable_reason"]) == (None, "scope_conflict")
    assert sorted(issue["type"] for issue in default["scope"]["issues"]) == [
        "parent_child", "parent_child", "parent_child", "source_conflict", "unknown_overlap",
    ]  # fmt: skip
    kulkas = _by_name(default)["Kulkas"]
    assert (kulkas["energy_kwh"], kulkas["energy_unavailable_reason"]) == (None, "source_conflict")
    assert [source["energy_kwh"] for source in kulkas["conflict_sources"]] == ["2.000", "2.000"]
    assert {row["share_percent"] for row in default["assets"]} == {None}
    assert meter["energy_kwh"] == "10.000" and meter["scope"]["valid"]
    assert parent_child["energy_kwh"] is None
    assert (
        parent_child["scope"]["issues"][0]["message"]
        == "Meter utama sudah mencakup TV. Keduanya tidak dapat dijumlahkan."
    )
    assert unknown["energy_kwh"] is None
    assert [issue["type"] for issue in unknown["scope"]["issues"]] == ["unknown_overlap"]
    assert _by_name(unknown)["Pompa Air"]["energy_kwh"] == "0.300"
    _golden("summary-scope.json", default)


async def test_partial_coverage_is_never_averaged_away(client: AsyncClient) -> None:
    """
    Condition:
    - AT-19 on h-learning-partial: Pompa Air lacks 24–25 Oktober, Kulkas lacks 22 Oktober 14.00–16.00.

    Expected:
    - Per-asset coverage and gaps, minimum and concurrent coverage are all reported; the total stays available.
    """
    body = await summary(client, await start_demo(client, "h-learning-partial"), **WEEK)
    rows = _by_name(body)

    assert rows["Pompa Air"]["gaps"] == [{"start": "2026-10-23T17:00:00Z", "end": "2026-10-25T17:00:00Z"}]
    assert rows["Kulkas"]["gaps"] == [{"start": "2026-10-22T07:00:00Z", "end": "2026-10-22T09:00:00Z"}]
    assert rows["Pompa Air"]["coverage"] == "0.714"
    assert body["coverage"]["minimum"] == "0.714"
    assert body["coverage"]["concurrent"] == "0.702"
    assert body["energy_kwh"] is not None


async def test_measured_zero_gives_no_percentages(client: AsyncClient) -> None:
    """
    Condition:
    - AT-21 on h-zero: every interval recorded 0 Wh.

    Expected:
    - A valid 0.000 kWh total with full coverage and no percentage anywhere.
    """
    body = await summary(client, await start_demo(client, "h-zero"), **WEEK)

    assert (body["energy_kwh"], body["coverage"]["minimum"]) == ("0.000", "1.000")
    assert {row["share_percent"] for row in body["assets"]} == {None}


async def _empty_site_with(client: AsyncClient, *names: str) -> tuple[dict, dict[str, UUID]]:
    session = await start_demo(client, "empty")
    return session, {name: await make_asset(UUID(session["site_id"]), name) for name in names}


async def _source(site_id: str, kind: MeasurementKind) -> SourceModel:
    rows = await execute(
        "INSERT INTO sources (id, site_id, label, origin, measurement_kind, cadence_seconds)"
        " VALUES (gen_random_uuid(), :site, 'Uji', 'simulated', :kind, 3600) RETURNING id",
        site=UUID(site_id),
        kind=kind.value,
    )
    return SourceModel(
        id=rows[0][0],
        site_id=UUID(site_id),
        label="Uji",
        origin=SourceOrigin.SIMULATED,
        measurement_kind=kind,
        cadence_seconds=3600,
        resolution_mwh=None,
        transport_status=TransportStatus.NONE,
    )


async def _bind(site_id: str, asset: UUID, source: UUID, start: datetime, end: datetime | None = None) -> None:
    await execute(
        "INSERT INTO bindings (id, site_id, source_id, asset_id, effective_from, effective_to, authoritative)"
        " VALUES (gen_random_uuid(), :site, :source, :asset, :start, :end, true)",
        site=UUID(site_id),
        source=source,
        asset=asset,
        start=start,
        end=end,
    )


async def _ingest(source: SourceModel, readings: list[ReadingInput]) -> None:
    async with get_session_factory()() as session:
        site = await SqlAlchemySiteRepository(session).lock(source.site_id)
        assert site is not None
        await build_ingest_service(session).ingest(site, source, readings, received_at=datetime.now(UTC))
        await session.commit()


def _hour(start: datetime, wh: int) -> ReadingInput:
    return ReadingInput(value=Decimal(wh), unit="Wh", interval_start=start, interval_end=start + timedelta(hours=1))


async def test_unrelated_meters_are_not_assumed_disjoint(client: AsyncClient) -> None:
    """
    Condition:
    - Two assets with readings and no relation between them.

    Expected:
    - Each value is visible, but the combined total and percentages are withheld as unconfirmed.
    """
    session, assets = await _empty_site_with(client, "Meter A", "Meter B")
    day = datetime(2026, 10, 18, 17, tzinfo=UTC)
    for name, asset in assets.items():
        source = await _source(session["site_id"], MeasurementKind.INTERVAL_ENERGY)
        await _bind(session["site_id"], asset, source.id, day)
        await _ingest(source, [_hour(day + timedelta(hours=i), 100 if name == "Meter A" else 50) for i in range(24)])

    body = await summary(client, session, start_date="2026-10-19", end_date="2026-10-19")

    assert (body["energy_kwh"], body["energy_unavailable_reason"]) == (None, "scope_conflict")
    assert [issue["type"] for issue in body["scope"]["issues"]] == ["unconfirmed"]
    assert {row["name"]: row["energy_kwh"] for row in body["assets"]} == {"Meter A": "2.400", "Meter B": "1.200"}
    assert {row["share_percent"] for row in body["assets"]} == {None}


async def test_binding_change_inside_an_interval_is_allocated_and_conserved(client: AsyncClient) -> None:
    """
    Condition:
    - One asset switches source at 10.30 inside hourly readings of 100 Wh from both sources.

    Expected:
    - Each source contributes its own half of its 10.00–11.00 reading; the day stays 2.400 kWh, flagged estimate.
    """
    session, assets = await _empty_site_with(client, "Kulkas")
    day = datetime(2026, 10, 18, 17, tzinfo=UTC)
    switch = day + timedelta(hours=10, minutes=30)
    old = await _source(session["site_id"], MeasurementKind.INTERVAL_ENERGY)
    new = await _source(session["site_id"], MeasurementKind.INTERVAL_ENERGY)
    await _bind(session["site_id"], assets["Kulkas"], old.id, day, switch)
    await _bind(session["site_id"], assets["Kulkas"], new.id, switch)
    for source in (old, new):
        await _ingest(source, [_hour(day + timedelta(hours=i), 100) for i in range(24)])

    body = await summary(client, session, start_date="2026-10-19", end_date="2026-10-19")

    assert body["energy_kwh"] == "2.400"
    assert body["coverage"] == {"minimum": "1.000", "concurrent": "1.000", "allocated_estimate": True}


async def test_long_counter_span_counts_whole_but_not_narrower(client: AsyncClient) -> None:
    """
    Condition:
    - Counter readings at 19 Oktober 22.00 and 20 Oktober 02.00, a four-hour span on an hourly source.

    Expected:
    - The two-day read includes its 0.040 kWh; the single day refuses it as insufficient resolution.
    """
    session, assets = await _empty_site_with(client, "Pompa")
    source = await _source(session["site_id"], MeasurementKind.COUNTER)
    start = datetime(2026, 10, 19, 15, tzinfo=UTC)
    await _bind(session["site_id"], assets["Pompa"], source.id, start - timedelta(days=1))
    await _ingest(
        source,
        [
            ReadingInput(value=Decimal(0), unit="Wh", measured_at=start),
            ReadingInput(value=Decimal(40), unit="Wh", measured_at=start + timedelta(hours=4)),
        ],
    )

    both = await summary(client, session, start_date="2026-10-19", end_date="2026-10-20")
    first = await summary(client, session, start_date="2026-10-19", end_date="2026-10-19")

    assert both["energy_kwh"] == "0.040"
    assert (first["energy_kwh"], first["energy_unavailable_reason"]) == (None, "insufficient_resolution")
    assert first["assets"][0]["energy_unavailable_reason"] == "insufficient_resolution"


async def test_site_timezone_sets_the_local_calendar(client: AsyncClient) -> None:
    """
    Condition:
    - The site's timezone changes to Asia/Makassar.

    Expected:
    - The same local day starts an hour earlier in UTC.
    """
    session = await start_demo(client)
    await client.patch(
        f"/api/v1/sites/{session['site_id']}", json={"timezone": "Asia/Makassar"}, headers=session["auth"]
    )

    body = await summary(client, session, start_date="2026-10-19", end_date="2026-10-19")

    assert (body["window"]["start"], body["window"]["timezone"]) == ("2026-10-18T16:00:00Z", "Asia/Makassar")


@pytest.mark.parametrize(
    ("params", "code"),
    [
        ({"start_date": "2025-10-01", "end_date": "2026-10-02"}, "RANGE_TOO_LARGE"),
        ({"start_date": "2026-10-20", "end_date": "2026-10-19"}, "BAD_REQUEST"),
        ({}, "BAD_REQUEST"),
        ({"preset": "today", "start_date": "2026-10-19", "end_date": "2026-10-19"}, "BAD_REQUEST"),
    ],
)
async def test_invalid_periods_are_refused(client: AsyncClient, params: dict, code: str) -> None:
    """
    Condition:
    - 367 days, a reversed range, no period, or both forms at once.

    Expected:
    - Each is refused with its code before any data is read.
    """
    session = await start_demo(client, "empty")

    response = await client.get(f"/api/v1/sites/{session['site_id']}/summary", params=params, headers=session["auth"])

    assert (response.status_code, response.json()["error"]["code"]) == (400, code)
