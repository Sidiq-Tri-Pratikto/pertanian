"""Half-open UTC windows from a site's local calendar. Weeks start on Monday."""

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from enum import StrEnum
from zoneinfo import ZoneInfo

from app.core.errors import codes
from app.core.errors.base import AppError, RequestInvalidError

MAX_DAYS = 366
_PERIOD_REQUIRED = "Pilih preset atau tanggal mulai dan selesai. Lalu coba lagi."
_PERIOD_REVERSED = "Tanggal mulai harus sebelum atau sama dengan tanggal selesai. Perbaiki rentangnya lalu coba lagi."


class RangeTooLargeError(AppError):
    """A requested range exceeds what one read may cover."""

    code = codes.APP_RANGE_TOO_LARGE


class Preset(StrEnum):
    """Named periods relative to site time."""

    TODAY = "today"
    THIS_WEEK = "this_week"
    LAST_7_DAYS = "last_7_days"


@dataclass(frozen=True)
class Window:
    """A resolved period: inclusive local dates and their half-open UTC instants.

    ``effective_end`` stops at site time, so unfinished intervals never count.
    """

    start_date: date
    end_date: date
    timezone: str
    start: datetime
    end: datetime
    effective_end: datetime

    @property
    def is_current(self) -> bool:
        """Whether site time falls inside the window."""
        return self.effective_end < self.end

    @property
    def elapsed(self) -> timedelta:
        """Time from the start up to site time, never negative."""
        return max(self.effective_end - self.start, timedelta(0))


def local_midnight(day: date, timezone: str) -> datetime:
    """Return the UTC instant of a local date's start.

    Args:
        day (date): Local date.
        timezone (str): IANA timezone.

    Returns:
        datetime: The instant, in UTC.
    """
    return datetime.combine(day, time(0), tzinfo=ZoneInfo(timezone)).astimezone(UTC)


def resolve_window(
    timezone: str,
    now: datetime,
    *,
    preset: Preset | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> Window:
    """Resolve a preset or an inclusive local date range against site time.

    Args:
        timezone (str): The site's IANA timezone.
        now (datetime): Site time from ``site_clock``.
        preset (Preset | None, optional): A named period. Defaults to None.
        start_date (date | None, optional): First local date. Defaults to None.
        end_date (date | None, optional): Last local date, inclusive. Defaults to None.

    Returns:
        Window: The window.

    Raises:
        RequestInvalidError: For neither or both forms, or a reversed range.
        RangeTooLargeError: For more than 366 days, checked before any data is read.
    """
    today = now.astimezone(ZoneInfo(timezone)).date()
    if preset is not None and start_date is None and end_date is None:
        if preset is Preset.TODAY:
            start_date = end_date = today
        elif preset is Preset.THIS_WEEK:
            start_date, end_date = today - timedelta(days=today.weekday()), today
        else:
            start_date, end_date = today - timedelta(days=7), today - timedelta(days=1)
    elif preset is not None or start_date is None or end_date is None:
        raise RequestInvalidError(_PERIOD_REQUIRED)
    if end_date < start_date:
        raise RequestInvalidError(_PERIOD_REVERSED)
    if (end_date - start_date).days + 1 > MAX_DAYS:
        raise RangeTooLargeError()
    start = local_midnight(start_date, timezone)
    end = local_midnight(end_date + timedelta(days=1), timezone)
    return Window(start_date, end_date, timezone, start, end, max(start, min(end, now)))
