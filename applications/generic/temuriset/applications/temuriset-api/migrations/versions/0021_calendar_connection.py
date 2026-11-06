"""Versioned, account-owned calendar connection and pending OAuth state.

Revision ID: 0021
Revises: 0020
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0021"
down_revision: str | None = "0020"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the private calendar state and ciphertext storage."""
    op.create_table(
        "calendar_connections",
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), server_default="0", nullable=False),
        sa.Column("provider_revocation_confirmed", sa.Boolean(), nullable=True),
        sa.Column("encrypted_token", sa.LargeBinary(), nullable=True),
        sa.Column("token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("state_sha256", sa.String(64), nullable=True),
        sa.Column("encrypted_verifier", sa.LargeBinary(), nullable=True),
        sa.Column("state_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("state_session_id", sa.Uuid(), nullable=True),
        sa.PrimaryKeyConstraint("account_id"),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.CheckConstraint("(encrypted_token IS NULL) = (token_expires_at IS NULL)", name="token_pair"),
        sa.CheckConstraint(
            "(state_sha256 IS NULL) = (encrypted_verifier IS NULL) AND "
            "(state_sha256 IS NULL OR state_expires_at IS NOT NULL) AND "
            "(state_expires_at IS NULL) = (state_session_id IS NULL)",
            name="state_group",
        ),
    )


def downgrade() -> None:
    """Remove the local adapter's state."""
    op.drop_table("calendar_connections")
