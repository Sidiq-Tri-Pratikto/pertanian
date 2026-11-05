"""Access: organizations, organization parties, memberships and invitations (spec 007).

Revision ID: 0003
Revises: 0002
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("kind IN ('company', 'nonprofit', 'community', 'research_group', 'other')", name="kind"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "invitations",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("capabilities", postgresql.ARRAY(sa.String(length=32)), nullable=False),
        sa.Column("token_sha256", sa.String(length=64), nullable=False),
        sa.Column("invited_by_account_id", sa.Uuid(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["invited_by_account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_sha256"),
    )
    op.create_index(op.f("ix_invitations_organization_id"), "invitations", ["organization_id"], unique=False)
    op.create_table(
        "memberships",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("capabilities", postgresql.ARRAY(sa.String(length=32)), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("status IN ('active', 'removed')", name="status"),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_memberships_account_id"), "memberships", ["account_id"], unique=False)
    op.create_index(
        "uq_memberships_active",
        "memberships",
        ["organization_id", "account_id"],
        unique=True,
        postgresql_where="status = 'active'",
    )
    op.add_column("parties", sa.Column("organization_id", sa.Uuid(), nullable=True))
    op.create_unique_constraint("parties_organization_id_key", "parties", ["organization_id"])
    op.create_foreign_key(
        "parties_organization_id_fkey", "parties", "organizations", ["organization_id"], ["id"], ondelete="RESTRICT"
    )
    # A party is exactly one personal party or one organization party.
    op.drop_constraint("kind", "parties", type_="check")
    op.create_check_constraint(
        "kind",
        "parties",
        "(kind = 'personal' AND account_id IS NOT NULL AND organization_id IS NULL) OR "
        "(kind = 'organization' AND organization_id IS NOT NULL AND account_id IS NULL)",
    )


def downgrade() -> None:
    op.drop_constraint("kind", "parties", type_="check")
    op.create_check_constraint("kind", "parties", "kind = 'personal' AND account_id IS NOT NULL")
    op.drop_constraint("parties_organization_id_fkey", "parties", type_="foreignkey")
    op.drop_constraint("parties_organization_id_key", "parties", type_="unique")
    op.drop_column("parties", "organization_id")
    op.drop_index("uq_memberships_active", table_name="memberships", postgresql_where="status = 'active'")
    op.drop_index(op.f("ix_memberships_account_id"), table_name="memberships")
    op.drop_table("memberships")
    op.drop_index(op.f("ix_invitations_organization_id"), table_name="invitations")
    op.drop_table("invitations")
    op.drop_table("organizations")
