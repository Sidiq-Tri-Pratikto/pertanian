"""Pure comparison: gates, exact median and MAD, and states."""

from datetime import UTC, datetime, time, timedelta
from fractions import Fraction

from app.baseline.service.compare import ComparisonState, Slot, WindowSlots, compare, median

T = datetime(2026, 10, 19, tzinfo=UTC)
H = timedelta(hours=1)


def _window(index: int, values: dict[int, int | None], hours: int = 10, resolution: int | None = 1000) -> WindowSlots:
    start = T - timedelta(weeks=index)
    window = WindowSlots(index, start, start + hours * H)
    for hour, mwh in values.items():
        if mwh is not None:
            window.slots[(0, time(hour), 0, 3600, "interval_energy")] = Slot(
                start + hour * H, start + (hour + 1) * H, mwh, resolution
            )
    return window


def _full(index: int, mwh: int, **kwargs: object) -> WindowSlots:
    return _window(index, dict.fromkeys(range(10), mwh), **kwargs)


def test_median_and_mad_are_exact() -> None:
    """
    Condition:
    - Two eligible windows of 1,000 and 1,001 mWh.

    Expected:
    - B is exactly 1,000.5 mWh and MAD exactly 0.5 mWh; no float rounding.
    """
    result = compare(
        _full(0, 100), [_full(1, 100), _window(2, {**dict.fromkeys(range(10), 100), 0: 101}), _window(3, {})]
    )

    assert median([1, 2]) == Fraction(3, 2)
    assert result.state is ComparisonState.COMPARABLE
    assert (result.baseline_mwh, result.mad_mwh) == (Fraction(2001, 2), Fraction(1, 2))
    assert result.resolution_mwh == 10_000


def test_one_eligible_window_is_learning() -> None:
    """
    Condition:
    - Only one prior window reaches 90% coverage.

    Expected:
    - Learning with the count in the reason, and no baseline.
    """
    result = compare(_full(0, 100), [_full(1, 100), _window(2, {0: 100}), _window(3, {})])

    assert result.state is ComparisonState.LEARNING
    assert "tersedia 1" in (result.reason or "")
    assert result.baseline_mwh is None


def test_low_current_coverage_is_not_comparable() -> None:
    """
    Condition:
    - The current window covers 80% of its elapsed time.

    Expected:
    - Not comparable, with the coverage in the reason.
    """
    result = compare(_window(0, dict.fromkeys(range(8), 100)), [_full(1, 100), _full(2, 100)])

    assert result.state is ComparisonState.NOT_COMPARABLE
    assert "80,0%" in (result.reason or "")


def test_thin_common_mask_suppresses_the_comparison() -> None:
    """
    Condition:
    - Each window covers 90%, but they miss different hours, so the common mask covers only 70%.

    Expected:
    - Not comparable: equal-looking totals on different hours are never compared.
    """
    current = _window(0, {h: 100 for h in range(10) if h != 0})
    first = _window(1, {h: 100 for h in range(10) if h != 1})
    second = _window(2, {h: 100 for h in range(10) if h != 2})

    result = compare(current, [first, second])

    assert result.state is ComparisonState.NOT_COMPARABLE
    assert result.mask_coverage == Fraction(7, 10)


def test_unknown_resolution_stays_descriptive() -> None:
    """
    Condition:
    - Prior windows whose source resolution is unknown.

    Expected:
    - Descriptive: numbers return, resolution stays unknown, so no automatic alert can follow.
    """
    result = compare(_full(0, 100), [_full(1, 100, resolution=None), _full(2, 100, resolution=None)])

    assert result.state is ComparisonState.DESCRIPTIVE
    assert result.baseline_mwh == 1000 and result.resolution_mwh is None


def test_zero_baseline_has_a_delta_without_division() -> None:
    """
    Condition:
    - AT-21: zero everywhere.

    Expected:
    - B is 0 and the change is 0; nothing divides by the baseline.
    """
    result = compare(_full(0, 0), [_full(1, 0), _full(2, 0), _full(3, 0)])

    assert (result.state, result.baseline_mwh, result.delta_mwh) == (ComparisonState.COMPARABLE, 0, 0)
