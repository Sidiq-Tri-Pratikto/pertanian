"""Household and industrial fixture definitions and the deterministic hourly generator (PRD §19)."""

from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

from app.assets.model.models import ExpectedUse

TIMEZONE = "Asia/Jakarta"
FIXTURE_START = datetime(2026, 9, 27, 17, tzinfo=UTC)  # 2026-09-28 00.00 WIB, a Monday
FIXTURE_HOURS = 28 * 24
NOW_MAIN = datetime(2026, 10, 25, 17, tzinfo=UTC)  # 2026-10-26 00.00 WIB
NOW_CURRENT = datetime(2026, 10, 21, 5, tzinfo=UTC)  # 2026-10-21 12.00 WIB
SELECTED_WEEK = (date(2026, 10, 19), date(2026, 10, 25))
HOUR = timedelta(hours=1)

WhRule = Callable[[int, int, date], int]
"""Wh for one hour, from the local hour, weekday (Monday 0) and local date."""


@dataclass(frozen=True)
class FixtureAsset:
    """One fixture load and its hourly rule."""

    key: str
    name: str
    category: str
    location: str
    expected_use: ExpectedUse
    wh: WhRule


@dataclass(frozen=True)
class ReadingSpec:
    """One generated interval reading in whole Wh, before ingestion."""

    source_key: str
    start: datetime
    end: datetime
    wh: int


HOUSEHOLD = (
    FixtureAsset("kulkas", "Kulkas", "Pendingin makanan", "Dapur", ExpectedUse.CONTINUOUS, lambda h, wd, d: 50),
    FixtureAsset("router", "Router", "Elektronik/TI", "Ruang tengah", ExpectedUse.CONTINUOUS, lambda h, wd, d: 10),
    FixtureAsset(
        "pompa",
        "Pompa Air",
        "Pompa",
        "Halaman belakang",
        ExpectedUse.INTERMITTENT,
        lambda h, wd, d: 150 if h in (6, 18) else 0,
    ),
    FixtureAsset(
        "tv",
        "TV",
        "Elektronik/TI",
        "Ruang tengah",
        ExpectedUse.INTERMITTENT,
        lambda h, wd, d: 120 if 20 <= h <= 22 else 0,
    ),
)

FACTORY = (
    FixtureAsset(
        "oven",
        "Oven",
        "Pemanas/memasak",
        "Area produksi",
        ExpectedUse.UNKNOWN,
        lambda h, wd, d: 2000 if wd <= 5 and 8 <= h <= 13 else 0,
    ),
    FixtureAsset(
        "kompresor",
        "Kompresor",
        "Motor/proses",
        "Area produksi",
        ExpectedUse.UNKNOWN,
        lambda h, wd, d: 1000 if wd <= 5 and 8 <= h <= 13 else 0,
    ),
    FixtureAsset(
        "press",
        "Mesin Press",
        "Motor/proses",
        "Area produksi",
        ExpectedUse.UNKNOWN,
        lambda h, wd, d: 1000 if wd <= 5 and 13 <= h <= 16 else 0,
    ),
    FixtureAsset(
        "lampu",
        "Lampu Area",
        "Penerangan",
        "Area produksi",
        ExpectedUse.UNKNOWN,
        lambda h, wd, d: 200 if wd <= 5 and 7 <= h <= 16 else 0,
    ),
)


def in_selected_week(day: date) -> bool:
    """Tell whether a local date is in 19–25 Oktober 2026.

    Args:
        day (date): Local date.

    Returns:
        bool: True inside the selected week.
    """
    return SELECTED_WEEK[0] <= day <= SELECTED_WEEK[1]


def hourly(
    source_key: str,
    wh: WhRule,
    *,
    start: datetime = FIXTURE_START,
    until: datetime | None = None,
    skip: Callable[[datetime], bool] | None = None,
) -> Iterator[ReadingSpec]:
    """Yield the fixture's hourly readings for one source. Zero hours are explicit readings, never omitted.

    Args:
        source_key (str): The source the readings belong to.
        wh (WhRule): Wh per local hour.
        start (datetime, optional): First hour, UTC. Defaults to the fixture start.
        until (datetime | None, optional): Exclusive end, UTC. Defaults to the fixture end.
        skip (Callable[[datetime], bool] | None, optional): Drops hours to model a gap. Defaults to None.

    Yields:
        ReadingSpec: One hour's reading.
    """
    zone = ZoneInfo(TIMEZONE)
    for index in range(FIXTURE_HOURS):
        hour_start = FIXTURE_START + index * HOUR
        if hour_start < start or (until is not None and hour_start >= until) or (skip and skip(hour_start)):
            continue
        local = hour_start.astimezone(zone)
        yield ReadingSpec(source_key, hour_start, hour_start + HOUR, wh(local.hour, local.weekday(), local.date()))
