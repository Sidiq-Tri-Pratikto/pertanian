"""Funding data access. Writes join the caller's transaction."""

from typing import Any
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.funding.repository.sqlalchemy.models import (
    FundingInventionLinkRecord,
    FundingRequestRecord,
    FundingRequestVersionRecord,
    LegalEntityRecord,
)


class SqlAlchemyFundingRepository:
    """Legal entities and funding requests over one session."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind to a session.

        Args:
            session (AsyncSession): The request's session.
        """
        self.session = session

    async def add(self, record: Any) -> Any:
        """Insert a row.

        Args:
            record (Any): An ORM row.

        Returns:
            Any: The row with generated values.
        """
        self.session.add(record)
        await self.session.flush()
        return record

    async def entity(self, entity_id: UUID) -> LegalEntityRecord | None:
        """Find a legal entity.

        Args:
            entity_id (UUID): The entity.

        Returns:
            LegalEntityRecord | None: The entity.
        """
        return await self.session.get(LegalEntityRecord, entity_id)

    async def entities_of(self, party_id: UUID) -> list[LegalEntityRecord]:
        """List a party's legal entities.

        Args:
            party_id (UUID): The owner.

        Returns:
            list[LegalEntityRecord]: Entities, oldest first.
        """
        query = select(LegalEntityRecord).where(LegalEntityRecord.owner_party_id == party_id)
        return list(await self.session.scalars(query.order_by(LegalEntityRecord.created_at)))

    async def find(self, request_id: UUID, *, lock: bool = False) -> FundingRequestRecord | None:
        """Find a funding request.

        Args:
            request_id (UUID): The request.
            lock (bool, optional): Lock it for this transaction. Defaults to False.

        Returns:
            FundingRequestRecord | None: The request.
        """
        query = select(FundingRequestRecord).where(FundingRequestRecord.id == request_id)
        return await self.session.scalar(query.with_for_update() if lock else query)

    async def of_party(self, party_id: UUID) -> list[FundingRequestRecord]:
        """List a party's funding requests.

        Args:
            party_id (UUID): The owner.

        Returns:
            list[FundingRequestRecord]: Requests, newest first.
        """
        query = select(FundingRequestRecord).where(FundingRequestRecord.owner_party_id == party_id)
        return list(await self.session.scalars(query.order_by(FundingRequestRecord.created_at.desc())))

    async def links(self, request_id: UUID) -> list[FundingInventionLinkRecord]:
        """The request's current invention links.

        Args:
            request_id (UUID): The request.

        Returns:
            list[FundingInventionLinkRecord]: Links in the owner's order.
        """
        query = select(FundingInventionLinkRecord).where(FundingInventionLinkRecord.funding_request_id == request_id)
        return list(await self.session.scalars(query.order_by(FundingInventionLinkRecord.position)))

    async def linked_requests(self, invention_id: UUID) -> list[UUID]:
        """Find requests whose current projection may contain the invention."""
        links = FundingInventionLinkRecord
        statement = select(links.funding_request_id).where(links.invention_id == invention_id)
        return list(await self.session.scalars(statement.order_by(links.funding_request_id)))

    async def replace_links(self, request_id: UUID, links: list[tuple[UUID, UUID]]) -> None:
        """Replace the current links.

        Args:
            request_id (UUID): The request.
            links (list[tuple[UUID, UUID]]): Invention and version pairs, in order.
        """
        await self.session.execute(
            delete(FundingInventionLinkRecord).where(FundingInventionLinkRecord.funding_request_id == request_id)
        )
        for position, (invention_id, version_id) in enumerate(links):
            self.session.add(
                FundingInventionLinkRecord(
                    funding_request_id=request_id,
                    position=position,
                    invention_id=invention_id,
                    invention_version_id=version_id,
                )
            )
        await self.session.flush()

    async def snapshot(self, request_id: UUID, number: int, snapshot: dict[str, Any]) -> None:
        """Keep the request as it stands at this version.

        Args:
            request_id (UUID): The request.
            number (int): The version.
            snapshot (dict[str, Any]): The rendered request.
        """
        self.session.add(FundingRequestVersionRecord(funding_request_id=request_id, number=number, snapshot=snapshot))
        await self.session.flush()

    async def version_snapshot(self, request_id: UUID, number: int) -> dict[str, Any] | None:
        """Read the request as it stood at one version.

        Args:
            request_id (UUID): The request.
            number (int): The version.

        Returns:
            dict[str, Any] | None: The snapshot.
        """
        return await self.session.scalar(
            select(FundingRequestVersionRecord.snapshot).where(
                FundingRequestVersionRecord.funding_request_id == request_id,
                FundingRequestVersionRecord.number == number,
            )
        )
