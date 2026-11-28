"""Per-aspect match breakdown across eight dimensions (spec 057). Pure Python, no I/O."""

from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from app.matching.engine.fit import WEIGHTS_A, WEIGHTS_B
from app.matching.engine.inputs import Money, Source, Target
from app.matching.engine.requirements import FAIL, PASS, UNKNOWN, Outcome

_WHOLE = Decimal("1")
_HUNDRED = Decimal("100")
_ENTRY = "SUBMISSION"


def _round_score(value: Decimal | None) -> int | None:
    if value is None:
        return None
    return int((value * _HUNDRED).quantize(_WHOLE, rounding=ROUND_HALF_UP))


def _status_for_score(score: int | None) -> str:
    if score is None:
        return "UNKNOWN"
    if score >= 80:
        return "MATCH"
    if score >= 40:
        return "PARTIAL"
    return "MISMATCH"


def _money_dict(money: Money | None) -> dict[str, Any] | None:
    if money is None or not money.known:
        return None
    return {
        "low": str(money.low),
        "high": str(money.high),
        "currency": money.currency,
        "subject": money.subject,
        "basis": money.basis,
        "months": money.months,
        "scope": money.scope,
    }


def build_breakdown(  # noqa: PLR0913 - explicit pure inputs for all eight dimensions
    *,
    source: Source,
    target: Target,
    rows: list[dict[str, Any]],
    evidence: dict[str, Any],
    sector_feature: Decimal | None,
    topic_feature: Decimal | None,
    topic_matched: list[str],
    topic_missing: list[str],
    readiness_val: Decimal | None,
    money_outcome: Outcome | None,
    form_feature: Decimal | None,
    available: bool,
) -> list[dict[str, Any]]:
    """Build the ordered eight-dimension breakdown for one evaluated pair.

    Args:
        source (Source): Applicant projection.
        target (Target): Mandate projection.
        rows (list[dict[str, Any]]): Evaluated requirement rows.
        evidence (dict[str, Any]): Evidence counts (``provided``, ``reviewed``, ``applicable``).
        sector_feature (Decimal | None): Computed sector feature in [0, 1] or None.
        topic_feature (Decimal | None): Computed topic overlap in [0, 1] or None.
        topic_matched (list[str]): Matched mandate keywords.
        topic_missing (list[str]): Missing mandate keywords.
        readiness_val (Decimal | None): Computed stage+TKT feature in [0, 1] or None.
        money_outcome (Outcome | None): Evaluated financial outcome.
        form_feature (Decimal | None): Computed relationship form feature in [0, 1] or None.
        available (bool): Whether the mandate currently accepts pitches.

    Returns:
        list[dict[str, Any]]: Eight JSON-ready dimension dictionaries.
    """
    sector_score = _round_score(sector_feature)
    topic_score = _round_score(topic_feature)
    readiness_score = _round_score(readiness_val)

    money_feature = money_outcome.feature if money_outcome is not None else None
    money_score = _round_score(money_feature)
    source_money = source.contribution if source.type == "FUNDING_REQUEST" else source.budget

    form_score = _round_score(form_feature)

    entry = [row for row in rows if row["applies_at"] == _ENTRY and row["mandatory"]]
    if not entry:
        req_score: int | None = None
        req_status = "NOT_APPLICABLE"
        req_values: dict[str, Any] = {"passed": 0, "failed": [], "unknown": [], "total": 0}
    else:
        passed = [row for row in entry if row["result"] == PASS]
        failed = [row["label"] for row in entry if row["result"] == FAIL]
        unknown = [row["label"] for row in entry if row["result"] == UNKNOWN]
        req_score = _round_score(Decimal(len(passed)) / Decimal(len(entry)))
        req_status = "MISMATCH" if failed else "UNKNOWN" if unknown else "MATCH"
        req_values = {"passed": len(passed), "failed": failed, "unknown": unknown, "total": len(entry)}

    applicable = int(evidence["applicable"])
    provided = int(evidence["provided"])
    reviewed = int(evidence["reviewed"])
    if applicable == 0:
        ev_score: int | None = None
        ev_status = "NOT_APPLICABLE"
    else:
        ev_score = _round_score(Decimal(provided + reviewed) / Decimal(applicable))
        ev_status = _status_for_score(ev_score)

    avail_score = 100 if available else 0
    avail_reason = target.availability.get("reason")

    return [
        {
            "id": "sector",
            "score": sector_score,
            "status": _status_for_score(sector_score),
            "weight": str(WEIGHTS_A["sector"]),
            "values": {"source": source.sector or None, "target": list(target.sectors)},
        },
        {
            "id": "topic",
            "score": topic_score,
            "status": _status_for_score(topic_score),
            "weight": str(WEIGHTS_A["problem"]),
            "values": {"matched": topic_matched, "missing": topic_missing},
        },
        {
            "id": "readiness",
            "score": readiness_score,
            "status": _status_for_score(readiness_score),
            "weight": str(WEIGHTS_A["stage"]),
            "values": {
                "stage": source.stage,
                "accepted_stages": list(target.accepted_stages),
                "tkt": source.tkt,
                "min_tkt": target.min_tkt,
            },
        },
        {
            "id": "money",
            "score": money_score,
            "status": _status_for_score(money_score),
            "weight": str(WEIGHTS_A["financial"]),
            "values": {
                "source": _money_dict(source_money),
                "target": _money_dict(target.financial),
                "accepts_partial": source.accepts_partial,
                "reason": money_outcome.reason if money_outcome is not None else None,
            },
        },
        {
            "id": "form",
            "score": form_score,
            "status": _status_for_score(form_score),
            "weight": str(WEIGHTS_B["form"]),
            "values": {"source": source.relationship, "target": list(target.relationship_forms)},
        },
        {
            "id": "requirements",
            "score": req_score,
            "status": req_status,
            "weight": None,
            "values": req_values,
        },
        {
            "id": "evidence",
            "score": ev_score,
            "status": ev_status,
            "weight": None,
            "values": {"provided": provided, "reviewed": reviewed, "applicable": applicable},
        },
        {
            "id": "availability",
            "score": avail_score,
            "status": "MATCH" if available else "MISMATCH",
            "weight": str(WEIGHTS_B["availability"]),
            "values": {"available": available, "reason": avail_reason},
        },
    ]
