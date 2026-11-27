"""The public invention page: owner switch, field-test summary, published photo and content language (spec 051).

A new table instead of new columns and constraints on ``inventions``: the release only adds schema, so the
migration compatibility check passes and old API and worker instances keep working while both versions run.

Revision ID: 0023
Revises: 0022
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0023"
down_revision: str | None = "0022"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "invention_public_pages",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "invention_id",
            sa.Uuid(),
            sa.ForeignKey("inventions.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("enabled", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("enabled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("field_test", sa.Text(), nullable=True),
        # Erasing the file removes it from the page too; nothing else references the version.
        sa.Column(
            "photo_version_id", sa.Uuid(), sa.ForeignKey("document_versions.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("photo_alt", sa.String(length=200), nullable=True),
        sa.Column("photo_width", sa.Integer(), nullable=True),
        sa.Column("photo_height", sa.Integer(), nullable=True),
        sa.Column("photo_orientation", sa.Integer(), nullable=True),
        sa.Column("content_locale", sa.String(length=2), server_default="id", nullable=False),
        sa.CheckConstraint("content_locale IN ('id', 'en')", name="content_locale"),
        sa.CheckConstraint("photo_version_id IS NULL OR length(coalesce(photo_alt, '')) > 0", name="photo_alt"),
    )


def downgrade() -> None:
    op.drop_table("invention_public_pages")
