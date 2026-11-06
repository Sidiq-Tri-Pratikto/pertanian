"""Feedback ORM records."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class InsightFeedbackRecord(Base):
    """Row in ``insight_feedback``."""

    __tablename__ = "insight_feedback"

    insight_id: Mapped[UUID] = mapped_column(primary_key=True)
    revision: Mapped[int] = mapped_column(Integer, primary_key=True)
    principal_id: Mapped[UUID] = mapped_column(ForeignKey("principals.id", ondelete="CASCADE"), primary_key=True)
    rating: Mapped[str | None] = mapped_column(Text)
    visibility: Mapped[str] = mapped_column(Text)
    until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FeedbackOperationRecord(Base):
    """Row in ``feedback_operations``."""

    __tablename__ = "feedback_operations"

    principal_id: Mapped[UUID] = mapped_column(ForeignKey("principals.id", ondelete="CASCADE"), primary_key=True)
    key: Mapped[str] = mapped_column(Text, primary_key=True)
    insight_id: Mapped[UUID] = mapped_column(ForeignKey("insights.id", ondelete="CASCADE"))
    revision: Mapped[int] = mapped_column(Integer)
    action: Mapped[str] = mapped_column(Text)
    response: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
