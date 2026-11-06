"""Matched baseline over seeded demo workspaces (AT-16, AT-17 numbers, AT-19, AT-20, AT-21)."""

import pytest
from httpx import AsyncClient

from tests.integration.conftest import execute, start_demo

pytestmark = pytest.mark.integration

WEEK = {"start_date": "2026-10-19", "end_date": "2026-10-25"}


async def _asset(client: AsyncClient, session: dict, name: str) -> str:
    items = (await client.get(f"/api/v1/sites/{session['site_id']}/assets", headers=session["auth"])).json()["items"]
    return next(item["id"] for item in items if item["name"] == name)


async def _compare(client: AsyncClient, session: dict, name: str, **params: str) -> dict:
    asset = await _asset(client, session, name)
    response = await client.get(f"/api/v1/assets/{asset}/comparison", params=params or WEEK, headers=session["auth"])
    assert response.status_code == 200, response.text
    return response.json()


async def test_household_change_numbers(client: AsyncClient) -> None:
    """
    Condition:
    - h-change: TV over 19–25 Oktober against three prior weeks.

    Expected:
    - Mask energy 3.920 against a 2.520 median, +1.400 kWh (55.56%), MAD 0, resolution 0.168, full mask.
    """
    body = await _compare(client, await start_demo(client, "h-change"), "TV")

    assert body["state"] == "comparable"
    assert (body["current"]["mask_kwh"], body["baseline_kwh"], body["delta_kwh"]) == ("3.920", "2.520", "1.400")
    assert (body["percent"], body["mad_kwh"], body["resolution_kwh"]) == ("55.56", "0.000", "0.168")
    assert body["mask_coverage"] == "1.000"
    assert [(w["weeks_before"], w["mask_kwh"], w["eligible"]) for w in body["historical"]] == [
        (1, "2.520", True),
        (2, "2.520", True),
        (3, "2.520", True),
    ]
    assert body["historical"][0]["start_date"] == "2026-10-12"
    assert body["common_mask"] == [{"start": "2026-10-18T17:00:00Z", "end": "2026-10-25T17:00:00Z"}]


async def test_base_and_industry_change_baselines(client: AsyncClient) -> None:
    """
    Condition:
    - TV on h-base, and Kompresor on i-change without a schedule.

    Expected:
    - No change for TV; Kompresor +3.000 kWh against 36.000, left to the insight rule to judge.
    """
    tv = await _compare(client, await start_demo(client), "TV")
    kompresor = await _compare(client, await start_demo(client, "i-change"), "Kompresor")

    assert (tv["state"], tv["delta_kwh"], tv["percent"]) == ("comparable", "0.000", "0.00")
    assert (kompresor["baseline_kwh"], kompresor["delta_kwh"]) == ("36.000", "3.000")


async def test_running_period_uses_the_same_elapsed_duration(client: AsyncClient) -> None:
    """
    Condition:
    - h-current today at 12.00.

    Expected:
    - Prior windows stop 12 hours after their start too, so Kulkas compares 0.600 with 0.600.
    """
    body = await _compare(client, await start_demo(client, "h-current"), "Kulkas", preset="today")

    assert body["state"] == "comparable"
    assert body["historical"][0]["end"] == "2026-10-14T05:00:00Z"
    assert (body["current"]["mask_kwh"], body["baseline_kwh"]) == ("0.600", "0.600")


async def test_learning_and_missing_data_give_no_verdict(client: AsyncClient) -> None:
    """
    Condition:
    - AT-16 h-learning-partial over the week, then Pompa Air on 24 Oktober with no data.

    Expected:
    - The week is learning with one eligible window and the measured total kept; the empty day is not comparable.
    """
    session = await start_demo(client, "h-learning-partial")

    learning = await _compare(client, session, "Kulkas")
    missing = await _compare(client, session, "Pompa Air", start_date="2026-10-24", end_date="2026-10-24")

    assert learning["state"] == "learning" and "tersedia 1" in learning["reason"]
    assert learning["baseline_kwh"] is None and learning["current"]["measured_kwh"] == "8.300"
    assert missing["state"] == "not_comparable"


async def test_unknown_resolution_is_descriptive(client: AsyncClient) -> None:
    """
    Condition:
    - AT-20: TV's source resolution becomes unknown.

    Expected:
    - A descriptive comparison with its numbers, and no resolution.
    """
    session = await start_demo(client, "h-change")
    await execute(
        "UPDATE sources SET resolution_mwh = NULL WHERE site_id = :site AND id IN"
        " (SELECT b.source_id FROM bindings b JOIN assets a ON a.id = b.asset_id WHERE a.name = 'TV')",
        site=session["site_id"],
    )

    body = await _compare(client, session, "TV")

    assert (body["state"], body["delta_kwh"], body["resolution_kwh"]) == ("descriptive", "1.400", None)


async def test_zero_baseline_has_no_percent(client: AsyncClient) -> None:
    """
    Condition:
    - AT-21 on h-zero.

    Expected:
    - Baseline and change are 0.000 and percent is null.
    """
    body = await _compare(client, await start_demo(client, "h-zero"), "TV")

    assert (body["baseline_kwh"], body["delta_kwh"], body["percent"]) == ("0.000", "0.000", None)


async def test_unavailable_cases(client: AsyncClient) -> None:
    """
    Condition:
    - Kulkas with unresolved sources on h-scope, a period of eight days, and today at virtual Monday 00.00.

    Expected:
    - Each is unavailable with its reason.
    """
    scope, base = await start_demo(client, "h-scope"), await start_demo(client)

    conflict = await _compare(client, scope, "Kulkas")
    long = await _compare(client, base, "TV", start_date="2026-10-18", end_date="2026-10-25")
    empty = await _compare(client, base, "TV", preset="today")

    assert (conflict["state"], long["state"], empty["state"]) == ("unavailable", "unavailable", "unavailable")
    assert "sumber acuan" in conflict["reason"] and "7 hari" in long["reason"]


async def test_daylight_saving_slots_align_by_local_time(client: AsyncClient) -> None:
    """
    Condition:
    - The site moves to Europe/Berlin; the week ends with the 25-hour day of 25 Oktober.

    Expected:
    - Slots align by local time: the repeated hour has no match and leaves the mask, which stays valid.
    """
    session = await start_demo(client)
    await client.patch(
        f"/api/v1/sites/{session['site_id']}", json={"timezone": "Europe/Berlin"}, headers=session["auth"]
    )

    body = await _compare(client, session, "Router")

    assert body["state"] == "comparable"
    assert body["mask_coverage"] != "1.000"
    assert len(body["common_mask"]) == 2


async def test_history_gains_a_reference_series_on_the_same_mask(client: AsyncClient) -> None:
    """
    Condition:
    - h-change TV daily over the selected week.

    Expected:
    - Each day carries 0.560 kWh on the mask against a 0.360 reference, beside the full energy.
    """
    session = await start_demo(client, "h-change")
    tv = await _asset(client, session, "TV")

    body = (await client.get(f"/api/v1/assets/{tv}/measurements", params=WEEK, headers=session["auth"])).json()

    assert body["comparison_state"] == "comparable"
    assert {(b["energy_kwh"], b["comparison_kwh"], b["reference_kwh"]) for b in body["buckets"]} == {
        ("0.560", "0.560", "0.360")
    }
