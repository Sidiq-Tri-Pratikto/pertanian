"""Pitch storage."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.pitches.repository.sqlalchemy.models import PitchRecord, PitchSubmissionFileRecord, PitchSubmissionRecord


class SqlAlchemyPitchRepository:
    """Writes and reads pitches and submissions."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind to the session.

        Args:
            session (AsyncSession): The request's session.
        """
        self.session = session

    async def add(
        self, record: PitchRecord | PitchSubmissionRecord | PitchSubmissionFileRecord
    ) -> PitchRecord | PitchSubmissionRecord | PitchSubmissionFileRecord:
        """Insert a record.

        Args:
            record (PitchRecord | PitchSubmissionRecord | PitchSubmissionFileRecord): The record.

        Returns:
            PitchRecord | PitchSubmissionRecord | PitchSubmissionFileRecord: The stored record.
        """
        self.session.add(record)
        await self.session.flush()
        return record

    async def active(
        self, subject_type: str, subject_id: UUID, recipient_party_id: UUID, opportunity_id: UUID
    ) -> PitchRecord | None:
        """Find the active pitch of a source to a target, whatever its purpose.

        Args:
            subject_type (str): Source type.
            subject_id (UUID): Source.
            recipient_party_id (UUID): Recipient.
            opportunity_id (UUID): Opportunity.

        Returns:
            PitchRecord | None: The pitch.
        """
        return await self.session.scalar(
            select(PitchRecord).where(
                PitchRecord.subject_type == subject_type,
                PitchRecord.subject_id == subject_id,
                PitchRecord.recipient_party_id == recipient_party_id,
                PitchRecord.opportunity_id == opportunity_id,
                PitchRecord.active,
            )
        )

    async def created_since(self, requester_party_id: UUID, since: datetime) -> int:
        """Count pitches a party started since a time.

        Args:
            requester_party_id (UUID): The requester.
            since (datetime): Window start.

        Returns:
            int: The count.
        """
        query = select(func.count()).where(
            PitchRecord.requester_party_id == requester_party_id, PitchRecord.created_at >= since
        )
        return await self.session.scalar(query) or 0

    async def oldest_since(self, requester_party_id: UUID, since: datetime) -> datetime | None:
        """Return when the oldest pitch in the window was started.

        Args:
            requester_party_id (UUID): The requester.
            since (datetime): Window start.

        Returns:
            datetime | None: The time.
        """
        query = select(func.min(PitchRecord.created_at)).where(
            PitchRecord.requester_party_id == requester_party_id, PitchRecord.created_at >= since
        )
        return await self.session.scalar(query)

    async def find(self, pitch_id: UUID) -> PitchRecord | None:
        """Find a pitch.

        Args:
            pitch_id (UUID): The pitch.

        Returns:
            PitchRecord | None: The pitch.
        """
        return await self.session.get(PitchRecord, pitch_id)

    async def of_party(self, party_id: UUID, *, incoming: bool, limit: int) -> list[PitchRecord]:
        """List a party's outgoing or incoming pitches, newest first.

        Args:
            party_id (UUID): The party.
            incoming (bool): Received rather than sent.
            limit (int): The most to return.

        Returns:
            list[PitchRecord]: Pitches.
        """
        column = PitchRecord.recipient_party_id if incoming else PitchRecord.requester_party_id
        query = select(PitchRecord).where(column == party_id).order_by(PitchRecord.created_at.desc()).limit(limit)
        return list(await self.session.scalars(query))

    async def submissions(self, pitch_id: UUID) -> list[tuple[PitchSubmissionRecord, list[PitchSubmissionFileRecord]]]:
        """Read a pitch's submissions in order, each with its files.

        Args:
            pitch_id (UUID): The pitch.

        Returns:
            list[tuple[PitchSubmissionRecord, list[PitchSubmissionFileRecord]]]: Submissions and files.
        """
        submissions = list(
            await self.session.scalars(
                select(PitchSubmissionRecord)
                .where(PitchSubmissionRecord.pitch_id == pitch_id)
                .order_by(PitchSubmissionRecord.number)
            )
        )
        result = []
        for submission in submissions:
            files = await self.session.scalars(
                select(PitchSubmissionFileRecord).where(PitchSubmissionFileRecord.submission_id == submission.id)
            )
            result.append((submission, list(files)))
        return result
