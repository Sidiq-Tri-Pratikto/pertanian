"""Legal entities, company funding requests, their versions and invention links."""

from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, MutableRow, Row

MONEY = Numeric(20, 4)


class LegalEntityRecord(MutableRow, Base):
    """A company as its owner declared it; review is a separate status, never implied."""

    __tablename__ = "legal_entities"
    __table_args__ = (CheckConstraint("review_status IN ('declared', 'verified')", name="review_status"),)

    owner_party_id: Mapped[UUID] = mapped_column(ForeignKey("parties.id", ondelete="RESTRICT"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    jurisdiction: Mapped[str] = mapped_column(String(120), default="")
    registration_reference: Mapped[str] = mapped_column(String(120), default="")
    review_status: Mapped[str] = mapped_column(String(16), default="declared")


class FundingRequestRecord(MutableRow, Base):
    """One company raise. It owns its target; linked inventions never carry amounts."""

    __tablename__ = "funding_requests"
    __table_args__ = (
        CheckConstraint("subject_type IN ('EXISTING_ENTITY', 'PROPOSED_ENTITY')", name="subject_type"),
        CheckConstraint(
            "(subject_type = 'EXISTING_ENTITY') = (legal_entity_id IS NOT NULL)", name="entity_matches_subject"
        ),
        CheckConstraint("status IN ('DRAFT', 'ACTIVE', 'PAUSED', 'CLOSED')", name="status"),
        CheckConstraint("target_amount > 0", name="target_positive"),
        CheckConstraint("desired_min >= 0", name="desired_min_not_negative"),
        CheckConstraint("desired_max >= desired_min", name="desired_max_not_below_min"),
    )

    owner_party_id: Mapped[UUID] = mapped_column(ForeignKey("parties.id", ondelete="RESTRICT"), index=True)
    subject_type: Mapped[str] = mapped_column(String(16))
    legal_entity_id: Mapped[UUID | None] = mapped_column(ForeignKey("legal_entities.id", ondelete="RESTRICT"))
    proposed_name: Mapped[str] = mapped_column(String(200), default="")
    financing_stage: Mapped[str | None] = mapped_column(String(16))
    financing_form: Mapped[str | None] = mapped_column(String(24))
    currency: Mapped[str | None] = mapped_column(String(3))
    target_amount: Mapped[Decimal | None] = mapped_column(MONEY)
    desired_min: Mapped[Decimal | None] = mapped_column(MONEY)
    desired_max: Mapped[Decimal | None] = mapped_column(MONEY)
    accepts_partial: Mapped[bool] = mapped_column(default=False)
    accepts_syndicated: Mapped[bool] = mapped_column(default=False)
    intended_use: Mapped[str] = mapped_column(Text, default="")
    timing: Mapped[str] = mapped_column(String(200), default="")
    status: Mapped[str] = mapped_column(String(16), default="DRAFT")


class FundingRequestVersionRecord(Row, Base):
    """The request as it stood at one version; a sent pitch keeps pointing here."""

    __tablename__ = "funding_request_versions"
    __table_args__ = (UniqueConstraint("funding_request_id", "number"),)

    funding_request_id: Mapped[UUID] = mapped_column(ForeignKey("funding_requests.id", ondelete="CASCADE"), index=True)
    number: Mapped[int]
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB)


class FundingInventionLinkRecord(Row, Base):
    """One invention version the raise develops. Earlier link sets live in the version snapshots."""

    __tablename__ = "funding_invention_links"
    __table_args__ = (UniqueConstraint("funding_request_id", "invention_id"),)

    funding_request_id: Mapped[UUID] = mapped_column(ForeignKey("funding_requests.id", ondelete="CASCADE"), index=True)
    position: Mapped[int]
    invention_id: Mapped[UUID] = mapped_column(ForeignKey("inventions.id", ondelete="RESTRICT"))
    invention_version_id: Mapped[UUID] = mapped_column(ForeignKey("invention_versions.id", ondelete="RESTRICT"))
