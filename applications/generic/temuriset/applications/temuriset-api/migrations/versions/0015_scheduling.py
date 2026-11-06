"""Schedule proposals, slots, meetings, bookings with a per-party exclusion constraint, outcomes (spec 028).

Revision ID: 0015
Revises: 0014
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0015"
down_revision: str | None = "0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # The exclusion constraint compares party_id with = inside a GiST index.
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
    op.create_table(
        "meetings",
        sa.Column("pitch_id", sa.Uuid(), nullable=False),
        sa.Column("proposal_id", sa.Uuid(), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("time_zone", sa.String(length=64), nullable=False),
        sa.Column("agenda", sa.String(length=1000), nullable=False),
        sa.Column("link", sa.String(length=500), nullable=True),
        sa.Column("state", sa.String(length=24), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("state IN ('CONFIRMED', 'COMPLETED', 'CANCELLED', 'NO_SHOW_REPORTED')", name="state"),
        sa.ForeignKeyConstraint(["pitch_id"], ["pitches.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_meetings_pitch_id"), "meetings", ["pitch_id"], unique=False)
    op.create_table(
        "schedule_proposals",
        sa.Column("pitch_id", sa.Uuid(), nullable=False),
        sa.Column("proposed_by_party_id", sa.Uuid(), nullable=False),
        sa.Column("proposed_by_account_id", sa.Uuid(), nullable=False),
        sa.Column("minutes", sa.Integer(), nullable=False),
        sa.Column("time_zone", sa.String(length=64), nullable=False),
        sa.Column("agenda", sa.String(length=1000), nullable=False),
        sa.Column("link", sa.String(length=500), nullable=True),
        sa.Column("state", sa.String(length=16), nullable=False),
        sa.Column("expired_reason", sa.String(length=16), nullable=True),
        sa.Column("replaces_meeting_id", sa.Uuid(), nullable=True),
        sa.Column("accepted_slot_id", sa.Uuid(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("expired_reason IS NULL OR expired_reason IN ('AGE', 'ALL_PAST')", name="expired_reason"),
        sa.CheckConstraint("state IN ('OPEN', 'ACCEPTED', 'SUPERSEDED', 'EXPIRED', 'CANCELLED')", name="state"),
        sa.CheckConstraint("minutes IN (30, 60)", name="minutes"),
        sa.ForeignKeyConstraint(["pitch_id"], ["pitches.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_schedule_proposals_pitch_id"), "schedule_proposals", ["pitch_id"], unique=False)
    op.create_table(
        "bookings",
        sa.Column("party_id", sa.Uuid(), nullable=False),
        sa.Column("meeting_id", sa.Uuid(), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("during", postgresql.TSTZRANGE(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        postgresql.ExcludeConstraint(
            (sa.column("party_id"), "="), (sa.column("during"), "&&"), using="gist", name="ex_bookings_party_during"
        ),
        sa.ForeignKeyConstraint(["meeting_id"], ["meetings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["party_id"], ["parties.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_bookings_meeting_id"), "bookings", ["meeting_id"], unique=False)
    op.create_index(op.f("ix_bookings_party_id"), "bookings", ["party_id"], unique=False)
    op.create_table(
        "meeting_outcomes",
        sa.Column("meeting_id", sa.Uuid(), nullable=False),
        sa.Column("party_id", sa.Uuid(), nullable=False),
        sa.Column("result", sa.String(length=16), nullable=False),
        sa.Column("note", sa.String(length=1000), nullable=False),
        sa.Column("recorded_by_account_id", sa.Uuid(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("result IN ('COMPLETED', 'NO_SHOW')", name="result"),
        sa.ForeignKeyConstraint(["meeting_id"], ["meetings.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("meeting_id", "party_id"),
    )
    op.create_index(op.f("ix_meeting_outcomes_meeting_id"), "meeting_outcomes", ["meeting_id"], unique=False)
    op.create_table(
        "schedule_slots",
        sa.Column("proposal_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["proposal_id"], ["schedule_proposals.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("proposal_id", "position"),
    )
    op.create_index(op.f("ix_schedule_slots_proposal_id"), "schedule_slots", ["proposal_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_schedule_slots_proposal_id"), table_name="schedule_slots")
    op.drop_table("schedule_slots")
    op.drop_index(op.f("ix_meeting_outcomes_meeting_id"), table_name="meeting_outcomes")
    op.drop_table("meeting_outcomes")
    op.drop_index(op.f("ix_bookings_party_id"), table_name="bookings")
    op.drop_index(op.f("ix_bookings_meeting_id"), table_name="bookings")
    op.drop_table("bookings")
    op.drop_index(op.f("ix_schedule_proposals_pitch_id"), table_name="schedule_proposals")
    op.drop_table("schedule_proposals")
    op.drop_index(op.f("ix_meetings_pitch_id"), table_name="meetings")
    op.drop_table("meetings")
