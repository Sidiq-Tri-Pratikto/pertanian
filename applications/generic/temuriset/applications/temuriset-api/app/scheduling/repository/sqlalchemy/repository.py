"""Scheduling storage."""

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.scheduling.repository.sqlalchemy.models import (
    BookingRecord,
    CalendarConnectionRecord,
    MeetingOutcomeRecord,
    MeetingRecord,
    ScheduleProposalRecord,
    ScheduleSlotRecord,
)


class SqlAlchemySchedulingRepository:
    """Writes and reads proposals, slots, meetings, bookings and outcomes."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind to the session.

        Args:
            session (AsyncSession): The request's session.
        """
        self.session = session

    async def add[RecordT](self, record: RecordT) -> RecordT:
        """Insert a record.

        Args:
            record (RecordT): Any scheduling record.

        Returns:
            RecordT: The stored record.
        """
        self.session.add(record)
        await self.session.flush()
        return record

    async def proposal(self, proposal_id: UUID, *, lock: bool = False) -> ScheduleProposalRecord | None:
        """Find a proposal.

        Args:
            proposal_id (UUID): The proposal.
            lock (bool, optional): Lock it for an acceptance or a change. Defaults to False.

        Returns:
            ScheduleProposalRecord | None: The proposal.
        """
        query = select(ScheduleProposalRecord).where(ScheduleProposalRecord.id == proposal_id)
        if lock:
            query = query.with_for_update().execution_options(populate_existing=True)
        return await self.session.scalar(query)

    async def proposals(self, pitch_ids: list[UUID], *, lock: bool = False) -> list[ScheduleProposalRecord]:
        """List proposals of pitches, newest first.

        Args:
            pitch_ids (list[UUID]): Pitches.
            lock (bool, optional): Lock them. Defaults to False.

        Returns:
            list[ScheduleProposalRecord]: Proposals.
        """
        query = select(ScheduleProposalRecord).where(ScheduleProposalRecord.pitch_id.in_(pitch_ids))
        query = query.order_by(ScheduleProposalRecord.created_at.desc())
        if lock:
            query = query.with_for_update().execution_options(populate_existing=True)
        return list(await self.session.scalars(query))

    async def slots(self, proposal_ids: list[UUID]) -> list[ScheduleSlotRecord]:
        """List the slots of proposals, in order.

        Args:
            proposal_ids (list[UUID]): Proposals.

        Returns:
            list[ScheduleSlotRecord]: Slots.
        """
        query = select(ScheduleSlotRecord).where(ScheduleSlotRecord.proposal_id.in_(proposal_ids))
        return list(await self.session.scalars(query.order_by(ScheduleSlotRecord.position)))

    async def meeting(self, meeting_id: UUID, *, lock: bool = False) -> MeetingRecord | None:
        """Find a meeting.

        Args:
            meeting_id (UUID): The meeting.
            lock (bool, optional): Lock it for a change. Defaults to False.

        Returns:
            MeetingRecord | None: The meeting.
        """
        query = select(MeetingRecord).where(MeetingRecord.id == meeting_id)
        if lock:
            query = query.with_for_update().execution_options(populate_existing=True)
        return await self.session.scalar(query)

    async def meetings(self, pitch_ids: list[UUID]) -> list[MeetingRecord]:
        """List meetings of pitches, newest first.

        Args:
            pitch_ids (list[UUID]): Pitches.

        Returns:
            list[MeetingRecord]: Meetings.
        """
        query = select(MeetingRecord).where(MeetingRecord.pitch_id.in_(pitch_ids))
        return list(await self.session.scalars(query.order_by(MeetingRecord.created_at.desc())))

    async def outcomes(self, meeting_ids: list[UUID]) -> list[MeetingOutcomeRecord]:
        """List outcomes of meetings.

        Args:
            meeting_ids (list[UUID]): Meetings.

        Returns:
            list[MeetingOutcomeRecord]: Outcomes.
        """
        query = select(MeetingOutcomeRecord).where(MeetingOutcomeRecord.meeting_id.in_(meeting_ids))
        return list(await self.session.scalars(query.order_by(MeetingOutcomeRecord.created_at)))

    async def outcome(self, meeting_id: UUID, party_id: UUID) -> MeetingOutcomeRecord | None:
        """Find one party's outcome of a meeting.

        Args:
            meeting_id (UUID): The meeting.
            party_id (UUID): The party.

        Returns:
            MeetingOutcomeRecord | None: The outcome.
        """
        return await self.session.scalar(
            select(MeetingOutcomeRecord).where(
                MeetingOutcomeRecord.meeting_id == meeting_id, MeetingOutcomeRecord.party_id == party_id
            )
        )

    async def release(self, meeting_id: UUID) -> None:
        """Delete a meeting's bookings, freeing its time for both parties.

        Args:
            meeting_id (UUID): The meeting.
        """
        await self.session.execute(delete(BookingRecord).where(BookingRecord.meeting_id == meeting_id))

    async def calendar(self, account_id: UUID, *, lock: bool = False) -> CalendarConnectionRecord | None:
        """Read only the named account's current calendar generation."""
        query = select(CalendarConnectionRecord).where(CalendarConnectionRecord.account_id == account_id)
        if lock:
            query = query.with_for_update()
        return await self.session.scalar(query.execution_options(populate_existing=True))

    async def lock_calendar(self, account_id: UUID) -> CalendarConnectionRecord:
        """Create the account's initial generation if absent and serialize its mutations."""
        await self.session.execute(
            insert(CalendarConnectionRecord).values(account_id=account_id).on_conflict_do_nothing()
        )
        record = await self.calendar(account_id, lock=True)
        assert record is not None  # noqa: S101 - the row was inserted or already exists in this transaction
        return record

    async def erase_calendar(self, account_id: UUID) -> None:
        """Erase the account's calendar metadata and ciphertext with the profile transaction."""
        await self.session.execute(
            delete(CalendarConnectionRecord).where(CalendarConnectionRecord.account_id == account_id)
        )
