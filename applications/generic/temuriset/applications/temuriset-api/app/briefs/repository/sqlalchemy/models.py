"""Preflights that pin every version a submission depends on, and briefs with references per sentence."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, Row


class PreflightRecord(Row, Base):
    """One check of one source version against one opportunity version, valid for 30 minutes.

    Only the token's SHA-256 is stored; the token itself goes to the client once.
    """

    __tablename__ = "preflights"

    actor_party_id: Mapped[UUID] = mapped_column(ForeignKey("parties.id", ondelete="CASCADE"), index=True)
    actor_account_id: Mapped[UUID]
    token_sha256: Mapped[str] = mapped_column(String(64), unique=True)
    source_type: Mapped[str] = mapped_column(String(16))
    source_id: Mapped[UUID]
    source_version: Mapped[int]
    invention_version_ids: Mapped[list[str]] = mapped_column(JSONB)
    opportunity_id: Mapped[UUID]
    opportunity_version_id: Mapped[UUID]
    recipient_party_id: Mapped[UUID]
    configuration_ref: Mapped[str] = mapped_column(String(200))
    permission_generation: Mapped[str] = mapped_column(String(64))
    result: Mapped[dict[str, Any]] = mapped_column(JSONB)
    shareable_files: Mapped[list[dict[str, Any]]] = mapped_column(JSONB)
    expires_at: Mapped[datetime]


class BriefRecord(Row, Base):
    """A brief built only from supplied facts. ``sentences`` keep each sentence's references for exact redaction."""

    __tablename__ = "briefs"

    preflight_id: Mapped[UUID] = mapped_column(ForeignKey("preflights.id", ondelete="CASCADE"), index=True)
    owner_party_id: Mapped[UUID] = mapped_column(ForeignKey("parties.id", ondelete="CASCADE"), index=True)
    summarizer: Mapped[str] = mapped_column(String(32), default="off")
    text: Mapped[str] = mapped_column(Text)
    sentences: Mapped[list[dict[str, Any]]] = mapped_column(JSONB)
