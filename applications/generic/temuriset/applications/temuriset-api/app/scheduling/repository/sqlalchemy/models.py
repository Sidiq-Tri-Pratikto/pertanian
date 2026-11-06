"""Schedule proposals and slots, meetings, per-party bookings and meeting outcomes (spec 028)."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import TSTZRANGE, ExcludeConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, MutableRow, Row

PROPOSAL_STATES = ("OPEN", "ACCEPTED", "SUPERSEDED", "EXPIRED", "CANCELLED")
MEETING_STATES = ("CONFIRMED", "COMPLETED", "CANCELLED", "NO_SHOW_REPORTED")


class ScheduleProposalRecord(MutableRow, Base):
    """2–5 slots of 30 or 60 minutes from one party; choosing one is not yet booking it."""

    __tablename__ = "schedule_proposals"
    __table_args__ = (
        CheckConstraint(f"state IN {PROPOSAL_STATES}", name="state"),
        CheckConstraint("minutes IN (30, 60)", name="minutes"),
        CheckConstraint("expired_reason IS NULL OR expired_reason IN ('AGE', 'ALL_PAST')", name="expired_reason"),
    )

    pitch_id: Mapped[UUID] = mapped_column(ForeignKey("pitches.id", ondelete="CASCADE"), index=True)
    proposed_by_party_id: Mapped[UUID]
    proposed_by_account_id: Mapped[UUID]
    minutes: Mapped[int]
    time_zone: Mapped[str] = mapped_column(String(64))
    agenda: Mapped[str] = mapped_column(String(1000))
    link: Mapped[str | None] = mapped_column(String(500))
    state: Mapped[str] = mapped_column(String(16), default="OPEN")
    expired_reason: Mapped[str | None] = mapped_column(String(16))
    replaces_meeting_id: Mapped[UUID | None]
    accepted_slot_id: Mapped[UUID | None]


class ScheduleSlotRecord(Row, Base):
    """One offered interval, half-open ``[starts_at, ends_at)``, stored in UTC."""

    __tablename__ = "schedule_slots"
    __table_args__ = (UniqueConstraint("proposal_id", "position"),)

    proposal_id: Mapped[UUID] = mapped_column(ForeignKey("schedule_proposals.id", ondelete="CASCADE"), index=True)
    position: Mapped[int]
    starts_at: Mapped[datetime]
    ends_at: Mapped[datetime]


class MeetingRecord(MutableRow, Base):
    """A confirmed meeting. Time passing never completes it; both parties' outcomes do (AC47)."""

    __tablename__ = "meetings"
    __table_args__ = (CheckConstraint(f"state IN {MEETING_STATES}", name="state"),)

    pitch_id: Mapped[UUID] = mapped_column(ForeignKey("pitches.id", ondelete="CASCADE"), index=True)
    proposal_id: Mapped[UUID]
    starts_at: Mapped[datetime]
    ends_at: Mapped[datetime]
    time_zone: Mapped[str] = mapped_column(String(64))
    agenda: Mapped[str] = mapped_column(String(1000))
    link: Mapped[str | None] = mapped_column(String(500))
    state: Mapped[str] = mapped_column(String(24), default="CONFIRMED")


class BookingRecord(Row, Base):
    """A party's busy interval. The exclusion constraint makes two overlapping bookings of one party impossible."""

    __tablename__ = "bookings"
    __table_args__ = (
        ExcludeConstraint(("party_id", "="), ("during", "&&"), name="ex_bookings_party_during", using="gist"),
    )

    party_id: Mapped[UUID] = mapped_column(ForeignKey("parties.id", ondelete="CASCADE"), index=True)
    meeting_id: Mapped[UUID | None] = mapped_column(ForeignKey("meetings.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200), default="")
    during: Mapped[Any] = mapped_column(TSTZRANGE)


class MeetingOutcomeRecord(MutableRow, Base):
    """What one party says happened."""

    __tablename__ = "meeting_outcomes"
    __table_args__ = (
        UniqueConstraint("meeting_id", "party_id"),
        CheckConstraint("result IN ('COMPLETED', 'NO_SHOW')", name="result"),
    )

    meeting_id: Mapped[UUID] = mapped_column(ForeignKey("meetings.id", ondelete="CASCADE"), index=True)
    party_id: Mapped[UUID]
    result: Mapped[str] = mapped_column(String(16))
    note: Mapped[str] = mapped_column(String(1000), default="")
    recorded_by_account_id: Mapped[UUID]


class CalendarConnectionRecord(Base):
    """The account's credential and at most one pending, session-bound OAuth attempt."""

    __tablename__ = "calendar_connections"
    __table_args__ = (
        CheckConstraint("(encrypted_token IS NULL) = (token_expires_at IS NULL)", name="token_pair"),
        CheckConstraint(
            "(state_sha256 IS NULL) = (encrypted_verifier IS NULL) AND "
            "(state_sha256 IS NULL OR state_expires_at IS NOT NULL) AND "
            "(state_expires_at IS NULL) = (state_session_id IS NULL)",
            name="state_group",
        ),
    )

    account_id: Mapped[UUID] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"), primary_key=True)
    version: Mapped[int] = mapped_column(default=0, server_default="0")
    provider_revocation_confirmed: Mapped[bool | None]
    encrypted_token: Mapped[bytes | None]
    token_expires_at: Mapped[datetime | None]
    state_sha256: Mapped[str | None] = mapped_column(String(64))
    encrypted_verifier: Mapped[bytes | None]
    state_expires_at: Mapped[datetime | None]
    state_session_id: Mapped[UUID | None]
