"""The pitch state table against PRD section 7, every status and action pair (spec 025)."""

import itertools

import pytest

from app.core.errors.base import InvalidTransitionError
from app.pitches.repository.sqlalchemy.models import PITCH_STATUSES
from app.pitches.service.transitions import TABLE, allowed, target, waiting_on

# PRD section 7, written out by hand so a change to the table has to change this too.
EXPECTED = {
    ("SUBMITTED", "begin_review"): "UNDER_REVIEW",
    ("SUBMITTED", "approve"): "APPROVED_FOR_DISCUSSION",
    ("UNDER_REVIEW", "approve"): "APPROVED_FOR_DISCUSSION",
    ("SUBMITTED", "reject"): "REJECTED",
    ("UNDER_REVIEW", "reject"): "REJECTED",
    ("SUBMITTED", "request_revision"): "REVISION_REQUESTED",
    ("UNDER_REVIEW", "request_revision"): "REVISION_REQUESTED",
    ("REVISION_REQUESTED", "resubmit"): "SUBMITTED",
    ("PENDING_WORKSPACE_REVIEW", "withdraw"): "WITHDRAWN",
    ("SUBMITTED", "withdraw"): "WITHDRAWN",
    ("UNDER_REVIEW", "withdraw"): "WITHDRAWN",
    ("REVISION_REQUESTED", "withdraw"): "WITHDRAWN",
    ("APPROVED_FOR_DISCUSSION", "close"): "CLOSED",
}


@pytest.mark.parametrize(("status", "action"), list(itertools.product(PITCH_STATUSES, TABLE)))
def test_every_status_and_action_pair_follows_the_prd(status: str, action: str) -> None:
    """
    Condition:
    - Each of the nine statuses meets each of the seven actions.

    Expected:
    - The move the PRD lists leads where it says; every other pair is ``INVALID_TRANSITION``.
    """
    expected = EXPECTED.get((status, action))

    if expected is None:
        with pytest.raises(InvalidTransitionError):
            target(status, action)
    else:
        assert target(status, action) == expected


def test_an_approved_pitch_cannot_go_back_to_revision_and_ended_ones_never_reopen() -> None:
    """
    Condition:
    - Approved, rejected, withdrawn and closed pitches.

    Expected:
    - Approval offers only closing; ended pitches offer nothing to either side and wait on no one.
    """
    assert allowed("APPROVED_FOR_DISCUSSION", "recipient") == ["close"]
    assert allowed("APPROVED_FOR_DISCUSSION", "requester") == ["close"]
    for status in ("REJECTED", "WITHDRAWN", "CLOSED"):
        assert allowed(status, "recipient") == allowed(status, "requester") == []
        assert waiting_on(status) is None


def test_whose_turn_follows_the_status() -> None:
    """
    Condition:
    - A submitted pitch, one in revision, and one in discussion.

    Expected:
    - The recipient, the requester, then no one.
    """
    assert waiting_on("SUBMITTED") == waiting_on("UNDER_REVIEW") == "recipient"
    assert waiting_on("REVISION_REQUESTED") == "requester"
    assert waiting_on("APPROVED_FOR_DISCUSSION") is None
