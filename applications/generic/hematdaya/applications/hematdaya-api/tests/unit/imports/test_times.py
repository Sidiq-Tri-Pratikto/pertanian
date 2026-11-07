"""Time cells are read by shape, never rolled into another date. Port of ``parseTime`` (L632)."""

from datetime import UTC, datetime, timedelta

import pytest

from app.imports.model.models import CellFailure, RowReason
from app.imports.service.times import parse_time, resolve_local

FORMAT_DETAIL = "format waktu tidak dikenali. Gunakan 2026-10-20 00:00 atau 2026-10-20T00:00:00+07:00."


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("2026-10-20 00:00", datetime(2026, 10, 20, 0, 0)),
        ("2026-10-20 08.30", datetime(2026, 10, 20, 8, 30)),
        ("2026-10-20 08.30.15", datetime(2026, 10, 20, 8, 30, 15)),
        ("2026-10-20 08:30.15", datetime(2026, 10, 20, 8, 30, 15)),
        ("2026-10-20T08:30:15", datetime(2026, 10, 20, 8, 30, 15)),
        ("  2026-10-20 00:00  ", datetime(2026, 10, 20, 0, 0)),
    ],
)
def test_time_without_offset_stays_naive(raw: str, expected: datetime) -> None:
    """
    Condition:
    - A time with no offset, in any accepted shape, including dotted times ``fromisoformat`` misreads.

    Expected:
    - The same wall clock, naive: only the caller may give it a zone.
    """
    result = parse_time(raw)
    assert result == expected
    assert result.tzinfo is None


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("2026-10-20T00:00:00+07:00", datetime(2026, 10, 19, 17, 0, tzinfo=UTC)),
        ("2026-10-20 00:00 +0700", datetime(2026, 10, 19, 17, 0, tzinfo=UTC)),
        ("2026-10-20T00:00:00Z", datetime(2026, 10, 20, 0, 0, tzinfo=UTC)),
        ("2026-10-20T00:00:00-05:00", datetime(2026, 10, 20, 5, 0, tzinfo=UTC)),
    ],
)
def test_offset_keeps_its_explicit_instant_in_utc(raw: str, expected: datetime) -> None:
    """
    Condition:
    - A time with an offset or ``Z``.

    Expected:
    - The same instant, normalized to UTC at once.
    """
    result = parse_time(raw)
    assert result == expected
    assert result.utcoffset() == expected.utcoffset()
    assert result.tzinfo is UTC


@pytest.mark.parametrize(
    ("raw", "microsecond"), [("2026-10-20T00:00:00.5Z", 500000), ("2026-10-20T00:00:00.123456789Z", 123456)]
)
def test_fractions_keep_microseconds_and_truncate_further_digits(raw: str, microsecond: int) -> None:
    """
    Condition:
    - A fractional second, up to nine digits.

    Expected:
    - Microseconds kept and truncated, so a sub-second interval does not reverse.
    """
    assert parse_time(raw) == datetime(2026, 10, 20, 0, 0, 0, microsecond, tzinfo=UTC)


@pytest.mark.parametrize(
    "raw",
    [
        "2026-02-30 00:00",
        "2026-10-20 24:00",
        "2026-10-20 00:60",
        "2026-10-20 00:00:60",
        "2026-13-01 00:00",
        "2026-10-20 00:00+24:00",
        "2026-10-20 00:00+07:60",
        "2026-10-20 00:00+99:99",
        "0000-10-20 00:00",
        "0001-01-01 00:00+07:00",
        "9999-12-31 23:59-07:00",
    ],
)
def test_impossible_time_is_rejected_with_the_cell_in_the_message(raw: str) -> None:
    """
    Condition:
    - A date, clock, offset or year overflow that has the right shape but cannot exist.

    Expected:
    - ``time_impossible`` naming the cell, never a rolled date.
    """
    assert parse_time(raw) == CellFailure(
        reason=RowReason.TIME_IMPOSSIBLE, detail=f"tanggal atau jam tidak ada ({raw})."
    )


