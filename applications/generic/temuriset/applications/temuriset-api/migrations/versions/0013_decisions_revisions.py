"""Decisions, revision rounds, items and answers; resubmissions carry no preflight (spec 025).

Revision ID: 0013
Revises: 0012
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0013"
down_revision: str | None = "0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "pitch_decisions",
        sa.Column("pitch_id", sa.Uuid(), nullable=False),
        sa.Column("submission_number", sa.Integer(), nullable=False),
        sa.Column("pitch_version", sa.Integer(), nullable=False),
        sa.Column("decision", sa.String(length=16), nullable=False),
        sa.Column("reason", sa.String(length=500), nullable=True),
        sa.Column("decided_by_party_id", sa.Uuid(), nullable=False),
        sa.Column("decided_by_account_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("decision IN ('APPROVE', 'REJECT')", name="decision"),
        sa.ForeignKeyConstraint(["pitch_id"], ["pitches.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_pitch_decisions_pitch_id"), "pitch_decisions", ["pitch_id"], unique=False)
    op.create_table(
        "revision_rounds",
        sa.Column("pitch_id", sa.Uuid(), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("submission_number", sa.Integer(), nullable=False),
        sa.Column("requested_by_party_id", sa.Uuid(), nullable=False),
        sa.Column("requested_by_account_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["pitch_id"], ["pitches.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("pitch_id", "number"),
    )
    op.create_index(op.f("ix_revision_rounds_pitch_id"), "revision_rounds", ["pitch_id"], unique=False)
    op.create_table(
        "revision_items",
        sa.Column("round_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(length=60), nullable=False),
        sa.Column("question", sa.String(length=1000), nullable=False),
        sa.Column("reason", sa.String(length=1000), nullable=False),
        sa.Column("required", sa.Boolean(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("expected_evidence", sa.String(length=500), nullable=False),
        sa.Column("review", sa.String(length=16), nullable=True),
        sa.Column("review_note", sa.String(length=1000), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("review IS NULL OR review IN ('ACCEPTED', 'NEEDS_DETAIL')", name="review"),
        sa.ForeignKeyConstraint(["round_id"], ["revision_rounds.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("round_id", "position"),
    )
    op.create_index(op.f("ix_revision_items_round_id"), "revision_items", ["round_id"], unique=False)
    op.create_table(
        "revision_answers",
        sa.Column("item_id", sa.Uuid(), nullable=False),
        sa.Column("response", sa.String(length=8), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("files", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("saved_by_account_id", sa.Uuid(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("response IN ('CAN', 'DISCUSS', 'CANNOT')", name="response"),
        sa.ForeignKeyConstraint(["item_id"], ["revision_items.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("item_id"),
    )
    op.alter_column("pitch_submissions", "preflight_id", existing_type=sa.UUID(), nullable=True)


def downgrade() -> None:
    # Resubmissions have no preflight; they cannot survive the older column.
    op.execute("DELETE FROM pitch_submissions WHERE preflight_id IS NULL")
    op.alter_column("pitch_submissions", "preflight_id", existing_type=sa.UUID(), nullable=False)
    op.drop_table("revision_answers")
    op.drop_index(op.f("ix_revision_items_round_id"), table_name="revision_items")
    op.drop_table("revision_items")
    op.drop_index(op.f("ix_revision_rounds_pitch_id"), table_name="revision_rounds")
    op.drop_table("revision_rounds")
    op.drop_index(op.f("ix_pitch_decisions_pitch_id"), table_name="pitch_decisions")
    op.drop_table("pitch_decisions")
