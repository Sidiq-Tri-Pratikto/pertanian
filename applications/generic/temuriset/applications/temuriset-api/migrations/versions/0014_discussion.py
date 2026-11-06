"""Messages, tasks and in-app notifications (spec 027).

Revision ID: 0014
Revises: 0013
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0014"
down_revision: str | None = "0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "messages",
        sa.Column("pitch_id", sa.Uuid(), nullable=False),
        sa.Column("author_party_id", sa.Uuid(), nullable=False),
        sa.Column("author_account_id", sa.Uuid(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["pitch_id"], ["pitches.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_messages_pitch_created", "messages", ["pitch_id", "created_at"], unique=False)
    op.create_table(
        "notifications",
        sa.Column("party_id", sa.Uuid(), nullable=False),
        sa.Column("pitch_id", sa.Uuid(), nullable=True),
        sa.Column("event_key", sa.String(length=200), nullable=False),
        sa.Column("channel", sa.String(length=16), nullable=False),
        sa.Column("text", sa.String(length=300), nullable=False),
        sa.Column("tab", sa.String(length=16), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["party_id"], ["parties.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["pitch_id"], ["pitches.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_key", "party_id", "channel"),
    )
    op.create_index("ix_notifications_party_created", "notifications", ["party_id", "created_at"], unique=False)
    op.create_table(
        "tasks",
        sa.Column("pitch_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("owner_party_id", sa.Uuid(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("reference", sa.String(length=300), nullable=False),
        sa.Column("status", sa.String(length=8), nullable=False),
        sa.Column("created_by_party_id", sa.Uuid(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("status IN ('OPEN', 'DONE')", name="status"),
        sa.ForeignKeyConstraint(["pitch_id"], ["pitches.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tasks_pitch_id"), "tasks", ["pitch_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_tasks_pitch_id"), table_name="tasks")
    op.drop_table("tasks")
    op.drop_index("ix_notifications_party_created", table_name="notifications")
    op.drop_table("notifications")
    op.drop_index("ix_messages_pitch_created", table_name="messages")
    op.drop_table("messages")
