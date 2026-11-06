"""Containment graph rules, pure."""

from collections import defaultdict
from collections.abc import Iterable
from uuid import UUID

MAX_DEPTH = 64


def would_create_cycle(containment: Iterable[tuple[UUID, UUID]], parent: UUID, child: UUID) -> bool:
    """Tell whether ``parent`` containing ``child`` closes a loop.

    Args:
        containment (Iterable[tuple[UUID, UUID]]): Existing (container, contained) pairs from parent links
            and ``contains`` relations.
        parent (UUID): The proposed container.
        child (UUID): The proposed contained asset.

    Returns:
        bool: True for a self-reference, a cycle, or a chain deeper than the walk allows.
    """
    if parent == child:
        return True
    children: dict[UUID, list[UUID]] = defaultdict(list)
    for container, contained in containment:
        children[container].append(contained)
    frontier, seen = [child], {child}
    for _ in range(MAX_DEPTH):
        if not frontier:
            return False
        if parent in frontier:
            return True
        frontier = [nxt for node in frontier for nxt in children[node] if nxt not in seen]
        seen.update(frontier)
    return True
