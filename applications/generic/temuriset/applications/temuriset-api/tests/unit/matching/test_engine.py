"""The matching engine against the prototype's oracles, with no database (spec 019).

Each case names the oracle in ``docs/generic/temuriset/app-prototype/tools/domain.test.mjs`` it ports.
"""

from dataclasses import replace
from decimal import Decimal
from itertools import product

import pytest

from app.matching.engine.evaluate import evaluate, rank
from app.matching.engine.fit import Side, fit_bounds, harmonic, relevance, side
from app.matching.engine.inputs import Money
from tests.unit.matching.builders import fraise01, row, support, target


def test_f01_against_a1_is_ready_and_later_work_does_not_block() -> None:
    """
    Condition:
    - F01, USD 20000–30000 over six months, against A1, USD 15000–40000 on the same scope (scenario 1).

    Expected:
    - Stage, file and budget pass, it is ready and eligible, and the commercialization certificate is later work.
    """
    result = evaluate(support("F01"), target("A1"))

    assert (result["eligibility"], result["readiness"]) == ("ELIGIBLE", "READY_TO_SUBMIT")
    assert [
        row(result, label)["result"] for label in ("Tahap inovasi", "Berkas uji fungsi", "Kisaran biaya pilot")
    ] == ["PASS"] * 3
    assert [item["label"] for item in result["later"]] == ["Sertifikat komersialisasi"]
    assert result["later"][0]["result"] == "UNKNOWN"
    assert result["label"] == "Kecocokan kuat"
    assert result["fit"] == {"lower": "88.11", "upper": "94.04", "coverage": "0.95"}
    assert result["reasons"] == [
        "Tahap inovasi diterima mandat ini.",
        "Berkas tersedia. Isinya belum diperiksa.",
        "Kisaran biaya beririsan pada cakupan dan periode yang sama.",
    ]


def test_f01_gap_needs_the_range_first() -> None:
    """
    Condition:
    - F01-GAP: the range is not filled in.

    Expected:
    - Budget is UNKNOWN, readiness NEEDS_INFORMATION, label "Perlu konfirmasi", and the gap asks for the range.
    """
    result = evaluate(support("F01", gap=True), target("A1"))

    assert result["readiness"] == "NEEDS_INFORMATION"
    assert result["label"] == "Perlu konfirmasi"
    assert result["gap"]["reason"] == "Kisaran biaya pilot untuk kebutuhan ini belum diisi."
    assert result["gap"]["action"] == "complete-budget"


def test_f02_authority_is_unknown_and_no_money_is_invented() -> None:
    """
    Condition:
    - F02, whose authority claim is only asserted, against A2, which needs reviewed authority (AC32).

    Expected:
    - Authority is UNKNOWN with the "bukan berarti" reason, and the fit has no financial feature to rest on.
    """
    result = evaluate(support("F02"), target("A2"))

    assert row(result, "Wewenang atas inovasi")["result"] == "UNKNOWN"
    assert "Ini bukan berarti wewenang tidak ada" in row(result, "Wewenang atas inovasi")["reason"]
    assert result["readiness"] == "NEEDS_INFORMATION"
    assert support("F02").budget.known is False


def test_f03_planned_sso_is_incompatible_despite_topic_overlap() -> None:
    """
    Condition:
    - F03 with PLANNED SSO against D1, which needs CURRENT SSO and shares its keywords (AC31).

    Expected:
    - The requirement fails, the target is incompatible and excluded from the positive list.
    """
    result = evaluate(support("F03"), target("D1"))

    assert row(result, "SSO yang sudah berjalan")["result"] == "FAIL"
    assert (result["eligibility"], result["readiness"]) == ("INCOMPATIBLE", "BLOCKED_FOR_THIS_TARGET")
    assert result["relevant"] is True
    assert result["label"] == "Tidak cocok untuk target ini"
    assert rank([result]) == ([], [result])


def test_fraise01_compares_the_desired_contribution_not_the_target() -> None:
    """
    Condition:
    - FRaise01, USD 500000 target and USD 50000–100000 per investor, against B1's USD 50000–150000 check (AC20).

    Expected:
    - The contribution passes and the raise is ready.
    """
    result = evaluate(fraise01(), target("B1"))

    assert row(result, "Kisaran kontribusi")["result"] == "PASS"
    assert "bukan dengan seluruh target" in row(result, "Kisaran kontribusi")["reason"]
    assert result["readiness"] == "READY_TO_SUBMIT"


