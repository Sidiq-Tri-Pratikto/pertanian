"""Fixture oracles from PRD §19: FX-01, AT-05, AT-06, FX-CUR and the change variants."""

from collections import defaultdict
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from app.assets.model.models import RelationKind
from app.core.errors.base import NotFoundError
from app.demo.fixtures import FIXTURE_START, NOW_CURRENT, ReadingSpec
from app.demo.scenarios import SCENARIOS, build_scenario

ZONE = ZoneInfo("Asia/Jakarta")


def _wh(readings: tuple[ReadingSpec, ...], first: date, last: date, until: datetime | None = None) -> int:
    """Plain integer sum of whole readings whose local date is in range and that end by ``until``."""
    return sum(
        r.wh for r in readings if first <= r.start.astimezone(ZONE).date() <= last and (until is None or r.end <= until)
    )


@pytest.mark.parametrize("scenario_id", ["h-base", "i-base"])
def test_fixtures_have_exact_shape(scenario_id: str) -> None:
    """
    Condition:
    - Fixture H or I.

    Expected:
    - 2,688 hourly rows of integer Wh over four pairwise-disjoint assets, from 2026-09-28 00.00 WIB to
      2026-10-26 00.00 exclusive, with explicit zero hours, simulated origin and no AC.
    """
    plan = build_scenario(scenario_id)

    assert len(plan.readings) == 2688
    assert len(plan.assets) == 4
    assert {r.end - r.start for r in plan.readings} == {timedelta(hours=1)}
    assert min(r.start for r in plan.readings) == FIXTURE_START
    assert max(r.end for r in plan.readings) == datetime(2026, 10, 25, 17, tzinfo=UTC)
    assert any(r.wh == 0 for r in plan.readings)
    assert all(isinstance(r.wh, int) for r in plan.readings)
    assert {s.origin for s in plan.sources} == {"simulated"}
    assert plan.timezone == "Asia/Jakarta"
    assert sum(relation.kind is RelationKind.DISJOINT for relation in plan.relations) == 6
    assert not any(asset.name.upper() == "AC" for asset in plan.assets)


def test_household_sums() -> None:
    """
    Condition:
    - Fixture H.

    Expected:
    - 2.100 kWh a day, 14.700 a week, 58.800 over four weeks; Kulkas 8.400 kWh of the week.
    """
    readings = build_scenario("h-base").readings

    assert _wh(readings, date(2026, 10, 19), date(2026, 10, 19)) == 2_100
    assert _wh(readings, date(2026, 10, 19), date(2026, 10, 25)) == 14_700
    assert _wh(readings, date(2026, 9, 28), date(2026, 10, 25)) == 58_800
    kulkas = tuple(r for r in readings if r.source_key == "src-kulkas")
    assert _wh(kulkas, date(2026, 10, 19), date(2026, 10, 25)) == 8_400


def test_industry_sums_and_sundays() -> None:
    """
    Condition:
    - Fixture I.

    Expected:
    - 24.000 kWh per output day, 144.000 a week, 576.000 over four weeks; every Sunday hour is an explicit zero.
    """
    readings = build_scenario("i-base").readings

    assert _wh(readings, date(2026, 10, 19), date(2026, 10, 19)) == 24_000
    assert _wh(readings, date(2026, 10, 19), date(2026, 10, 25)) == 144_000
    assert _wh(readings, date(2026, 9, 28), date(2026, 10, 25)) == 576_000
    sundays = [r for r in readings if r.start.astimezone(ZONE).weekday() == 6]
    assert len(sundays) == 4 * 24 * 4
    assert {r.wh for r in sundays} == {0}


def test_current_period_oracles() -> None:
    """
    Condition:
    - FX-CUR at 2026-10-21 12.00 WIB: rows ending after now are excluded.

    Expected:
    - H 0.870 kWh today and 5.070 kWh since Monday; I 13.000 and 61.000 kWh.
    """
    household, industry = build_scenario("h-current"), build_scenario("i-current")
    today, monday = date(2026, 10, 21), date(2026, 10, 19)

    assert household.virtual_now == NOW_CURRENT
    assert _wh(household.readings, today, today, NOW_CURRENT) == 870
    assert _wh(household.readings, monday, today, NOW_CURRENT) == 5_070
    assert _wh(industry.readings, today, today, NOW_CURRENT) == 13_000
    assert _wh(industry.readings, monday, today, NOW_CURRENT) == 61_000


