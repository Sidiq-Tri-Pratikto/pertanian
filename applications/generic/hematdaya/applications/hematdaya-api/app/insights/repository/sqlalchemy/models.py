"""Insight ORM records."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class InsightRecord(Base):
    """Row in ``insights``."""

    __tablename__ = "insights"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    site_id: Mapped[UUID] = mapped_column(ForeignKey("sites.id", ondelete="CASCADE"))
    kind: Mapped[str] = mapped_column(Text)
    asset_id: Mapped[UUID] = mapped_column(ForeignKey("assets.id", ondelete="CASCADE"))
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    identity_key: Mapped[str] = mapped_column(Text)
    current_revision: Mapped[int] = mapped_column(Integer)
    active: Mapped[bool]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class InsightRevisionRecord(Base):
    """Row in ``insight_revisions``."""

    __tablename__ = "insight_revisions"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    insight_id: Mapped[UUID] = mapped_column(ForeignKey("insights.id", ondelete="CASCADE"))
    revision: Mapped[int] = mapped_column(Integer)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSONB)
    evidence_hash: Mapped[str] = mapped_column(Text)
    policy_id: Mapped[str] = mapped_column(Text)
    policy_version: Mapped[int] = mapped_column(Integer)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    superseded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
