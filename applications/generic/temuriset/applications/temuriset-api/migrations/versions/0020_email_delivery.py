"""Version the email notification preference and add expiring, deduplicated job input."""

import sqlalchemy as sa
from alembic import op

revision: str = "0020"
down_revision: str | None = "0019"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade() -> None:
    """Add an off-by-default preference and optional job delivery metadata."""
    op.add_column("accounts", sa.Column("email_notifications", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("jobs", sa.Column("input_expires_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("jobs", sa.Column("dedupe_key", sa.String(64), nullable=True))
    op.create_index("uq_jobs_dedupe_key", "jobs", ["dedupe_key"], unique=True)


def downgrade() -> None:
    """Remove the preference and job delivery metadata."""
    # Earlier workers cannot consume or scrub email jobs.
    op.execute("DELETE FROM jobs WHERE kind IN ('email.secret_delivery', 'email.notification_delivery')")
    op.drop_index("uq_jobs_dedupe_key", table_name="jobs")
    op.drop_column("jobs", "dedupe_key")
    op.drop_column("jobs", "input_expires_at")
    op.drop_column("accounts", "email_notifications")
