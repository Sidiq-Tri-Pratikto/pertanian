"""Scope validity: a total needs positive evidence that loads are separate."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.assets.model.models import BindingModel, RelationKind, RelationModel
from app.energy.service.authority import resolve_asset_authorities, shared_source_pairs
from app.scope.service.validity import IssueType, scope_issues


def _relation(first, second, kind: RelationKind) -> RelationModel:
    return RelationModel(id=uuid4(), site_id=uuid4(), from_asset_id=first, to_asset_id=second, kind=kind)


def test_disjoint_evidence_allows_a_total() -> None:
    """
    Condition:
    - Two assets with a disjoint relation.

    Expected:
    - No issue.
    """
    a, b = uuid4(), uuid4()

    assert scope_issues([a, b], [], [_relation(a, b, RelationKind.DISJOINT)], set()) == []


def test_every_other_case_refuses_the_total() -> None:
    """
    Condition:
    - Indirect containment, an unknown overlap, no evidence, and an asset with unresolved sources.

    Expected:
    - Each produces its issue; the container is named first.
    """
    meter, circuit, kulkas, pompa, tv = (uuid4() for _ in range(5))
    relations = [_relation(meter, pompa, RelationKind.UNKNOWN_OVERLAP)]

    issues = scope_issues([kulkas, meter, pompa, tv], [(meter, circuit), (circuit, kulkas)], relations, {tv})

    assert [(issue.type, issue.asset_ids) for issue in issues if issue.type is not IssueType.UNCONFIRMED] == [
        (IssueType.PARENT_CHILD, [meter, kulkas]),
        (IssueType.UNKNOWN_OVERLAP, [meter, pompa]),
        (IssueType.SOURCE_CONFLICT, [tv]),
    ]
    assert sum(issue.type is IssueType.UNCONFIRMED for issue in issues) == 4


def test_a_single_asset_is_always_summable() -> None:
    """
    Condition:
    - One asset with no relations.

    Expected:
    - No issue.
    """
    assert scope_issues([uuid4()], [], [], set()) == []


def test_contradictory_reversed_evidence_keeps_conflicts_visible() -> None:
    """Positive evidence cannot override unknown overlap, containment, or reuse of a source."""
    first, second, child = (uuid4() for _ in range(3))
    relations = [
        _relation(first, second, RelationKind.DISJOINT),
        _relation(first, second, RelationKind.UNKNOWN_OVERLAP),
        _relation(second, first, RelationKind.UNKNOWN_OVERLAP),
    ]
    shared = {frozenset((first, second))}
    issues = scope_issues([first, second], [], relations, set(), shared)
    assert [issue.type for issue in issues] == [IssueType.SHARED_SOURCE, IssueType.UNKNOWN_OVERLAP]
    issues = scope_issues([first, second], [(first, child), (child, second)], relations, set(), shared)
    assert [issue.type for issue in issues] == [IssueType.SHARED_SOURCE, IssueType.PARENT_CHILD]


def test_shared_source_compares_half_open_implicit_and_explicit_authority() -> None:
    """Intersecting authority refuses a positively disjoint pair even in the absence of readings."""
    site, first, second, source = (uuid4() for _ in range(4))
    start = datetime(2026, 10, 25, tzinfo=UTC)
    midpoint, end = start + timedelta(hours=1), start + timedelta(hours=2)
    explicit = BindingModel(
        id=uuid4(),
        site_id=site,
        asset_id=first,
        source_id=source,
        effective_from=start,
        effective_to=midpoint,
        authoritative=True,
    )
    implicit = explicit.model_copy(
        update={
            "id": uuid4(),
            "asset_id": second,
            "effective_to": end,
            "authoritative": False,
        }
    )
    assets = [first, second]
    positive = [_relation(first, second, RelationKind.DISJOINT)]
    overlap = resolve_asset_authorities(assets, [explicit, implicit], start, end)
    issues = scope_issues(assets, [], positive, set(), shared_source_pairs(overlap))
    assert [issue.type for issue in issues] == [IssueType.SHARED_SOURCE]
    adjacent = resolve_asset_authorities(
        assets, [explicit, implicit.model_copy(update={"effective_from": midpoint})], start, end
    )
    assert scope_issues(assets, [], positive, set(), shared_source_pairs(adjacent)) == []
