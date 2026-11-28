"""Unit tests for the eight-dimension match breakdown, topic prose matching, and readiness TKT (spec 057)."""

from dataclasses import replace
from decimal import Decimal
from typing import Any

import pytest

from app.matching.engine.breakdown import _round_score, _status_for_score
from app.matching.engine.evaluate import POLICY_VERSIONS, evaluate
from app.matching.engine.fit import extract_terms, join_normalized_text, readiness_feature, topic_overlap
from app.matching.engine.inputs import Source, Target
from tests.unit.matching.builders import fraise01, support, target

EXPECTED_ORDER = ["sector", "topic", "readiness", "money", "form", "requirements", "evidence", "availability"]


def _dim(result: dict[str, Any], dim_id: str) -> dict[str, Any]:
    return next(item for item in result["breakdown"] if item["id"] == dim_id)


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (None, "UNKNOWN"),
        (0, "MISMATCH"),
        (39, "MISMATCH"),
        (40, "PARTIAL"),
        (79, "PARTIAL"),
        (80, "MATCH"),
        (100, "MATCH"),
    ],
)
def test_dimension_status_thresholds(score: int | None, expected: str) -> None:
    """
    Condition:
    - Boundary scores 0, 39, 40, 79, 80, 100 and None.

    Expected:
    - Exact status boundaries: <40 MISMATCH, 40–79 PARTIAL, >=80 MATCH, None UNKNOWN.
    """
    assert _status_for_score(score) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, None),
        (Decimal("0.004"), 0),
        (Decimal("0.005"), 1),
        (Decimal("0.25"), 25),
        (Decimal("0.665"), 67),
        (Decimal("1"), 100),
    ],
)
def test_round_score_uses_half_up(value: Decimal | None, expected: int | None) -> None:
    """
    Condition:
    - Decimal values at half-up boundaries and None.

    Expected:
    - Half-up whole percentage integers or None.
    """
    assert _round_score(value) == expected


def test_policy_versions_include_fit_features_v2() -> None:
    """
    Condition:
    - Engine policy versions for spec 057.

    Expected:
    - matching-weights stays 1, fit-thresholds stays 1, fit-features is 2.
    """
    assert POLICY_VERSIONS == {"matching-weights": 1, "fit-thresholds": 1, "fit-features": 2}


@pytest.mark.parametrize(
    ("source_sector", "target_sectors", "expected_score", "expected_status"),
    [
        ("Energi", ("Energi", "Pertanian"), 100, "MATCH"),
        ("Air dan sanitasi", ("Pertanian",), 0, "MISMATCH"),
        ("", ("Pertanian",), None, "UNKNOWN"),
        ("Energi", (), None, "UNKNOWN"),
    ],
)
def test_sector_dimension(
    source_sector: str, target_sectors: tuple[str, ...], expected_score: int | None, expected_status: str
) -> None:
    """
    Condition:
    - Matching, mismatching, and missing sectors on either side.

    Expected:
    - 100/MATCH, 0/MISMATCH, or None/UNKNOWN with raw source/target values.
    """
    src = replace(support("F01"), sector=source_sector)
    tgt = target("A1", sectors=target_sectors)
    dim = _dim(evaluate(src, tgt), "sector")
    assert (dim["score"], dim["status"], dim["weight"]) == (expected_score, expected_status, "0.15")
    assert dim["values"] == {"source": source_sector or None, "target": list(target_sectors)}


