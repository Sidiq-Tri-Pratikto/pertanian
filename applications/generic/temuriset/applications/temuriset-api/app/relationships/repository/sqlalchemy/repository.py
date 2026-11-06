"""Relationship storage."""

from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.relationships.repository.sqlalchemy.models import (
    PartnershipConfirmationRecord,
    PartnershipRecord,
    PartnershipRestrictionRecord,
    PartnershipVersionRecord,
)


class SqlAlchemyRelationshipRepository:
    """Writes and reads partnerships, versions, confirmations and restrictions."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind to the session.

        Args:
            session (AsyncSession): The request's session.
        """
        self.session = session

    async def add[RecordT](self, record: RecordT) -> RecordT:
        """Insert a record.

        Args:
            record (RecordT): Any relationship record.

        Returns:
            RecordT: The stored record.
        """
        self.session.add(record)
        await self.session.flush()
        return record

    async def find(self, partnership_id: UUID, *, lock: bool = False) -> PartnershipRecord | None:
        """Find a partnership.

        Args:
            partnership_id (UUID): The partnership.
            lock (bool, optional): Lock it for a change. Defaults to False.

        Returns:
            PartnershipRecord | None: The partnership.
        """
        query = select(PartnershipRecord).where(PartnershipRecord.id == partnership_id)
        if lock:
            query = query.with_for_update().execution_options(populate_existing=True)
        return await self.session.scalar(query)

    async def of_pitches(self, pitch_ids: list[UUID]) -> list[PartnershipRecord]:
        """List the partnerships of pitches.

        Args:
            pitch_ids (list[UUID]): Pitches.

        Returns:
            list[PartnershipRecord]: Partnerships.
        """
        return list(
            await self.session.scalars(select(PartnershipRecord).where(PartnershipRecord.pitch_id.in_(pitch_ids)))
        )

    async def of_party(self, party_id: UUID) -> list[PartnershipRecord]:
        """List a party's partnerships, oldest first.

        Args:
            party_id (UUID): The party.

        Returns:
            list[PartnershipRecord]: Partnerships.
        """
        query = select(PartnershipRecord).where(
            or_(PartnershipRecord.requester_party_id == party_id, PartnershipRecord.recipient_party_id == party_id)
        )
        return list(await self.session.scalars(query.order_by(PartnershipRecord.created_at)))

    async def versions(self, partnership_ids: list[UUID]) -> list[PartnershipVersionRecord]:
        """List versions of partnerships, in number order.

        Args:
            partnership_ids (list[UUID]): Partnerships.

        Returns:
            list[PartnershipVersionRecord]: Versions.
        """
        query = select(PartnershipVersionRecord).where(PartnershipVersionRecord.partnership_id.in_(partnership_ids))
        return list(await self.session.scalars(query.order_by(PartnershipVersionRecord.number)))

    async def confirmations(self, version_ids: list[UUID]) -> list[PartnershipConfirmationRecord]:
        """List confirmations of versions.

        Args:
            version_ids (list[UUID]): Versions.

        Returns:
            list[PartnershipConfirmationRecord]: Confirmations.
        """
        query = select(PartnershipConfirmationRecord).where(PartnershipConfirmationRecord.version_id.in_(version_ids))
        return list(await self.session.scalars(query.order_by(PartnershipConfirmationRecord.created_at)))

    async def restrictions(self, partnership_ids: list[UUID]) -> list[PartnershipRestrictionRecord]:
        """List restrictions of partnerships, oldest first.

        Args:
            partnership_ids (list[UUID]): Partnerships.

        Returns:
            list[PartnershipRestrictionRecord]: Restrictions.
        """
        query = select(PartnershipRestrictionRecord).where(
            PartnershipRestrictionRecord.partnership_id.in_(partnership_ids)
        )
        return list(await self.session.scalars(query.order_by(PartnershipRestrictionRecord.created_at)))
