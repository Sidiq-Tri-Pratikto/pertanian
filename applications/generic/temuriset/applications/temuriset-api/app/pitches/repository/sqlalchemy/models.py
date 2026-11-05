"""Pitches, their frozen submissions and the file versions each submission shared."""

from typing import Any
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, MutableRow, Row

PITCH_STATUSES = (
    "DRAFT",
    "PENDING_WORKSPACE_REVIEW",
    "SUBMITTED",
    "UNDER_REVIEW",
    "REVISION_REQUESTED",
    "APPROVED_FOR_DISCUSSION",
    "REJECTED",
    "WITHDRAWN",
    "CLOSED",
)


class PitchRecord(MutableRow, Base):
    """One source pitched to one opportunity. At most one active pitch per source, recipient, target and purpose."""

    __tablename__ = "pitches"
    __table_args__ = (
        CheckConstraint(f"status IN {PITCH_STATUSES}", name="status"),
        CheckConstraint("subject_type IN ('SUPPORT_REQUEST', 'FUNDING_REQUEST')", name="subject_type"),
        Index(
            "uq_pitches_active",
            "subject_type",
            "subject_id",
            "recipient_party_id",
            "opportunity_id",
            "purpose",
            unique=True,
            postgresql_where=text("active"),
        ),
    )

    requester_party_id: Mapped[UUID] = mapped_column(ForeignKey("parties.id", ondelete="RESTRICT"), index=True)
    recipient_party_id: Mapped[UUID] = mapped_column(ForeignKey("parties.id", ondelete="RESTRICT"), index=True)
    opportunity_id: Mapped[UUID]
    opportunity_version_id: Mapped[UUID]
    opportunity_title: Mapped[str] = mapped_column(String(200), default="")
    subject_type: Mapped[str] = mapped_column(String(16))
    subject_id: Mapped[UUID]
    subject_title: Mapped[str] = mapped_column(String(200), default="")
    purpose: Mapped[str] = mapped_column(String(16), default="")
    status: Mapped[str] = mapped_column(String(32), default="SUBMITTED")
    active: Mapped[bool] = mapped_column(default=True)


class PitchSubmissionRecord(Row, Base):
    """What was sent, frozen: references plus the facts shown, never document bytes (FR-004)."""

    __tablename__ = "pitch_submissions"
    __table_args__ = (UniqueConstraint("pitch_id", "number"),)

    pitch_id: Mapped[UUID] = mapped_column(ForeignKey("pitches.id", ondelete="CASCADE"), index=True)
    number: Mapped[int]
    preflight_id: Mapped[UUID]
    brief: Mapped[str] = mapped_column(Text)
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB)
    submitted_by_account_id: Mapped[UUID]


class PitchSubmissionFileRecord(Row, Base):
    """One document version a submission shared, with the grant made for it."""

    __tablename__ = "pitch_submission_files"

    submission_id: Mapped[UUID] = mapped_column(ForeignKey("pitch_submissions.id", ondelete="CASCADE"), index=True)
    document_id: Mapped[UUID]
    document_version_id: Mapped[UUID]
    version: Mapped[int]
    title: Mapped[str] = mapped_column(String(200), default="")
    grant_id: Mapped[UUID]
