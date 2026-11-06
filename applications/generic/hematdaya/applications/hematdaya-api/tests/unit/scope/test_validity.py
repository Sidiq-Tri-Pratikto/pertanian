"""Scope validity: a total needs positive evidence that loads are separate."""

from uuid import uuid4

from app.assets.model.models import RelationKind, RelationModel
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
