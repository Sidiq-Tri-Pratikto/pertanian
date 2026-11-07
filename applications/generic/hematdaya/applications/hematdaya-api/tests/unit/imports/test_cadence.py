"""A stream's cadence from its timestamps, in integer microseconds. Port of ``inferCadence`` (L694)."""

from datetime import timedelta

import pytest

from app.imports.service.cadence import infer_cadence

SECOND = 1_000_000
HOUR = 3600 * SECOND


def _from_gaps(gaps: list[int]) -> list[int]:
    timestamps = [0]
    for gap in gaps:
        timestamps.append(timestamps[-1] + gap)
    return timestamps


@pytest.mark.parametrize("timestamps", [[], [0], [5, 5, 5]], ids=["none", "one", "only_repeats"])
def test_no_positive_gap_gives_no_cadence(timestamps: list[int]) -> None:
    """
    Condition:
    - No timestamps, one, or only repeats.

    Expected:
    - None, because there is no gap to measure.
    """
    assert infer_cadence(timestamps) is None


def test_repeated_timestamps_leave_the_denominator() -> None:
    """
    Condition:
    - ``00:00, 00:00, 01:00, 02:00``.

    Expected:
    - One hour: a repeat is no gap, not a gap of zero.
    """
    assert infer_cadence([0, 0, HOUR, 2 * HOUR]) == timedelta(hours=1)


def test_exactly_ninety_percent_agreement_gives_the_median() -> None:
    """
    Condition:
    - 9 of 10 gaps agree.

    Expected:
    - The median, since the rule is at least 90%.
    """
    assert infer_cadence(_from_gaps([HOUR] * 9 + [5 * HOUR])) == timedelta(hours=1)


def test_below_ninety_percent_agreement_gives_no_cadence() -> None:
    """
    Condition:
    - 8 of 9 gaps agree, about 88.9%.

    Expected:
    - None.
    """
    assert infer_cadence(_from_gaps([HOUR] * 8 + [5 * HOUR])) is None


def test_gap_exactly_one_second_from_the_median_agrees() -> None:
    """
    Condition:
    - 4 gaps at the median and 1 exactly one second above it, where failure would make agreement 80%.

    Expected:
    - It agrees, so the median stands.
    """
    assert infer_cadence(_from_gaps([HOUR] * 4 + [HOUR + SECOND])) == timedelta(hours=1)


def test_gap_just_over_one_second_from_the_median_disagrees() -> None:
    """
    Condition:
    - The same stream with that gap one microsecond further out.

    Expected:
    - It disagrees, agreement falls to 80%, and there is no cadence.
    """
    assert infer_cadence(_from_gaps([HOUR] * 4 + [HOUR + SECOND + 1])) is None


def test_even_count_median_stays_exact() -> None:
    """
    Condition:
    - Two gaps of 3,600 s and 3,601 s, whose median is not a whole second.

    Expected:
    - Exactly 3,600.5 s, in integers, where ``statistics.median`` would return a float.
    """
    assert infer_cadence(_from_gaps([3600 * SECOND, 3601 * SECOND])) == timedelta(seconds=3600, microseconds=500000)


def test_input_order_does_not_matter() -> None:
    """
    Condition:
    - Regular timestamps given out of order.

    Expected:
    - The same cadence as in order, and the iterable is consumed only once.
    """
    assert infer_cadence(iter([3 * HOUR, 0, 2 * HOUR, HOUR])) == timedelta(hours=1)
