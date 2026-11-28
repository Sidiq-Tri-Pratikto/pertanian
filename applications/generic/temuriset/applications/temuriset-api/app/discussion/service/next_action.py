"""Whose turn it is on one pitch, for one side: the prototype's ``pitchTurn`` on the server (spec 027 FR-001)."""

from dataclasses import dataclass, field, replace
from typing import Literal
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.locale import locale
from app.pitches.repository.sqlalchemy.models import PitchRecord

Side = Literal["requester", "recipient"]

_ENDED = {
    "REJECTED": "Pitching ditolak",
    "WITHDRAWN": "Pitching ditarik",
    "CLOSED": "Diskusi ditutup",
}


_EN = {
    "Pitching ditolak": "Pitch declined",
    "Pitching ditarik": "Pitch withdrawn",
    "Diskusi ditutup": "Discussion closed",
    "Menunggu tinjauan organisasi": "Waiting for organization review",
    "Peninjau organisasi memeriksa versi yang tepat ini.": "An organization reviewer is checking this exact version.",
    "Putuskan pitching ini": "Decide on this pitch",
    "Setujui untuk diskusi, minta revisi, atau tolak dengan alasan.": (
        "Approve for discussion, ask for a revision, or decline with a reason."
    ),
    "Pitching Anda sedang menunggu keputusan": "Your pitch is waiting for a decision",
    "{other_name} dapat menyetujui, meminta revisi, atau menolak.": (
        "{other_name} can approve, ask for a revision, or decline."
    ),
    "Menunggu jawaban revisi": "Waiting for the revision answers",
    "{other_name} sedang menjawab permintaan Anda.": "{other_name} is answering your request.",
    "Jawab permintaan revisi": "Answer the revision request",
    "Pertanyaan wajib perlu dijawab sebelum mengirim ulang.": "Required questions need answers before you resubmit.",
    "Waktu yang berlalu tidak otomatis berarti pertemuan selesai.": (
        "A time that has passed does not mean the meeting took place."
    ),
    "Kerja Sama dikonfirmasi kedua pihak": "Partnership confirmed by both sides",
    "Hanya data yang diizinkan kedua pihak yang tampil di publik.": "Only what both sides allow appears in public.",
    "Ringkasan Kerja Sama ditolak": "Partnership summary declined",
    "Menunggu konfirmasi pihak lain": "Waiting for the other side to confirm",
    "{other_name} perlu mengonfirmasi ringkasan versi {number}.": (
        "{other_name} needs to confirm summary version {number}."
    ),
    "Konfirmasi ringkasan Kerja Sama versi {number}": "Confirm partnership summary version {number}",
    "Periksa isi ringkasan dan data yang boleh tampil di publik.": "Check the summary and what may appear in public.",
    "Usulkan ringkasan Kerja Sama": "Propose a partnership summary",
    "Diskusi selesai. Kerja Sama hanya tercatat setelah kedua pihak mengonfirmasi versi yang sama.": (
        "The discussion is done. A partnership is recorded only after both sides confirm the same version."
    ),
    "Pertemuan sudah dikonfirmasi": "Meeting confirmed",
    "Menunggu catatan pihak lain": "Waiting for the other side's notes",
    "Catat hasil pertemuan": "Record the meeting outcome",
    "Menunggu pihak lain memilih waktu": "Waiting for the other side to choose a time",
    "{other_name} dapat memilih satu waktu atau mengusulkan waktu lain.": (
        "{other_name} can choose a time or propose other times."
    ),
    "Pilih waktu pertemuan": "Choose a meeting time",
    "Memilih belum memesan waktu. Konfirmasi agar pertemuan tercatat.": (
        "Choosing does not book the time yet. Confirm so the meeting is recorded."
    ),
    "Usulkan waktu pertemuan": "Propose meeting times",
    "Persetujuan ini membuka diskusi; belum merupakan pendanaan atau kerja sama.": (
        "This approval opens a discussion; it is not yet funding or a partnership."
    ),
}


def _t(text: str, **values: object) -> str:
    """The text in the request's language; templates keep their ``{name}`` placeholders in both."""
    translated = _EN.get(text, text) if locale() == "en" else text
    return translated.format(**values) if values else translated


