"""Plan authority and relation edits without persisting the projected state."""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from app.assets.model.models import BindingModel, RelationKind, RelationModel
from app.core.errors.base import NotFoundError
from app.energy.service.authority import binding_active_at


class AmbiguousAuthorityError(Exception):
    """Multiple rows could represent the requested source at the effective instant."""


@dataclass
class AuthorityChange:
    """The changed interval and the edits that realize it."""

    asset_id: UUID
    source_id: UUID
    start: datetime
    end: datetime | None
    updated: list[BindingModel] = field(default_factory=list)
    inserted: list[BindingModel] = field(default_factory=list)

    def split(self, binding: BindingModel, authoritative: bool) -> None:
        """Retain the original row ID on the first segment."""
        start = max(binding.effective_from, self.start)
        end = _first_end(binding.effective_to, self.end)
        segments = []
        if binding.effective_from < start:
            segments.append(binding.model_copy(update={"effective_to": start}))
        segments.append(
            binding.model_copy(
                update={
                    "effective_from": start,
                    "effective_to": end,
                    "authoritative": authoritative,
                }
            )
        )
        if end is not None and (binding.effective_to is None or end < binding.effective_to):
            segments.append(binding.model_copy(update={"effective_from": end}))
        self.updated.append(segments[0])
        self.inserted.extend(segment.model_copy(update={"id": uuid4()}) for segment in segments[1:])


def _first_end(first: datetime | None, second: datetime | None) -> datetime | None:
    if first is None or second is None:
        return first or second
    return min(first, second)


def plan_authority(bindings: list[BindingModel], source_id: UUID, at: datetime) -> AuthorityChange | None:
    """Choose one candidate until it ends or an already scheduled authority begins."""
    candidates = [row for row in bindings if row.source_id == source_id and binding_active_at(row, at)]
    if not candidates:
        raise NotFoundError()
    if len(candidates) != 1:
        raise AmbiguousAuthorityError()
    candidate = candidates[0]
    if candidate.authoritative:
        return None

    explicit = [row for row in bindings if row.authoritative]
    next_start = min((row.effective_from for row in explicit if row.effective_from > at), default=None)
    end = _first_end(candidate.effective_to, next_start)
    change = AuthorityChange(candidate.asset_id, source_id, at, end)
    for row in explicit:
        if binding_active_at(row, at):
            change.split(row, authoritative=False)
    # Old authority must be shortened or demoted before the candidate can be promoted.
    change.split(candidate, authoritative=True)
    return change


@dataclass
class DisjointChange:
    """Remove contrary unknown edges and supply positive evidence if absent."""

    pair: tuple[UUID, UUID]
    removed: list[UUID]
    added: RelationModel | None


def plan_disjoint(
    site_id: UUID, relations: list[RelationModel], pairs: list[tuple[UUID, UUID]]
) -> list[DisjointChange]:
    """Plan one change per validated unordered pair, accepting legacy reverse edges."""
    by_pair: dict[frozenset[UUID], list[RelationModel]] = {}
    for relation in relations:
        key = frozenset((relation.from_asset_id, relation.to_asset_id))
        by_pair.setdefault(key, []).append(relation)

    changes = []
    for first, second in pairs:
        existing = by_pair.get(frozenset((first, second)), [])
        removed = [relation.id for relation in existing if relation.kind is RelationKind.UNKNOWN_OVERLAP]
        added = None
        if not any(relation.kind is RelationKind.DISJOINT for relation in existing):
            added = RelationModel(
                id=uuid4(), site_id=site_id, from_asset_id=first, to_asset_id=second, kind=RelationKind.DISJOINT
            )
        if removed or added is not None:
            changes.append(DisjointChange((first, second), removed, added))
    return changes
