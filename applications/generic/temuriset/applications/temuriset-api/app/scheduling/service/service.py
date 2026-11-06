"""Propose, accept, replace, cancel and record outcomes; bookings are race-safe through the database (spec 028)."""

from collections import defaultdict
from datetime import timedelta
from typing import Any
from uuid import UUID

from sqlalchemy.dialects.postgresql import Range
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.access.model.models import Capability
from app.access.service.policy import check_context
from app.access.service.service import party_names
from app.core import clock
from app.core.errors import codes
from app.core.errors.base import AppError, FieldsInvalidError, ForbiddenError, InvalidTransitionError, NotFoundError
from app.identity.model.models import Principal
from app.pitches.repository.sqlalchemy.models import PitchRecord
from app.pitches.service.decisions import visible_pitch
from app.platform.service.audit import record_audit
from app.platform.service.outbox import enqueue_job, publish
from app.platform.service.versions import check_expected
from app.scheduling.model.schema import (
    AcceptRequest,
    MeetingResponse,
    OutcomeRequest,
    OutcomeResponse,
    ProposalResponse,
    ProposeRequest,
    ScheduleResponse,
    SlotResponse,
    VersionedRequest,
)
from app.scheduling.repository.sqlalchemy.models import (
    BookingRecord,
    MeetingOutcomeRecord,
    MeetingRecord,
    ScheduleProposalRecord,
    ScheduleSlotRecord,
)
from app.scheduling.repository.sqlalchemy.repository import SqlAlchemySchedulingRepository
from app.scheduling.service.calendar_adapter import CalendarWindow
from app.scheduling.service.expiry import expire_if_due, expires_at
from app.scheduling.service.ics import calendar

EXPIRE_JOB = "scheduling.expire"

_CLOSED_REASON = {
    "EXPIRED": "Usulan ini sudah kedaluwarsa. Pitching tetap disetujui untuk diskusi.",
    "SUPERSEDED": "Usulan ini sudah diganti dengan usulan yang lebih baru.",
    "ACCEPTED": "Usulan ini sudah dikonfirmasi.",
    "CANCELLED": "Usulan ini sudah dibatalkan.",
}


class BookingConflictError(AppError):
    """The slot overlaps a booking of either party."""

    code = codes.APP_BOOKING_CONFLICT


class ProposalClosedError(AppError):
    """The proposal is no longer open."""

    code = codes.APP_PROPOSAL_CLOSED


def _field(name: str, message: str) -> dict[str, Any]:
    return {"loc": ["body", name], "msg": message, "type": name}


