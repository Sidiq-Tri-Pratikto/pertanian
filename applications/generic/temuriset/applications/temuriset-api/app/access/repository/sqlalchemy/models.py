"""Parties, organizations, memberships and invitations."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, MutableRow, Row


class OrganizationRecord(MutableRow, Base):
    """A company, nonprofit, community or research group that people act for."""

    __tablename__ = "organizations"
    __table_args__ = (
        CheckConstraint("kind IN ('company', 'nonprofit', 'community', 'research_group', 'other')", name="kind"),
    )

    name: Mapped[str] = mapped_column(String(160))
    kind: Mapped[str] = mapped_column(String(32))


class PartyRecord(MutableRow, Base):
    """Exactly one of: a personal party (one per account) or an organization party."""

    __tablename__ = "parties"
    __table_args__ = (
        CheckConstraint(
            "(kind = 'personal' AND account_id IS NOT NULL AND organization_id IS NULL) OR "
            "(kind = 'organization' AND organization_id IS NOT NULL AND account_id IS NULL)",
            name="kind",
        ),
    )

    kind: Mapped[str] = mapped_column(String(16))
    display_name: Mapped[str] = mapped_column(String(160))
    account_id: Mapped[UUID | None] = mapped_column(ForeignKey("accounts.id", ondelete="RESTRICT"), unique=True)
    organization_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT"), unique=True
    )
    # The public profile (031): nothing shows until the party publishes it deliberately.
    bio: Mapped[str] = mapped_column(Text, default="", server_default="")
    profile_published: Mapped[bool] = mapped_column(default=False, server_default="false")


class MembershipRecord(MutableRow, Base):
    """An account's capabilities inside an organization. Removal keeps the row for history."""

    __tablename__ = "memberships"
    __table_args__ = (
        CheckConstraint("status IN ('active', 'removed')", name="status"),
        Index(
            "uq_memberships_active",
            "organization_id",
            "account_id",
            unique=True,
            postgresql_where="status = 'active'",
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"))
    account_id: Mapped[UUID] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"), index=True)
    capabilities: Mapped[list[str]] = mapped_column(ARRAY(String(32)))
    status: Mapped[str] = mapped_column(String(16), default="active")
    revoked_at: Mapped[datetime | None]


class InvitationRecord(Row, Base):
    """An emailed invitation. Only the token's SHA-256 is stored."""

    __tablename__ = "invitations"

    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True)
    email: Mapped[str] = mapped_column(String(254))
    capabilities: Mapped[list[str]] = mapped_column(ARRAY(String(32)))
    token_sha256: Mapped[str] = mapped_column(String(64), unique=True)
    invited_by_account_id: Mapped[UUID] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"))
    expires_at: Mapped[datetime]
    revoked_at: Mapped[datetime | None]
    accepted_at: Mapped[datetime | None]
