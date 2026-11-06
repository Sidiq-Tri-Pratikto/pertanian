"""Pure energy rules: periods, allocation, coverage and source authority."""

from datetime import UTC, date, datetime, timedelta
from uuid import uuid4

import pytest

from app.assets.model.models import BindingModel
from app.core.errors.base import RequestInvalidError
from app.energy.service.authority import resolve_authority
from app.energy.service.format import kwh, percent, ratio
from app.energy.service.intervals import allocate, complement, intersect, union
from app.energy.service.periods import Preset, RangeTooLargeError, resolve_window

MONDAY = datetime(2026, 10, 25, 17, tzinfo=UTC)  # 2026-10-26 00.00 WIB
T = datetime(2026, 10, 19, 3, tzinfo=UTC)


@pytest.mark.parametrize(
    ("preset", "expected"),
    [
        (Preset.TODAY, (date(2026, 10, 26), date(2026, 10, 26))),
        (Preset.THIS_WEEK, (date(2026, 10, 26), date(2026, 10, 26))),
        (Preset.LAST_7_DAYS, (date(2026, 10, 19), date(2026, 10, 25))),
    ],
)
def test_presets_follow_site_time(preset: Preset, expected: tuple[date, date]) -> None:
    """
    Condition:
    - Each preset at virtual Monday 00.00 WIB.

    Expected:
    - Today and this week are that Monday; the last seven days are 19–25 Oktober.
    """
    window = resolve_window("Asia/Jakarta", MONDAY, preset=preset)

    assert (window.start_date, window.end_date) == expected


def test_window_is_half_open_and_stops_at_site_time() -> None:
    """
    Condition:
    - Wednesday 21 Oktober at 12.00 WIB, this week.

    Expected:
    - Monday 00.00 WIB to the next Monday, effective until now, current.
    """
    now = datetime(2026, 10, 21, 5, tzinfo=UTC)

    window = resolve_window("Asia/Jakarta", now, preset=Preset.THIS_WEEK)

    assert (window.start, window.end, window.effective_end) == (
        datetime(2026, 10, 18, 17, tzinfo=UTC),
        datetime(2026, 10, 21, 17, tzinfo=UTC),
        now,
    )
    assert window.is_current


def test_ranges_are_capped_before_reading() -> None:
    """
    Condition:
    - 366 days, then 367, then a reversed range.

    Expected:
    - 366 resolves, 367 is too large, reversed is invalid.
    """
    assert resolve_window("Asia/Jakarta", MONDAY, start_date=date(2025, 10, 26), end_date=date(2026, 10, 26))
    with pytest.raises(RangeTooLargeError):
        resolve_window("Asia/Jakarta", MONDAY, start_date=date(2025, 10, 25), end_date=date(2026, 10, 26))
    with pytest.raises(RequestInvalidError):
        resolve_window("Asia/Jakarta", MONDAY, start_date=date(2026, 10, 2), end_date=date(2026, 10, 1))


def test_adjacent_fragments_conserve_the_interval() -> None:
    """
    Condition:
    - 100 mWh over one hour split at 20 and 40 minutes; 1 mWh split in half.

    Expected:
    - Fragments sum exactly to the source value, rounding ties to even.
    """
    interval = (T, T + timedelta(hours=1))
    cuts = [T, T + timedelta(minutes=20), T + timedelta(minutes=40), T + timedelta(hours=1)]

    parts = [allocate(100, interval, (lo, hi)) for lo, hi in zip(cuts, cuts[1:], strict=False)]
    halves = [
        allocate(1, interval, (T, cuts[0] + timedelta(minutes=30))),
        allocate(1, interval, (T + timedelta(minutes=30), interval[1])),
    ]

    assert parts == [33, 34, 33] and sum(parts) == 100
    assert sum(halves) == 1


def test_coverage_set_operations() -> None:
    """
    Condition:
    - Touching and overlapping spans, a second set, and a range with gaps.

    Expected:
    - Union merges, intersection keeps the common part, complement lists the gaps.
    """
    h = timedelta(hours=1)
    spans = union([(T + 2 * h, T + 3 * h), (T, T + h), (T + h, T + 2 * h), (T + 5 * h, T + 6 * h)])

    assert spans == [(T, T + 3 * h), (T + 5 * h, T + 6 * h)]
    assert intersect(spans, [(T + 2 * h, T + 6 * h)]) == [(T + 2 * h, T + 3 * h), (T + 5 * h, T + 6 * h)]
    assert complement(spans, T, T + 7 * h) == [(T + 3 * h, T + 5 * h), (T + 6 * h, T + 7 * h)]


def _binding(start: datetime, end: datetime | None, authoritative: bool) -> BindingModel:
    return BindingModel(
        id=uuid4(), site_id=uuid4(), source_id=uuid4(), asset_id=uuid4(), effective_from=start, effective_to=end,
        authoritative=authoritative,
    )  # fmt: skip


def test_authority_prefers_the_authoritative_binding() -> None:
    """
    Condition:
    - A candidate overlapping an authoritative binding for part of the window.

    Expected:
    - The authoritative source counts where it applies, the candidate only outside it, and nothing conflicts.
    """
    h = timedelta(hours=1)
    lead, candidate = _binding(T + 2 * h, None, True), _binding(T, None, False)

    authority = resolve_authority([lead, candidate], T, T + 4 * h)

    assert [(p.source_id, p.start, p.end) for p in authority.parts] == [
        (candidate.source_id, T, T + 2 * h),
        (lead.source_id, T + 2 * h, T + 4 * h),
    ]
    assert authority.conflicts == []


def test_two_candidates_are_unresolved() -> None:
    """
    Condition:
    - Two candidates for one load over the same hours.

    Expected:
    - Neither counts; both are reported over the overlap.
    """
    first, second = _binding(T, None, False), _binding(T, None, False)

    authority = resolve_authority([first, second], T, T + timedelta(hours=2))

    assert authority.parts == []
    assert {part.source_id for part in authority.conflicts} == {first.source_id, second.source_id}


def test_wire_formats() -> None:
    """
    Condition:
    - Energy, a near-complete ratio and a share.

    Expected:
    - Three-decimal kWh, coverage rounded down, two-decimal percent.
    """
    assert kwh(14_700_000) == "14.700"
    assert kwh(1_500) == "0.002"  # 0.0015 rounds half to even
    assert ratio(0.99999) == "0.999"
    assert percent(8_400, 14_700) == "57.14"
