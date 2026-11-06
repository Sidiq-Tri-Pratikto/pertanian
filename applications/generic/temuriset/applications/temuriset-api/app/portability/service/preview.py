"""Compare normalized source rows against owned drafts and reviewed facts."""

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from app.portability.model.schema import ConflictField
from app.portability.service.file_format import InventionRow, same_fact
from app.portfolio.model.schema import FactInput, InventionResponse, InventionVersionResponse


def _protected(fact: FactInput) -> bool:
    key = (fact.key or fact.label).casefold()
    return (
        fact.provenance == "REVIEWED"
        or fact.document_version_id is not None
        or key.startswith(("rights", "authority", "ownership"))
    )


def _value(fact: FactInput) -> tuple[str, str, str, str]:
    return fact.label, fact.value, fact.unit, fact.timing


@dataclass
class DraftComparison:
    """Only the differences safe to apply and names of fields needing owner review."""

    changes: dict[str, Any]
    conflicts: list[ConflictField]


def compare_draft(row: InventionRow, current: InventionResponse | None) -> DraftComparison:
    """Merge supplied fields and facts, preserving reviewed values and omitted data."""
    updates = row.fields.model_dump(mode="json", exclude_unset=True, exclude={"facts"})
    if current is None:
        if row.fields.facts:
            updates["facts"] = [fact.model_dump(mode="json") for fact in row.fields.facts]
        return DraftComparison(updates, [])

    conflicts: list[ConflictField] = []
    if current.status == "ARCHIVED":
        conflicts.append("destination")
    baseline = current.draft or current.published
    versions = [version for version in (current.draft, current.published) if version is not None]
    if _reviewed_claim_conflict(row, versions):
        conflicts.append("rights_claims")
    existing = list(baseline.facts) if baseline else []
    protected = [fact for version in versions for fact in version.facts if _protected(fact)]
    merged: list[FactInput] = list(existing)
    for incoming in row.fields.facts:
        matches = [index for index, fact in enumerate(merged) if same_fact(incoming, fact)]
        comparisons = [fact for fact in protected if same_fact(incoming, fact)]
        if comparisons:
            if any(_value(incoming) != _value(previous) for previous in comparisons):
                conflicts.append("facts")
            # A matching assertion does not replace the reviewed fact or its provenance.
        elif len(matches) > 1:
            conflicts.append("facts")
        elif matches:
            merged[matches[0]] = incoming
        else:
            merged.append(incoming)
    if len(merged) > 50:
        conflicts.append("facts")
    elif merged != existing:
        updates["facts"] = [fact.model_dump(mode="json") for fact in merged]
    if baseline:
        data = baseline.model_dump(mode="json")
        updates = {field: value for field, value in updates.items() if value != data[field]}
    return DraftComparison(updates, list(dict.fromkeys(conflicts)))


def _reviewed_claim_conflict(row: InventionRow, versions: Iterable[InventionVersionResponse]) -> bool:
    return any(
        previous.kind == incoming.kind
        and previous.status == "reviewed"
        and (previous.subject_name, previous.scope) != (incoming.subject_name, incoming.scope)
        for version in versions
        for previous in version.claims
        for incoming in row.rights_claims
    )