def _extra_by_day(base: str, variant: str, source_key: str) -> dict[tuple[date, int], int]:
    before = {(r.source_key, r.start): r.wh for r in build_scenario(base).readings}
    extra: dict[tuple[date, int], int] = defaultdict(int)
    for r in build_scenario(variant).readings:
        delta = r.wh - before[(r.source_key, r.start)]
        if delta:
            assert r.source_key == source_key
            local = r.start.astimezone(ZONE)
            extra[(local.date(), local.hour)] += delta
    return dict(extra)


def test_household_change_is_selected_week_only() -> None:
    """
    Condition:
    - The household change variant.

    Expected:
    - TV gains 200 Wh at 19.00 on exactly the seven days 19–25 Oktober, and nothing else changes.
    """
    extra = _extra_by_day("h-base", "h-change", "src-tv")

    assert extra == {(date(2026, 10, 19) + timedelta(days=i), 19): 200 for i in range(7)}


def test_industry_change_is_selected_week_output_days_only() -> None:
    """
    Condition:
    - The industrial change variant.

    Expected:
    - Kompresor gains 500 Wh at 18.00 on the six output days 19–24 Oktober only.
    """
    extra = _extra_by_day("i-base", "i-change", "src-kompresor")

    assert extra == {(date(2026, 10, 19) + timedelta(days=i), 18): 500 for i in range(6)}


def test_catalog_is_complete_and_deterministic() -> None:
    """
    Condition:
    - Every catalog scenario is built twice.

    Expected:
    - Each has an ID, Indonesian name, description and segment, and builds identically both times.
    """
    expected = {
        "h-base", "h-notariff", "h-change", "h-current", "h-learning-partial", "h-zero", "h-stale-offline",
        "h-historical-offline", "h-scope", "empty", "i-base", "i-optional", "i-change", "i-current",
    }  # fmt: skip

    assert {scenario.id for scenario in SCENARIOS} == expected
    for scenario in SCENARIOS:
        assert scenario.name and scenario.description and scenario.segment in ("household", "industry")
        assert build_scenario(scenario.id) == build_scenario(scenario.id)


def test_scenario_quirks() -> None:
    """
    Condition:
    - The learning, stale, scope, empty and optional scenarios.

    Expected:
    - Each keeps the prototype's states: gaps, a stale simulated-live Router, the scope overlap, an empty
      workspace, the synthetic tariff label, and optional inputs only where declared.
    """
    learning = build_scenario("h-learning-partial")
    pompa_last = max(r.end for r in learning.readings if r.source_key == "src-pompa")
    kulkas_gap = [
        r
        for r in learning.readings
        if r.source_key == "src-kulkas" and r.start.astimezone(ZONE).date() == date(2026, 10, 22)
    ]
    stale = build_scenario("h-stale-offline")
    scope = build_scenario("h-scope")
    empty = build_scenario("empty")

    assert min(r.start for r in learning.readings).astimezone(ZONE).date() == date(2026, 10, 12)
    assert pompa_last == datetime(2026, 10, 23, 17, tzinfo=UTC)
    assert len(kulkas_gap) == 22 and learning.tariff is None
    router = next(s for s in stale.sources if s.key == "src-router")
    assert router.transport_status == "simulated_live" and stale.client_offline
    assert max(r.end for r in stale.readings if r.source_key == "src-router") == datetime(2026, 10, 25, 11, tzinfo=UTC)
    assert [s.authoritative for s in scope.sources if s.asset_key == "kulkas"] == [False, False]
    assert {(r.from_key, r.to_key, r.kind) for r in scope.relations if r.from_key == "meter"} == {
        ("meter", "kulkas", "contains"),
        ("meter", "router", "contains"),
        ("meter", "tv", "contains"),
        ("meter", "pompa", "unknown_overlap"),
    }
    assert (empty.assets, empty.readings) == ((), ())
    assert build_scenario("h-base").tariff["label"] == "Tarif simulasi, bukan tarif PLN"
    assert build_scenario("i-optional").metric["quantity"] == 2880
    assert build_scenario("i-base").schedule is None


def test_unknown_scenario_is_not_found() -> None:
    """
    Condition:
    - An ID outside the catalog.

    Expected:
    - NotFoundError.
    """
    with pytest.raises(NotFoundError):
        build_scenario("h-ac")
