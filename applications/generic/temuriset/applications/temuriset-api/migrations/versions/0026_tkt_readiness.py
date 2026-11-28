"""TKT readiness on invention versions and optional minimum TKT on mandates (spec 055).

``invention_readiness`` is a new table so its constraints never touch an existing table, and
``opportunity_versions.min_tkt`` is a nullable column with no table constraint (validated in the API).
Both changes are expand-only so old API and worker instances keep working while both versions run.

Revision ID: 0026
Revises: 0025
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0026"
down_revision: str | None = "0025"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "invention_readiness",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column(
            "version_id",
            sa.Uuid(),
            sa.ForeignKey("invention_versions.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("tkt_level", sa.SmallInteger(), nullable=False),
        sa.Column("note", sa.Text(), server_default="", nullable=False),
        sa.Column(
            "evidence_version_id",
            sa.Uuid(),
            sa.ForeignKey("document_versions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.CheckConstraint("tkt_level >= 1 AND tkt_level <= 9", name="tkt_level"),
        sa.CheckConstraint("length(note) <= 500", name="note_length"),
    )
    op.add_column("opportunity_versions", sa.Column("min_tkt", sa.SmallInteger(), nullable=True))


def downgrade() -> None:
    op.drop_column("opportunity_versions", "min_tkt")
    op.drop_table("invention_readiness")
