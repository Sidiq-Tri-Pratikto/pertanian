"""Whose turn it is on one pitch, for one side: the prototype's ``pitchTurn`` on the server (spec 027 FR-001)."""

from dataclasses import dataclass, field
from typing import Literal
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.pitches.repository.sqlalchemy.models import PitchRecord

Side = Literal["requester", "recipient"]

_ENDED = {
    "REJECTED": "Pitching ditolak",
    "WITHDRAWN": "Pitching ditarik",
    "CLOSED": "Diskusi ditutup",
}


@dataclass(frozen=True)
class ScheduleState:
    """What scheduling says about one approved pitch.

    Attributes:
        open_proposal_by (UUID | None): Party that made the open proposal, if one is open.
        meeting_starts_passed (bool | None): For the confirmed meeting, whether it has started; None without one.
        outcomes_by (frozenset[UUID]): Parties that recorded an outcome of the confirmed meeting.
        completed (bool): A meeting was completed by both parties.
    """

    open_proposal_by: UUID | None = None
    meeting_starts_passed: bool | None = None
    outcomes_by: frozenset[UUID] = field(default_factory=frozenset)
    completed: bool = False


NO_SCHEDULE = ScheduleState()


class NextAction(BaseModel):
    """Who acts next and what that is, for the reader's side."""

    who: Literal["you", "other"] | None
    title: str
    text: str
    tab: str
    action: str | None = None


def _you(title: str, text: str, tab: str, action: str) -> NextAction:
    return NextAction(who="you", title=title, text=text, tab=tab, action=action)


def _other(title: str, text: str, tab: str) -> NextAction:
    return NextAction(who="other", title=title, text=text, tab=tab)


def next_action(status: str, side: Side, party_id: UUID, other_name: str, schedule: ScheduleState) -> NextAction:
    """Return the next action on a pitch for one side.

    Args:
        status (str): The pitch status.
        side (Side): The reader's side.
        party_id (UUID): The reader's party.
        other_name (str): The other party's name.
        schedule (ScheduleState): Scheduling state, for an approved pitch.

    Returns:
        NextAction: Who acts next, a title, a sentence, the room tab and an action key.
    """
    recipient = side == "recipient"
    if status == "PENDING_WORKSPACE_REVIEW":
        return _other(
            "Menunggu tinjauan organisasi", "Peninjau organisasi memeriksa versi yang tepat ini.", "ringkasan"
        )
    if status in ("SUBMITTED", "UNDER_REVIEW"):
        if recipient:
            return _you(
                "Putuskan pitching ini",
                "Setujui untuk diskusi, minta revisi, atau tolak dengan alasan.",
                "ringkasan",
                "decide",
            )
        return _other(
            "Pitching Anda sedang menunggu keputusan",
            f"{other_name} dapat menyetujui, meminta revisi, atau menolak.",
            "ringkasan",
        )
    if status == "REVISION_REQUESTED":
        if recipient:
            return _other("Menunggu jawaban revisi", f"{other_name} sedang menjawab permintaan Anda.", "revisi")
        return _you(
            "Jawab permintaan revisi",
            "Pertanyaan wajib perlu dijawab sebelum mengirim ulang.",
            "revisi",
            "answer_revision",
        )
    if status != "APPROVED_FOR_DISCUSSION":
        return NextAction(who=None, title=_ENDED.get(status, status), text="", tab="ringkasan")
    passing = "Waktu yang berlalu tidak otomatis berarti pertemuan selesai."
    if schedule.completed:
        # ponytail: the relationship summary (030) is not built, so a completed meeting waits on no one yet.
        return NextAction(
            who=None,
            title="Pertemuan selesai",
            text="Kedua pihak mencatat pertemuan selesai. Kerja Sama hanya tercatat setelah keduanya mengonfirmasi.",
            tab="jadwal",
        )
    if schedule.meeting_starts_passed is not None:
        if not schedule.meeting_starts_passed:
            return NextAction(who=None, title="Pertemuan sudah dikonfirmasi", text="", tab="jadwal")
        if party_id in schedule.outcomes_by:
            return _other("Menunggu catatan pihak lain", passing, "jadwal")
        return _you("Catat hasil pertemuan", passing, "jadwal", "record_outcome")
    if schedule.open_proposal_by is not None:
        if schedule.open_proposal_by == party_id:
            return _other(
                "Menunggu pihak lain memilih waktu",
                f"{other_name} dapat memilih satu waktu atau mengusulkan waktu lain.",
                "jadwal",
            )
        return _you(
            "Pilih waktu pertemuan",
            "Memilih belum memesan waktu. Konfirmasi agar pertemuan tercatat.",
            "jadwal",
            "choose_slot",
        )
    return _you(
        "Usulkan waktu pertemuan",
        "Persetujuan ini membuka diskusi; belum merupakan pendanaan atau kerja sama.",
        "jadwal",
        "propose_slots",
    )


async def schedule_states(session: AsyncSession, pitch_ids: list[UUID]) -> dict[UUID, ScheduleState]:
    """Scheduling state per pitch, from spec 028.

    Args:
        session (AsyncSession): The request's session.
        pitch_ids (list[UUID]): Pitches.

    Returns:
        dict[UUID, ScheduleState]: States; a missing pitch has no proposal or meeting.
    """
    from app.scheduling.service.state import schedule_states as read  # noqa: PLC0415 - scheduling imports this module

    return await read(session, pitch_ids)


async def waiting_parties(session: AsyncSession, records: list[PitchRecord]) -> dict[UUID, UUID | None]:
    """Return whose turn it is per pitch: the one party whose next action is theirs, or None.

    Args:
        session (AsyncSession): The request's session.
        records (list[PitchRecord]): Pitches.

    Returns:
        dict[UUID, UUID | None]: Pitch to waiting party; None when both or neither may act.
    """
    states = await schedule_states(session, [record.id for record in records])
    result: dict[UUID, UUID | None] = {}
    for record in records:
        state = states.get(record.id, NO_SCHEDULE)
        sides: tuple[tuple[UUID, Side], ...] = (
            (record.requester_party_id, "requester"),
            (record.recipient_party_id, "recipient"),
        )
        mine = [party for party, side in sides if next_action(record.status, side, party, "", state).who == "you"]
        result[record.id] = mine[0] if len(mine) == 1 else None
    return result
