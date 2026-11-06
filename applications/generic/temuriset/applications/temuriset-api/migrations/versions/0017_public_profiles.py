"""Parties gain a biography and a published flag for public profiles (spec 031).

Revision ID: 0017
Revises: 0016
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0017"
down_revision: str | None = "0016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("parties", sa.Column("bio", sa.Text(), server_default="", nullable=False))
    op.add_column("parties", sa.Column("profile_published", sa.Boolean(), server_default="false", nullable=False))


def downgrade() -> None:
    op.drop_column("parties", "profile_published")
    op.drop_column("parties", "bio")
