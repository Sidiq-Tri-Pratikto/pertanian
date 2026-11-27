"""Public updates the managing party writes about an invention (spec 052).

Revision ID: 0024
Revises: 0023
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0024"
down_revision: str | None = "0023"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "invention_updates",
        sa.Column("invention_id", sa.Uuid(), nullable=False),
        sa.Column("author_account_id", sa.Uuid(), nullable=False),
        sa.Column("author_party_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("content_locale", sa.String(length=2), server_default="id", nullable=False),
        sa.Column("status", sa.String(length=16), server_default="DRAFT", nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("withdrawn_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("status IN ('DRAFT', 'PUBLISHED', 'WITHDRAWN')", name="status"),
        sa.CheckConstraint("content_locale IN ('id', 'en')", name="content_locale"),
        sa.CheckConstraint("length(body) <= 1200", name="body_length"),
        sa.ForeignKeyConstraint(["invention_id"], ["inventions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_invention_updates_invention_status_published",
        "invention_updates",
        ["invention_id", "status", "published_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_invention_updates_invention_status_published", table_name="invention_updates")
    op.drop_table("invention_updates")
