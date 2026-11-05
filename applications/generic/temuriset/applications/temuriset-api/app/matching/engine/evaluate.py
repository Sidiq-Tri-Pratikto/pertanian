"""One source against one target: rows, eligibility, readiness, relevance, fit, label, reasons, gap and later work.

Pure and deterministic. A known failed mandatory requirement is never averaged away, a target with no relevance
signal abstains, and ``UNKNOWN`` outranks any score in the label.
"""

from decimal import Decimal
from typing import Any

from app.matching.engine.fit import (
    MIN_COVERAGE,
    POTENTIAL_COVERAGE,
    POTENTIAL_LOWER,
    STRONG_COVERAGE,
    STRONG_LOWER,
    WEIGHTS_A,
    WEIGHTS_B,
    fit_bounds,
    relevance,
    side,
)
from app.matching.engine.inputs import Source, Target
from app.matching.engine.requirements import FAIL, PASS, UNKNOWN, evaluate_requirement

ENGINE = "lexical-rules@1"
POLICY_VERSIONS = {"matching-weights": 1, "fit-thresholds": 1}
ENTRY = "SUBMISSION"
_ELIGIBILITY_ORDER = {"ELIGIBLE": 0, "NEEDS_VERIFICATION": 1, "INCOMPATIBLE": 2}
NO_CHECKLIST = "Belum ada checklist"


def _label(eligibility: str, relevant: bool, lower: Decimal, coverage: Decimal) -> str:
    if eligibility == "INCOMPATIBLE":
        return "Tidak cocok untuk target ini"
    if not relevant:
        return "Belum ada sinyal relevansi"
    if eligibility == "NEEDS_VERIFICATION":
        return "Perlu konfirmasi"
    if coverage < MIN_COVERAGE:
        return "Informasi belum cukup"
    if lower >= STRONG_LOWER and coverage >= STRONG_COVERAGE:
        return "Kecocokan kuat"
    if lower >= POTENTIAL_LOWER and coverage >= POTENTIAL_COVERAGE:
        return "Kecocokan potensial"
    return "Kecocokan lemah"


def _one(value: bool) -> Decimal:
    return Decimal(1) if value else Decimal(0)


def evaluate(source: Source, target: Target) -> dict[str, Any]:
    """Evaluate one source against one opportunity version.

    Args:
        source (Source): The applicant's authorized projection.
        target (Target): The opportunity's applicant-visible projection.

    Returns:
        dict[str, Any]: JSON-ready result; numbers are decimal strings.
    """
    rows: list[dict[str, Any]] = []
    money = None
    for requirement in target.requirements:
        outcome = evaluate_requirement(requirement, source, target)
        row = {
            "requirement_id": requirement["id"],
            "label": requirement["label"],
            "field": requirement["field"],
            "mandatory": requirement["mandatory"],
            "applies_at": requirement["applies_at"],
            "verification_mode": requirement["verification_mode"],
            "result": outcome.result,
            "reason": outcome.reason,
            "action": outcome.action,
        }
        rows.append(row)
        if money is None and requirement["field"] in ("budget", "contribution"):
            money = outcome
    entry = [row for row in rows if row["applies_at"] == ENTRY and row["mandatory"]]
    failed = [row for row in entry if row["result"] == FAIL]
    unknown = [row for row in entry if row["result"] == UNKNOWN]
    eligibility = "INCOMPATIBLE" if failed else "NEEDS_VERIFICATION" if unknown else "ELIGIBLE"
    readiness = "BLOCKED_FOR_THIS_TARGET" if failed else "NEEDS_INFORMATION" if unknown else "READY_TO_SUBMIT"
    overlap = relevance(source.keywords, target.keywords)
    a = side(
        {
            "problem": overlap,
            "stage": None if source.stage is None else _one(source.stage in target.accepted_stages),
            "sector": _one(source.sector in target.sectors) if source.sector else None,
            "financial": money.feature if money else None,
            "timing": None,
        },
        WEIGHTS_A,
    )
    b = side(
        {
            "support": Decimal(1),
            "form": _one(source.relationship in target.relationship_forms),
            "geo": Decimal(1),
            "availability": _one(target.active),
        },
        WEIGHTS_B,
    )
    fit = fit_bounds(a, b)
    # No relevance signal means abstaining: compatible stage or geography alone never recommends a target.
    relevant = overlap > 0
    gap = (failed or unknown or [None])[0]
    return {
        "opportunity_id": target.opportunity_id,
        "opportunity_version_id": target.version_id,
        "opportunity_version": target.number,
        "partner_party_id": target.partner_party_id,
        "partner": target.partner_name,
        "title": target.title,
        "availability": target.availability,
        "eligibility": eligibility,
        "readiness": readiness,
        "relevant": relevant,
        "label": _label(eligibility, relevant, fit.lower, fit.coverage),
        "fit": {"lower": str(fit.lower), "upper": str(fit.upper), "coverage": str(fit.coverage)},
        "reasons": [row["reason"] for row in rows if row["result"] == PASS and row["applies_at"] == ENTRY][:3],
        "gap": gap,
        "later": [row for row in rows if row["applies_at"] != ENTRY],
        "rows": rows,
        "evidence": {
            "provided": sum(1 for r in rows if r["verification_mode"] != "REVIEWER_CONFIRMED" and r["result"] == PASS),
            "reviewed": sum(1 for r in rows if r["verification_mode"] == "REVIEWER_CONFIRMED" and r["result"] == PASS),
            "applicable": len(rows),
            "note": NO_CHECKLIST if not rows else None,
        },
    }


def rank(results: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Order results and split off what must not be shown as a positive match.

    Each opportunity is evaluated on its own before any grouping, so nothing merges across a partner's targets (AC25).

    Args:
        results (list[dict[str, Any]]): One result per target.

    Returns:
        tuple[list[dict[str, Any]], list[dict[str, Any]]]: Recommended results, then excluded ones (incompatible, or
            with no relevance signal), each ordered by eligibility, lower bound, relevance and id.
    """
    ordered = sorted(
        results,
        key=lambda result: (
            _ELIGIBILITY_ORDER[result["eligibility"]],
            -Decimal(result["fit"]["lower"]),
            not result["relevant"],
            result["opportunity_id"],
        ),
    )
    shown = [result for result in ordered if result["relevant"] and result["eligibility"] != "INCOMPATIBLE"]
    excluded = [result for result in ordered if not (result["relevant"] and result["eligibility"] != "INCOMPATIBLE")]
    return shown, excluded
