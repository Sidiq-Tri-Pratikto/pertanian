"""History buckets over seeded demo workspaces: reconciliation, states, DST and limits."""

from collections.abc import Callable
from decimal import Decimal
from uuid import UUID

import pytest
from httpx import AsyncClient

from tests.integration.conftest import (
    execute,
    make_switchable_scope_site,
    scope_confirmation,
    scope_path,
    start_demo,
    summary,
)

pytestmark = pytest.mark.integration

WEEK = {"start_date": "2026-10-19", "end_date": "2026-10-25"}


async def _asset(client: AsyncClient, session: dict, name: str) -> str:
    items = (await client.get(f"/api/v1/sites/{session['site_id']}/assets", headers=session["auth"])).json()["items"]
    return next(item["id"] for item in items if item["name"] == name)


async def _history(client: AsyncClient, session: dict, asset: str, **params: str) -> dict:
    response = await client.get(f"/api/v1/assets/{asset}/measurements", params=params, headers=session["auth"])
    assert response.status_code == 200, response.text
    return response.json()


async def test_daily_buckets_reconcile_with_the_summary(client: AsyncClient) -> None:
    """
    Condition:
    - Kulkas on h-base and Oven on i-base, daily over 19–25 Oktober.

    Expected:
    - Seven 1.200 kWh Kulkas buckets sum to its 8.400 kWh; Oven's buckets sum to 72.000 kWh; the highest Oven
      bucket is the earliest of the tied output days.
    """
    household, industry = await start_demo(client), await start_demo(client, "i-base")
    kulkas, oven = await _asset(client, household, "Kulkas"), await _asset(client, industry, "Oven")

    k = await _history(client, household, kulkas, **WEEK)
    o = await _history(client, industry, oven, **WEEK)
    k_summary = await summary(client, household, f"/api/v1/assets/{kulkas}/summary", **WEEK)
    o_summary = await summary(client, industry, f"/api/v1/assets/{oven}/summary", **WEEK)

    assert [b["energy_kwh"] for b in k["buckets"]] == ["1.200"] * 7
    assert {b["state"] for b in k["buckets"]} == {"measured"}
    assert str(sum(Decimal(b["energy_kwh"]) for b in k["buckets"])) == k_summary["energy_kwh"] == "8.400"
    assert str(sum(Decimal(b["energy_kwh"]) for b in o["buckets"])) == o_summary["energy_kwh"] == "72.000"
    assert o["highest_bucket"] == {"start": "2026-10-18T17:00:00Z"}
    assert (k["origins"], k["resolution_mwh"], k["bucket"]) == (["simulated"], 1000, "day")


async def test_hourly_day_has_local_labels(client: AsyncClient) -> None:
    """
    Condition:
    - Pompa Air hourly on 19 Oktober in Jakarta.

    Expected:
    - 24 buckets labelled 00:00 to 23:00 at +07:00, with 0.150 kWh at 06:00 and 18:00 and measured zeros between.
    """
    session = await start_demo(client)
    pompa = await _asset(client, session, "Pompa Air")

    body = await _history(client, session, pompa, start_date="2026-10-19", end_date="2026-10-19", bucket="hour")

    assert len(body["buckets"]) == 24
    assert {b["utc_offset"] for b in body["buckets"]} == {"+07:00"}
    assert [b["local_time"] for b in body["buckets"]][:2] == ["00:00", "01:00"]
    assert {b["local_time"]: b["energy_kwh"] for b in body["buckets"] if b["energy_kwh"] != "0.000"} == {
        "06:00": "0.150",
        "18:00": "0.150",
    }
    assert body["highest_bucket"] == {"start": "2026-10-18T23:00:00Z"}


