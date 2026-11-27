"""The public invention page: owner switch, field-test summary, published photo and content language (spec 051).

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
    op.add_column("inventions", sa.Column("public_page", sa.Boolean(), server_default="false", nullable=False))
    op.add_column("inventions", sa.Column("public_page_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("inventions", sa.Column("public_field_test", sa.Text(), nullable=True))
    op.add_column("inventions", sa.Column("public_photo_version_id", sa.Uuid(), nullable=True))
    op.add_column("inventions", sa.Column("public_photo_alt", sa.String(length=200), nullable=True))
    op.add_column("inventions", sa.Column("public_photo_width", sa.Integer(), nullable=True))
    op.add_column("inventions", sa.Column("public_photo_height", sa.Integer(), nullable=True))
    op.add_column("inventions", sa.Column("public_photo_orientation", sa.Integer(), nullable=True))
    op.add_column(
        "inventions", sa.Column("public_content_locale", sa.String(length=2), server_default="id", nullable=False)
    )
    # Erasing the file removes it from the page too; nothing else references the version.
    op.create_foreign_key(
        "inventions_public_photo_version_id_fkey",
        "inventions",
        "document_versions",
        ["public_photo_version_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_check_constraint("public_content_locale", "inventions", "public_content_locale IN ('id', 'en')")
    op.create_check_constraint(
        "public_photo_alt",
        "inventions",
        "public_photo_version_id IS NULL OR length(coalesce(public_photo_alt, '')) > 0",
    )


def downgrade() -> None:
    op.drop_constraint("public_photo_alt", "inventions", type_="check")
    op.drop_constraint("public_content_locale", "inventions", type_="check")
    op.drop_constraint("inventions_public_photo_version_id_fkey", "inventions", type_="foreignkey")
    op.drop_column("inventions", "public_content_locale")
    op.drop_column("inventions", "public_photo_orientation")
    op.drop_column("inventions", "public_photo_height")
    op.drop_column("inventions", "public_photo_width")
    op.drop_column("inventions", "public_photo_alt")
    op.drop_column("inventions", "public_photo_version_id")
    op.drop_column("inventions", "public_field_test")
    op.drop_column("inventions", "public_page_at")
    op.drop_column("inventions", "public_page")