class SchedulingService:
    """Meetings for approved pitches. Choosing a slot is not booking it; confirming is."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind to the request.

        Args:
            session (AsyncSession): The request's session.
        """
        self.session = session
        self.repository = SqlAlchemySchedulingRepository(session)

    async def _room(self, principal: Principal, pitch_id: UUID, acting_party_id: UUID | None = None) -> PitchRecord:
        """The pitch, for a member who may schedule on an approved pitch."""
        if acting_party_id is not None:
            check_context(principal, acting_party_id)
        record, _ = await visible_pitch(self.session, principal, pitch_id)
        if Capability.SCHEDULE not in principal.capabilities:
            raise ForbiddenError()
        if record.status != "APPROVED_FOR_DISCUSSION":
            raise InvalidTransitionError()
        return record

    async def propose(
        self, principal: Principal, pitch_id: UUID, request: ProposeRequest, operation_id: UUID | None = None
    ) -> ProposalResponse:
        """Offer 2–5 future slots; an open proposal of either party is superseded (a counter).

        Args:
            principal (Principal): Who is signed in.
            pitch_id (UUID): The pitch.
            request (ProposeRequest): Slots, length, zone, agenda, link and the meeting it replaces.
            operation_id (UUID | None, optional): For the response. Defaults to None.

        Returns:
            ProposalResponse: The proposal.

        Raises:
            FieldsInvalidError: For a past slot, a replacement of no confirmed meeting, or a second meeting.
        """
        record = await self._room(principal, pitch_id, request.acting_party_id)
        now = clock.now()
        errors = []
        if any(slot <= now for slot in request.slots):
            errors.append(_field("slots", "Waktu yang diusulkan harus setelah jam saat ini."))
        if len(set(request.slots)) != len(request.slots):
            errors.append(_field("slots", "Setiap waktu yang diusulkan harus berbeda."))
        confirmed = [m for m in await self.repository.meetings([record.id]) if m.state == "CONFIRMED"]
        if request.replaces_meeting_id is not None and request.replaces_meeting_id not in {m.id for m in confirmed}:
            errors.append(_field("replaces_meeting_id", "Pilih pertemuan terkonfirmasi yang ingin diganti."))
        if request.replaces_meeting_id is None and confirmed:
            errors.append(_field("replaces_meeting_id", "Pertemuan sudah dikonfirmasi; usulkan jadwal pengganti."))
        if errors:
            raise FieldsInvalidError(errors)
        for open_ in await self.repository.proposals([record.id], lock=True):
            if open_.state == "OPEN":
                open_.state = "SUPERSEDED"
                open_.version += 1
        proposal = await self.repository.add(
            ScheduleProposalRecord(
                pitch_id=record.id,
                proposed_by_party_id=principal.active_party_id,
                proposed_by_account_id=principal.account_id,
                minutes=request.minutes,
                time_zone=request.time_zone,
                agenda=request.agenda,
                link=request.link,
                replaces_meeting_id=request.replaces_meeting_id,
            )
        )
        slots = []
        for position, start in enumerate(sorted(request.slots), start=1):
            slots.append(
                await self.repository.add(
                    ScheduleSlotRecord(
                        proposal_id=proposal.id,
                        position=position,
                        starts_at=start,
                        ends_at=start + timedelta(minutes=request.minutes),
                    )
                )
            )
        await enqueue_job(
            self.session,
            EXPIRE_JOB,
            {"proposal_id": str(proposal.id)},
            actor_party_id=principal.active_party_id,
            run_after=expires_at(proposal, slots),
        )
        await self._event(principal, record, "schedule.proposed", {"proposal_id": str(proposal.id)})
        names = await party_names(self.session, [principal.active_party_id])
        return self._proposal(proposal, slots, principal, names, operation_id)

    async def _event(self, principal: Principal, record: PitchRecord, topic: str, payload: dict[str, Any]) -> None:
        await publish(
            self.session,
            topic,
            {"pitch_id": str(record.id), "actor_party_id": str(principal.active_party_id), **payload},
        )
        await record_audit(
            self.session,
            action=topic,
            subject_type="pitch",
            subject_id=str(record.id),
            actor_account_id=principal.account_id,
            actor_party_id=principal.active_party_id,
        )

    async def _open(self, principal: Principal, proposal_id: UUID, acting_party_id: UUID) -> tuple[Any, PitchRecord]:
        proposal = await self.repository.proposal(proposal_id, lock=True)
        if proposal is None:
            raise NotFoundError()
        record = await self._room(principal, proposal.pitch_id, acting_party_id)
        slots = await self.repository.slots([proposal.id])
        expire_if_due(proposal, slots, clock.now())
        if proposal.state != "OPEN":
            await self.session.flush()
            raise ProposalClosedError(public_fields={"reason": _CLOSED_REASON[proposal.state]})
        return (proposal, slots), record

    async def accept(
        self, principal: Principal, proposal_id: UUID, request: AcceptRequest, operation_id: UUID | None = None
    ) -> MeetingResponse:
        """Confirm one slot: the meeting, both bookings and any replacement commit together (FR-002, AC50, AC51).

        Args:
            principal (Principal): Who is signed in.
            proposal_id (UUID): The proposal.
            request (AcceptRequest): The slot and ``expected_version``.
            operation_id (UUID | None, optional): For the response. Defaults to None.

        Returns:
            MeetingResponse: The confirmed meeting.

        Raises:
            ProposalClosedError: When it expired, was superseded, accepted or cancelled.
            ForbiddenError: For the proposer, who cannot accept its own proposal.
            BookingConflictError: When either party is already booked then; nothing changes.
        """
        (proposal, slots), record = await self._open(principal, proposal_id, request.acting_party_id)
        if proposal.proposed_by_party_id == principal.active_party_id:
            # The proposer cannot accept its own proposal; the other party chooses.
            raise ForbiddenError()
        check_expected(proposal.version, request.expected_version)
        slot = next((slot for slot in slots if slot.id == request.slot_id), None)
        if slot is None:
            raise NotFoundError()
        try:
            async with self.session.begin_nested():
                if proposal.replaces_meeting_id is not None:
                    old = await self.repository.meeting(proposal.replaces_meeting_id, lock=True)
                    if old is None or old.state != "CONFIRMED":
                        raise InvalidTransitionError()
                    await self.repository.release(old.id)
                    old.state = "CANCELLED"
                    old.version += 1
                meeting = await self.repository.add(
                    MeetingRecord(
                        pitch_id=record.id,
                        proposal_id=proposal.id,
                        starts_at=slot.starts_at,
                        ends_at=slot.ends_at,
                        time_zone=proposal.time_zone,
                        agenda=proposal.agenda,
                        link=proposal.link,
                    )
                )
                for party in (record.requester_party_id, record.recipient_party_id):
                    await self.repository.add(
                        BookingRecord(
                            party_id=party,
                            meeting_id=meeting.id,
                            title="Diskusi pitching",
                            during=Range(slot.starts_at, slot.ends_at, bounds="[)"),
                        )
                    )
        except IntegrityError as error:
            # The exclusion constraint refused an overlap; the savepoint kept the old meeting and its bookings.
            raise BookingConflictError(public_fields={"slot_id": str(slot.id)}, error=error) from error
        proposal.state, proposal.accepted_slot_id = "ACCEPTED", slot.id
        proposal.version += 1
        await self.session.flush()
        topic = "meeting.replaced" if proposal.replaces_meeting_id else "meeting.confirmed"
        await self._event(principal, record, topic, {"meeting_id": str(meeting.id)})
        return await self._meeting(meeting, record, operation_id)

    async def cancel_proposal(
        self, principal: Principal, proposal_id: UUID, request: VersionedRequest, operation_id: UUID | None = None
    ) -> ProposalResponse:
        """Cancel an open proposal. A meeting it would replace stays confirmed.

        Args:
            principal (Principal): Who is signed in.
            proposal_id (UUID): The proposal.
            request (VersionedRequest): ``expected_version``.
            operation_id (UUID | None, optional): For the response. Defaults to None.

        Returns:
            ProposalResponse: The proposal.
        """
        (proposal, slots), record = await self._open(principal, proposal_id, request.acting_party_id)
        check_expected(proposal.version, request.expected_version)
        proposal.state = "CANCELLED"
        proposal.version += 1
        await self.session.flush()
        await self._event(principal, record, "schedule.cancelled", {"proposal_id": str(proposal.id)})
        names = await party_names(self.session, [proposal.proposed_by_party_id])
        return self._proposal(proposal, slots, principal, names, operation_id)

    async def _confirmed(
        self, principal: Principal, meeting_id: UUID, acting_party_id: UUID
    ) -> tuple[MeetingRecord, PitchRecord]:
        meeting = await self.repository.meeting(meeting_id, lock=True)
        if meeting is None:
            raise NotFoundError()
        record = await self._room(principal, meeting.pitch_id, acting_party_id)
        if meeting.state != "CONFIRMED":
            raise InvalidTransitionError()
        return meeting, record

    async def cancel_meeting(
        self, principal: Principal, meeting_id: UUID, request: VersionedRequest, operation_id: UUID | None = None
    ) -> MeetingResponse:
        """Cancel a confirmed meeting and free both bookings; a separate action from cancelling a proposal.

        Args:
            principal (Principal): Who is signed in.
            meeting_id (UUID): The meeting.
            request (VersionedRequest): ``expected_version``.
            operation_id (UUID | None, optional): For the response. Defaults to None.

        Returns:
            MeetingResponse: The meeting.
        """
        meeting, record = await self._confirmed(principal, meeting_id, request.acting_party_id)
        check_expected(meeting.version, request.expected_version)
        await self.repository.release(meeting.id)
        meeting.state = "CANCELLED"
        meeting.version += 1
        await self.session.flush()
        await self._event(principal, record, "meeting.cancelled", {"meeting_id": str(meeting.id)})
        return await self._meeting(meeting, record, operation_id)

    async def record_outcome(
        self, principal: Principal, meeting_id: UUID, request: OutcomeRequest, operation_id: UUID | None = None
    ) -> MeetingResponse:
        """Record what the acting party says happened. Only both parties agreeing settles the meeting (AC47).

        Args:
            principal (Principal): Who is signed in.
            meeting_id (UUID): The meeting.
            request (OutcomeRequest): Result and note.
            operation_id (UUID | None, optional): For the response. Defaults to None.

        Returns:
            MeetingResponse: The meeting.

        Raises:
            InvalidTransitionError: Before the meeting starts, or once it is settled.
        """
        meeting, record = await self._confirmed(principal, meeting_id, request.acting_party_id)
        if clock.now() < meeting.starts_at:
            raise InvalidTransitionError()
        mine = await self.repository.outcome(meeting.id, principal.active_party_id)
        if mine is None:
            await self.repository.add(
                MeetingOutcomeRecord(
                    meeting_id=meeting.id,
                    party_id=principal.active_party_id,
                    result=request.result,
                    note=request.note,
                    recorded_by_account_id=principal.account_id,
                )
            )
        else:
            mine.result, mine.note, mine.recorded_by_account_id = request.result, request.note, principal.account_id
            mine.version += 1
        results = {outcome.party_id: outcome.result for outcome in await self.repository.outcomes([meeting.id])}
        both = [results.get(record.requester_party_id), results.get(record.recipient_party_id)]
        if both[0] and both[0] == both[1]:
            meeting.state = "COMPLETED" if both[0] == "COMPLETED" else "NO_SHOW_REPORTED"
        meeting.version += 1
        await self.session.flush()
        await self._event(principal, record, "meeting.outcome", {"meeting_id": str(meeting.id)})
        return await self._meeting(meeting, record, operation_id)

    async def read(self, principal: Principal, pitch_id: UUID) -> ScheduleResponse:
        """Read every proposal and meeting of a pitch, expiring proposals whose time is up.

        Args:
            principal (Principal): Who is signed in.
            pitch_id (UUID): The pitch.

        Returns:
            ScheduleResponse: Proposals newest first, meetings newest first, and whether the reader may schedule.
        """
        record, _ = await visible_pitch(self.session, principal, pitch_id)
        proposals = await self.repository.proposals([record.id])
        slots: dict[UUID, list[ScheduleSlotRecord]] = defaultdict(list)
        for slot in await self.repository.slots([proposal.id for proposal in proposals]):
            slots[slot.proposal_id].append(slot)
        now = clock.now()
        for proposal in proposals:
            expire_if_due(proposal, slots[proposal.id], now)
        await self.session.flush()
        names = await party_names(self.session, [record.requester_party_id, record.recipient_party_id])
        meetings = [await self._meeting(meeting, record) for meeting in await self.repository.meetings([record.id])]
        return ScheduleResponse(
            proposals=[self._proposal(p, slots[p.id], principal, names) for p in proposals],
            meetings=meetings,
            can_schedule=record.status == "APPROVED_FOR_DISCUSSION" and Capability.SCHEDULE in principal.capabilities,
        )

    @staticmethod
    def calendar_windows(schedule: ScheduleResponse) -> tuple[UUID, dict[UUID, CalendarWindow]] | None:
        """Limit external reads to the current proposal's future slots."""
        open_proposal = next((proposal for proposal in schedule.proposals if proposal.state == "OPEN"), None)
        if open_proposal is None:
            return None
        now = clock.now()
        windows = {
            slot.id: CalendarWindow(slot.starts_at, slot.ends_at)
            for slot in open_proposal.slots
            if slot.starts_at > now
        }
        return (open_proposal.id, windows) if windows else None

    @staticmethod
    def annotate_calendar(
        schedule: ScheduleResponse,
        query: tuple[UUID, dict[UUID, CalendarWindow]],
        busy: list[CalendarWindow],
    ) -> None:
        """Apply the advisory result only to queried slots still in the same open proposal."""
        current = SchedulingService.calendar_windows(schedule)
        if current is None or current[0] != query[0]:
            return
        proposal = next(proposal for proposal in schedule.proposals if proposal.id == query[0])
        for slot in proposal.slots:
            window = current[1].get(slot.id)
            if window is not None and window == query[1].get(slot.id):
                slot.external_availability = "busy" if any(window.overlaps(interval) for interval in busy) else "free"
                schedule.external_calendar = "advisory"

    async def ics(self, principal: Principal, meeting_id: UUID) -> str:
        """Build a calendar file from the stored UTC instants (FR-004, AC68).

        Args:
            principal (Principal): Who is signed in.
            meeting_id (UUID): The meeting.

        Returns:
            str: The iCalendar text.

        Raises:
            NotFoundError: For a meeting outside the reader's pitches, or one that is not confirmed.
        """
        meeting = await self.repository.meeting(meeting_id)
        if meeting is None:
            raise NotFoundError()
        record, _ = await visible_pitch(self.session, principal, meeting.pitch_id)
        if meeting.state not in ("CONFIRMED", "COMPLETED"):
            raise NotFoundError()
        return calendar(meeting, f"{record.subject_title} → {record.opportunity_title}", clock.now())

    @staticmethod
    def _proposal(
        proposal: ScheduleProposalRecord,
        slots: list[ScheduleSlotRecord],
        principal: Principal,
        names: dict[UUID, str],
        operation_id: UUID | None = None,
    ) -> ProposalResponse:
        return ProposalResponse(
            id=proposal.id,
            proposed_by_party_id=proposal.proposed_by_party_id,
            proposed_by_name=names.get(proposal.proposed_by_party_id, ""),
            mine=proposal.proposed_by_party_id == principal.active_party_id,
            minutes=proposal.minutes,
            time_zone=proposal.time_zone,
            agenda=proposal.agenda,
            link=proposal.link,
            state=proposal.state,  # type: ignore[arg-type]
            expired_reason=proposal.expired_reason,  # type: ignore[arg-type]
            replaces_meeting_id=proposal.replaces_meeting_id,
            accepted_slot_id=proposal.accepted_slot_id,
            version=proposal.version,
            created_at=proposal.created_at,
            expires_at=expires_at(proposal, slots),
            slots=[
                SlotResponse(id=slot.id, position=slot.position, starts_at=slot.starts_at, ends_at=slot.ends_at)
                for slot in slots
            ],
            operation_id=operation_id,
        )

    async def _meeting(
        self, meeting: MeetingRecord, record: PitchRecord, operation_id: UUID | None = None
    ) -> MeetingResponse:
        outcomes = await self.repository.outcomes([meeting.id])
        names = await party_names(self.session, [outcome.party_id for outcome in outcomes])
        results = {outcome.result for outcome in outcomes}
        return MeetingResponse(
            id=meeting.id,
            proposal_id=meeting.proposal_id,
            starts_at=meeting.starts_at,
            ends_at=meeting.ends_at,
            time_zone=meeting.time_zone,
            agenda=meeting.agenda,
            link=meeting.link,
            state=meeting.state,  # type: ignore[arg-type]
            version=meeting.version,
            started=meeting.starts_at <= clock.now(),
            outcomes=[
                OutcomeResponse(
                    party_id=o.party_id,
                    party_name=names.get(o.party_id, ""),
                    result=o.result,  # type: ignore[arg-type]
                    note=o.note,
                )
                for o in outcomes
            ],
            disagreement=len(outcomes) == 2 and len(results) == 2,
            operation_id=operation_id,
        )

    async def expire(self, proposal_id: UUID) -> None:
        """Persist a proposal's expiry when its time comes; the worker job calls it.

        Args:
            proposal_id (UUID): The proposal.
        """
        proposal = await self.repository.proposal(proposal_id, lock=True)
        if proposal is not None:
            expire_if_due(proposal, await self.repository.slots([proposal.id]), clock.now())
            await self.session.flush()
