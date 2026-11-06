"""Which source speaks for an asset at each instant, from its effective bindings."""

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
