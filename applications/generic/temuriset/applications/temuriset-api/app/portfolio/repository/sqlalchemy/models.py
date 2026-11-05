"""Inventions, their versions, facts and claims."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, MutableRow, Row


class InventionRecord(MutableRow, Base):
    """One invention managed by one party, with a published pointer and at most one draft."""

    __tablename__ = "inventions"
    __table_args__ = (CheckConstraint("status IN ('DRAFT', 'PENDING_REVIEW', 'PUBLISHED', 'ARCHIVED')", name="status"),)

    managing_party_id: Mapped[UUID] = mapped_column(ForeignKey("parties.id", ondelete="RESTRICT"), index=True)
    status: Mapped[str] = mapped_column(String(16), default="DRAFT")
    published_version_id: Mapped[UUID | None]
    draft_version_id: Mapped[UUID | None]


class InventionVersionRecord(MutableRow, Base):
    """One numbered version. Once published it never changes; an edit starts a draft successor."""

    __tablename__ = "invention_versions"
    __table_args__ = (
        UniqueConstraint("invention_id", "number"),
        CheckConstraint("state IN ('draft', 'published', 'superseded')", name="state"),
    )

    invention_id: Mapped[UUID] = mapped_column(ForeignKey("inventions.id", ondelete="CASCADE"), index=True)
    number: Mapped[int]
    state: Mapped[str] = mapped_column(String(16), default="draft")
    title: Mapped[str] = mapped_column(String(200), default="")
    summary: Mapped[str] = mapped_column(Text, default="")
    problem: Mapped[str] = mapped_column(Text, default="")
    solution: Mapped[str] = mapped_column(Text, default="")
    intended_users: Mapped[str] = mapped_column(Text, default="")
    sector: Mapped[str] = mapped_column(String(80), default="")
    stage: Mapped[str | None] = mapped_column(String(16))
    keywords: Mapped[list[str]] = mapped_column(ARRAY(String(40)), default=list)
    # Never part of the public projection.
    private_notes: Mapped[str] = mapped_column(Text, default="")
    published_at: Mapped[datetime | None]


class InventionFactRecord(Row, Base):
    """A statement about the invention: what exists now or is planned, and who says so."""

    __tablename__ = "invention_facts"
    __table_args__ = (
        CheckConstraint("timing IN ('CURRENT', 'PLANNED', 'REQUESTED')", name="timing"),
        CheckConstraint(
            "provenance IN ('SOURCE_REPORTED', 'SELF_DECLARED', 'PROVIDED', 'REVIEWED', 'UNKNOWN')", name="provenance"
        ),
    )

    version_id: Mapped[UUID] = mapped_column(ForeignKey("invention_versions.id", ondelete="CASCADE"), index=True)
    position: Mapped[int]
    label: Mapped[str] = mapped_column(String(120))
    value: Mapped[str] = mapped_column(String(200))
    unit: Mapped[str] = mapped_column(String(40), default="")
    timing: Mapped[str] = mapped_column(String(16))
    provenance: Mapped[str] = mapped_column(String(16))
    key: Mapped[str | None] = mapped_column(String(64))
    document_version_id: Mapped[UUID | None]


class InventionClaimRecord(Row, Base):
    """Creator, contributor, manager, rights holder or authority: an assertion, never a certificate."""

    __tablename__ = "invention_claims"
    __table_args__ = (
        CheckConstraint("kind IN ('creator', 'contributor', 'manager', 'rights_holder', 'authority')", name="kind"),
        CheckConstraint("status IN ('asserted', 'not_established', 'reviewed')", name="status"),
    )

    version_id: Mapped[UUID] = mapped_column(ForeignKey("invention_versions.id", ondelete="CASCADE"), index=True)
    position: Mapped[int]
    kind: Mapped[str] = mapped_column(String(16))
    subject_name: Mapped[str] = mapped_column(String(160))
    party_id: Mapped[UUID | None]
    scope: Mapped[str] = mapped_column(String(200), default="")
    status: Mapped[str] = mapped_column(String(16))
    source: Mapped[str] = mapped_column(String(200), default="")
    asserted_at: Mapped[datetime | None]
