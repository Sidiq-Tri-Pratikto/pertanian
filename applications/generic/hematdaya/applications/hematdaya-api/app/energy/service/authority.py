"""Which source speaks for an asset at each instant, from its effective bindings."""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from app.assets.model.models import BindingModel


@dataclass(frozen=True)
class AuthorityPart:
    """A source attributed to an asset over ``[start, end)``."""

    source_id: UUID
    start: datetime
    end: datetime


@dataclass
class AssetAuthority:
    """Resolved authority within a window: parts that count, and candidates left unresolved."""

    parts: list[AuthorityPart] = field(default_factory=list)
    conflicts: list[AuthorityPart] = field(default_factory=list)


def _extend(target: list[AuthorityPart], source_id: UUID, start: datetime, end: datetime) -> None:
    if target and target[-1].source_id == source_id and target[-1].end == start:
        target[-1] = AuthorityPart(source_id, target[-1].start, end)
    else:
        target.append(AuthorityPart(source_id, start, end))


def binding_active_at(binding: BindingModel, at: datetime) -> bool:
    """Whether the instant lies inside this binding's half-open range."""
    return binding.effective_from <= at and (binding.effective_to is None or at < binding.effective_to)


def resolve_authority(bindings: list[BindingModel], start: datetime, end: datetime) -> AssetAuthority:
    """Resolve an asset's sources over ``[start, end)``.

    An authoritative binding wins. Without one, a single candidate counts. Two or more candidates at once are
    unresolved: none of them counts, and their ranges are reported so values can be shown side by side.

    Args:
        bindings (list[BindingModel]): The asset's bindings.
        start (datetime): Window start.
        end (datetime): Window end.

    Returns:
        AssetAuthority: Counting parts and unresolved candidates.
    """
    ranges = [
        (binding, max(start, binding.effective_from), min(end, binding.effective_to or end)) for binding in bindings
    ]
    ranges = [(binding, lo, hi) for binding, lo, hi in ranges if lo < hi]
    points = sorted({point for _, lo, hi in ranges for point in (lo, hi)})
    authority = AssetAuthority()
    for lo, hi in zip(points, points[1:], strict=False):
        active = [binding for binding, b_lo, b_hi in ranges if b_lo <= lo and hi <= b_hi]
        leaders = [binding for binding in active if binding.authoritative] or active
        if len(leaders) == 1:
            _extend(authority.parts, leaders[0].source_id, lo, hi)
        elif leaders:
            for binding in sorted(leaders, key=lambda item: str(item.source_id)):
                authority.conflicts.append(AuthorityPart(binding.source_id, lo, hi))
    return authority


def resolve_asset_authorities(
    asset_ids: list[UUID], bindings: list[BindingModel], start: datetime, end: datetime
) -> dict[UUID, AssetAuthority]:
    """Resolve selected assets independently against one elapsed window."""
    by_asset: dict[UUID, list[BindingModel]] = defaultdict(list)
    for binding in bindings:
        by_asset[binding.asset_id].append(binding)
    return {asset_id: resolve_authority(by_asset[asset_id], start, end) for asset_id in asset_ids}


def shared_source_pairs(authorities: dict[UUID, AssetAuthority]) -> set[frozenset[UUID]]:
    """Find distinct assets with intersecting resolved authority over a common source."""
    by_source: dict[UUID, list[tuple[datetime, datetime, UUID]]] = defaultdict(list)
    for asset_id, authority in authorities.items():
        for part in authority.parts:
            by_source[part.source_id].append((part.start, part.end, asset_id))

    pairs: set[frozenset[UUID]] = set()
    for parts in by_source.values():
        latest_ends: dict[UUID, datetime] = {}
        for start, end, asset_id in sorted(parts):
            latest_ends = {other: until for other, until in latest_ends.items() if start < until}
            pairs.update(frozenset((asset_id, other)) for other in latest_ends if other != asset_id)
            latest_ends[asset_id] = end
    return pairs
