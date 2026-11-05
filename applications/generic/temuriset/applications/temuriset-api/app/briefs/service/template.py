"""The deterministic template brief: every sentence comes from a supplied fact and says which (FR-002)."""

from typing import Any

from app.funding.model.schema import FundingRequestResponse
from app.needs.model.schema import SupportRequestResponse
from app.portfolio.model.schema import InventionVersionResponse

_BASIS = {"total_period": "total", "monthly": "per bulan", "yearly": "per tahun"}
_TEAM = {"creator": "pembuat", "contributor": "kontributor", "manager": "pengelola"}


def amount(value: str) -> str:
    """Indonesian grouping for a decimal string, as the web's ``money.ts`` shows it; never through a float.

    Args:
        value (str): A decimal string such as ``"20000.0000"``.

    Returns:
        str: ``"20.000"``.
    """
    whole, _, fraction = value.partition(".")
    grouped = f"{int(whole):,}".replace(",", ".")
    fraction = fraction.rstrip("0")
    return f"{grouped},{fraction}" if fraction else grouped


def _sentence(text: str, *refs: dict[str, Any]) -> dict[str, Any]:
    return {"text": text, "refs": list(refs)}


def _invention_sentences(versions: list[InventionVersionResponse], ids: list[str]) -> list[dict[str, Any]]:
    sentences = []
    many = len(versions) > 1
    for version, version_id in zip(versions, ids, strict=True):
        ref = {"kind": "invention_version", "id": version_id}
        label = f" ({version.title})" if many else ""
        sentences.append(_sentence(f"Masalah{label}: {version.problem}", ref))
        sentences.append(_sentence(f"Solusi saat ini{label}: {version.solution}", ref))
        for position, fact in enumerate(version.facts):
            unit = f" {fact.unit}" if fact.unit else ""
            when = "Saat ini" if fact.timing == "CURRENT" else "Direncanakan"
            fact_ref = {
                "kind": "fact",
                "id": version_id,
                "position": position,
                "document_version_id": str(fact.document_version_id) if fact.document_version_id else None,
            }
            sentences.append(_sentence(f"{when}: {fact.label} {fact.value}{unit}.", fact_ref))
    return sentences


def _money_sentence(request: SupportRequestResponse | None, raise_: FundingRequestResponse | None) -> dict[str, Any]:
    if raise_ is not None:
        ref = {"kind": "funding_request", "id": str(raise_.id), "version": raise_.version}
        currency = raise_.currency or ""
        if raise_.target_amount and raise_.desired_min and raise_.desired_max:
            return _sentence(
                f"Target Pendanaan {currency} {amount(raise_.target_amount)} untuk satu perusahaan; kontribusi yang "
                f"diinginkan {currency} {amount(raise_.desired_min)}–{amount(raise_.desired_max)} per investor.",
                ref,
            )
        return _sentence("Kisaran pendanaan belum ditentukan.", ref)
    assert request is not None  # noqa: S101 - a brief has exactly one source
    ref = {"kind": "support_request", "id": str(request.id), "version": request.version}
    budget = request.budget
    if budget is None or budget.min is None or budget.max is None:
        return _sentence("Kebutuhan dana belum ditentukan.", ref)
    period = f" {budget.period}" if budget.period else ""
    scope = f" untuk {budget.scope}" if budget.scope else ""
    money = f"{budget.currency} {amount(budget.min)}–{amount(budget.max)}"
    return _sentence(f"Kebutuhan {money}, {_BASIS[budget.basis]}{period}{scope}.", ref)


def template_brief(
    *,
    versions: list[InventionVersionResponse],
    version_ids: list[str],
    request: SupportRequestResponse | None,
    raise_: FundingRequestResponse | None,
    opportunity: dict[str, Any],
    result: dict[str, Any],
) -> list[dict[str, Any]]:
    """Build the brief from the source, its invention versions and the match result only.

    Args:
        versions (list[InventionVersionResponse]): Linked invention versions, in order.
        version_ids (list[str]): Their ids.
        request (SupportRequestResponse | None): The support request, when that is the source.
        raise_ (FundingRequestResponse | None): The raise, when that is the source.
        opportunity (dict[str, Any]): ``id``, ``version_id`` and ``title`` of the target.
        result (dict[str, Any]): The engine's result for this target.

    Returns:
        list[dict[str, Any]]: Sentences with their references.
    """
    sentences = _invention_sentences(versions, version_ids)
    if raise_ is not None:
        ref = {"kind": "funding_request", "id": str(raise_.id), "version": raise_.version}
        purpose = raise_.intended_use or "pengembangan perusahaan"
        sentences.append(_sentence(f"Pendanaan perusahaan untuk {raise_.subject_label}: {purpose}.", ref))
    elif request is not None:
        ref = {"kind": "support_request", "id": str(request.id), "version": request.version}
        sentences.append(_sentence(f"Dukungan yang diminta: {request.outcome or 'belum dinyatakan'}.", ref))
    sentences.append(_money_sentence(request, raise_))
    target = {"kind": "opportunity", "id": opportunity["id"], "version_id": opportunity["version_id"]}
    reasons = "; ".join(reason.rstrip(".") for reason in result["reasons"])
    sentences.append(_sentence(f"Relevansi: {opportunity['title']}{'. ' + reasons if reasons else ''}.", target))
    for row in result["rows"]:
        if row["result"] != "PASS":
            sentences.append(_sentence(f"Belum selesai: {row['label']}. {row['reason']}", target))
    team = [
        f"{claim.subject_name} ({_TEAM[claim.kind]})"
        for version, version_id in zip(versions, version_ids, strict=True)
        for claim in version.claims
        if claim.kind in _TEAM
    ]
    if team:
        sentences.append(
            _sentence(
                f"Tim: {', '.join(dict.fromkeys(team))}.",
                *({"kind": "invention_version", "id": i} for i in version_ids),
            )
        )
    return sentences


def brief_text(sentences: list[dict[str, Any]]) -> str:
    """Join sentences into the editable text, one per line.

    Args:
        sentences (list[dict[str, Any]]): Sentences.

    Returns:
        str: The text.
    """
    return "\n".join(sentence["text"] for sentence in sentences)
