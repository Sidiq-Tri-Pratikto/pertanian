"""HTML body storage for development mailbox and one-click unsubscribe links (spec 060).

``mailbox_messages.html`` is a nullable text column with no table constraint, and ``unsubscribe_links`` is a new table
so existing API and worker instances keep working while both versions run.

Revision ID: 0027
Revises: 0026
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0027"
down_revision: str | None = "0026"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("mailbox_messages", sa.Column("html", sa.Text(), nullable=True))
    op.create_table(
        "unsubscribe_links",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("target_id", sa.Uuid(), nullable=False),
        sa.Column("token_sha256", sa.String(64), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("kind IN ('subscription', 'follow')", name="ck_unsubscribe_links_kind"),
    )
    op.create_index("ix_unsubscribe_links_target_id", "unsubscribe_links", ["target_id"])


def downgrade() -> None:
    op.drop_index("ix_unsubscribe_links_target_id", table_name="unsubscribe_links")
    op.drop_table("unsubscribe_links")
    op.drop_column("mailbox_messages", "html")