@dataclass(frozen=True)
class ScheduleState:
    """What scheduling says about one approved pitch.

    Attributes:
        open_proposal_by (UUID | None): Party that made the open proposal, if one is open.
        meeting_starts_passed (bool | None): For the confirmed meeting, whether it has started; None without one.
        outcomes_by (frozenset[UUID]): Parties that recorded an outcome of the confirmed meeting.
        completed (bool): A meeting was completed by both parties.
        partnership_number (int | None): The relationship's current version, once one is proposed (030).
        partnership_status (str | None): That version's status.
        partnership_confirmed_by (frozenset[UUID]): Parties that confirmed that version.
    """

    open_proposal_by: UUID | None = None
    meeting_starts_passed: bool | None = None
    outcomes_by: frozenset[UUID] = field(default_factory=frozenset)
    completed: bool = False
    partnership_number: int | None = None
    partnership_status: str | None = None
    partnership_confirmed_by: frozenset[UUID] = field(default_factory=frozenset)


NO_SCHEDULE = ScheduleState()


class NextAction(BaseModel):
    """Who acts next and what that is, for the reader's side."""

    who: Literal["you", "other"] | None
    title: str
    text: str
    tab: str
    action: str | None = None


def _you(title: str, text: str, tab: str, action: str) -> NextAction:
    return NextAction(who="you", title=_t(title), text=_t(text), tab=tab, action=action)


def _other(title: str, text: str, tab: str) -> NextAction:
    return NextAction(who="other", title=_t(title), text=_t(text), tab=tab)


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
            _t("{other_name} dapat menyetujui, meminta revisi, atau menolak.", other_name=other_name),
            "ringkasan",
        )
    if status == "REVISION_REQUESTED":
        if recipient:
            return _other(
                "Menunggu jawaban revisi",
                _t("{other_name} sedang menjawab permintaan Anda.", other_name=other_name),
                "revisi",
            )
        return _you(
            "Jawab permintaan revisi",
            "Pertanyaan wajib perlu dijawab sebelum mengirim ulang.",
            "revisi",
            "answer_revision",
        )
    if status != "APPROVED_FOR_DISCUSSION":
        return NextAction(who=None, title=_t(_ENDED.get(status, status)), text="", tab="ringkasan")
    passing = "Waktu yang berlalu tidak otomatis berarti pertemuan selesai."
    if schedule.partnership_number is not None:
        number = schedule.partnership_number
        if schedule.partnership_status == "CONFIRMED":
            return NextAction(
                who=None,
                title=_t("Kerja Sama dikonfirmasi kedua pihak"),
                text=_t("Hanya data yang diizinkan kedua pihak yang tampil di publik."),
                tab="ringkasan",
            )
        if schedule.partnership_status == "DECLINED":
            return NextAction(who=None, title=_t("Ringkasan Kerja Sama ditolak"), text="", tab="ringkasan")
        if party_id in schedule.partnership_confirmed_by:
            return _other(
                "Menunggu konfirmasi pihak lain",
                _t("{other_name} perlu mengonfirmasi ringkasan versi {number}.", other_name=other_name, number=number),
                "ringkasan",
            )
        return _you(
            _t("Konfirmasi ringkasan Kerja Sama versi {number}", number=number),
            "Periksa isi ringkasan dan data yang boleh tampil di publik.",
            "ringkasan",
            "confirm_partnership",
        )
    if schedule.completed:
        return _you(
            "Usulkan ringkasan Kerja Sama",
            "Diskusi selesai. Kerja Sama hanya tercatat setelah kedua pihak mengonfirmasi versi yang sama.",
            "jadwal",
            "propose_partnership",
        )
    if schedule.meeting_starts_passed is not None:
        if not schedule.meeting_starts_passed:
            return NextAction(who=None, title=_t("Pertemuan sudah dikonfirmasi"), text="", tab="jadwal")
        if party_id in schedule.outcomes_by:
            return _other("Menunggu catatan pihak lain", passing, "jadwal")
        return _you("Catat hasil pertemuan", passing, "jadwal", "record_outcome")
    if schedule.open_proposal_by is not None:
        if schedule.open_proposal_by == party_id:
            return _other(
                "Menunggu pihak lain memilih waktu",
                _t("{other_name} dapat memilih satu waktu atau mengusulkan waktu lain.", other_name=other_name),
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
    # Both import this module for ScheduleState, so they load here.
    from app.relationships.service.state import partnership_states  # noqa: PLC0415
    from app.scheduling.service.state import schedule_states as read  # noqa: PLC0415

    states = await read(session, pitch_ids)
    for pitch_id, partnership in (await partnership_states(session, pitch_ids)).items():
        states[pitch_id] = replace(states.get(pitch_id, NO_SCHEDULE), **partnership)
    return states


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
