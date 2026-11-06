"""Matching: runs and results, reproducible from their inputs and versions (spec 019).

Revision ID: 0010
Revises: 0009
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "match_runs",
        sa.Column("actor_party_id", sa.Uuid(), nullable=False),
        sa.Column("source_type", sa.String(length=16), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("source_version", sa.Integer(), nullable=False),
        sa.Column("source_title", sa.String(length=200), nullable=False),
        sa.Column("engine", sa.String(length=40), nullable=False),
        sa.Column("policy_versions", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("inputs", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["actor_party_id"], ["parties.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_match_runs_actor_party_id"), "match_runs", ["actor_party_id"], unique=False)
    op.create_table(
        "match_results",
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("shown", sa.Boolean(), nullable=False),
        sa.Column("opportunity_version_id", sa.Uuid(), nullable=False),
        sa.Column("eligibility", sa.String(length=24), nullable=False),
        sa.Column("readiness", sa.String(length=32), nullable=False),
        sa.Column("relevant", sa.Boolean(), nullable=False),
        sa.Column("fit_lower", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("fit_upper", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("coverage", sa.Numeric(precision=3, scale=2), nullable=False),
        sa.Column("result", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["match_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_match_results_run_id"), "match_results", ["run_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_match_results_run_id"), table_name="match_results")
    op.drop_table("match_results")
    op.drop_index(op.f("ix_match_runs_actor_party_id"), table_name="match_runs")
    op.drop_table("match_runs")