async def test_missing_partial_zero_and_future_stay_distinct(client: AsyncClient) -> None:
    """
    Condition:
    - Pompa Air without data on 24 Oktober, Kulkas missing two hours on 22 Oktober, h-zero, and h-current hours.

    Expected:
    - Missing is null with state missing; partial keeps its recorded value and coverage; zero is measured;
      hours after 12.00 are future.
    """
    learning = await start_demo(client, "h-learning-partial")
    zero = await start_demo(client, "h-zero")
    current = await start_demo(client, "h-current")
    pompa, kulkas = await _asset(client, learning, "Pompa Air"), await _asset(client, learning, "Kulkas")

    missing = (await _history(client, learning, pompa, start_date="2026-10-24", end_date="2026-10-24"))["buckets"][0]
    partial = (await _history(client, learning, kulkas, start_date="2026-10-22", end_date="2026-10-22"))["buckets"][0]
    measured_zero = (
        await _history(client, zero, await _asset(client, zero, "TV"), start_date="2026-10-19", end_date="2026-10-19")
    )["buckets"][0]
    hours = (await _history(client, current, await _asset(client, current, "Kulkas"), preset="today", bucket="hour"))[
        "buckets"
    ]

    assert (missing["energy_kwh"], missing["state"], missing["coverage"]) == (None, "missing", "0.000")
    assert (partial["energy_kwh"], partial["state"], partial["coverage"]) == ("1.100", "partial", "0.916")
    assert (measured_zero["energy_kwh"], measured_zero["state"]) == ("0.000", "measured")
    assert [b["state"] for b in hours].count("measured") == 12
    assert [b["state"] for b in hours][12:] == ["future"] * 12
    assert {b["energy_kwh"] for b in hours[12:]} == {None}


async def test_unresolved_sources_make_buckets_unavailable(client: AsyncClient) -> None:
    """
    Condition:
    - Kulkas on h-scope, with two unresolved sources.

    Expected:
    - Each bucket is unavailable with reason source_conflict and no value; no bucket is highest.
    """
    session = await start_demo(client, "h-scope")

    body = await _history(client, session, await _asset(client, session, "Kulkas"), **WEEK)

    assert {(b["state"], b["unavailable_reason"], b["energy_kwh"]) for b in body["buckets"]} == {
        ("unavailable", "source_conflict", None)
    }
    assert body["highest_bucket"] is None

    meter = await _history(client, session, await _asset(client, session, "Meter utama"), **WEEK)
    assert meter["window"]["timezone"] == "Asia/Jakarta"
    assert {(bucket["state"], bucket["energy_kwh"]) for bucket in meter["buckets"]} == {("measured", "10.000")}


async def test_daylight_saving_days_have_their_real_hours(client: AsyncClient) -> None:
    """
    Condition:
    - The site moves to Europe/Berlin: hourly buckets on 25 Oktober 2026 (clocks go back) and 29 Maret 2026.

    Expected:
    - 25 and 23 buckets with unique UTC starts; the repeated 02:00 appears at +02:00 and then +01:00.
    """
    session = await start_demo(client)
    await client.patch(
        f"/api/v1/sites/{session['site_id']}", json={"timezone": "Europe/Berlin"}, headers=session["auth"]
    )
    router = await _asset(client, session, "Router")

    autumn = (await _history(client, session, router, start_date="2026-10-25", end_date="2026-10-25", bucket="hour"))[
        "buckets"
    ]
    spring = (await _history(client, session, router, start_date="2026-03-29", end_date="2026-03-29", bucket="hour"))[
        "buckets"
    ]

    assert len(autumn) == 25 and len({b["start"] for b in autumn}) == 25
    assert [(b["local_time"], b["utc_offset"]) for b in autumn if b["local_time"] == "02:00"] == [
        ("02:00", "+02:00"),
        ("02:00", "+01:00"),
    ]
    assert len(spring) == 23
    assert {b["state"] for b in spring} == {"missing"}


