"""Following one invention by email, its one-time links, and which update each follower got (spec 053).

Revision ID: 0025
Revises: 0024
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0025"
down_revision: str | None = "0024"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "invention_follows",
        sa.Column("invention_id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("locale", sa.String(length=8), nullable=False),
        sa.Column("consent_source", sa.String(length=32), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("unsubscribed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("locale IN ('id', 'en')", name="locale"),
        sa.CheckConstraint("status IN ('PENDING', 'ACTIVE', 'UNSUBSCRIBED')", name="status"),
        sa.ForeignKeyConstraint(["invention_id"], ["inventions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("invention_id", "email"),
    )
    op.create_index(
        "ix_invention_follows_invention_status", "invention_follows", ["invention_id", "status"], unique=False
    )
    op.create_table(
        "invention_follow_deliveries",
        sa.Column("follow_id", sa.Uuid(), nullable=False),
        sa.Column("update_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["follow_id"], ["invention_follows.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["update_id"], ["invention_updates.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("follow_id", "update_id"),
    )
    op.create_index(
        op.f("ix_invention_follow_deliveries_update_id"), "invention_follow_deliveries", ["update_id"], unique=False
    )
    op.create_table(
        "invention_follow_links",
        sa.Column("follow_id", sa.Uuid(), nullable=False),
        sa.Column("purpose", sa.String(length=8), nullable=False),
        sa.Column("token_sha256", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("purpose IN ('confirm', 'manage')", name="purpose"),
        sa.ForeignKeyConstraint(["follow_id"], ["invention_follows.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_sha256"),
    )
    op.create_index(op.f("ix_invention_follow_links_follow_id"), "invention_follow_links", ["follow_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_invention_follow_links_follow_id"), table_name="invention_follow_links")
    op.drop_table("invention_follow_links")
    op.drop_index(op.f("ix_invention_follow_deliveries_update_id"), table_name="invention_follow_deliveries")
    op.drop_table("invention_follow_deliveries")
    op.drop_index("ix_invention_follows_invention_status", table_name="invention_follows")
    op.drop_table("invention_follows")
