"""Investor quick subscriptions, their one-time links, what each received, and request counts (spec 046)."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, MutableRow, Row


class InvestorSubscriptionRecord(MutableRow, Base):
    """An email and its topics. It is not an account and can see only what is already public."""

    __tablename__ = "investor_subscriptions"
    __table_args__ = (CheckConstraint("status IN ('PENDING', 'ACTIVE', 'UNSUBSCRIBED')", name="status"),)

    email: Mapped[str] = mapped_column(String(320), unique=True)
    topics: Mapped[dict[str, Any]] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(16), default="PENDING")
    locale: Mapped[str] = mapped_column(String(8), default="id")
    consent_source: Mapped[str] = mapped_column(String(32), default="quick_signup")
    confirmed_at: Mapped[datetime | None]
    unsubscribed_at: Mapped[datetime | None]


class SubscriptionLinkRecord(Row, Base):
    """A one-time confirmation link or a manage link, stored only as a hash."""

    __tablename__ = "subscription_links"
    __table_args__ = (CheckConstraint("purpose IN ('confirm', 'manage')", name="purpose"),)

    subscription_id: Mapped[UUID] = mapped_column(
        ForeignKey("investor_subscriptions.id", ondelete="CASCADE"), index=True
    )
    purpose: Mapped[str] = mapped_column(String(8))
    token_sha256: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime]
    used_at: Mapped[datetime | None]


class SubscriptionDeliveryRecord(Row, Base):
    """One invention sent to one subscriber; never twice (FR-004)."""

    __tablename__ = "subscription_deliveries"
    __table_args__ = (
        UniqueConstraint("subscription_id", "invention_id"),
        CheckConstraint("kind IN ('ALERT', 'DIGEST')", name="kind"),
        Index("ix_subscription_deliveries_alerts", "subscription_id", "kind", "created_at"),
    )

    subscription_id: Mapped[UUID] = mapped_column(ForeignKey("investor_subscriptions.id", ondelete="CASCADE"))
    invention_id: Mapped[UUID] = mapped_column(ForeignKey("inventions.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(8))


class SubscriptionRequestRecord(Row, Base):
    """One subscription request, counted per email and per client address for rate limits."""

    __tablename__ = "subscription_requests"
    __table_args__ = (
        Index("ix_subscription_requests_email", "email_sha256", "created_at"),
        Index("ix_subscription_requests_address", "address_sha256", "created_at"),
    )

    email_sha256: Mapped[str] = mapped_column(String(64))
    address_sha256: Mapped[str] = mapped_column(String(64))
