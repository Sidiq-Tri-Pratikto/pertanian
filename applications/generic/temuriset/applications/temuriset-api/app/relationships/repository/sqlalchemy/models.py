"""Relationships: versions confirmed by checksum, per-party consent, append-only restrictions (030)."""

from typing import Any
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, MutableRow, Row

VERSION_STATUSES = ("PENDING_COUNTERPARTY", "CONFIRMED", "CHANGES_REQUESTED", "DECLINED")


class PartnershipRecord(MutableRow, Base):
    """One relationship that grew out of one pitch."""

    __tablename__ = "partnerships"
    __table_args__ = (CheckConstraint("type IN ('PROJECT', 'LICENSE', 'EQUITY')", name="type"),)

    pitch_id: Mapped[UUID] = mapped_column(ForeignKey("pitches.id", ondelete="CASCADE"), unique=True)
    type: Mapped[str] = mapped_column(String(16))
    requester_party_id: Mapped[UUID] = mapped_column(index=True)
    recipient_party_id: Mapped[UUID] = mapped_column(index=True)
    invention_ids: Mapped[list[str]] = mapped_column(JSONB, default=list)
    contested: Mapped[bool] = mapped_column(default=False)


class PartnershipVersionRecord(Row, Base):
    """One proposed summary; its checksum is what each party confirms."""

    __tablename__ = "partnership_versions"
    __table_args__ = (
        UniqueConstraint("partnership_id", "number"),
        CheckConstraint(f"status IN {VERSION_STATUSES}", name="status"),
    )

    partnership_id: Mapped[UUID] = mapped_column(ForeignKey("partnerships.id", ondelete="CASCADE"), index=True)
    number: Mapped[int]
    values: Mapped[dict[str, Any]] = mapped_column(JSONB)
    ceiling: Mapped[list[str]] = mapped_column(JSONB)
    checksum: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(24), default="PENDING_COUNTERPARTY")
    proposed_by_party_id: Mapped[UUID]
    note: Mapped[str] = mapped_column(String(1000), default="")


class PartnershipConfirmationRecord(Row, Base):
    """One party confirming one version's checksum, with the fields it allows in public."""

    __tablename__ = "partnership_confirmations"
    __table_args__ = (UniqueConstraint("version_id", "party_id"),)

    version_id: Mapped[UUID] = mapped_column(ForeignKey("partnership_versions.id", ondelete="CASCADE"), index=True)
    party_id: Mapped[UUID]
    subset: Mapped[list[str]] = mapped_column(JSONB)
    checksum: Mapped[str] = mapped_column(String(64))
    confirmed_by_account_id: Mapped[UUID]


class PartnershipRestrictionRecord(Row, Base):
    """An append-only narrowing of one public field by one party, applied on the next read."""

    __tablename__ = "partnership_restrictions"

    partnership_id: Mapped[UUID] = mapped_column(ForeignKey("partnerships.id", ondelete="CASCADE"), index=True)
    field: Mapped[str] = mapped_column(String(16))
    party_id: Mapped[UUID]
    restricted_by_account_id: Mapped[UUID]
