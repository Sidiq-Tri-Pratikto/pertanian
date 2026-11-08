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
from tests.integration.conftest import (
    execute,
    make_asset,
    make_binding,
    make_source,
    scope_confirmation,
    scope_path,
    start_demo,
    summary,
)

pytestmark = pytest.mark.integration
DAY = {"start_date": "2026-10-25", "end_date": "2026-10-25"}

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
        service = EnergyService(SqlAlchemyEnergyRepository(session), demo.sites, demo.assets, demo.selections)
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
    week = await summary(client, session, **WEEK)
    assert week["window"]["timezone"] == "Asia/Jakarta"
    assert (week["energy_kwh"], _by_name(week)["Meter utama"]["energy_kwh"]) == (None, "70.000")
    assert {row["share_percent"] for row in week["assets"]} == {None}
    assert {row["state"] for row in week["source_freshness"] if row["asset_id"] == kulkas["asset_id"]} == {"unknown"}
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
    assert body["energy_kwh"] == "14.000"


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


@pytest.mark.parametrize("scenario", ["h-base", "h-scope", "h-learning-partial"])
async def test_asset_summary_row_matches_the_site_summary_row(client: AsyncClient, scenario: str) -> None:
    """
    Condition:
    - One seeded demo workspace at its initial period, read through both summary routes.

    Expected:
    - Every asset's row from its own summary equals its row from the site summary, apart from ``share_percent``.
    """
    session = await start_demo(client, scenario)
    initial = session["initial_period"]
    period = {"start_date": initial["start_date"], "end_date": initial["end_date"]}
    site = await summary(client, session, **period)

    assert site["assets"]
    for row in site["assets"]:
        own = await summary(client, session, f"/api/v1/assets/{row['asset_id']}/summary", **period)
        assert len(own["assets"]) == 1
        assert {**own["assets"][0], "share_percent": None} == {**row, "share_percent": None}


async def test_stale_source_freshness_is_independent_of_report_window(client: AsyncClient) -> None:
    """Router freshness uses the site clock and the owned stream, even for an earlier report."""
    session = await start_demo(client, "h-stale-offline")
    week = await summary(client, session, **WEEK)
    earlier = await summary(client, session, start_date="2026-10-19", end_date="2026-10-19")
    router = _by_name(week)["Router"]
    stale = [source for source in week["source_freshness"] if source["state"] == "stale"]
    assert week["energy_kwh"] == "14.640"
    assert len(stale) == 1
    assert stale[0]["asset_id"] == router["asset_id"]
    assert stale[0]["last_capture_at"] == "2026-10-25T11:00:00Z"
    assert stale[0]["cadence_seconds"] == 3600 and stale[0]["policy_version"] == 1
    assert earlier["source_freshness"] == week["source_freshness"]
    path = f"/api/v1/assets/{router['asset_id']}/summary"
    owned = await client.get(path, params=WEEK, headers=session["auth"])
    assert owned.status_code == 200 and owned.json()["source_freshness"] == stale
    stranger = await start_demo(client)
    assert (await client.get(path, params=WEEK, headers=stranger["auth"])).status_code == 404


async def test_current_binding_excludes_old_future_and_long_gap_captures(client: AsyncClient) -> None:
    """Latest freshness belongs to the effective authority, never an older binding or unusable capture."""
    session = await start_demo(client, "h-stale-offline")
    report = await summary(client, session, **WEEK)
    site_id = UUID(session["site_id"])
    asset_id = UUID(_by_name(report)["Router"]["asset_id"])
    old_source = next(row for row in report["source_freshness"] if row["asset_id"] == str(asset_id))
    source_id = UUID(old_source["source_id"])

    # Replace the newest current row with a long-gap revision. Its superseded valid version cannot qualify.
    await execute(
        "INSERT INTO measurements (source_id, identity_key, revision, kind, interval_start, interval_end,"
        " energy_mwh, quality, received_at) SELECT source_id, identity_key, revision + 1, kind,"
        " interval_start, interval_end, energy_mwh, 'long_gap', now() FROM current_measurements"
        " WHERE source_id = :source AND interval_end = '2026-10-25T11:00:00Z'",
        source=source_id,
    )
    later = await summary(client, session, **WEEK)
    router = next(row for row in later["source_freshness"] if row["asset_id"] == str(asset_id))
    assert router["last_capture_at"] == "2026-10-25T10:00:00Z"

    boundary = datetime(2026, 10, 25, 12, tzinfo=UTC)
    await execute(
        "UPDATE bindings SET effective_to = :boundary WHERE asset_id = :asset",
        boundary=boundary,
        asset=asset_id,
    )
    replacement = await make_source(site_id, "Router baru")
    await execute(
        "UPDATE sources SET cadence_seconds = 900, transport_status = 'simulated_live' WHERE id = :source",
        source=replacement,
    )
    await make_binding(site_id, asset_id, replacement, boundary.isoformat())
    await execute(
        "INSERT INTO measurements (source_id, identity_key, revision, kind, interval_start, interval_end,"
        " energy_mwh, quality, received_at) VALUES"
        " (:source, 'prior', 1, 'interval_energy',"
        " '2026-10-25T11:45:00Z', '2026-10-25T12:00:00Z', 5, 'valid', now()),"
        " (:source, 'future', 1, 'interval_energy',"
        " '2026-10-25T17:00:00Z', '2026-10-25T17:15:00Z', 5, 'valid', now())",
        source=replacement,
    )
    rebound = await summary(client, session, **WEEK)
    router_rows = [row for row in rebound["source_freshness"] if row["asset_id"] == str(asset_id)]
    assert len(router_rows) == 1
    assert router_rows[0]["source_id"] == str(replacement)
    assert router_rows[0]["state"] == "unknown" and router_rows[0]["last_capture_at"] is None


