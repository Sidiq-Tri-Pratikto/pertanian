"""Pitches, their frozen submissions, shared file versions, decisions and itemized revision rounds."""

from datetime import date
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
    preflight_id: Mapped[UUID | None]
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


class PitchDecisionRecord(Row, Base):
    """One recipient decision on one submission and pitch version. The reason is shared with the requester only."""

    __tablename__ = "pitch_decisions"
    __table_args__ = (CheckConstraint("decision IN ('APPROVE', 'REJECT')", name="decision"),)

    pitch_id: Mapped[UUID] = mapped_column(ForeignKey("pitches.id", ondelete="CASCADE"), index=True)
    submission_number: Mapped[int]
    pitch_version: Mapped[int]
    decision: Mapped[str] = mapped_column(String(16))
    reason: Mapped[str | None] = mapped_column(String(500))
    decided_by_party_id: Mapped[UUID]
    decided_by_account_id: Mapped[UUID]


class RevisionRoundRecord(Row, Base):
    """One numbered round of itemized revision requests on one submission."""

    __tablename__ = "revision_rounds"
    __table_args__ = (UniqueConstraint("pitch_id", "number"),)

    pitch_id: Mapped[UUID] = mapped_column(ForeignKey("pitches.id", ondelete="CASCADE"), index=True)
    number: Mapped[int]
    submission_number: Mapped[int]
    requested_by_party_id: Mapped[UUID]
    requested_by_account_id: Mapped[UUID]


class RevisionItemRecord(MutableRow, Base):
    """One question of a round, with the recipient's review of its answer."""

    __tablename__ = "revision_items"
    __table_args__ = (
        UniqueConstraint("round_id", "position"),
        CheckConstraint("review IS NULL OR review IN ('ACCEPTED', 'NEEDS_DETAIL')", name="review"),
    )

    round_id: Mapped[UUID] = mapped_column(ForeignKey("revision_rounds.id", ondelete="CASCADE"), index=True)
    position: Mapped[int]
    category: Mapped[str] = mapped_column(String(60))
    question: Mapped[str] = mapped_column(String(1000))
    reason: Mapped[str] = mapped_column(String(1000))
    required: Mapped[bool]
    due_date: Mapped[date | None]
    expected_evidence: Mapped[str] = mapped_column(String(500), default="")
    review: Mapped[str | None] = mapped_column(String(16))
    review_note: Mapped[str | None] = mapped_column(String(1000))


class RevisionAnswerRecord(MutableRow, Base):
    """The requester's answer to one item: a draft with its own version until the round is resubmitted."""

    __tablename__ = "revision_answers"
    __table_args__ = (CheckConstraint("response IN ('CAN', 'DISCUSS', 'CANNOT')", name="response"),)

    item_id: Mapped[UUID] = mapped_column(ForeignKey("revision_items.id", ondelete="CASCADE"), unique=True)
    response: Mapped[str] = mapped_column(String(8))
    text: Mapped[str] = mapped_column(Text, default="")
    files: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    saved_by_account_id: Mapped[UUID]
