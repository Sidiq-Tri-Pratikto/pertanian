"""Pitches: active-pitch index, frozen submissions and shared file versions (spec 023).

Revision ID: 0012
Revises: 0011
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0012"
down_revision: str | None = "0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "pitches",
        sa.Column("requester_party_id", sa.Uuid(), nullable=False),
        sa.Column("recipient_party_id", sa.Uuid(), nullable=False),
        sa.Column("opportunity_id", sa.Uuid(), nullable=False),
        sa.Column("opportunity_version_id", sa.Uuid(), nullable=False),
        sa.Column("opportunity_title", sa.String(length=200), nullable=False),
        sa.Column("subject_type", sa.String(length=16), nullable=False),
        sa.Column("subject_id", sa.Uuid(), nullable=False),
        sa.Column("subject_title", sa.String(length=200), nullable=False),
        sa.Column("purpose", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('DRAFT', 'PENDING_WORKSPACE_REVIEW', 'SUBMITTED', 'UNDER_REVIEW', 'REVISION_REQUESTED', "
            "'APPROVED_FOR_DISCUSSION', 'REJECTED', 'WITHDRAWN', 'CLOSED')",
            name="status",
        ),
        sa.CheckConstraint("subject_type IN ('SUPPORT_REQUEST', 'FUNDING_REQUEST')", name="subject_type"),
        sa.ForeignKeyConstraint(["recipient_party_id"], ["parties.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["requester_party_id"], ["parties.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_pitches_recipient_party_id"), "pitches", ["recipient_party_id"], unique=False)
    op.create_index(op.f("ix_pitches_requester_party_id"), "pitches", ["requester_party_id"], unique=False)
    op.create_index(
        "uq_pitches_active",
        "pitches",
        ["subject_type", "subject_id", "recipient_party_id", "opportunity_id", "purpose"],
        unique=True,
        postgresql_where=sa.text("active"),
    )
    op.create_table(
        "pitch_submissions",
        sa.Column("pitch_id", sa.Uuid(), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("preflight_id", sa.Uuid(), nullable=False),
        sa.Column("brief", sa.Text(), nullable=False),
        sa.Column("snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("submitted_by_account_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["pitch_id"], ["pitches.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("pitch_id", "number"),
    )
    op.create_index(op.f("ix_pitch_submissions_pitch_id"), "pitch_submissions", ["pitch_id"], unique=False)
    op.create_table(
        "pitch_submission_files",
        sa.Column("submission_id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("document_version_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("grant_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["submission_id"], ["pitch_submissions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_pitch_submission_files_submission_id"), "pitch_submission_files", ["submission_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_pitch_submission_files_submission_id"), table_name="pitch_submission_files")
    op.drop_table("pitch_submission_files")
    op.drop_index(op.f("ix_pitch_submissions_pitch_id"), table_name="pitch_submissions")
    op.drop_table("pitch_submissions")
    op.drop_index("uq_pitches_active", table_name="pitches", postgresql_where=sa.text("active"))
    op.drop_index(op.f("ix_pitches_requester_party_id"), table_name="pitches")
    op.drop_index(op.f("ix_pitches_recipient_party_id"), table_name="pitches")
    op.drop_table("pitches")