async def test_saved_scope_preserves_archived_ids_and_never_substitutes_new_assets(client: AsyncClient) -> None:
    """Archiving excludes a stored member from totals without rewriting confirmed membership."""
    demo = await start_demo(client, "h-scope")
    path, auth = scope_path(demo["site_id"]), demo["auth"]
    original = await summary(client, demo, **DAY)
    meter = _by_name(original)["Meter utama"]["asset_id"]
    child = _by_name(original)["TV"]["asset_id"]
    proposal = {"selected_asset_ids": [meter], "period": DAY}
    preview = (await client.post(f"{path}/preview", headers=auth, json=proposal)).json()
    saved = await client.put(path, headers=auth, json=scope_confirmation(proposal, preview))
    assert saved.status_code == 200, saved.text

    asset_path = f"/api/v1/assets/{meter}"
    archive = await client.patch(asset_path, headers=auth, json={"archived": True})
    assert archive.status_code == 200, archive.text
    new_asset = str(await make_asset(UUID(demo["site_id"]), "Baru"))
    archived = await summary(client, demo, **DAY)
    reasons = {row["asset_id"]: row["reason"] for row in archived["scope"]["excluded"]}
    assert archived["energy_kwh"] is None and not archived["scope"]["included"]
    assert archived["selection_revision"] == 1
    assert reasons[meter] == "archived" and reasons[new_asset] == reasons[child] == "not_selected"
    confirmed = (await client.get(path, headers=auth)).json()
    assert confirmed["selected_asset_ids"] == [meter] and confirmed["binding_revision"] == archived["binding_revision"]
    preview = (await client.post(f"{path}/preview", headers=auth, json=proposal)).json()
    repeated = await client.put(path, headers=auth, json=scope_confirmation(proposal, preview))
    assert repeated.status_code == 200 and repeated.json() == confirmed

    assert (await client.patch(f"/api/v1/assets/{child}", headers=auth, json={"archived": True})).status_code == 200
    rejected = await client.post(
        f"{path}/preview", headers=auth, json=proposal | {"selected_asset_ids": [meter, child]}
    )
    assert rejected.status_code == 400 and rejected.json()["error"]["code"] == "BAD_REQUEST"

    restored = await client.patch(asset_path, headers=auth, json={"archived": False})
    assert restored.status_code == 200, restored.text
    result = await summary(client, demo, **DAY)
    assert result["energy_kwh"] == "10.000" and result["selection_revision"] == 1
    assert [row["asset_id"] for row in result["scope"]["included"]] == [meter]
    assert {row["name"] for row in result["assets"]} == {"Meter utama"}


async def test_stale_saved_parent_keeps_scope_window_and_missing_state(client: AsyncClient) -> None:
    """A stale main meter keeps its historical total and has no fallback in a missing current period."""
    demo = await start_demo(client, "h-scope")
    path, auth = scope_path(demo["site_id"]), demo["auth"]
    original = await summary(client, demo, **DAY)
    meter = _by_name(original)["Meter utama"]["asset_id"]
    proposal = {"selected_asset_ids": [meter], "period": DAY}
    preview = (await client.post(f"{path}/preview", headers=auth, json=proposal)).json()
    saved = await client.put(path, headers=auth, json=scope_confirmation(proposal, preview))
    assert saved.status_code == 200, saved.text
    await execute(
        "UPDATE sources SET transport_status = 'simulated_live' WHERE id IN "
        "(SELECT source_id FROM bindings WHERE asset_id = CAST(:meter AS uuid))",
        meter=meter,
    )
    await execute(
        "UPDATE sites SET virtual_now = virtual_now + interval '6 hours' WHERE id = :id", id=UUID(demo["site_id"])
    )

    past = await summary(client, demo, **DAY)
    current = await summary(client, demo, preset="today")
    assert past["energy_kwh"] == "10.000" and past["coverage"]["minimum"] == "1.000"
    assert past["window"] == preview["summary"]["window"]
    assert current["window"]["start_date"] == "2026-10-26"
    assert current["window"]["timezone"] == "Asia/Jakarta"
    assert current["window"]["effective_end"] == "2026-10-25T23:00:00Z"
    assert current["energy_kwh"] is None and current["energy_unavailable_reason"] == "no_data"
    assert current["coverage"]["minimum"] == "0.000"
    for body in (past, current):
        assert [row["asset_id"] for row in body["scope"]["included"]] == [meter]
        assert [row["name"] for row in body["assets"]] == ["Meter utama"]
        (freshness,) = body["source_freshness"]
        assert freshness["state"] == "stale" and freshness["asset_id"] == meter
        assert freshness["last_capture_at"] == "2026-10-25T17:00:00Z"
    assert current["assets"][0]["share_percent"] is None
