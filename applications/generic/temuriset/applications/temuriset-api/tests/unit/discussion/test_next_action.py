"""Whose turn it is, every pitch and scheduling state for both parties, against the prototype's ``pitchTurn``."""

from uuid import UUID

import pytest

from app.discussion.service.next_action import NO_SCHEDULE, ScheduleState, next_action

RANI = UUID("00000000-0000-4000-8000-00000000000a")
MITRA = UUID("00000000-0000-4000-8000-00000000000b")

# (status, schedule, requester's who and title, recipient's who and title)
CASES = [
    (
        "PENDING_WORKSPACE_REVIEW",
        NO_SCHEDULE,
        ("other", "Menunggu tinjauan organisasi"),
        ("other", "Menunggu tinjauan organisasi"),
    ),
    ("SUBMITTED", NO_SCHEDULE, ("other", "Pitching Anda sedang menunggu keputusan"), ("you", "Putuskan pitching ini")),
    (
        "UNDER_REVIEW",
        NO_SCHEDULE,
        ("other", "Pitching Anda sedang menunggu keputusan"),
        ("you", "Putuskan pitching ini"),
    ),
    ("REVISION_REQUESTED", NO_SCHEDULE, ("you", "Jawab permintaan revisi"), ("other", "Menunggu jawaban revisi")),
    ("APPROVED_FOR_DISCUSSION", NO_SCHEDULE, ("you", "Usulkan waktu pertemuan"), ("you", "Usulkan waktu pertemuan")),
    (
        "APPROVED_FOR_DISCUSSION",
        ScheduleState(open_proposal_by=MITRA),
        ("you", "Pilih waktu pertemuan"),
        ("other", "Menunggu pihak lain memilih waktu"),
    ),
    (
        "APPROVED_FOR_DISCUSSION",
        ScheduleState(meeting_starts_passed=False),
        (None, "Pertemuan sudah dikonfirmasi"),
        (None, "Pertemuan sudah dikonfirmasi"),
    ),
    (
        "APPROVED_FOR_DISCUSSION",
        ScheduleState(meeting_starts_passed=True),
        ("you", "Catat hasil pertemuan"),
        ("you", "Catat hasil pertemuan"),
    ),
    (
        "APPROVED_FOR_DISCUSSION",
        ScheduleState(meeting_starts_passed=True, outcomes_by=frozenset({RANI})),
        ("other", "Menunggu catatan pihak lain"),
        ("you", "Catat hasil pertemuan"),
    ),
    (
        "APPROVED_FOR_DISCUSSION",
        ScheduleState(completed=True),
        (None, "Pertemuan selesai"),
        (None, "Pertemuan selesai"),
    ),
    ("REJECTED", NO_SCHEDULE, (None, "Pitching ditolak"), (None, "Pitching ditolak")),
    ("WITHDRAWN", NO_SCHEDULE, (None, "Pitching ditarik"), (None, "Pitching ditarik")),
    ("CLOSED", NO_SCHEDULE, (None, "Diskusi ditutup"), (None, "Diskusi ditutup")),
]


@pytest.mark.parametrize(("status", "schedule", "requester", "recipient"), CASES)
def test_each_state_names_who_acts_for_both_parties(
    status: str, schedule: ScheduleState, requester: tuple[str | None, str], recipient: tuple[str | None, str]
) -> None:
    """
    Condition:
    - Rani (requester) and Mitra A (recipient) read the same pitch in one pitch and scheduling state.

    Expected:
    - Each gets the prototype's ``who`` and title; a meeting time that passed never completes it by itself (AC47).
    """
    mine = next_action(status, "requester", RANI, "Mitra A", schedule)
    theirs = next_action(status, "recipient", MITRA, "Rani", schedule)

    assert (mine.who, mine.title) == requester
    assert (theirs.who, theirs.title) == recipient


def test_the_actions_point_at_the_room_tab_that_holds_them() -> None:
    """
    Condition:
    - The decision, revision and slot-choice states.

    Expected:
    - Each names its action key and tab, and the other side's text names the party it waits on.
    """
    decide = next_action("SUBMITTED", "recipient", MITRA, "Rani", NO_SCHEDULE)
    revise = next_action("REVISION_REQUESTED", "requester", RANI, "Mitra A", NO_SCHEDULE)
    waiting = next_action("SUBMITTED", "requester", RANI, "Mitra A", NO_SCHEDULE)

    assert (decide.action, decide.tab) == ("decide", "ringkasan")
    assert (revise.action, revise.tab) == ("answer_revision", "revisi")
    assert waiting.text.startswith("Mitra A dapat")
