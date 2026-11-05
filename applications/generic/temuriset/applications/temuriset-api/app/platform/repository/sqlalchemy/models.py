"""Platform tables: idempotency records, audit events, outbox events and deliveries, jobs."""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core import clock
from app.core.database import Base


class _Row:
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    created_at: Mapped[datetime] = mapped_column(default=clock.now)


class _MutableRow(_Row):
    updated_at: Mapped[datetime] = mapped_column(default=clock.now, onupdate=clock.now)
    version: Mapped[int] = mapped_column(default=1, server_default="1")


class IdempotencyRecord(_MutableRow, Base):
    """One consequential request, keyed by actor, operation and client key."""

    __tablename__ = "idempotency_records"
    __table_args__ = (
        UniqueConstraint("actor_party_id", "operation", "key"),
        CheckConstraint("status IN ('pending', 'committed')", name="status"),
    )

    actor_party_id: Mapped[UUID]
    operation: Mapped[str] = mapped_column(String(128))
    # Released (set to NULL) when an expired key is reused, so the old operation stays readable.
    key: Mapped[str | None] = mapped_column(String(128))
    request_sha256: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(16))
    response_status: Mapped[int | None]
    response_body: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    operation_id: Mapped[UUID] = mapped_column(unique=True, default=uuid4)
    result: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    expires_at: Mapped[datetime]


class AuditEventRecord(_Row, Base):
    """Who did what to which subject. Append-only: the database refuses updates and deletes."""

    __tablename__ = "audit_events"
    __table_args__ = (Index("ix_audit_events_subject", "subject_type", "subject_id"),)

    actor_account_id: Mapped[UUID | None]
    actor_party_id: Mapped[UUID | None]
    action: Mapped[str] = mapped_column(String(128))
    subject_type: Mapped[str] = mapped_column(String(64))
    subject_id: Mapped[str] = mapped_column(String(128))
    detail: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)


class OutboxEventRecord(_Row, Base):
    """A side effect to run after its decision committed."""

    __tablename__ = "outbox_events"
    __table_args__ = (Index("ix_outbox_events_due", "available_at", postgresql_where="dispatched_at IS NULL"),)

    topic: Mapped[str] = mapped_column(String(128))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB)
    available_at: Mapped[datetime] = mapped_column(default=clock.now)
    attempts: Mapped[int] = mapped_column(default=0, server_default="0")
    dispatched_at: Mapped[datetime | None]
    last_error_code: Mapped[str | None] = mapped_column(String(64))


class OutboxDeliveryRecord(_Row, Base):
    """One consumer handled one event. The unique pair makes consumers idempotent."""

    __tablename__ = "outbox_deliveries"
    __table_args__ = (UniqueConstraint("event_id", "consumer"),)

    event_id: Mapped[UUID] = mapped_column(ForeignKey("outbox_events.id", ondelete="CASCADE"))
    consumer: Mapped[str] = mapped_column(String(128))


JOB_STATUSES = ("PENDING", "RUNNING", "SUCCEEDED", "FAILED", "CANCELLED", "NEEDS_MANUAL_INPUT")


class JobRecord(_MutableRow, Base):
    """Background work with a lifecycle the actor can follow."""

    __tablename__ = "jobs"
    __table_args__ = (
        CheckConstraint(f"status IN {JOB_STATUSES}", name="status"),
        Index("ix_jobs_due", "run_after", postgresql_where="status = 'PENDING'"),
    )

    kind: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32), default="PENDING")
    actor_party_id: Mapped[UUID | None]
    input: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    result_ref: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    attempts: Mapped[int] = mapped_column(default=0, server_default="0")
    run_after: Mapped[datetime] = mapped_column(default=clock.now)
    last_error_code: Mapped[str | None] = mapped_column(String(64))
