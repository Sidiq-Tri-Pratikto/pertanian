"""Freshness uses known recurring cadence and a valid capture."""

from datetime import UTC, datetime, timedelta

import pytest

from app.energy.service.freshness import recurring_state

NOW = datetime(2026, 10, 26, tzinfo=UTC)


@pytest.mark.parametrize(
    ("cadence", "age", "state"),
    [
        (3600, timedelta(hours=2), "current"),
        (3600, timedelta(hours=2, microseconds=1), "stale"),
        (900, timedelta(minutes=30), "current"),
        (900, timedelta(minutes=31), "stale"),
        (None, timedelta(days=1), "unknown"),
        (0, timedelta(days=1), "unknown"),
        (-1, timedelta(days=1), "unknown"),
        (3600, None, "unknown"),
    ],
)
def test_recurring_threshold(cadence: int | None, age: timedelta | None, state: str) -> None:
    """Check the strict boundary and refuse to infer missing cadence or capture."""
    assert recurring_state(NOW, NOW - age if age is not None else None, cadence) == state