@pytest.mark.parametrize(
    "raw",
    [
        "2026-02-30",
        "2026-10-20",
        "20261020",
        "2026-W43-2",
        "2026-10-20T08",
        "٢٠٢٦-10-20 00:00",
        "2026-10-20t00:00",
        "",
        "   ",
        "kemarin",
    ],
)
def test_unknown_shape_is_a_format_failure(raw: str) -> None:
    """
    Condition:
    - A date without a time, a shape ``fromisoformat`` would accept, non-ASCII digits, or text.

    Expected:
    - ``time_format`` with the example.
    """
    assert parse_time(raw) == CellFailure(reason=RowReason.TIME_FORMAT, detail=FORMAT_DETAIL)


@pytest.mark.parametrize(
    ("zone", "expected"),
    [
        ("Asia/Jakarta", datetime(2026, 10, 19, 17, 0, tzinfo=UTC)),
        ("Asia/Makassar", datetime(2026, 10, 19, 16, 0, tzinfo=UTC)),
    ],
)
def test_local_time_resolves_to_utc_in_the_confirmed_zone(zone: str, expected: datetime) -> None:
    """
    Condition:
    - A naive time in a confirmed Indonesian zone.

    Expected:
    - The instant that zone gives, in UTC, with no offset table and no default zone.
    """
    result = resolve_local(datetime(2026, 10, 20), zone, "2026-10-20 00:00")
    assert result == expected
    assert result.tzinfo is UTC


def test_local_time_in_a_gap_does_not_exist() -> None:
    """
    Condition:
    - 02:30 on the day New York's clocks jump from 02:00 to 03:00. ``ZoneInfo`` raises nothing here.

    Expected:
    - ``time_nonexistent`` naming the cell and the zone, asking for an offset.
    """
    assert resolve_local(datetime(2026, 3, 8, 2, 30), "America/New_York", "2026-03-08 02:30") == CellFailure(
        reason=RowReason.TIME_NONEXISTENT,
        detail=(
            "waktu lokal 2026-03-08 02:30 tidak ada di zona America/New_York. Tambahkan offset atau perbaiki waktunya."
        ),
    )


def test_local_time_in_a_fold_is_ambiguous() -> None:
    """
    Condition:
    - 01:30 on the day New York's clocks fall back, which happens twice.

    Expected:
    - ``time_ambiguous`` naming the cell and the zone, asking for an offset to choose one.
    """
    assert resolve_local(datetime(2026, 11, 1, 1, 30), "America/New_York", "2026-11-01 01:30") == CellFailure(
        reason=RowReason.TIME_AMBIGUOUS,
        detail=(
            "waktu lokal 2026-11-01 01:30 terjadi dua kali di zona America/New_York. "
            "Tambahkan offset untuk memilih salah satunya."
        ),
    )


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("2026-11-01 01:30-04:00", datetime(2026, 11, 1, 5, 30, tzinfo=UTC)),
        ("2026-11-01 01:30-05:00", datetime(2026, 11, 1, 6, 30, tzinfo=UTC)),
    ],
)
def test_offset_chooses_between_the_two_readings_of_a_fold(raw: str, expected: datetime) -> None:
    """
    Condition:
    - The ambiguous 01:30, written with each of its two offsets.

    Expected:
    - Each keeps its own instant, one hour apart.
    """
    assert parse_time(raw) == expected


def test_arithmetic_across_a_clock_change_uses_instants() -> None:
    """
    Condition:
    - One hour added to the resolved 01:00 on the day New York's clocks jump.

    Expected:
    - 07:00Z, the real hour later. Wall-clock arithmetic on a shared ``ZoneInfo`` would disagree.
    """
    start = resolve_local(datetime(2026, 3, 8, 1, 0), "America/New_York", "2026-03-08 01:00")
    assert start + timedelta(hours=1) == datetime(2026, 3, 8, 7, 0, tzinfo=UTC)


def test_local_time_beyond_the_calendar_is_impossible() -> None:
    """
    Condition:
    - The first representable moment, in a zone ahead of UTC, so its instant falls before year 1.

    Expected:
    - ``time_impossible``, not an ``OverflowError``.
    """
    assert resolve_local(datetime(1, 1, 1), "Asia/Jakarta", "0001-01-01 00:00") == CellFailure(
        reason=RowReason.TIME_IMPOSSIBLE, detail="tanggal atau jam tidak ada (0001-01-01 00:00)."
    )
