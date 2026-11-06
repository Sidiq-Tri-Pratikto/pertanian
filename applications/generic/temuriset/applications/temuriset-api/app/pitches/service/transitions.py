"""The pitch state table of PRD section 7, as data. Every status change goes through ``target``."""

from typing import Literal

from app.core.errors.base import InvalidTransitionError

Side = Literal["requester", "recipient"]
Action = Literal["begin_review", "approve", "reject", "request_revision", "resubmit", "withdraw", "close"]

_REVIEWABLE = frozenset({"SUBMITTED", "UNDER_REVIEW"})

# action: (statuses it may start from, status it leads to, sides that may take it)
TABLE: dict[str, tuple[frozenset[str], str, frozenset[str]]] = {
    "begin_review": (frozenset({"SUBMITTED"}), "UNDER_REVIEW", frozenset({"recipient"})),
    "approve": (_REVIEWABLE, "APPROVED_FOR_DISCUSSION", frozenset({"recipient"})),
    "reject": (_REVIEWABLE, "REJECTED", frozenset({"recipient"})),
    "request_revision": (_REVIEWABLE, "REVISION_REQUESTED", frozenset({"recipient"})),
    "resubmit": (frozenset({"REVISION_REQUESTED"}), "SUBMITTED", frozenset({"requester"})),
    "withdraw": (
        frozenset({"PENDING_WORKSPACE_REVIEW", "SUBMITTED", "UNDER_REVIEW", "REVISION_REQUESTED"}),
        "WITHDRAWN",
        frozenset({"requester"}),
    ),
    "close": (frozenset({"APPROVED_FOR_DISCUSSION"}), "CLOSED", frozenset({"requester", "recipient"})),
}

TERMINAL = frozenset({"REJECTED", "WITHDRAWN", "CLOSED"})

# Whose move it is, until discussion tasks (027) give a finer projection. Discussion and terminal states wait on no one.
_WAITING_ON: dict[str, Side] = {
    "PENDING_WORKSPACE_REVIEW": "requester",
    "SUBMITTED": "recipient",
    "UNDER_REVIEW": "recipient",
    "REVISION_REQUESTED": "requester",
}


def target(status: str, action: str) -> str:
    """Return the status an action leads to.

    Args:
        status (str): The current status.
        action (str): The action.

    Returns:
        str: The next status.

    Raises:
        InvalidTransitionError: When the table has no such move.
    """
    entry = TABLE.get(action)
    if entry is None or status not in entry[0]:
        raise InvalidTransitionError()
    return entry[1]


def allowed(status: str, side: Side) -> list[str]:
    """List the actions a side may take from a status, in table order.

    Args:
        status (str): The current status.
        side (Side): ``requester`` or ``recipient``.

    Returns:
        list[str]: Actions.
    """
    return [action for action, (starts, _, sides) in TABLE.items() if status in starts and side in sides]


def waiting_on(status: str) -> Side | None:
    """Return whose move it is.

    Args:
        status (str): The current status.

    Returns:
        Side | None: The side, or None while both discuss or once it ended.
    """
    return _WAITING_ON.get(status)
