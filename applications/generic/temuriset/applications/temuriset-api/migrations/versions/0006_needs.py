"""Needs: support requests, their versions, project budgets and lines (spec 013).

Revision ID: 0006
Revises: 0005
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "support_requests",
        sa.Column("invention_id", sa.Uuid(), nullable=False),
        sa.Column("owner_party_id", sa.Uuid(), nullable=False),
        sa.Column("invention_version_id", sa.Uuid(), nullable=False),
        sa.Column("outcome", sa.String(length=200), nullable=False),
        sa.Column("support_forms", postgresql.ARRAY(sa.String(length=40)), nullable=False),
        sa.Column("relationship_form", sa.String(length=16), nullable=False),
        sa.Column("scope", sa.Text(), nullable=False),
        sa.Column("months", sa.Integer(), nullable=True),
        sa.Column("region", sa.String(length=120), nullable=False),
        sa.Column("accepts_partial", sa.Boolean(), nullable=False),
        sa.Column("accepts_noncash", sa.Boolean(), nullable=False),
        sa.Column("noncash_description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("relationship_form IN ('PROJECT', 'LICENSE')", name="relationship_form"),
        sa.CheckConstraint("status IN ('DRAFT', 'ACTIVE', 'PAUSED', 'CLOSED', 'EXPIRED')", name="status"),
        sa.ForeignKeyConstraint(["invention_id"], ["inventions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["invention_version_id"], ["invention_versions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["owner_party_id"], ["parties.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_support_requests_invention_id"), "support_requests", ["invention_id"], unique=False)
    op.create_index(op.f("ix_support_requests_owner_party_id"), "support_requests", ["owner_party_id"], unique=False)
    op.create_table(
        "project_budgets",
        sa.Column("support_request_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("min_amount", sa.Numeric(precision=20, scale=4), nullable=True),
        sa.Column("max_amount", sa.Numeric(precision=20, scale=4), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=True),
        sa.Column("basis", sa.String(length=16), nullable=False),
        sa.Column("period", sa.String(length=80), nullable=False),
        sa.Column("scope", sa.Text(), nullable=False),
        sa.Column("estimated_on", sa.Date(), nullable=True),
        sa.Column("assumptions", sa.Text(), nullable=False),
        sa.Column("unknown_reason", sa.String(length=32), nullable=True),
        sa.Column("financial", sa.Boolean(), nullable=False),
        sa.Column("lines_explanation", sa.Text(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("basis IN ('total_period', 'monthly', 'yearly')", name="basis"),
        sa.CheckConstraint(
            "(min_amount IS NULL AND max_amount IS NULL AND unknown_reason IS NOT NULL) OR "
            "(min_amount IS NOT NULL AND max_amount IS NOT NULL AND currency IS NOT NULL)",
            name="known_or_explained",
        ),
        sa.CheckConstraint("max_amount >= min_amount", name="max_not_below_min"),
        sa.CheckConstraint("min_amount >= 0", name="min_not_negative"),
        sa.ForeignKeyConstraint(["support_request_id"], ["support_requests.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("support_request_id", "version"),
    )
    op.create_index(
        op.f("ix_project_budgets_support_request_id"), "project_budgets", ["support_request_id"], unique=False
    )
    op.create_table(
        "support_request_versions",
        sa.Column("support_request_id", sa.Uuid(), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["support_request_id"], ["support_requests.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("support_request_id", "number"),
    )
    op.create_index(
        op.f("ix_support_request_versions_support_request_id"),
        "support_request_versions",
        ["support_request_id"],
        unique=False,
    )
    op.create_table(
        "project_budget_lines",
        sa.Column("budget_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(length=160), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=20, scale=4), nullable=False),
        sa.Column("unit_cost", sa.Numeric(precision=20, scale=4), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["budget_id"], ["project_budgets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_project_budget_lines_budget_id"), "project_budget_lines", ["budget_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_project_budget_lines_budget_id"), table_name="project_budget_lines")
    op.drop_table("project_budget_lines")
    op.drop_index(op.f("ix_support_request_versions_support_request_id"), table_name="support_request_versions")
    op.drop_table("support_request_versions")
    op.drop_index(op.f("ix_project_budgets_support_request_id"), table_name="project_budgets")
    op.drop_table("project_budgets")
    op.drop_index(op.f("ix_support_requests_owner_party_id"), table_name="support_requests")
    op.drop_index(op.f("ix_support_requests_invention_id"), table_name="support_requests")
    op.drop_table("support_requests")
