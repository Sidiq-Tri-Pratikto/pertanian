"""Pure interval arithmetic for coverage, gaps and boundary allocation."""

from datetime import datetime
from fractions import Fraction

Span = tuple[datetime, datetime]


def union(spans: list[Span]) -> list[Span]:
    """Merge half-open spans.

    Args:
        spans (list[Span]): Spans in any order.

    Returns:
        list[Span]: Disjoint, ordered spans; touching spans merge.
    """
    merged: list[Span] = []
    for start, end in sorted(spans):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def intersect(left: list[Span], right: list[Span]) -> list[Span]:
    """Intersect two sets of disjoint ordered spans.

    Args:
        left (list[Span]): First set.
        right (list[Span]): Second set.

    Returns:
        list[Span]: Their intersection.
    """
    out: list[Span] = []
    for a_start, a_end in left:
        for b_start, b_end in right:
            start, end = max(a_start, b_start), min(a_end, b_end)
            if start < end:
                out.append((start, end))
    return union(out)


def complement(spans: list[Span], start: datetime, end: datetime) -> list[Span]:
    """Return the parts of ``[start, end)`` that no span covers.

    Args:
        spans (list[Span]): Disjoint ordered spans.
        start (datetime): Range start.
        end (datetime): Range end.

    Returns:
        list[Span]: The gaps.
    """
    gaps, cursor = [], start
    for span_start, span_end in spans:
        if span_start > cursor:
            gaps.append((cursor, min(span_start, end)))
        cursor = max(cursor, span_end)
        if cursor >= end:
            break
    if cursor < end:
        gaps.append((cursor, end))
    return [gap for gap in gaps if gap[0] < gap[1]]


def length(spans: list[Span]) -> float:
    """Total seconds covered by disjoint spans.

    Args:
        spans (list[Span]): Disjoint spans.

    Returns:
        float: Seconds.
    """
    return sum((end - start).total_seconds() for start, end in spans)


def _cumulative(energy: int, interval: Span, at: datetime) -> int:
    elapsed = Fraction(int((at - interval[0]).total_seconds() * 1_000_000), 1)
    total = Fraction(int((interval[1] - interval[0]).total_seconds() * 1_000_000), 1)
    return round(energy * elapsed / total)  # Fraction rounds half to even.


def allocate(energy: int, interval: Span, fragment: Span) -> int:
    """Allocate an interval's energy to a fragment, uniformly within the interval.

    Each fragment is the difference of cumulative integer allocations from the interval start, so adjacent
    fragments always sum to the source value.

    Args:
        energy (int): The interval's mWh.
        interval (Span): The whole interval.
        fragment (Span): A part of it.

    Returns:
        int: The fragment's mWh.
    """
    return _cumulative(energy, interval, fragment[1]) - _cumulative(energy, interval, fragment[0])