def test_proposed_entity_fails_b1_and_may_discuss_with_b2() -> None:
    """
    Condition:
    - FRaise01 for a company not founded yet (AC21).

    Expected:
    - B1's incorporated-entity requirement fails; B2, which needs no entity, is ready.
    """
    assert row(evaluate(fraise01(proposed=True), target("B1")), "Badan usaha yang sudah berdiri")["result"] == "FAIL"
    assert evaluate(fraise01(proposed=True), target("B2"))["readiness"] == "READY_TO_SUBMIT"


def test_f06_mentoring_passes_and_entity_is_unknown_for_equity() -> None:
    """
    Condition:
    - F06 against A3 (mentoring) and B1 (equity).

    Expected:
    - A3 is ready; B1's entity requirement is UNKNOWN, never a guess.
    """
    assert evaluate(support("F06"), target("A3"))["readiness"] == "READY_TO_SUBMIT"
    assert row(evaluate(support("F06"), target("B1")), "Badan usaha yang sudah berdiri")["result"] == "UNKNOWN"


def test_project_funding_against_an_equity_only_mandate_fails_the_form() -> None:
    """
    Condition:
    - F01, project funding, against B1, equity only.

    Expected:
    - The relationship form fails.
    """
    assert row(evaluate(support("F01"), target("B1")), "Bentuk pendanaan")["result"] == "FAIL"


@pytest.mark.parametrize(
    ("changes", "reason"),
    [
        ({"currency": "EUR"}, "Mata uang berbeda dan tidak ada dasar konversi yang disetujui."),
        ({"months": 1}, "Periode atau cakupan berbeda, jadi jumlahnya belum sebanding."),
        ({"basis": "monthly", "months": None}, "Periode atau cakupan berbeda, jadi jumlahnya belum sebanding."),
        ({"scope": "biaya produksi"}, "Periode atau cakupan berbeda, jadi jumlahnya belum sebanding."),
    ],
)
def test_unlike_money_stays_unknown(changes: dict, reason: str) -> None:
    """
    Condition:
    - F01's budget in EUR, over one month, monthly, or for another scope, against A1 (AC18).

    Expected:
    - The budget is UNKNOWN with the reason; nothing is converted or compared.
    """
    source = support("F01")
    result = evaluate(replace(source, budget=replace(source.budget, **changes)), target("A1"))

    assert row(result, "Kisaran biaya pilot")["result"] == "UNKNOWN"
    assert row(result, "Kisaran biaya pilot")["reason"] == reason


@pytest.mark.parametrize(
    ("low", "high", "partial", "result", "feature"),
    [
        ("41000", "50000", True, "PASS", "Kisaran tidak beririsan, tetapi dukungan sebagian diterima."),
        ("41000", "50000", False, "FAIL", "Kisaran biaya tidak beririsan dan dukungan penuh diwajibkan."),
        ("40000", "50000", False, "PASS", "Kisaran biaya beririsan pada cakupan dan periode yang sama."),
    ],
)
def test_non_overlap_scores_by_partial_support(low: str, high: str, partial: bool, result: str, feature: str) -> None:
    """
    Condition:
    - A budget beside A1's range, with or without partial support (FR-004).

    Expected:
    - Overlap passes, non-overlap passes at half with partial support and fails without it; edges overlap.
    """
    source = support("F01")
    source = replace(
        source, budget=replace(source.budget, low=Decimal(low), high=Decimal(high)), accepts_partial=partial
    )
    found = row(evaluate(source, target("A1")), "Kisaran biaya pilot")

    assert (found["result"], found["reason"]) == (result, feature)


