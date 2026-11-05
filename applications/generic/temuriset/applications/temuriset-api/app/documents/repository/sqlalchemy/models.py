"""Documents, versions, upload intents, grants and download events."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, MutableRow, Row

FILE_STATES = ("CREATED", "UPLOADING", "QUARANTINED", "AVAILABLE", "REJECTED")
EXTRACTION_STATES = ("NOT_REQUESTED", "PENDING", "RUNNING", "SUCCEEDED", "FAILED", "NEEDS_MANUAL_INPUT")
REVIEW_STATES = (
    "PROVIDED_UNREVIEWED",
    "REVIEWED_SUPPORTED",
    "REVIEWED_UNSUPPORTED",
    "NEEDS_CLARIFICATION",
    "EXPIRED",
    "SUPERSEDED",
)


class DocumentRecord(MutableRow, Base):
    """A private document owned by one party."""

    __tablename__ = "documents"

    owner_party_id: Mapped[UUID] = mapped_column(ForeignKey("parties.id", ondelete="RESTRICT"), index=True)
    kind: Mapped[str] = mapped_column(String(32))
    title: Mapped[str] = mapped_column(String(200))


class UploadIntentRecord(Row, Base):
    """Permission to send one file of a declared type and size, until it expires."""

    __tablename__ = "upload_intents"

    owner_party_id: Mapped[UUID] = mapped_column(ForeignKey("parties.id", ondelete="CASCADE"), index=True)
    document_id: Mapped[UUID | None] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(200))
    kind: Mapped[str] = mapped_column(String(32))
    media_type: Mapped[str] = mapped_column(String(120))
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    created_by_account_id: Mapped[UUID]
    expires_at: Mapped[datetime]
    completed_at: Mapped[datetime | None]


class DocumentVersionRecord(MutableRow, Base):
    """One stored file. File, extraction and review states are separate and never overwrite each other."""

    __tablename__ = "document_versions"
    __table_args__ = (
        UniqueConstraint("document_id", "number"),
        CheckConstraint(f"file_state IN {FILE_STATES}", name="file_state"),
        CheckConstraint(f"extraction_state IN {EXTRACTION_STATES}", name="extraction_state"),
        CheckConstraint(f"review_state IN {REVIEW_STATES}", name="review_state"),
    )

    document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    number: Mapped[int]
    storage_key: Mapped[str] = mapped_column(String(80), unique=True)
    sha256: Mapped[str] = mapped_column(String(64))
    media_type: Mapped[str] = mapped_column(String(120))
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    file_state: Mapped[str] = mapped_column(String(16), default="QUARANTINED")
    extraction_state: Mapped[str] = mapped_column(String(24), default="NOT_REQUESTED")
    review_state: Mapped[str] = mapped_column(String(24), default="PROVIDED_UNREVIEWED")
    reviewed_by: Mapped[UUID | None]
    review_scope: Mapped[str | None] = mapped_column(String(200))
    extracted_characters: Mapped[int | None]


class DocumentGrantRecord(Row, Base):
    """One version shared with one party for one purpose. Revocation blocks new requests only."""

    __tablename__ = "document_grants"
    __table_args__ = (
        Index(
            "uq_document_grants_active",
            "document_version_id",
            "grantee_party_id",
            "purpose",
            unique=True,
            postgresql_where="revoked_at IS NULL",
        ),
    )

    document_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("document_versions.id", ondelete="CASCADE"), index=True
    )
    grantee_party_id: Mapped[UUID] = mapped_column(ForeignKey("parties.id", ondelete="CASCADE"), index=True)
    purpose: Mapped[str] = mapped_column(String(32))
    pitch_id: Mapped[UUID | None]
    granted_by_account_id: Mapped[UUID]
    expires_at: Mapped[datetime | None]
    revoked_at: Mapped[datetime | None]


class DownloadEventRecord(Row, Base):
    """Evidence that a copy left the gateway: it cannot be recalled."""

    __tablename__ = "download_events"

    grant_id: Mapped[UUID] = mapped_column(ForeignKey("document_grants.id", ondelete="CASCADE"), index=True)
    actor_party_id: Mapped[UUID]
    range: Mapped[str | None] = mapped_column(String(64))
