"""Opportunity states and target availability without a database (spec 016, D10, D16)."""

from datetime import UTC, date, datetime, timedelta

import pytest

from app.intake.service.service import TRANSITIONS, effective_status, target_availability_of

NOW = datetime(2027, 1, 10, 9, 0, tzinfo=UTC)
TODAY = NOW.date()


def test_transitions_match_the_needs_table() -> None:
    """
    Condition:
    - The allowed moves.

    Expected:
    - Activate from draft or paused, pause from active, close from anything still open; expiry is never a person's move.
    """
    assert TRANSITIONS == {
        "activate": ({"DRAFT", "PAUSED"}, "ACTIVE"),
        "pause": ({"ACTIVE"}, "PAUSED"),
        "close": ({"DRAFT", "ACTIVE", "PAUSED"}, "CLOSED"),
    }


@pytest.mark.parametrize(
    ("status", "closes_at", "expected"),
    [
        ("ACTIVE", None, "ACTIVE"),
        ("ACTIVE", NOW + timedelta(seconds=1), "ACTIVE"),
        ("ACTIVE", NOW, "EXPIRED"),
        ("ACTIVE", NOW - timedelta(seconds=1), "EXPIRED"),
        ("PAUSED", NOW - timedelta(seconds=1), "EXPIRED"),
        ("DRAFT", NOW - timedelta(seconds=1), "DRAFT"),
        ("CLOSED", NOW - timedelta(seconds=1), "CLOSED"),
        ("EXPIRED", None, "EXPIRED"),
    ],
)
def test_effective_status(status: str, closes_at: datetime | None, expected: str) -> None:
    """
    Condition:
    - A stored status and a closing time before, at or after now.

    Expected:
    - Only a live opportunity expires, from the closing instant on.
    """
    assert effective_status(status, closes_at, NOW) == expected


@pytest.mark.parametrize(
    ("kind", "status", "route", "intake", "window", "expected"),
    [
        ("SPECIFIC", "ACTIVE", "IN_APP", "OPEN", (None, None), None),
        ("GENERAL_INTAKE", "ACTIVE", "IN_APP", "OPEN", (None, None), None),
        ("SPECIFIC", "PAUSED", "IN_APP", "OPEN", (None, None), "TARGET_NOT_ACTIVE"),
        ("GENERAL_INTAKE", "EXPIRED", "IN_APP", "OPEN", (None, None), "TARGET_NOT_ACTIVE"),
        ("SPECIFIC", "ACTIVE", "EXTERNAL", "OPEN", (None, None), "EXTERNAL_ROUTE"),
        ("SPECIFIC", "ACTIVE", "NONE", "OPEN", (None, None), "NO_NEW_APPROACHES"),
        ("SPECIFIC", "ACTIVE", "IN_APP", "CLOSED", (None, None), None),
        ("GENERAL_INTAKE", "ACTIVE", "IN_APP", "CLOSED", (None, None), "DIRECT_INTAKE_CLOSED"),
        ("SPECIFIC", "ACTIVE", "IN_APP", "UNCONFIRMED", (None, None), None),
        ("GENERAL_INTAKE", "ACTIVE", "IN_APP", "UNCONFIRMED", (None, None), "INTAKE_UNCONFIRMED"),
        ("GENERAL_INTAKE", "ACTIVE", "IN_APP", "OPEN", (None, TODAY - timedelta(days=1)), "INTAKE_UNCONFIRMED"),
        ("GENERAL_INTAKE", "ACTIVE", "IN_APP", "OPEN", (TODAY + timedelta(days=1), None), "INTAKE_UNCONFIRMED"),
        ("GENERAL_INTAKE", "ACTIVE", "IN_APP", "OPEN", (TODAY, TODAY), None),
        ("GENERAL_INTAKE", "ACTIVE", "NONE", "CLOSED", (None, None), "NO_NEW_APPROACHES"),
    ],
)
def test_target_availability_follows_the_table_in_order(
    kind: str,
    status: str,
    route: str,
    intake: str,
    window: tuple[date | None, date | None],
    expected: str | None,
) -> None:
    """
    Condition:
    - Each combination in the availability table, including the state only a directory entry can hold.

    Expected:
    - The first failing check gives the reason; a specific target ignores direct intake.
    """
    result = target_availability_of(
        kind=kind,
        status=status,
        contact_route=route,
        intake_status=intake,
        intake_from=window[0],
        intake_until=window[1],
        today=TODAY,
    )

    assert result.available is (expected is None)
    assert result.reason == expected