def test_each_target_of_one_partner_is_evaluated_separately() -> None:
    """
    Condition:
    - F01 against A1, A2 and A3, all from Mitra A (AC25).

    Expected:
    - Three results with their own rows; A2's failing stage is not rescued by A1's pass.
    """
    results = {key: evaluate(support("F01"), target(key)) for key in ("A1", "A2", "A3")}

    assert results["A1"]["eligibility"] == "ELIGIBLE"
    assert results["A2"]["eligibility"] == "INCOMPATIBLE"
    assert [len(result["rows"]) for result in results.values()] == [4, 2, 1]


def test_a_narrative_requirement_is_manual_and_never_blocks() -> None:
    """
    Condition:
    - A1 with an extra narrative requirement stored as non-mandatory manual review (AC27).

    Expected:
    - It is UNKNOWN for manual review, and F01 stays ready.
    """
    narrative = {
        "id": "A1-n",
        "label": "Dampak sosial",
        "field": "narrative",
        "operator": "manual_review",
        "value": None,
        "mandatory": False,
        "applies_at": "SUBMISSION",
        "verification_mode": "DECLARATION",
        "reason": "",
    }
    base = target("A1")
    result = evaluate(support("F01"), replace(base, requirements=(*base.requirements, narrative)))

    assert row(result, "Dampak sosial")["result"] == "UNKNOWN"
    assert row(result, "Dampak sosial")["reason"] == "Perlu ditinjau secara manual."
    assert result["readiness"] == "READY_TO_SUBMIT"


def test_no_relevance_signal_abstains() -> None:
    """
    Condition:
    - F01 against A3, whose rules pass but whose keywords F01 never states.

    Expected:
    - Ready, not relevant, "Belum ada sinyal relevansi", and excluded from the positive list; F06 is relevant.
    """
    result = evaluate(support("F01"), target("A3"))

    assert (result["readiness"], result["relevant"]) == ("READY_TO_SUBMIT", False)
    assert result["label"] == "Belum ada sinyal relevansi"
    assert rank([result]) == ([], [result])
    assert evaluate(support("F06"), target("A3"))["relevant"] is True


def test_no_checklist_says_so_instead_of_a_percentage() -> None:
    """
    Condition:
    - A target with no requirements.

    Expected:
    - The evidence note says "Belum ada checklist".
    """
    result = evaluate(support("F06"), target("A3", requirements=()))

    assert result["evidence"] == {"provided": 0, "reviewed": 0, "applicable": 0, "note": "Belum ada checklist"}


def test_ac33_bounds_are_71_72_to_80() -> None:
    """
    Condition:
    - A = 0.80 fully known; B known at 0.65 with 0.15 of weight unknown (AC33).

    Expected:
    - Bounds 71.72–80.00.
    """
    bounds = fit_bounds(
        Side(low=Decimal("0.8"), high=Decimal("0.8"), known=Decimal(1)),
        Side(low=Decimal("0.65"), high=Decimal("0.8"), known=Decimal("0.85")),
    )

    assert (str(bounds.lower), str(bounds.upper)) == ("71.72", "80.00")


def test_unknown_weight_widens_only_the_upper_bound() -> None:
    """
    Condition:
    - One unknown feature of weight 0.10.

    Expected:
    - It adds to the upper bound only, and known drops by its weight; harmonic of zeros is zero.
    """
    bounds = side({"a": Decimal(1), "b": None}, {"a": Decimal("0.9"), "b": Decimal("0.1")})

    assert (bounds.low, bounds.high, bounds.known) == (Decimal("0.9"), Decimal("1.0"), Decimal("0.9"))
    assert harmonic(Decimal(0), Decimal(0)) == 0
    assert relevance(("Air",), ()) == 0


def test_a_mandatory_unknown_keeps_perlu_konfirmasi_whatever_the_score() -> None:
    """
    Condition:
    - F02 against A2: high topic overlap, a mandatory UNKNOWN (AC33).

    Expected:
    - The label is "Perlu konfirmasi", never a strong match.
    """
    assert evaluate(support("F02"), target("A2"))["label"] == "Perlu konfirmasi"


