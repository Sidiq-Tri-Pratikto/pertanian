"""Effective-dated changes preserve authority outside the proposed interval."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.assets.model.models import BindingModel
from app.energy.service.authority import resolve_authority

START = datetime(2026, 10, 24, tzinfo=UTC)
CUT = START + timedelta(hours=1)
END = START + timedelta(hours=2)
LATER = START + timedelta(hours=3)


def _binding(asset, source, start=START, end=None, *, authoritative=False) -> BindingModel:
    return BindingModel(
        id=uuid4(),
        site_id=uuid4(),
        asset_id=asset,
        source_id=source,
        effective_from=start,
        effective_to=end,
        authoritative=authoritative,
    )


@pytest.mark.parametrize(("candidate_end", "next_start", "effective_end"), [(END, LATER, END), (None, END, END)])
def test_switch_splits_both_timelines(candidate_end, next_start, effective_end) -> None:
    """A finite candidate end or a later explicit start bounds the new authority."""
    from app.scope.service.proposal import plan_authority

    asset, old, chosen, next_source = (uuid4() for _ in range(4))
    current = _binding(asset, old, end=next_start, authoritative=True)
    candidate = _binding(asset, chosen, end=candidate_end)
    later = _binding(asset, next_source, start=next_start, authoritative=True)
    change = plan_authority([current, candidate, later], chosen, CUT)
    assert change is not None and change.start == CUT and change.end == effective_end
    projected = [*change.updated, *change.inserted, later]
    assert [
        (part.source_id, part.start, part.end)
        for part in resolve_authority(projected, START, LATER + timedelta(hours=1)).parts
    ] == [
        (old, START, CUT),
        (chosen, CUT, effective_end),
        *([(old, END, LATER)] if candidate_end else []),
        (next_source, next_start, LATER + timedelta(hours=1)),
    ]
    assert {binding.id for binding in change.updated} == {current.id, candidate.id}
    assert plan_authority(projected, chosen, CUT) is None


def test_an_implicit_binding_becomes_explicit_even_from_its_start() -> None:
    """An explicit confirmation changes the implicit single candidate without generating extra segments."""
    from app.scope.service.proposal import plan_authority

    candidate = _binding(uuid4(), uuid4())
    change = plan_authority([candidate], candidate.source_id, START)
    assert change is not None and change.end is None
    assert change.updated == [candidate.model_copy(update={"authoritative": True})]
    assert change.inserted == []


def test_repeated_candidates_are_ambiguous_at_the_cutover() -> None:
    """Two active rows for the same proposed source do not identify one candidate."""
    from app.scope.service.proposal import AmbiguousAuthorityError, plan_authority

    candidate = _binding(uuid4(), uuid4())
    duplicate = candidate.model_copy(update={"id": uuid4(), "effective_from": CUT})
    with pytest.raises(AmbiguousAuthorityError):
        plan_authority([candidate, duplicate], candidate.source_id, CUT)
