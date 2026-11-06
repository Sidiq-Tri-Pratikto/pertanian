"""Wall-clock time. Product time comes from ``site_clock``; this serves audit, expiry and security."""

from datetime import UTC, datetime


def wall_now() -> datetime:
    """Return the current UTC instant.

    Returns:
        datetime: Timezone-aware now.
    """
    return datetime.now(UTC)
