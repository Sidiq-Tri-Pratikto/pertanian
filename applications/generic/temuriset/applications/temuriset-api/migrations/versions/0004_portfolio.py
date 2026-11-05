"""Portfolio: inventions, versions, facts and claims (spec 009).

Revision ID: 0004
Revises: 0003
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "inventions",
        sa.Column("managing_party_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("published_version_id", sa.Uuid(), nullable=True),
        sa.Column("draft_version_id", sa.Uuid(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("status IN ('DRAFT', 'PENDING_REVIEW', 'PUBLISHED', 'ARCHIVED')", name="status"),
        sa.ForeignKeyConstraint(["managing_party_id"], ["parties.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_inventions_managing_party_id"), "inventions", ["managing_party_id"], unique=False)
    op.create_table(
        "invention_versions",
        sa.Column("invention_id", sa.Uuid(), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("state", sa.String(length=16), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("problem", sa.Text(), nullable=False),
        sa.Column("solution", sa.Text(), nullable=False),
        sa.Column("intended_users", sa.Text(), nullable=False),
        sa.Column("sector", sa.String(length=80), nullable=False),
        sa.Column("stage", sa.String(length=16), nullable=True),
        sa.Column("keywords", postgresql.ARRAY(sa.String(length=40)), nullable=False),
        sa.Column("private_notes", sa.Text(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("state IN ('draft', 'published', 'superseded')", name="state"),
        sa.ForeignKeyConstraint(["invention_id"], ["inventions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("invention_id", "number"),
    )
    op.create_index(op.f("ix_invention_versions_invention_id"), "invention_versions", ["invention_id"], unique=False)
    op.create_table(
        "invention_claims",
        sa.Column("version_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("subject_name", sa.String(length=160), nullable=False),
        sa.Column("party_id", sa.Uuid(), nullable=True),
        sa.Column("scope", sa.String(length=200), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("source", sa.String(length=200), nullable=False),
        sa.Column("asserted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("kind IN ('creator', 'contributor', 'manager', 'rights_holder', 'authority')", name="kind"),
        sa.CheckConstraint("status IN ('asserted', 'not_established', 'reviewed')", name="status"),
        sa.ForeignKeyConstraint(["version_id"], ["invention_versions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_invention_claims_version_id"), "invention_claims", ["version_id"], unique=False)
    op.create_table(
        "invention_facts",
        sa.Column("version_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(length=120), nullable=False),
        sa.Column("value", sa.String(length=200), nullable=False),
        sa.Column("unit", sa.String(length=40), nullable=False),
        sa.Column("timing", sa.String(length=16), nullable=False),
        sa.Column("provenance", sa.String(length=16), nullable=False),
        sa.Column("key", sa.String(length=64), nullable=True),
        sa.Column("document_version_id", sa.Uuid(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "provenance IN ('SOURCE_REPORTED', 'SELF_DECLARED', 'PROVIDED', 'REVIEWED', 'UNKNOWN')", name="provenance"
        ),
        sa.CheckConstraint("timing IN ('CURRENT', 'PLANNED', 'REQUESTED')", name="timing"),
        sa.ForeignKeyConstraint(["version_id"], ["invention_versions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_invention_facts_version_id"), "invention_facts", ["version_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_invention_facts_version_id"), table_name="invention_facts")
    op.drop_table("invention_facts")
    op.drop_index(op.f("ix_invention_claims_version_id"), table_name="invention_claims")
    op.drop_table("invention_claims")
    op.drop_index(op.f("ix_invention_versions_invention_id"), table_name="invention_versions")
    op.drop_table("invention_versions")
    op.drop_index(op.f("ix_inventions_managing_party_id"), table_name="inventions")
    op.drop_table("inventions")
