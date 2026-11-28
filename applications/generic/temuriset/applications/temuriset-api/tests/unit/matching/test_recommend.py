"""Unit tests for honest, conditional improvement recommendations (spec 058)."""

from dataclasses import replace
from decimal import Decimal

from app.matching.engine.evaluate import evaluate
from app.matching.engine.inputs import Money
from app.matching.engine.recommend import recommend
from tests.unit.matching.builders import support, target


def test_blocking_requirement_comes_first_and_estimate_matches_evaluate() -> None:
    """
    Condition:
    - F01-GAP (missing budget) against A1, where budget is a mandatory submission requirement.

    Expected:
    - The blocking requirement recommendation comes first, links to budget, and its estimate equals evaluate() on
      a source with A1's range.
    """
    src = replace(support("F01", gap=True), invention_id="inv-1")
    tgt = target("A1")
    res = evaluate(src, tgt)
    recs = recommend(src, tgt, res)

    assert recs[0]["kind"] == "requirement"
    assert recs[0]["blocking"] is True
    assert recs[0]["target"]["field"] == "budget"
    expected_after = evaluate(replace(src, budget=tgt.financial), tgt)
    assert recs[0]["estimate"]["label"] == expected_after["label"]
    assert recs[0]["estimate"]["fit"] == expected_after["fit"]


def test_honesty_sector_and_stage_never_carry_estimates() -> None:
    """
    Condition:
    - Produk A (Air dan sanitasi, PROTOTYPE, TKT 4) against a Pertanian PILOT mandate with min_tkt 6.

    Expected:
    - Recommendations include topic, tkt_below (with estimate), stage (no estimate), and sector (no estimate).
    """
    src = replace(
        support("F01"),
        invention_id="inv-a",
        sector="Air dan sanitasi",
        stage="PROTOTYPE",
        tkt=4,
        keywords=("air", "desa"),
        text_terms=("air", "desa"),
        text="air desa",
    )
    tgt = target(
        "A1",
        sectors=("Pertanian",),
        accepted_stages=("PILOT", "WORKING"),
        keywords=("pertanian", "panen", "irigasi", "desa"),
        min_tkt=6,
        requirements=(),
    )
    res = evaluate(src, tgt)
    recs = recommend(src, tgt, res)
    by_kind = {item["kind"]: item for item in recs}

    assert set(by_kind) >= {"topic", "tkt_below", "stage", "sector"}
    assert by_kind["topic"]["values"]["missing"] == ["pertanian", "panen", "irigasi"]
    assert by_kind["topic"]["estimate"] is not None
    assert by_kind["tkt_below"]["values"] == {"tkt": 4, "min_tkt": 6}
    assert by_kind["tkt_below"]["estimate"] is not None
    assert Decimal(by_kind["tkt_below"]["estimate"]["gain"]) > 0
    assert by_kind["stage"]["estimate"] is None
    assert by_kind["sector"]["estimate"] is None


def test_tkt_missing_money_gap_form_availability_and_preview_rules() -> None:
    """
    Condition:
    - Missing TKT against min_tkt, non-overlapping money, mismatched form, unavailable target, and preview mode.

    Expected:
    - Each rule fires with the right kind, raw values, and expected estimate presence; preview puts no_need first
      and omits money/form recommendations.
    """
    src = replace(
        support("F01"),
        invention_id="inv-x",
        tkt=None,
        relationship="LICENSE",
        budget=Money(
            Decimal("90000"), Decimal("100000"), "USD", "project", "total_period", 6, "biaya pilot enam bulan"
        ),
    )
    tgt = target(
        "A1",
        min_tkt=5,
        requirements=(),
        active=False,
        availability={"available": False, "reason": "TARGET_NOT_ACTIVE"},
    )
    res = evaluate(src, tgt)
    recs = recommend(src, tgt, res)
    by_kind = {item["kind"]: item for item in recs}

    assert "tkt_missing" in by_kind and by_kind["tkt_missing"]["estimate"] is not None
    assert "money_gap" in by_kind and by_kind["money_gap"]["estimate"] is not None
    assert "form" in by_kind and by_kind["form"]["estimate"] is not None
    assert "availability" in by_kind and by_kind["availability"]["estimate"] is None

    preview_src = replace(src, budget=None, relationship=None)
    preview_res = evaluate(preview_src, tgt)
    preview_recs = recommend(preview_src, tgt, preview_res, preview=True)
    assert preview_recs[0]["kind"] == "no_need"
    assert not any(r["kind"] in ("money_missing", "money_gap", "form") for r in preview_recs)
