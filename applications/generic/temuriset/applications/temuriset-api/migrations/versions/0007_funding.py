"""Funding: legal entities, funding requests, their versions and invention links (spec 014).

Revision ID: 0007
Revises: 0006
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "legal_entities",
        sa.Column("owner_party_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("jurisdiction", sa.String(length=120), nullable=False),
        sa.Column("registration_reference", sa.String(length=120), nullable=False),
        sa.Column("review_status", sa.String(length=16), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("review_status IN ('declared', 'verified')", name="review_status"),
        sa.ForeignKeyConstraint(["owner_party_id"], ["parties.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_legal_entities_owner_party_id"), "legal_entities", ["owner_party_id"], unique=False)
    op.create_table(
        "funding_requests",
        sa.Column("owner_party_id", sa.Uuid(), nullable=False),
        sa.Column("subject_type", sa.String(length=16), nullable=False),
        sa.Column("legal_entity_id", sa.Uuid(), nullable=True),
        sa.Column("proposed_name", sa.String(length=200), nullable=False),
        sa.Column("financing_stage", sa.String(length=16), nullable=True),
        sa.Column("financing_form", sa.String(length=24), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=True),
        sa.Column("target_amount", sa.Numeric(precision=20, scale=4), nullable=True),
        sa.Column("desired_min", sa.Numeric(precision=20, scale=4), nullable=True),
        sa.Column("desired_max", sa.Numeric(precision=20, scale=4), nullable=True),
        sa.Column("accepts_partial", sa.Boolean(), nullable=False),
        sa.Column("accepts_syndicated", sa.Boolean(), nullable=False),
        sa.Column("intended_use", sa.Text(), nullable=False),
        sa.Column("timing", sa.String(length=200), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "(subject_type = 'EXISTING_ENTITY') = (legal_entity_id IS NOT NULL)", name="entity_matches_subject"
        ),
        sa.CheckConstraint("status IN ('DRAFT', 'ACTIVE', 'PAUSED', 'CLOSED')", name="status"),
        sa.CheckConstraint("subject_type IN ('EXISTING_ENTITY', 'PROPOSED_ENTITY')", name="subject_type"),
        sa.CheckConstraint("desired_max >= desired_min", name="desired_max_not_below_min"),
        sa.CheckConstraint("desired_min >= 0", name="desired_min_not_negative"),
        sa.CheckConstraint("target_amount > 0", name="target_positive"),
        sa.ForeignKeyConstraint(["legal_entity_id"], ["legal_entities.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["owner_party_id"], ["parties.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_funding_requests_owner_party_id"), "funding_requests", ["owner_party_id"], unique=False)
    op.create_table(
        "funding_invention_links",
        sa.Column("funding_request_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("invention_id", sa.Uuid(), nullable=False),
        sa.Column("invention_version_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["funding_request_id"], ["funding_requests.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["invention_id"], ["inventions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["invention_version_id"], ["invention_versions.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("funding_request_id", "invention_id"),
    )
    op.create_index(
        op.f("ix_funding_invention_links_funding_request_id"),
        "funding_invention_links",
        ["funding_request_id"],
        unique=False,
    )
    op.create_table(
        "funding_request_versions",
        sa.Column("funding_request_id", sa.Uuid(), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["funding_request_id"], ["funding_requests.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("funding_request_id", "number"),
    )
    op.create_index(
        op.f("ix_funding_request_versions_funding_request_id"),
        "funding_request_versions",
        ["funding_request_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_funding_request_versions_funding_request_id"), table_name="funding_request_versions")
    op.drop_table("funding_request_versions")
    op.drop_index(op.f("ix_funding_invention_links_funding_request_id"), table_name="funding_invention_links")
    op.drop_table("funding_invention_links")
    op.drop_index(op.f("ix_funding_requests_owner_party_id"), table_name="funding_requests")
    op.drop_table("funding_requests")
    op.drop_index(op.f("ix_legal_entities_owner_party_id"), table_name="legal_entities")
    op.drop_table("legal_entities")
