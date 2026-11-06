"""Engine inputs built from the plain fixture data, with no database."""

from dataclasses import replace
from decimal import Decimal
from typing import Any

from app.matching.engine.inputs import Money, Source, Target
from tests.factories.inventors import F01_GAP_BUDGET, FRAISE01, INVENTIONS, SUPPORT_REQUESTS
from tests.factories.recipients import OPPORTUNITIES, PROFILES


def _money(values: dict[str, Any] | None, **extra: Any) -> Money | None:
    if values is None:
        return None
    low, high = values.get("min"), values.get("max")
    return Money(
        low=None if low is None else Decimal(low),
        high=None if high is None else Decimal(high),
        currency=values.get("currency"),
        subject=values.get("subject"),
        basis=values.get("basis"),
        months=values.get("months"),
        scope=values.get("scope", ""),
        **extra,
    )


def target(key: str, **changes: Any) -> Target:
    """Opportunity ``key`` (such as ``A1``) as the engine reads it.

    Args:
        key (str): Target.
        **changes (Any): Fields to replace.

    Returns:
        Target: The engine input.
    """
    content = OPPORTUNITIES[key]["content"]
    built = Target(
        opportunity_id=key,
        version_id=f"{key}-v1",
        number=1,
        partner_party_id=OPPORTUNITIES[key]["partner"],
        partner_name=PROFILES[OPPORTUNITIES[key]["partner"]]["party"]["name"],
        title=content["title"],
        active=True,
        accepted_stages=tuple(content["accepted_stages"]),
        sectors=tuple(content["sectors"]),
        keywords=tuple(content["keywords"]),
        relationship_forms=tuple(content["relationship_forms"]),
        financial=_money(content["financial"]) if content["financial"].get("min") else None,
        requirements=tuple(
            {**requirement, "id": f"{key}-{position}"} for position, requirement in enumerate(content["requirements"])
        ),
        availability={"available": True, "reason": None},
    )
    return replace(built, **changes)


def _invention(key: str) -> dict[str, Any]:
    content = INVENTIONS[key]["content"]
    return {
        "stage": content["stage"],
        "sector": content["sector"],
        "keywords": tuple(content["keywords"]),
        "facts": tuple((fact["key"], fact["timing"]) for fact in content["facts"] if fact["key"]),
        "authority": tuple(
            claim.get("status", "asserted") for claim in content.get("claims", []) if claim["kind"] == "authority"
        ),
        "documents": {
            name: ({"DOCUMENT_PRESENT": "PASS", "REVIEWER_CONFIRMED": "UNKNOWN"},)
            for name in INVENTIONS[key].get("documents", {})
        },
    }


def support(key: str, *, gap: bool = False, **changes: Any) -> Source:
    """Fixture ``key``'s support request (such as ``F01``) as the engine reads it.

    Args:
        key (str): Fixture.
        gap (bool, optional): F01-GAP. Defaults to False.
        **changes (Any): Fields to replace.

    Returns:
        Source: The engine input.
    """
    request = SUPPORT_REQUESTS[key]
    budget = F01_GAP_BUDGET if gap else request["budget"]
    built = Source(
        type="SUPPORT_REQUEST",
        id=key,
        version=1,
        relationship=request["relationship_form"],
        budget=_money({**budget, "basis": budget.get("basis", "total_period"), "months": request["months"]}),
        accepts_partial=request["accepts_partial"],
        **_invention(key),
    )
    return replace(built, **changes)


def fraise01(*, proposed: bool = False) -> Source:
    """FRaise01 as the engine reads it.

    Args:
        proposed (bool, optional): For a company not founded yet. Defaults to False.

    Returns:
        Source: The engine input.
    """
    first, second = (_invention(key) for key in FRAISE01["inventions"])
    content = FRAISE01["content"]
    return Source(
        type="FUNDING_REQUEST",
        id="FRaise01",
        version=1,
        stage=first["stage"],
        sector=first["sector"],
        keywords=first["keywords"] + second["keywords"],
        relationship="EQUITY",
        entity="PROPOSED" if proposed else "IDENTIFIED",
        contribution=Money(
            low=Decimal(content["desired_min"]), high=Decimal(content["desired_max"]), currency=content["currency"]
        ),
        accepts_partial=content["accepts_partial"],
    )


def row(result: dict[str, Any], label: str) -> dict[str, Any]:
    """Find a requirement row by label.

    Args:
        result (dict[str, Any]): An engine result.
        label (str): The requirement's label.

    Returns:
        dict[str, Any]: The row.
    """
    return next(item for item in result["rows"] if item["label"] == label)