async def test_bucket_limit_is_enforced_before_reading(client: AsyncClient) -> None:
    """
    Condition:
    - Hourly buckets for 42 days (1,008 buckets) and for 41 days (984).

    Expected:
    - The first is RANGE_TOO_LARGE; the second is served.
    """
    session = await start_demo(client)
    kulkas = await _asset(client, session, "Kulkas")
    path = f"/api/v1/assets/{kulkas}/measurements"

    too_many = await client.get(
        path, params={"start_date": "2026-09-15", "end_date": "2026-10-26", "bucket": "hour"}, headers=session["auth"]
    )
    allowed = await client.get(
        path, params={"start_date": "2026-09-16", "end_date": "2026-10-26", "bucket": "hour"}, headers=session["auth"]
    )

    assert (too_many.status_code, too_many.json()["error"]["code"]) == (400, "RANGE_TOO_LARGE")
    assert allowed.status_code == 200 and len(allowed.json()["buckets"]) == 984


@pytest.mark.parametrize("long_counter", [False, True])
async def test_scope_cutover_preserves_prior_history_and_respects_resolution(
    client: AsyncClient, acting: Callable[[UUID], dict], long_counter: bool
) -> None:
    """A mid-reading source switch allocates supported intervals and refuses long counter fragments."""
    owner, site, asset, old, candidate = await make_switchable_scope_site()
    await execute("UPDATE bindings SET effective_from = '2026-10-23T17:00:00Z' WHERE source_id = :old", old=old)
    await execute(
        "INSERT INTO measurements (source_id, identity_key, kind, interval_start, interval_end, "
        "energy_mwh, quality, received_at) VALUES "
        "(:old, 'earlier', 'interval_energy', '2026-10-23T17:00:00Z', '2026-10-23T18:00:00Z', "
        "3000000, 'valid', now())",
        old=old,
    )
    await execute(
        "UPDATE bindings SET effective_to = '2026-10-24T18:00:00Z' WHERE source_id = :candidate",
        candidate=candidate,
    )
    if long_counter:
        await execute(
            "UPDATE measurements SET kind = 'counter_delta', quality = 'long_gap' WHERE source_id = :candidate",
            candidate=candidate,
        )
    auth = acting(owner)
    site_id, asset_id = str(site), str(asset)
    session = {"site_id": site_id, "auth": auth}
    path = scope_path(site_id)
    period = {"start_date": "2026-10-24", "end_date": "2026-10-25"}
    before = await _history(client, session, asset_id, **period)
    proposal = {
        "selected_asset_ids": [asset_id],
        "period": period,
        "authority_actions": [
            {
                "action": "choose",
                "asset_id": asset_id,
                "source_id": str(candidate),
                "effective_from": "2026-10-24T17:30:00Z",
            }
        ],
    }
    preview = await client.post(f"{path}/preview", headers=auth, json=proposal)
    assert preview.status_code == 200, preview.text
    candidates = preview.json()["candidates"]
    historical = next(row for row in candidates if row["source_id"] == str(candidate))
    assert historical["effective_to"] == "2026-10-24T18:00:00Z"
    assert str(candidate) not in {
        row["source_id"] for row in (await client.get(path, headers=auth)).json()["candidates"]
    }

    saved = await client.put(path, headers=auth, json=scope_confirmation(proposal, preview.json()))
    assert saved.status_code == 200, saved.text
    after = await _history(client, session, asset_id, **period)
    assert before["buckets"][0]["energy_kwh"] == after["buckets"][0]["energy_kwh"] == "3.000"
    assert before["buckets"][1]["energy_kwh"] == "1.000"
    bucket = after["buckets"][1]
    if long_counter:
        assert (bucket["energy_kwh"], bucket["unavailable_reason"]) == (None, "insufficient_resolution")
    else:
        assert bucket["energy_kwh"] == "1.500"
        assert preview.json()["summary"]["coverage"]["allocated_estimate"]
    readings = await execute(
        "SELECT count(*) FROM measurements WHERE source_id IN (:old, :new)", old=old, new=candidate
    )
    assert readings[0][0] == 3
