"""Accounts, email codes, sessions and the development mailbox."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, false
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, MutableRow, Row


class AccountRecord(MutableRow, Base):
    """A person who signs in with a verified email. Emails are stored trimmed and lower-case."""

    __tablename__ = "accounts"
    __table_args__ = (
        CheckConstraint("persona IN ('inovator', 'mitra')", name="persona"),
        CheckConstraint("kind IN ('user', 'demo')", name="kind"),
        CheckConstraint("status IN ('active', 'suspended')", name="status"),
    )

    email: Mapped[str] = mapped_column(String(254), unique=True)
    email_verified_at: Mapped[datetime | None]
    display_name: Mapped[str] = mapped_column(String(80))
    locale: Mapped[str] = mapped_column(String(8))
    time_zone: Mapped[str] = mapped_column(String(64))
    persona: Mapped[str] = mapped_column(String(16))
    kind: Mapped[str] = mapped_column(String(8), default="user")
    status: Mapped[str] = mapped_column(String(16), default="active")
    email_notifications: Mapped[bool] = mapped_column(default=False, server_default=false())


class EmailCodeRecord(Row, Base):
    """One emailed six-digit code, stored salted and hashed."""

    __tablename__ = "email_codes"
    __table_args__ = (
        Index("ix_email_codes_email_created", "email", "created_at"),
        Index("ix_email_codes_address_created", "requester_address_sha256", "created_at"),
        CheckConstraint("purpose IN ('sign_up', 'sign_in')", name="purpose"),
    )

    email: Mapped[str] = mapped_column(String(254))
    purpose: Mapped[str] = mapped_column(String(16))
    code_sha256: Mapped[str] = mapped_column(String(64))
    salt: Mapped[str] = mapped_column(String(32))
    # Name, locale, time zone and persona typed at sign-up, applied only when the code is verified.
    profile: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    requester_address_sha256: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime]
    attempts: Mapped[int] = mapped_column(default=0, server_default="0")
    consumed_at: Mapped[datetime | None]


class SessionRecord(Row, Base):
    """A signed-in browser. Only the token's SHA-256 is stored."""

    __tablename__ = "sessions"

    account_id: Mapped[UUID] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"), index=True)
    token_sha256: Mapped[str] = mapped_column(String(64), unique=True)
    active_party_id: Mapped[UUID]
    expires_at: Mapped[datetime]
    revoked_at: Mapped[datetime | None]
    last_seen_at: Mapped[datetime]


class MailboxMessageRecord(Row, Base):
    """Development and test mailbox until real email delivery (spec 042)."""

    __tablename__ = "mailbox_messages"
    __table_args__ = (Index("ix_mailbox_messages_to_email", "to_email", "created_at"),)

    to_email: Mapped[str] = mapped_column(String(254))
    subject: Mapped[str] = mapped_column(String(200))
    body: Mapped[str]
