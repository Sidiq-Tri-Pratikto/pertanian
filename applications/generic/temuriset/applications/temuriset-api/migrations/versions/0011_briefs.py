"""Briefs: preflights that pin every version, and briefs with references per sentence (spec 022).

Revision ID: 0011
Revises: 0010
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "preflights",
        sa.Column("actor_party_id", sa.Uuid(), nullable=False),
        sa.Column("actor_account_id", sa.Uuid(), nullable=False),
        sa.Column("token_sha256", sa.String(length=64), nullable=False),
        sa.Column("source_type", sa.String(length=16), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("source_version", sa.Integer(), nullable=False),
        sa.Column("invention_version_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("opportunity_id", sa.Uuid(), nullable=False),
        sa.Column("opportunity_version_id", sa.Uuid(), nullable=False),
        sa.Column("recipient_party_id", sa.Uuid(), nullable=False),
        sa.Column("configuration_ref", sa.String(length=200), nullable=False),
        sa.Column("permission_generation", sa.String(length=64), nullable=False),
        sa.Column("result", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("shareable_files", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["actor_party_id"], ["parties.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_sha256"),
    )
    op.create_index(op.f("ix_preflights_actor_party_id"), "preflights", ["actor_party_id"], unique=False)
    op.create_table(
        "briefs",
        sa.Column("preflight_id", sa.Uuid(), nullable=False),
        sa.Column("owner_party_id", sa.Uuid(), nullable=False),
        sa.Column("summarizer", sa.String(length=32), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("sentences", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["owner_party_id"], ["parties.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["preflight_id"], ["preflights.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_briefs_owner_party_id"), "briefs", ["owner_party_id"], unique=False)
    op.create_index(op.f("ix_briefs_preflight_id"), "briefs", ["preflight_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_briefs_preflight_id"), table_name="briefs")
    op.drop_index(op.f("ix_briefs_owner_party_id"), table_name="briefs")
    op.drop_table("briefs")
    op.drop_index(op.f("ix_preflights_actor_party_id"), table_name="preflights")
    op.drop_table("preflights")
