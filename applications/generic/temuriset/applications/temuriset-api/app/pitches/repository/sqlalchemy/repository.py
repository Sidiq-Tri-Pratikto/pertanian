"""Pitch storage."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.pitches.repository.sqlalchemy.models import (
    PitchDecisionRecord,
    PitchRecord,
    PitchSubmissionFileRecord,
    PitchSubmissionRecord,
    RevisionAnswerRecord,
    RevisionItemRecord,
    RevisionRoundRecord,
)


class SqlAlchemyPitchRepository:
    """Writes and reads pitches and submissions."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind to the session.

        Args:
            session (AsyncSession): The request's session.
        """
        self.session = session

    async def add[RecordT](self, record: RecordT) -> RecordT:
        """Insert a record.

        Args:
            record (RecordT): A pitch, submission, file, decision, round, item or answer.

        Returns:
            RecordT: The stored record.
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

    async def find(self, pitch_id: UUID, *, lock: bool = False, share: bool = False) -> PitchRecord | None:
        """Find a pitch.

        Args:
            pitch_id (UUID): The pitch.
            lock (bool, optional): Lock it for a status change. Defaults to False.
            share (bool, optional): Hold it against a status change while answers are saved. Defaults to False.

        Returns:
            PitchRecord | None: The pitch.
        """
        query = select(PitchRecord).where(PitchRecord.id == pitch_id)
        if lock:
            query = query.with_for_update()
        elif share:
            query = query.with_for_update(read=True)
        return await self.session.scalar(query.execution_options(populate_existing=lock or share))

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

    async def last_submission(self, pitch_id: UUID) -> PitchSubmissionRecord | None:
        """Return the newest submission.

        Args:
            pitch_id (UUID): The pitch.

        Returns:
            PitchSubmissionRecord | None: The submission.
        """
        return await self.session.scalar(
            select(PitchSubmissionRecord)
            .where(PitchSubmissionRecord.pitch_id == pitch_id)
            .order_by(PitchSubmissionRecord.number.desc())
            .limit(1)
        )

    async def decisions(self, pitch_id: UUID) -> list[PitchDecisionRecord]:
        """Read a pitch's decisions in order.

        Args:
            pitch_id (UUID): The pitch.

        Returns:
            list[PitchDecisionRecord]: Decisions.
        """
        query = select(PitchDecisionRecord).where(PitchDecisionRecord.pitch_id == pitch_id)
        return list(await self.session.scalars(query.order_by(PitchDecisionRecord.created_at)))

    async def rounds(
        self, pitch_id: UUID
    ) -> list[tuple[RevisionRoundRecord, list[tuple[RevisionItemRecord, RevisionAnswerRecord | None]]]]:
        """Read a pitch's rounds in order, each with its items and their answers.

        Args:
            pitch_id (UUID): The pitch.

        Returns:
            list[tuple[RevisionRoundRecord, list[tuple[RevisionItemRecord, RevisionAnswerRecord | None]]]]: Rounds.
        """
        rounds = list(
            await self.session.scalars(
                select(RevisionRoundRecord)
                .where(RevisionRoundRecord.pitch_id == pitch_id)
                .order_by(RevisionRoundRecord.number)
            )
        )
        rows = (
            await self.session.execute(
                select(RevisionItemRecord, RevisionAnswerRecord)
                .outerjoin(RevisionAnswerRecord, RevisionAnswerRecord.item_id == RevisionItemRecord.id)
                .where(RevisionItemRecord.round_id.in_([item.id for item in rounds]))
                .order_by(RevisionItemRecord.position)
            )
        ).all()
        return [(item, [(row[0], row[1]) for row in rows if row[0].round_id == item.id]) for item in rounds]

    async def item(self, item_id: UUID, *, lock: bool = False) -> tuple[RevisionItemRecord, RevisionRoundRecord] | None:
        """Find an item with its round.

        Args:
            item_id (UUID): The item.
            lock (bool, optional): Lock the item. Defaults to False.

        Returns:
            tuple[RevisionItemRecord, RevisionRoundRecord] | None: The item and round.
        """
        query = (
            select(RevisionItemRecord, RevisionRoundRecord)
            .join(RevisionRoundRecord, RevisionRoundRecord.id == RevisionItemRecord.round_id)
            .where(RevisionItemRecord.id == item_id)
        )
        if lock:
            query = query.with_for_update(of=RevisionItemRecord).execution_options(populate_existing=True)
        row = (await self.session.execute(query)).first()
        return (row[0], row[1]) if row else None

    async def answer(self, item_id: UUID) -> RevisionAnswerRecord | None:
        """Find an item's answer, locked for a save.

        Args:
            item_id (UUID): The item.

        Returns:
            RevisionAnswerRecord | None: The answer.
        """
        return await self.session.scalar(
            select(RevisionAnswerRecord)
            .where(RevisionAnswerRecord.item_id == item_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
