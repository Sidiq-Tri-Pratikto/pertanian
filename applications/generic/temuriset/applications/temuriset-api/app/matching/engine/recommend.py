"""Honest, conditional improvement recommendations with engine-computed what-if estimates (spec 058). Pure Python."""

from dataclasses import replace
from decimal import Decimal
from typing import Any

from app.matching.engine.evaluate import ENTRY, evaluate
from app.matching.engine.fit import extract_terms, join_normalized_text
from app.matching.engine.inputs import Source, Target
from app.matching.engine.requirements import FAIL, PASS, UNKNOWN

_KIND_ORDER: dict[str, int] = {
    "no_need": 0,
    "requirement": 1,
    "tkt_below": 2,
    "topic": 3,
    "money_missing": 4,
    "money_gap": 5,
    "form": 6,
    "evidence": 7,
    "tkt_missing": 8,
    "stage": 9,
    "sector": 10,
    "availability": 11,
}


def _estimate(base: dict[str, Any], modified: Source, target: Target) -> dict[str, Any]:
    after = evaluate(modified, target)
    gain = Decimal(after["fit"]["lower"]) - Decimal(base["fit"]["lower"])
    return {
        "label": after["label"],
        "fit": after["fit"],
        "gain": str(gain),
    }


def _requirement_target(source: Source, action: str | None, field: str) -> dict[str, Any]:
    if action == "add-document" or field.startswith("document:"):
        return {"invention_id": source.invention_id, "field": "documents"}
    if action == "add-fact" or field.startswith("feature:"):
        return {"invention_id": source.invention_id, "field": "facts"}
    if action == "complete-budget" or field == "budget":
        return {"need_id": source.id, "source_type": source.type, "field": "budget"}
    if action == "complete-contribution" or field == "contribution":
        return {"need_id": source.id, "source_type": source.type, "field": "contribution"}
    if action == "clarify-authority" or field == "authority":
        return {"invention_id": source.invention_id, "field": "authority"}
    if field == "relationship":
        return {"need_id": source.id, "source_type": source.type, "field": "form"}
    if field == "stage":
        return {"invention_id": source.invention_id, "field": "stage"}
    return {}


def _requirement_what_if(source: Source, target: Target, row: dict[str, Any]) -> Source | None:
    field = row["field"]
    if field == "stage":
        return None  # Honesty principle: never estimate changing stage.
    if field.startswith("document:"):
        key = field.partition(":")[2]
        docs = dict(source.documents)
        docs[key] = ({"DOCUMENT_PRESENT": PASS, "REVIEWER_CONFIRMED": PASS},)
        return replace(source, documents=docs)
    if field.startswith("feature:"):
        key = field.partition(":")[2]
        return replace(source, facts=(*source.facts, (key, "CURRENT")))
    if field == "budget" and target.financial is not None and target.financial.known:
        return replace(source, budget=target.financial)
    if field == "contribution" and target.financial is not None and target.financial.known:
        return replace(source, contribution=target.financial)
    if field == "authority":
        return replace(source, authority=(*source.authority, "reviewed"))
    if field == "entity":
        return replace(source, entity="IDENTIFIED")
    if field == "relationship" and target.relationship_forms:
        return replace(source, relationship=target.relationship_forms[0])
    return None


def _dim(result: dict[str, Any], dim_id: str) -> dict[str, Any] | None:
    for item in result.get("breakdown", []):
        if item["id"] == dim_id:
            return item
    return None


def _sort_key(item: dict[str, Any]) -> tuple[int, int, int, Decimal, int]:
    is_no_need = 0 if item["kind"] == "no_need" else 1
    blocking = 0 if item["blocking"] else 1
    est = item.get("estimate")
    has_est = 0 if est is not None else 1
    gain = -Decimal(est["gain"]) if est is not None else Decimal(0)
    return (is_no_need, blocking, has_est, gain, _KIND_ORDER.get(item["kind"], 99))


