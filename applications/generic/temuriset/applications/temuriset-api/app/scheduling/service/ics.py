"""An iCalendar file built from stored UTC instants, with no calendar connection (FR-004)."""

from datetime import datetime

from app.scheduling.repository.sqlalchemy.models import MeetingRecord


def _stamp(instant: datetime) -> str:
    return instant.strftime("%Y%m%dT%H%M%SZ")


def _text(value: str) -> str:
    """Escape a TEXT value as RFC 5545 requires."""
    return value.replace("\\", "\\\\").replace(";", r"\;").replace(",", "\\,").replace("\r", "").replace("\n", "\\n")


def calendar(meeting: MeetingRecord, title: str, now: datetime) -> str:
    """Build the calendar text of one meeting.

    Args:
        meeting (MeetingRecord): The meeting.
        title (str): What the meeting is about.
        now (datetime): Product time, for ``DTSTAMP``.

    Returns:
        str: The iCalendar text, CRLF line endings.
    """
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//TemuRiset//ID",
        "BEGIN:VEVENT",
        f"UID:{meeting.id}@temuriset",
        f"DTSTAMP:{_stamp(now)}",
        f"DTSTART:{_stamp(meeting.starts_at)}",
        f"DTEND:{_stamp(meeting.ends_at)}",
        f"SUMMARY:{_text('Diskusi pitching: ' + title)}",
        f"DESCRIPTION:{_text(meeting.agenda)}",
        *([f"URL:{meeting.link}"] if meeting.link else []),
        "END:VEVENT",
        "END:VCALENDAR",
    ]
    return "\r\n".join(lines) + "\r\n"
