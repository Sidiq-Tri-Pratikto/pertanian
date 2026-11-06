"""Infers one stream's cadence from its timestamps, in integer microseconds."""

from collections.abc import Iterable
from datetime import timedelta

_DOUBLED_TOLERANCE = 2_000_000
"""One second, doubled, because gaps are compared against a doubled median to stay in integers."""


def infer_cadence(timestamps: Iterable[int]) -> timedelta | None:
    """Find a stream's regular gap, when at least 90% of its positive gaps are within one second of their median.

    Args:
        timestamps (Iterable[int]): The stream's instants in microseconds, in any order. Repeats are no gap.

    Returns:
        timedelta | None: The median gap, or None when there is no gap or the gaps disagree.
    """
    distinct = sorted(set(timestamps))
    gaps = sorted(later - earlier for earlier, later in zip(distinct, distinct[1:], strict=False))
    if not gaps:
        return None
    middle = len(gaps) // 2
    doubled_median = 2 * gaps[middle] if len(gaps) % 2 else gaps[middle - 1] + gaps[middle]
    agreeing = sum(abs(2 * gap - doubled_median) <= _DOUBLED_TOLERANCE for gap in gaps)
    if agreeing * 10 < len(gaps) * 9:
        return None
    return timedelta(microseconds=doubled_median // 2)
