"""The search projection, saved items, private relevance feedback and the alias table."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import CheckConstraint, Computed, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, MutableRow, Row


class SearchDocumentRecord(MutableRow, Base):
    """One published subject as discovery may show it. Outbox consumers write it; nothing private enters."""

    __tablename__ = "search_documents"
    __table_args__ = (
        CheckConstraint("subject_type IN ('INVENTION', 'FUNDING_REQUEST', 'PARTNER')", name="subject_type"),
        UniqueConstraint("subject_type", "subject_id"),
        Index("ix_search_documents_tsv", "tsv", postgresql_using="gin"),
        Index(
            "ix_search_documents_title_trgm",
            "title",
            postgresql_using="gin",
            postgresql_ops={"title": "gin_trgm_ops"},
        ),
        Index("ix_search_documents_order", "subject_type", "published_at", "id"),
    )

    subject_type: Mapped[str] = mapped_column(String(16))
    subject_id: Mapped[UUID]
    version_id: Mapped[UUID | None]
    owner_party_id: Mapped[UUID] = mapped_column(index=True)
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text, default="")
    tsv: Mapped[Any] = mapped_column(
        TSVECTOR, Computed("to_tsvector('simple', title || ' ' || body)", persisted=True), nullable=True
    )
    filters: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    card: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    published_at: Mapped[datetime]
    curated: Mapped[bool] = mapped_column(default=False)


class SavedItemRecord(Row, Base):
    """One party saved one subject. Only that party ever sees it."""

    __tablename__ = "saved_items"
    __table_args__ = (UniqueConstraint("party_id", "subject_type", "subject_id"),)

    party_id: Mapped[UUID] = mapped_column(ForeignKey("parties.id", ondelete="CASCADE"), index=True)
    subject_type: Mapped[str] = mapped_column(String(16))
    subject_id: Mapped[UUID]


class RelevanceFeedbackRecord(Row, Base):
    """One party said "Kurang relevan" about one subject. It hides the subject from that party only."""

    __tablename__ = "relevance_feedback"
    __table_args__ = (UniqueConstraint("party_id", "subject_type", "subject_id"),)

    party_id: Mapped[UUID] = mapped_column(ForeignKey("parties.id", ondelete="CASCADE"), index=True)
    subject_type: Mapped[str] = mapped_column(String(16))
    subject_id: Mapped[UUID]


class AliasTermRecord(Row, Base):
    """A search word in another language and the Indonesian word it also matches, such as water and air."""

    __tablename__ = "alias_terms"

    term: Mapped[str] = mapped_column(String(80), unique=True)
    canonical: Mapped[str] = mapped_column(String(80))
