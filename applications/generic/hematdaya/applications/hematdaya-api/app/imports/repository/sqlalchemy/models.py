"""Import ORM records."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ImportRecord(Base):
    """Row in ``imports``."""

    __tablename__ = "imports"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    site_id: Mapped[UUID] = mapped_column(ForeignKey("sites.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(Text)
    file_name: Mapped[str] = mapped_column(Text)
    content_sha256: Mapped[str] = mapped_column(Text)
    mapping: Mapped[dict[str, Any]] = mapped_column(JSONB)
    total_rows: Mapped[int] = mapped_column(Integer)
    accepted_rows: Mapped[int] = mapped_column(Integer)
    invalid_rows: Mapped[int] = mapped_column(Integer)
    duplicate_rows: Mapped[int] = mapped_column(Integer)
    conflict_rows: Mapped[int] = mapped_column(Integer)
    pending_rows: Mapped[int] = mapped_column(Integer)
    blocked: Mapped[bool]
    block_reasons: Mapped[list[str]] = mapped_column(JSONB)
    needs_acknowledgment: Mapped[bool]
    questions: Mapped[list[dict[str, Any]]] = mapped_column(JSONB)
    assumptions: Mapped[list[str]] = mapped_column(JSONB)
    period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    measurement_revision: Mapped[int] = mapped_column(BigInteger)
    binding_revision: Mapped[int] = mapped_column(BigInteger)
    idempotency_key: Mapped[str | None] = mapped_column(Text)
    # A preview holds SQL NULL, because JSON null would pass the CHECK as a result.
    commit_result: Mapped[dict[str, Any] | None] = mapped_column(JSONB(none_as_null=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ImportRowRecord(Base):
    """Row in ``import_rows``."""

    __tablename__ = "import_rows"

    import_id: Mapped[UUID] = mapped_column(ForeignKey("imports.id", ondelete="CASCADE"), primary_key=True)
    data_row: Mapped[int] = mapped_column(Integer, primary_key=True)
    file_line: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(Text)
    reason: Mapped[str | None] = mapped_column(Text)
    field: Mapped[str | None] = mapped_column(Text)
    message: Mapped[str | None] = mapped_column(Text)
    # A row with nothing to store holds SQL NULL, not JSON null.
    parsed: Mapped[dict[str, Any] | None] = mapped_column(JSONB(none_as_null=True))
