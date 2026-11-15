"""Subscription storage."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.subscriptions.repository.sqlalchemy.models import (
    InvestorSubscriptionRecord,
    SubscriptionDeliveryRecord,
    SubscriptionLinkRecord,
    SubscriptionRequestRecord,
)


class SqlAlchemySubscriptionRepository:
    """Writes and reads subscriptions, links, deliveries and request counts."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind to the session.

        Args:
            session (AsyncSession): The request's session.
        """
        self.session = session

    async def add[RecordT](self, record: RecordT) -> RecordT:
        """Insert a record.

        Args:
            record (RecordT): Any subscription record.

        Returns:
            RecordT: The stored record.
        """
        self.session.add(record)
        await self.session.flush()
        return record

    async def by_email(self, email: str) -> InvestorSubscriptionRecord | None:
        """Find a subscription by email, locked for a change.

        Args:
            email (str): Lower-cased email.

        Returns:
            InvestorSubscriptionRecord | None: The subscription.
        """
        query = select(InvestorSubscriptionRecord).where(InvestorSubscriptionRecord.email == email).with_for_update()
        return await self.session.scalar(query.execution_options(populate_existing=True))

    async def find(self, subscription_id: UUID) -> InvestorSubscriptionRecord | None:
        """Find a subscription.

        Args:
            subscription_id (UUID): The subscription.

        Returns:
            InvestorSubscriptionRecord | None: The subscription.
        """
        return await self.session.get(InvestorSubscriptionRecord, subscription_id)

    async def link(self, token_sha256: str) -> SubscriptionLinkRecord | None:
        """Find a link by its token hash, locked.

        Args:
            token_sha256 (str): The hash.

        Returns:
            SubscriptionLinkRecord | None: The link.
        """
        query = select(SubscriptionLinkRecord).where(SubscriptionLinkRecord.token_sha256 == token_sha256)
        return await self.session.scalar(query.with_for_update().execution_options(populate_existing=True))

    async def requests_since(
        self, *, email_sha256: str | None = None, address_sha256: str | None = None, since: datetime
    ) -> list[datetime]:
        """Times of subscription requests since a moment, by email or by address, oldest first.

        Args:
            email_sha256 (str | None, optional): Hashed email. Defaults to None.
            address_sha256 (str | None, optional): Hashed client address. Defaults to None.
            since (datetime): Window start.

        Returns:
            list[datetime]: Request times.
        """
        query = select(SubscriptionRequestRecord.created_at).where(SubscriptionRequestRecord.created_at >= since)
        if email_sha256 is not None:
            query = query.where(SubscriptionRequestRecord.email_sha256 == email_sha256)
        if address_sha256 is not None:
            query = query.where(SubscriptionRequestRecord.address_sha256 == address_sha256)
        return list(await self.session.scalars(query.order_by(SubscriptionRequestRecord.created_at)))

    async def active(self) -> list[InvestorSubscriptionRecord]:
        """List active subscriptions, oldest first.

        Returns:
            list[InvestorSubscriptionRecord]: Subscriptions.
        """
        query = select(InvestorSubscriptionRecord).where(InvestorSubscriptionRecord.status == "ACTIVE")
        return list(await self.session.scalars(query.order_by(InvestorSubscriptionRecord.created_at)))

    async def delivered(self, subscription_id: UUID) -> set[UUID]:
        """Inventions already sent to a subscriber.

        Args:
            subscription_id (UUID): The subscription.

        Returns:
            set[UUID]: Invention ids.
        """
        query = select(SubscriptionDeliveryRecord.invention_id).where(
            SubscriptionDeliveryRecord.subscription_id == subscription_id
        )
        return set(await self.session.scalars(query))

    async def alerts_since(self, subscription_id: UUID, since: datetime) -> int:
        """Count direct alerts sent to a subscriber since a moment.

        Args:
            subscription_id (UUID): The subscription.
            since (datetime): Window start.

        Returns:
            int: The count.
        """
        query = select(func.count()).where(
            SubscriptionDeliveryRecord.subscription_id == subscription_id,
            SubscriptionDeliveryRecord.kind == "ALERT",
            SubscriptionDeliveryRecord.created_at >= since,
        )
        return await self.session.scalar(query) or 0

    async def record_delivery(self, subscription_id: UUID, invention_id: UUID, kind: str, at: datetime) -> bool:
        """Record that an invention goes to a subscriber, unless it already went.

        Args:
            subscription_id (UUID): The subscription.
            invention_id (UUID): The invention.
            kind (str): ``ALERT`` or ``DIGEST``.
            at (datetime): Product time.

        Returns:
            bool: Whether this call recorded it, so only one sender sends.
        """
        statement = (
            insert(SubscriptionDeliveryRecord)
            .values(subscription_id=subscription_id, invention_id=invention_id, kind=kind, created_at=at)
            .on_conflict_do_nothing(index_elements=["subscription_id", "invention_id"])
        )
        return bool((await self.session.execute(statement)).rowcount)  # type: ignore[attr-defined]
