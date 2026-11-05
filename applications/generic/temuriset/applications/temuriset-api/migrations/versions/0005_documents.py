"""Documents: upload intents, versions with separate states, grants, download events (spec 010).

Revision ID: 0005
Revises: 0004
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("owner_party_id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["owner_party_id"], ["parties.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_documents_owner_party_id"), "documents", ["owner_party_id"], unique=False)
    op.create_table(
        "document_versions",
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("storage_key", sa.String(length=80), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("media_type", sa.String(length=120), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("file_state", sa.String(length=16), nullable=False),
        sa.Column("extraction_state", sa.String(length=24), nullable=False),
        sa.Column("review_state", sa.String(length=24), nullable=False),
        sa.Column("reviewed_by", sa.Uuid(), nullable=True),
        sa.Column("review_scope", sa.String(length=200), nullable=True),
        sa.Column("extracted_characters", sa.Integer(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "extraction_state IN ('NOT_REQUESTED', 'PENDING', 'RUNNING', 'SUCCEEDED', 'FAILED', 'NEEDS_MANUAL_INPUT')",
            name="extraction_state",
        ),
        sa.CheckConstraint(
            "file_state IN ('CREATED', 'UPLOADING', 'QUARANTINED', 'AVAILABLE', 'REJECTED')", name="file_state"
        ),
        sa.CheckConstraint(
            "review_state IN ('PROVIDED_UNREVIEWED', 'REVIEWED_SUPPORTED', 'REVIEWED_UNSUPPORTED', "
            "'NEEDS_CLARIFICATION', 'EXPIRED', 'SUPERSEDED')",
            name="review_state",
        ),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id", "number"),
        sa.UniqueConstraint("storage_key"),
    )
    op.create_index(op.f("ix_document_versions_document_id"), "document_versions", ["document_id"], unique=False)
    op.create_table(
        "upload_intents",
        sa.Column("owner_party_id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("media_type", sa.String(length=120), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("created_by_account_id", sa.Uuid(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["owner_party_id"], ["parties.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_upload_intents_owner_party_id"), "upload_intents", ["owner_party_id"], unique=False)
    op.create_table(
        "document_grants",
        sa.Column("document_version_id", sa.Uuid(), nullable=False),
        sa.Column("grantee_party_id", sa.Uuid(), nullable=False),
        sa.Column("purpose", sa.String(length=32), nullable=False),
        sa.Column("pitch_id", sa.Uuid(), nullable=True),
        sa.Column("granted_by_account_id", sa.Uuid(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["document_version_id"], ["document_versions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["grantee_party_id"], ["parties.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_document_grants_document_version_id"), "document_grants", ["document_version_id"], unique=False
    )
    op.create_index(op.f("ix_document_grants_grantee_party_id"), "document_grants", ["grantee_party_id"], unique=False)
    op.create_index(
        "uq_document_grants_active",
        "document_grants",
        ["document_version_id", "grantee_party_id", "purpose"],
        unique=True,
        postgresql_where="revoked_at IS NULL",
    )
    op.create_table(
        "download_events",
        sa.Column("grant_id", sa.Uuid(), nullable=False),
        sa.Column("actor_party_id", sa.Uuid(), nullable=False),
        sa.Column("range", sa.String(length=64), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["grant_id"], ["document_grants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_download_events_grant_id"), "download_events", ["grant_id"], unique=False)
    op.create_foreign_key(
        "invention_facts_document_version_id_fkey",
        "invention_facts",
        "document_versions",
        ["document_version_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint("invention_facts_document_version_id_fkey", "invention_facts", type_="foreignkey")
    op.drop_index(op.f("ix_download_events_grant_id"), table_name="download_events")
    op.drop_table("download_events")
    op.drop_index("uq_document_grants_active", table_name="document_grants", postgresql_where="revoked_at IS NULL")
    op.drop_index(op.f("ix_document_grants_grantee_party_id"), table_name="document_grants")
    op.drop_index(op.f("ix_document_grants_document_version_id"), table_name="document_grants")
    op.drop_table("document_grants")
    op.drop_index(op.f("ix_upload_intents_owner_party_id"), table_name="upload_intents")
    op.drop_table("upload_intents")
    op.drop_index(op.f("ix_document_versions_document_id"), table_name="document_versions")
    op.drop_table("document_versions")
    op.drop_index(op.f("ix_documents_owner_party_id"), table_name="documents")
    op.drop_table("documents")