def recommend(source: Source, target: Target, result: dict[str, Any], *, preview: bool = False) -> list[dict[str, Any]]:
    """Produce ordered, conditional improvement recommendations for an applicant (spec 058).

    Never called for recipients or investor previews. Never suggests changing sector or stage for a higher score.

    Args:
        source (Source): The applicant's source projection.
        target (Target): The mandate projection.
        result (dict[str, Any]): The evaluated result from ``evaluate(source, target)``.
        preview (bool, optional): Whether ``source`` is a need-less preview from a published product. Defaults to False.

    Returns:
        list[dict[str, Any]]: Ordered JSON-ready recommendation dictionaries.
    """
    items: list[dict[str, Any]] = []
    if preview:
        items.append(
            {
                "kind": "no_need",
                "blocking": False,
                "dimension": None,
                "target": {"invention_id": source.invention_id, "field": "new_need"},
                "values": {},
                "estimate": None,
            }
        )

    # 1. Blocking entry-stage required items.
    covered_doc_keys: set[str] = set()
    covered_money_req = False
    for row in result.get("rows", []):
        if row["applies_at"] == ENTRY and row["mandatory"] and row["result"] in (FAIL, UNKNOWN):
            field = row["field"]
            if field.startswith("document:"):
                covered_doc_keys.add(field.partition(":")[2])
            if field in ("budget", "contribution"):
                covered_money_req = True
            modified = _requirement_what_if(source, target, row)
            items.append(
                {
                    "kind": "requirement",
                    "blocking": True,
                    "dimension": "requirements",
                    "target": _requirement_target(source, row.get("action"), field),
                    "values": {
                        "label": row["label"],
                        "reason": row["reason"],
                        "action": row.get("action"),
                        "field": field,
                        "result": row["result"],
                    },
                    "estimate": _estimate(result, modified, target) if modified is not None else None,
                }
            )

    # 2. Topic shortfall.
    topic_dim = _dim(result, "topic")
    if topic_dim and topic_dim["score"] is not None and topic_dim["score"] < 100:
        missing = list(topic_dim["values"].get("missing") or [])
        if missing:
            new_keywords = tuple((*source.keywords, *missing))
            modified = replace(
                source,
                keywords=new_keywords,
                text_terms=extract_terms(new_keywords, source.text),
                text=join_normalized_text(new_keywords, source.text),
            )
            items.append(
                {
                    "kind": "topic",
                    "blocking": False,
                    "dimension": "topic",
                    "target": {"invention_id": source.invention_id, "field": "keywords"},
                    "values": {"missing": missing, "matched": list(topic_dim["values"].get("matched") or [])},
                    "estimate": _estimate(result, modified, target),
                }
            )

    # 3. Readiness (TKT below / TKT missing / stage not accepted).
    readiness_dim = _dim(result, "readiness")
    if readiness_dim:
        r_vals = readiness_dim["values"]
        tkt = r_vals.get("tkt")
        min_tkt = r_vals.get("min_tkt")
        stage = r_vals.get("stage")
        accepted_stages = list(r_vals.get("accepted_stages") or [])
        if min_tkt is not None and tkt is not None and tkt < min_tkt:
            items.append(
                {
                    "kind": "tkt_below",
                    "blocking": False,
                    "dimension": "readiness",
                    "target": {"invention_id": source.invention_id, "field": "tkt"},
                    "values": {"tkt": tkt, "min_tkt": min_tkt},
                    "estimate": _estimate(result, replace(source, tkt=min_tkt), target),
                }
            )
        elif min_tkt is not None and tkt is None:
            items.append(
                {
                    "kind": "tkt_missing",
                    "blocking": False,
                    "dimension": "readiness",
                    "target": {"invention_id": source.invention_id, "field": "tkt"},
                    "values": {"min_tkt": min_tkt},
                    "estimate": _estimate(result, replace(source, tkt=min_tkt), target),
                }
            )
        if stage is not None and accepted_stages and stage not in accepted_stages:
            items.append(
                {
                    "kind": "stage",
                    "blocking": False,
                    "dimension": "readiness",
                    "target": {"invention_id": source.invention_id, "field": "stage"},
                    "values": {"stage": stage, "accepted_stages": accepted_stages},
                    "estimate": None,
                }
            )

    # 4. Money (only when not a need-less preview).
    money_dim = _dim(result, "money")
    if not preview and money_dim:
        source_money = source.contribution if source.type == "FUNDING_REQUEST" else source.budget
        money_field = "contribution" if source.type == "FUNDING_REQUEST" else "budget"
        expected_subject = "investorCheck" if source.type == "FUNDING_REQUEST" else "partner"
        comparable_target = (
            target.financial
            if target.financial is not None and target.financial.known and target.financial.subject == expected_subject
            else None
        )
        if money_dim["score"] is None and not covered_money_req and (source_money is None or not source_money.known):
            modified = (
                replace(
                    source,
                    **(
                        {"contribution": comparable_target}
                        if source.type == "FUNDING_REQUEST"
                        else {"budget": comparable_target}
                    ),
                )
                if comparable_target is not None
                else None
            )
            items.append(
                {
                    "kind": "money_missing",
                    "blocking": False,
                    "dimension": "money",
                    "target": {"need_id": source.id, "source_type": source.type, "field": money_field},
                    "values": {"target": money_dim["values"].get("target")},
                    "estimate": _estimate(result, modified, target) if modified is not None else None,
                }
            )
        elif money_dim["score"] in (0, 50) and not covered_money_req:
            modified = (
                replace(
                    source,
                    **(
                        {"contribution": comparable_target}
                        if source.type == "FUNDING_REQUEST"
                        else {"budget": comparable_target}
                    ),
                )
                if comparable_target is not None
                else None
            )
            items.append(
                {
                    "kind": "money_gap",
                    "blocking": False,
                    "dimension": "money",
                    "target": {"need_id": source.id, "source_type": source.type, "field": money_field},
                    "values": {
                        "source": money_dim["values"].get("source"),
                        "target": money_dim["values"].get("target"),
                        "accepts_partial": source.accepts_partial,
                    },
                    "estimate": _estimate(result, modified, target) if modified is not None else None,
                }
            )

    # 5. Form of partnership (only when not a need-less preview).
    form_dim = _dim(result, "form")
    if not preview and form_dim and form_dim["score"] == 0 and target.relationship_forms:
        modified = replace(source, relationship=target.relationship_forms[0])
        items.append(
            {
                "kind": "form",
                "blocking": False,
                "dimension": "form",
                "target": {"need_id": source.id, "source_type": source.type, "field": "form"},
                "values": {"source": source.relationship, "target": list(target.relationship_forms)},
                "estimate": _estimate(result, modified, target),
            }
        )

    # 6. Evidence (remaining non-blocking unprovided documents).
    ev_dim = _dim(result, "evidence")
    if ev_dim and ev_dim["score"] is not None and ev_dim["score"] < 100:
        missing_docs = [
            row
            for row in result.get("rows", [])
            if row["field"].startswith("document:")
            and row["result"] != PASS
            and row["field"].partition(":")[2] not in covered_doc_keys
        ]
        if missing_docs:
            docs = dict(source.documents)
            for row in missing_docs:
                docs[row["field"].partition(":")[2]] = ({"DOCUMENT_PRESENT": PASS, "REVIEWER_CONFIRMED": PASS},)
            items.append(
                {
                    "kind": "evidence",
                    "blocking": False,
                    "dimension": "evidence",
                    "target": {"invention_id": source.invention_id, "field": "documents"},
                    "values": {"items": [row["label"] for row in missing_docs]},
                    "estimate": _estimate(result, replace(source, documents=docs), target),
                }
            )

    # 7. Sector mismatch (no estimate per honesty principle).
    sector_dim = _dim(result, "sector")
    if sector_dim and sector_dim["score"] == 0:
        items.append(
            {
                "kind": "sector",
                "blocking": False,
                "dimension": "sector",
                "target": {"invention_id": source.invention_id, "field": "sector"},
                "values": {"source": source.sector, "target": list(target.sectors)},
                "estimate": None,
            }
        )

    # 8. Investor unavailable.
    avail_dim = _dim(result, "availability")
    if avail_dim and avail_dim["score"] == 0:
        items.append(
            {
                "kind": "availability",
                "blocking": False,
                "dimension": "availability",
                "target": {"partner_party_id": target.partner_party_id},
                "values": {"reason": avail_dim["values"].get("reason")},
                "estimate": None,
            }
        )

    items.sort(key=_sort_key)
    return items
