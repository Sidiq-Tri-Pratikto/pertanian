"""Reads a time cell by its shape and resolves local times to UTC."""

import re
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from app.imports.model.models import CellFailure, RowReason

_TIME = re.compile(
    r"([0-9]{4})-([0-9]{2})-([0-9]{2})[ T]([0-9]{2})[:.]([0-9]{2})(?:[:.]([0-9]{2}))?(?:\.([0-9]+))?"
    r"\s*(Z|[+-][0-9]{2}:?[0-9]{2})?",
    re.ASCII,
)
_MICROSECOND_DIGITS = 6


def impossible_time(text: str) -> CellFailure:
    """Say that a time cannot exist.

    Args:
        text (str): The cell as written, stripped.

    Returns:
        CellFailure: A ``time_impossible`` failure naming the cell.
    """
    return CellFailure(reason=RowReason.TIME_IMPOSSIBLE, detail=f"tanggal atau jam tidak ada ({text}).")


def _offset(written: str) -> timedelta | None:
    if written == "Z":
        return timedelta(0)
    digits = written[1:].replace(":", "")
    hours, minutes = int(digits[:2]), int(digits[2:])
    if hours > 23 or minutes > 59:
        return None
    magnitude = timedelta(hours=hours, minutes=minutes)
    return -magnitude if written[0] == "-" else magnitude


def parse_time(raw: str) -> datetime | CellFailure:
    """Read a time cell by its shape, never rolling an impossible date forward.

    Args:
        raw (str): The cell as written.

    Returns:
        datetime | CellFailure: Naive when the cell has no offset, otherwise the same instant in UTC.
    """
    text = raw.strip()
    match = _TIME.fullmatch(text)
    if match is None:
        return CellFailure(
            reason=RowReason.TIME_FORMAT,
            detail="format waktu tidak dikenali. Gunakan 2026-10-20 00:00 atau 2026-10-20T00:00:00+07:00.",
        )
    year, month, day, hour, minute, second, fraction, written_offset = match.groups()
    microsecond = int((fraction or "").ljust(_MICROSECOND_DIGITS, "0")[:_MICROSECOND_DIGITS])
    try:
        wall_clock = datetime(int(year), int(month), int(day), int(hour), int(minute), int(second or 0), microsecond)
    except ValueError:
        return impossible_time(text)
    if written_offset is None:
        return wall_clock
    offset = _offset(written_offset)
    if offset is None:
        return impossible_time(text)
    try:
        return (wall_clock - offset).replace(tzinfo=UTC)
    except OverflowError:
        return impossible_time(text)


def resolve_local(naive: datetime, zone: str, raw: str) -> datetime | CellFailure:
    """Resolve a naive time in a confirmed zone to UTC, refusing to guess across a clock change.

    ``ZoneInfo`` never raises on a gap, so the two fold readings are compared, then round-tripped through UTC.

    Args:
        naive (datetime): The wall clock.
        zone (str): IANA zone name.
        raw (str): The cell as written, for the message.

    Returns:
        datetime | CellFailure: The instant in UTC, or why this wall clock names no single instant.
    """
    text = raw.strip()
    site_zone = ZoneInfo(zone)
    earlier = naive.replace(tzinfo=site_zone, fold=0)
    later = naive.replace(tzinfo=site_zone, fold=1)
    try:
        instant = earlier.astimezone(UTC)
        if earlier.utcoffset() == later.utcoffset():
            return instant
        round_trip = instant.astimezone(site_zone).replace(tzinfo=None, fold=0)
    except OverflowError:
        return impossible_time(text)
    if round_trip != naive:
        return CellFailure(
            reason=RowReason.TIME_NONEXISTENT,
            detail=f"waktu lokal {text} tidak ada di zona {zone}. Tambahkan offset atau perbaiki waktunya.",
        )
    return CellFailure(
        reason=RowReason.TIME_AMBIGUOUS,
        detail=f"waktu lokal {text} terjadi dua kali di zona {zone}. Tambahkan offset untuk memilih salah satunya.",
    )
