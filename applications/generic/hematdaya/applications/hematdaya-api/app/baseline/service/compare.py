"""Pure matched-baseline comparison. Exact arithmetic only: integer mWh in, Fractions until serialization."""

from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from enum import StrEnum
from fractions import Fraction

MIN_COVERAGE = Fraction(9, 10)
MIN_ELIGIBLE = 2
MAX_PERIOD = timedelta(days=7)

SlotKey = tuple[int, time, int, int, str]
"""Relative local day, local clock time, occurrence of a repeated local time, duration seconds, stored kind."""


class ComparisonState(StrEnum):
    """What the comparison can honestly say."""

    COMPARABLE = "comparable"
    LEARNING = "learning"
    NOT_COMPARABLE = "not_comparable"
    DESCRIPTIVE = "descriptive"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class Slot:
    """One whole reading aligned to its window."""

    start: datetime
    end: datetime
    energy_mwh: int
    resolution_mwh: int | None


@dataclass
class WindowSlots:
    """A window's aligned readings. ``index`` is 0 for the current window, k for k weeks before."""

    index: int
    start: datetime
    end: datetime
    slots: dict[SlotKey, Slot] = field(default_factory=dict)

    @property
    def coverage(self) -> Fraction:
        """Share of the elapsed duration covered by whole readings."""
        total = (self.end - self.start).total_seconds()
        covered = sum((slot.end - slot.start).total_seconds() for slot in self.slots.values())
        return Fraction(int(covered), int(total)) if total else Fraction(0)

    @property
    def measured_mwh(self) -> int:
        """Every whole reading in the window, mask or not."""
        return sum(slot.energy_mwh for slot in self.slots.values())


@dataclass
class Comparison:
    """A comparison's state and, when it has a valid mask, every number behind it."""

    state: ComparisonState
    reason: str | None
    current: WindowSlots | None = None
    historical: list[WindowSlots] = field(default_factory=list)
    eligible: list[int] = field(default_factory=list)
    mask: list[SlotKey] = field(default_factory=list)
    current_mask_mwh: int | None = None
    historical_mask_mwh: dict[int, int] = field(default_factory=dict)
    baseline_mwh: Fraction | None = None
    mad_mwh: Fraction | None = None
    resolution_mwh: int | None = None
    mask_coverage: Fraction | None = None

    @property
    def delta_mwh(self) -> Fraction | None:
        """``C − B``."""
        if self.current_mask_mwh is None or self.baseline_mwh is None:
            return None
        return self.current_mask_mwh - self.baseline_mwh

    def mask_sum(self, window: WindowSlots, keys: list[SlotKey] | None = None) -> int:
        """Sum a window's readings on the common mask, or on a subset of it.

        Args:
            window (WindowSlots): The window.
            keys (list[SlotKey] | None, optional): Mask keys to include. Defaults to the whole mask.

        Returns:
            int: mWh.
        """
        return sum(window.slots[key].energy_mwh for key in (self.mask if keys is None else keys))


def median(values: list[Fraction | int]) -> Fraction:
    """Return the exact median; an even count averages the middle pair without rounding.

    Args:
        values (list[Fraction | int]): At least one value.

    Returns:
        Fraction: The median.
    """
    ordered = sorted(Fraction(value) for value in values)
    middle = len(ordered) // 2
    return ordered[middle] if len(ordered) % 2 else (ordered[middle - 1] + ordered[middle]) / 2


def _percent(value: Fraction) -> str:
    return f"{float(value * 100):.1f}".replace(".", ",") + "%"


def compare(current: WindowSlots, historical: list[WindowSlots]) -> Comparison:
    """Compare the current window with up to three prior windows on their common mask.

    Each window needs at least 90% coverage, at least two prior windows must qualify, and the slots present
    in all of them must cover at least 90% of the elapsed time. ``B`` is the median of eligible windows on
    that mask, and MAD the median absolute deviation from it. Unknown resolution leaves a descriptive result.

    Args:
        current (WindowSlots): The current window.
        historical (list[WindowSlots]): Prior windows with the same elapsed duration.

    Returns:
        Comparison: The result.
    """
    result = Comparison(ComparisonState.COMPARABLE, None, current=current, historical=historical)
    if current.coverage < MIN_COVERAGE:
        result.state = ComparisonState.NOT_COMPARABLE
        result.reason = f"Kelengkapan data periode ini {_percent(current.coverage)}, di bawah 90%."
        return result
    eligible = [window for window in historical if window.coverage >= MIN_COVERAGE]
    result.eligible = [window.index for window in eligible]
    if len(eligible) < MIN_ELIGIBLE:
        result.state = ComparisonState.LEARNING
        result.reason = (
            "Belum cukup periode pembanding: perlu minimal 2 dari 3 minggu sebelumnya dengan kelengkapan data"
            f" minimal 90%; tersedia {len(eligible)}."
        )
        return result
    mask = sorted(key for key in current.slots if all(key in window.slots for window in eligible))
    elapsed = (current.end - current.start).total_seconds()
    mask_seconds = sum((current.slots[key].end - current.slots[key].start).total_seconds() for key in mask)
    result.mask = mask
    result.mask_coverage = Fraction(int(mask_seconds), int(elapsed))
    if result.mask_coverage < MIN_COVERAGE:
        result.state = ComparisonState.NOT_COMPARABLE
        result.reason = f"Waktu dengan data di semua periode hanya {_percent(result.mask_coverage)}, di bawah 90%."
        return result
    result.current_mask_mwh = result.mask_sum(current)
    result.historical_mask_mwh = {window.index: result.mask_sum(window) for window in eligible}
    sums = list(result.historical_mask_mwh.values())
    result.baseline_mwh = median(sums)
    result.mad_mwh = median([abs(value - result.baseline_mwh) for value in sums])
    resolutions = []
    for window in [current, *eligible]:
        steps = [window.slots[key].resolution_mwh for key in mask]
        resolutions.append(None if None in steps else sum(steps))
    if None in resolutions:
        result.state = ComparisonState.DESCRIPTIVE
        result.reason = "Resolusi sumber tidak diketahui: perbandingan hanya deskriptif, tanpa saran otomatis."
    else:
        result.resolution_mwh = max(resolutions)
    return result