@pytest.mark.parametrize(
    ("target_kw", "source_kw", "prose", "expected_score", "expected_matched", "expected_missing"),
    [
        (
            ("pertanian", "panen", "irigasi", "desa"),
            ("air", "desa"),
            ("Saringan air", "Untuk desa"),
            25,
            ["desa"],
            ["pertanian", "panen", "irigasi"],
        ),
        (
            ("surya", "energi terbarukan"),
            ("panel",),
            ("Kotak surya untuk energi terbarukan di rumah",),
            100,
            ["surya", "energi terbarukan"],
            [],
        ),
        (
            ("air",),
            (),
            ("Saringan udara bersih",),
            0,
            [],
            ["air"],
        ),
        (
            ("air",),
            (),
            ("Pengairan sawah",),
            0,
            [],
            ["air"],
        ),
        (
            (),
            ("air",),
            ("Filter air",),
            None,
            [],
            [],
        ),
    ],
)
def test_topic_overlap_whole_word_and_phrase(
    target_kw: tuple[str, ...],
    source_kw: tuple[str, ...],
    prose: tuple[str, ...],
    expected_score: int | None,
    expected_matched: list[str],
    expected_missing: list[str],
) -> None:
    """
    Condition:
    - Single-word, multi-word, substring false-positive ("pengairan" vs "air"), and empty mandate keywords.

    Expected:
    - Whole-word case-insensitive matches only; empty target keywords yield None/UNKNOWN.
    """
    terms = extract_terms(source_kw, *prose)
    joined = join_normalized_text(source_kw, *prose)
    overlap, matched, missing = topic_overlap(target_kw, source_kw, terms, joined)
    assert _round_score(overlap) == expected_score
    assert matched == expected_matched
    assert missing == expected_missing


@pytest.mark.parametrize(
    ("stage", "accepted", "tkt", "min_tkt", "expected_score", "expected_status"),
    [
        ("PROTOTYPE", ("PROTOTYPE", "PILOT"), 6, 5, 100, "MATCH"),
        ("PROTOTYPE", ("PILOT", "WORKING"), 4, 6, 25, "MISMATCH"),
        ("PROTOTYPE", ("PROTOTYPE",), 4, 6, 75, "PARTIAL"),
        ("PROTOTYPE", ("PROTOTYPE",), 2, 7, 50, "PARTIAL"),
        ("PROTOTYPE", ("PROTOTYPE",), None, 6, 100, "MATCH"),
        (None, ("PROTOTYPE",), 4, 6, 50, "PARTIAL"),
        (None, ("PROTOTYPE",), None, 6, None, "UNKNOWN"),
        ("PROTOTYPE", (), None, None, None, "UNKNOWN"),
    ],
)
def test_readiness_dimension_stage_and_tkt(
    stage: str | None,
    accepted: tuple[str, ...],
    tkt: int | None,
    min_tkt: int | None,
    expected_score: int | None,
    expected_status: str,
) -> None:
    """
    Condition:
    - Combinations of stage match/mismatch and TKT meeting/below/absent against mandate minimum TKT.

    Expected:
    - Mean of known parts; TKT penalty is 25 per level below minimum clamped at 0; unknown when both omitted.
    """
    val = readiness_feature(stage, accepted, tkt, min_tkt)
    assert _round_score(val) == expected_score
    src = replace(support("F01"), stage=stage, tkt=tkt)
    tgt = target("A1", accepted_stages=accepted, min_tkt=min_tkt)
    dim = _dim(evaluate(src, tgt), "readiness")
    assert (dim["score"], dim["status"]) == (expected_score, expected_status)
    assert dim["values"] == {"stage": stage, "accepted_stages": list(accepted), "tkt": tkt, "min_tkt": min_tkt}


def test_money_dimension_runs_even_without_budget_requirement_row() -> None:
    """
    Condition:
    - A mandate with financial range and NO requirement rows, matched against overlapping,
      partial, non-overlapping, and unknown budgets.

    Expected:
    - Scores 100, 50, 0, and None/UNKNOWN respectively, and enters fit.
    """
    tgt = target("A1", requirements=())
    overlap_src = support("F01")
    assert _dim(evaluate(overlap_src, tgt), "money")["score"] == 100

    partial_src = replace(
        overlap_src,
        budget=replace(overlap_src.budget, low=Decimal("50000"), high=Decimal("60000")),
        accepts_partial=True,
    )
    partial_dim = _dim(evaluate(partial_src, tgt), "money")
    assert (partial_dim["score"], partial_dim["status"]) == (50, "PARTIAL")

    full_only_src = replace(partial_src, accepts_partial=False)
    full_dim = _dim(evaluate(full_only_src, tgt), "money")
    assert (full_dim["score"], full_dim["status"]) == (0, "MISMATCH")

    gap_dim = _dim(evaluate(support("F01", gap=True), tgt), "money")
    assert (gap_dim["score"], gap_dim["status"]) == (None, "UNKNOWN")


