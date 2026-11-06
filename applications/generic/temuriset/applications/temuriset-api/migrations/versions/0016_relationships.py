"""Partnerships, versions with checksums, confirmations and restrictions (spec 030).

Revision ID: 0016
Revises: 0015
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0016"
down_revision: str | None = "0015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "partnerships",
        sa.Column("pitch_id", sa.Uuid(), nullable=False),
        sa.Column("type", sa.String(length=16), nullable=False),
        sa.Column("requester_party_id", sa.Uuid(), nullable=False),
        sa.Column("recipient_party_id", sa.Uuid(), nullable=False),
        sa.Column("invention_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("contested", sa.Boolean(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("type IN ('PROJECT', 'LICENSE', 'EQUITY')", name="type"),
        sa.ForeignKeyConstraint(["pitch_id"], ["pitches.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("pitch_id"),
    )
    op.create_index(op.f("ix_partnerships_recipient_party_id"), "partnerships", ["recipient_party_id"], unique=False)
    op.create_index(op.f("ix_partnerships_requester_party_id"), "partnerships", ["requester_party_id"], unique=False)
    op.create_table(
        "partnership_restrictions",
        sa.Column("partnership_id", sa.Uuid(), nullable=False),
        sa.Column("field", sa.String(length=16), nullable=False),
        sa.Column("party_id", sa.Uuid(), nullable=False),
        sa.Column("restricted_by_account_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["partnership_id"], ["partnerships.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_partnership_restrictions_partnership_id"), "partnership_restrictions", ["partnership_id"], unique=False
    )
    op.create_table(
        "partnership_versions",
        sa.Column("partnership_id", sa.Uuid(), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("values", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("ceiling", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("proposed_by_party_id", sa.Uuid(), nullable=False),
        sa.Column("note", sa.String(length=1000), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('PENDING_COUNTERPARTY', 'CONFIRMED', 'CHANGES_REQUESTED', 'DECLINED')", name="status"
        ),
        sa.ForeignKeyConstraint(["partnership_id"], ["partnerships.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("partnership_id", "number"),
    )
    op.create_index(
        op.f("ix_partnership_versions_partnership_id"), "partnership_versions", ["partnership_id"], unique=False
    )
    op.create_table(
        "partnership_confirmations",
        sa.Column("version_id", sa.Uuid(), nullable=False),
        sa.Column("party_id", sa.Uuid(), nullable=False),
        sa.Column("subset", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.Column("confirmed_by_account_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["version_id"], ["partnership_versions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("version_id", "party_id"),
    )
    op.create_index(
        op.f("ix_partnership_confirmations_version_id"), "partnership_confirmations", ["version_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_partnership_confirmations_version_id"), table_name="partnership_confirmations")
    op.drop_table("partnership_confirmations")
    op.drop_index(op.f("ix_partnership_versions_partnership_id"), table_name="partnership_versions")
    op.drop_table("partnership_versions")
    op.drop_index(op.f("ix_partnership_restrictions_partnership_id"), table_name="partnership_restrictions")
    op.drop_table("partnership_restrictions")
    op.drop_index(op.f("ix_partnerships_requester_party_id"), table_name="partnerships")
    op.drop_index(op.f("ix_partnerships_recipient_party_id"), table_name="partnerships")
    op.drop_table("partnerships")
