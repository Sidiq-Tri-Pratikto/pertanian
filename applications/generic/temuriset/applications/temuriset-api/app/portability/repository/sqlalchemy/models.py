"""Private staging, external identity mappings and export artifacts."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, MutableRow, Row


class ImportRunRecord(MutableRow, Base):
    """Separate stages and durable cursors of a bounded import."""

    __tablename__ = "portability_import_runs"

    party_id: Mapped[UUID] = mapped_column(ForeignKey("parties.id", ondelete="CASCADE"), index=True)
    account_id: Mapped[UUID] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"), index=True)
    session_id: Mapped[UUID]
    membership_id: Mapped[UUID | None]
    expires_at: Mapped[datetime]
    sha256: Mapped[str] = mapped_column(String(64))
    map_private_notes: Mapped[bool]
    external_system: Mapped[str | None] = mapped_column(String(160))
    validation_job_id: Mapped[UUID | None]
    preview_job_id: Mapped[UUID | None]
    apply_job_id: Mapped[UUID | None]
    total: Mapped[int] = mapped_column(default=0)
    previewed: Mapped[int] = mapped_column(default=0)
    applied: Mapped[int] = mapped_column(default=0)
    committed: Mapped[int] = mapped_column(default=0)
    skipped: Mapped[int] = mapped_column(default=0)
    cancelled_stage: Mapped[str | None] = mapped_column(String(16))
    expired: Mapped[bool] = mapped_column(default=False)


class ImportRowRecord(Base):
    """Validated source content and its comparison, purged when staging expires."""

    __tablename__ = "portability_import_rows"

    run_id: Mapped[UUID] = mapped_column(ForeignKey("portability_import_runs.id", ondelete="CASCADE"), primary_key=True)
    position: Mapped[int] = mapped_column(primary_key=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB)
    comparison: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    outcome: Mapped[str | None] = mapped_column(String(16))


class ExternalReferenceRecord(MutableRow, Base):
    """One source identifier in a managing party's context."""

    __tablename__ = "portability_external_references"
    __table_args__ = (UniqueConstraint("party_id", "external_system", "external_id"),)

    party_id: Mapped[UUID] = mapped_column(ForeignKey("parties.id", ondelete="CASCADE"))
    external_system: Mapped[str] = mapped_column(String(160))
    external_id: Mapped[str] = mapped_column(String(160))
    invention_id: Mapped[UUID | None] = mapped_column(ForeignKey("inventions.id", ondelete="CASCADE"), index=True)
    source: Mapped[dict[str, Any]] = mapped_column(JSONB)


class ExportJobRecord(Row, Base):
    """An owner-only job with exact authorized dependencies and an irreversible expiry."""

    __tablename__ = "portability_export_jobs"

    party_id: Mapped[UUID] = mapped_column(ForeignKey("parties.id", ondelete="CASCADE"), index=True)
    account_id: Mapped[UUID] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"), index=True)
    session_id: Mapped[UUID]
    membership_id: Mapped[UUID | None]
    expires_at: Mapped[datetime]
    job_id: Mapped[UUID | None]
    dependencies: Mapped[list[dict[str, Any]]] = mapped_column(JSONB)
    size_bytes: Mapped[int | None]
    expired: Mapped[bool] = mapped_column(default=False)
