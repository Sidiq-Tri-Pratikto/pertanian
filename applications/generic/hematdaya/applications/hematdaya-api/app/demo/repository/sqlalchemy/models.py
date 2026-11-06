"""Demo ORM records."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, LargeBinary, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class DemoSessionRecord(Base):
    """Row in ``demo_sessions``."""

    __tablename__ = "demo_sessions"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    principal_id: Mapped[UUID] = mapped_column(ForeignKey("principals.id", ondelete="CASCADE"), unique=True)
    site_id: Mapped[UUID] = mapped_column(ForeignKey("sites.id", ondelete="CASCADE"))
    scenario_id: Mapped[str] = mapped_column(Text)
    token_hash: Mapped[bytes] = mapped_column(LargeBinary, unique=True)
    key_version: Mapped[str] = mapped_column(Text)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CreateOperationRecord(Base):
    """Row in ``demo_create_operations``."""

    __tablename__ = "demo_create_operations"

    operation_id: Mapped[str] = mapped_column(Text, primary_key=True)
    session_id: Mapped[UUID | None] = mapped_column(ForeignKey("demo_sessions.id", ondelete="SET NULL"))
    scenario_id: Mapped[str] = mapped_column(Text)
    replay_proof_hash: Mapped[bytes] = mapped_column(LargeBinary)
    key_version: Mapped[str] = mapped_column(Text)
    response: Mapped[dict[str, Any]] = mapped_column(JSONB)
    replay_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    retain_until: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
