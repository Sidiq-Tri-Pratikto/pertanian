"""Whether selected assets may be added together. Unknown is never treated as disjoint."""

from collections import defaultdict
from enum import StrEnum
from itertools import combinations
from uuid import UUID

from pydantic import BaseModel

from app.assets.model.models import RelationKind, RelationModel


class IssueType(StrEnum):
    """Why a combined total is refused."""

    PARENT_CHILD = "parent_child"
    UNKNOWN_OVERLAP = "unknown_overlap"
    UNCONFIRMED = "unconfirmed"
    SOURCE_CONFLICT = "source_conflict"
    SHARED_SOURCE = "shared_source"


class ScopeIssue(BaseModel):
    """One reason the selection cannot be summed."""

    type: IssueType
    asset_ids: list[UUID]


def containment_closure(containment: list[tuple[UUID, UUID]]) -> set[tuple[UUID, UUID]]:
    """Return all directed containment pairs, including transitive relationships."""
    children: dict[UUID, set[UUID]] = defaultdict(set)
    for parent, child in containment:
        children[parent].add(child)
    closed: set[tuple[UUID, UUID]] = set()
    for root in list(children):
        stack, seen = list(children[root]), set()
        while stack:
            node = stack.pop()
            if node in seen:
                continue
            seen.add(node)
            closed.add((root, node))
            stack.extend(children.get(node, ()))
    return closed


def scope_issues(
    selected: list[UUID],
    containment: list[tuple[UUID, UUID]],
    relations: list[RelationModel],
    conflicted: set[UUID],
    shared_sources: set[frozenset[UUID]] | None = None,
) -> list[ScopeIssue]:
    """List every reason the selected assets cannot be added together.

    A pair adds up only when a ``disjoint`` relation says so. Containment, direct or through intermediate
    assets, an unknown overlap, or no evidence at all each refuse the combined total. An asset with
    unresolved alternative sources has no value to add.

    Args:
        selected (list[UUID]): Selected active assets, in a stable order.
        containment (list[tuple[UUID, UUID]]): (container, contained) pairs.
        relations (list[RelationModel]): The site's relations.
        conflicted (set[UUID]): Assets with unresolved alternative sources in the window.
        shared_sources (set[frozenset[UUID]] | None): Asset pairs whose effective source authority overlaps.

    Returns:
        list[ScopeIssue]: Issues; empty when the total is valid.
    """
    contains = containment_closure(containment)
    known: dict[frozenset[UUID], set[RelationKind]] = defaultdict(set)
    for relation in relations:
        known[frozenset((relation.from_asset_id, relation.to_asset_id))].add(relation.kind)
    issues: list[ScopeIssue] = []
    for first, second in combinations(selected, 2):
        pair = frozenset((first, second))
        if shared_sources and pair in shared_sources:
            issues.append(ScopeIssue(type=IssueType.SHARED_SOURCE, asset_ids=[first, second]))
        if (second, first) in contains:
            first, second = second, first  # Container first.
        if (first, second) in contains:
            issue = IssueType.PARENT_CHILD
        elif RelationKind.UNKNOWN_OVERLAP in known[pair]:
            issue = IssueType.UNKNOWN_OVERLAP
        elif RelationKind.DISJOINT in known[pair]:
            continue
        else:
            issue = IssueType.UNCONFIRMED
        issues.append(ScopeIssue(type=issue, asset_ids=[first, second]))
    issues.extend(
        ScopeIssue(type=IssueType.SOURCE_CONFLICT, asset_ids=[asset_id])
        for asset_id in selected
        if asset_id in conflicted
    )
    return issues
