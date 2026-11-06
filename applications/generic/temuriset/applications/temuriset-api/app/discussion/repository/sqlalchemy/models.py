"""Pitch-scoped messages and tasks, and per-party in-app notifications (spec 027)."""

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, MutableRow, Row


class MessageRecord(Row, Base):
    """One message in a pitch room. Its text is never logged."""

    __tablename__ = "messages"
    __table_args__ = (Index("ix_messages_pitch_created", "pitch_id", "created_at"),)

    pitch_id: Mapped[UUID] = mapped_column(ForeignKey("pitches.id", ondelete="CASCADE"))
    author_party_id: Mapped[UUID]
    author_account_id: Mapped[UUID]
    text: Mapped[str] = mapped_column(Text)


class TaskRecord(MutableRow, Base):
    """A clarification task with an owner party, due date and what it refers to."""

    __tablename__ = "tasks"
    __table_args__ = (CheckConstraint("status IN ('OPEN', 'DONE')", name="status"),)

    pitch_id: Mapped[UUID] = mapped_column(ForeignKey("pitches.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(300))
    owner_party_id: Mapped[UUID]
    due_date: Mapped[date | None]
    reference: Mapped[str] = mapped_column(String(300), default="")
    status: Mapped[str] = mapped_column(String(8), default="OPEN")
    created_by_party_id: Mapped[UUID]
    completed_at: Mapped[datetime | None]


class NotificationRecord(Row, Base):
    """One in-app notification for one party; at most one per event, party and channel (AC46)."""

    __tablename__ = "notifications"
    __table_args__ = (
        UniqueConstraint("event_key", "party_id", "channel"),
        Index("ix_notifications_party_created", "party_id", "created_at"),
    )

    party_id: Mapped[UUID] = mapped_column(ForeignKey("parties.id", ondelete="CASCADE"))
    pitch_id: Mapped[UUID | None] = mapped_column(ForeignKey("pitches.id", ondelete="CASCADE"))
    event_key: Mapped[str] = mapped_column(String(200))
    channel: Mapped[str] = mapped_column(String(16), default="in_app")
    text: Mapped[str] = mapped_column(String(300))
    tab: Mapped[str] = mapped_column(String(16), default="ringkasan")
    read_at: Mapped[datetime | None]