def test_form_dimension_handles_unknown_preview_source() -> None:
    """
    Condition:
    - A source with relationship=None (as in preview) versus PROJECT/EQUITY.

    Expected:
    - None yields UNKNOWN instead of 0%; matching yields 100/MATCH; mismatch yields 0/MISMATCH.
    """
    tgt = target("A1")
    preview = replace(support("F01"), relationship=None)
    assert (_dim(evaluate(preview, tgt), "form")["score"], _dim(evaluate(preview, tgt), "form")["status"]) == (
        None,
        "UNKNOWN",
    )
    assert _dim(evaluate(support("F01"), tgt), "form")["score"] == 100
    assert _dim(evaluate(fraise01(), tgt), "form")["score"] == 0


def test_requirements_evidence_and_availability_dimensions() -> None:
    """
    Condition:
    - F01 vs A1 (passing), F01-GAP vs A1 (unknown entry item), F03 vs D1 (failing entry item),
      and a target with no requirements and unavailable intake.

    Expected:
    - Every result has all eight dimensions in canonical order; failed required item keeps label
      incompatible; no checklist yields NOT_APPLICABLE.
    """
    res_ok = evaluate(support("F01"), target("A1"))
    assert [item["id"] for item in res_ok["breakdown"]] == EXPECTED_ORDER
    assert _dim(res_ok, "requirements")["status"] == "MATCH"
    assert _dim(res_ok, "requirements")["score"] == 100
    assert _dim(res_ok, "evidence")["score"] == 75
    assert _dim(res_ok, "availability")["score"] == 100

    res_gap = evaluate(support("F01", gap=True), target("A1"))
    assert _dim(res_gap, "requirements")["status"] == "UNKNOWN"
    assert _dim(res_gap, "requirements")["values"]["unknown"] == ["Kisaran biaya pilot"]

    res_fail = evaluate(support("F03"), target("D1"))
    assert _dim(res_fail, "requirements")["status"] == "MISMATCH"
    assert "SSO yang sudah berjalan" in _dim(res_fail, "requirements")["values"]["failed"]
    assert res_fail["label"] == "Tidak cocok untuk target ini"

    closed_target = target(
        "A3", requirements=(), active=False, availability={"available": False, "reason": "TARGET_NOT_ACTIVE"}
    )
    res_closed = evaluate(support("F06"), closed_target)
    assert _dim(res_closed, "requirements")["status"] == "NOT_APPLICABLE"
    assert _dim(res_closed, "requirements")["score"] is None
    assert _dim(res_closed, "evidence")["status"] == "NOT_APPLICABLE"
    assert _dim(res_closed, "evidence")["score"] is None
    assert (_dim(res_closed, "availability")["score"], _dim(res_closed, "availability")["status"]) == (0, "MISMATCH")
    assert _dim(res_closed, "availability")["values"] == {"available": False, "reason": "TARGET_NOT_ACTIVE"}


def test_empty_source_never_shows_zero_for_unknown() -> None:
    """
    Condition:
    - A bare preview Source with no sector, stage, budget, relationship or keywords against a target with no keywords.

    Expected:
    - Unknown dimensions return score=None and status=UNKNOWN, never 0.
    """
    bare = Source(type="SUPPORT_REQUEST", id="x", version=1, stage=None, sector="", keywords=(), relationship=None)
    tgt = Target(
        opportunity_id="o",
        version_id="v",
        number=1,
        partner_party_id="p",
        partner_name="Partner",
        title="Mandat",
        active=True,
        accepted_stages=(),
        sectors=(),
        keywords=(),
        relationship_forms=(),
        financial=None,
        requirements=(),
        availability={"available": True, "reason": None},
    )
    res = evaluate(bare, tgt)
    for dim_id in ("sector", "topic", "readiness", "money", "form"):
        dim = _dim(res, dim_id)
        assert dim["score"] is None and dim["status"] == "UNKNOWN"