@pytest.mark.parametrize(
    ("stage", "relationship", "currency", "keyword"),
    list(product(["IDEA", "PROTOTYPE", "MARKET"], ["PROJECT", "EQUITY"], ["USD", "IDR"], ["air", "x"])),
)
def test_a_mandatory_failure_never_yields_a_positive_label(
    stage: str, relationship: str, currency: str, keyword: str
) -> None:
    """
    Condition:
    - F01 varied across stage, form, currency and keywords, against A1 and B1.

    Expected:
    - Whenever a mandatory entry requirement fails, the result is incompatible and never shown as positive.
    """
    source = support("F01")
    source = replace(
        source,
        stage=stage,
        relationship=relationship,
        keywords=(keyword,),
        budget=replace(source.budget, currency=currency),
    )
    for key in ("A1", "B1"):
        result = evaluate(source, target(key))
        failed = any(
            item["result"] == "FAIL" and item["mandatory"] and item["applies_at"] == "SUBMISSION"
            for item in result["rows"]
        )
        if failed:
            assert result["label"] == "Tidak cocok untuk target ini"
            assert rank([result])[0] == []


def test_ranking_orders_by_eligibility_then_lower_bound() -> None:
    """
    Condition:
    - F01's results against every target.

    Expected:
    - A1 is the only recommendation; excluded results follow eligibility order, then id.
    """
    results = [evaluate(support("F01"), target(key)) for key in ("D1", "C1", "B1", "A3", "A2", "A1")]
    shown, excluded = rank(results)

    assert [result["opportunity_id"] for result in shown] == ["A1"]
    assert [result["eligibility"] for result in excluded] == ["ELIGIBLE"] + ["INCOMPATIBLE"] * 4


@pytest.mark.parametrize(
    ("operator", "limit", "expected"),
    [
        ("minimum", "20000", "PASS"),
        ("minimum", "25000", "FAIL"),
        ("maximum", "30000", "PASS"),
        ("maximum", "29999", "FAIL"),
    ],
)
def test_minimum_and_maximum_compare_the_applicants_own_amount(operator: str, limit: str, expected: str) -> None:
    """
    Condition:
    - A budget bound requirement against F01's USD 20000–30000.

    Expected:
    - ``minimum`` reads the lowest amount and ``maximum`` the highest; an unknown amount is UNKNOWN.
    """
    bound = {
        "id": "x",
        "label": "Batas",
        "field": "budget",
        "operator": operator,
        "value": limit,
        "mandatory": True,
        "applies_at": "SUBMISSION",
        "verification_mode": "DECLARATION",
        "reason": "",
    }
    assert row(evaluate(support("F01"), target("A1", requirements=(bound,))), "Batas")["result"] == expected
    assert row(evaluate(support("F01", gap=True), target("A1", requirements=(bound,))), "Batas")["result"] == "UNKNOWN"


def test_document_states_and_features_never_pass_what_they_did_not_earn() -> None:
    """
    Condition:
    - F01 with its file still in quarantine, with no file, and F03's SSO with no timing requirement.

    Expected:
    - A quarantined file is UNKNOWN "belum lolos", no file is "belum disediakan", and an unknown feature is UNKNOWN.
    """
    quarantined = support(
        "F01", documents={"function": ({"DOCUMENT_PRESENT": "UNKNOWN", "REVIEWER_CONFIRMED": "UNKNOWN"},)}
    )
    assert (
        row(evaluate(quarantined, target("A1")), "Berkas uji fungsi")["reason"]
        == "Berkas belum lolos pemeriksaan keamanan."
    )
    assert (
        row(evaluate(support("F01", documents={}), target("A1")), "Berkas uji fungsi")["reason"]
        == "Berkas belum disediakan."
    )
    assert row(evaluate(support("F01"), target("D1")), "SSO yang sudah berjalan")["result"] == "UNKNOWN"


def test_contribution_is_unknown_for_a_support_request_and_an_unstated_check() -> None:
    """
    Condition:
    - F06's support request against B1, and FRaise01 against a check stated in another currency.

    Expected:
    - Both are UNKNOWN; nothing is converted.
    """
    assert (
        row(evaluate(support("F06"), target("B1")), "Kisaran kontribusi")["reason"] == "Dasar kontribusi belum jelas."
    )
    other = target("B1", financial=Money(Decimal(1), Decimal(2), "IDR", "investorCheck", "per_investment"))
    assert row(evaluate(fraise01(), other), "Kisaran kontribusi")["result"] == "UNKNOWN"
