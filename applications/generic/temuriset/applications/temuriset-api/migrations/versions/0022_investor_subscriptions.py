"""Investor quick subscriptions, links, deliveries, request counts; the invention digest switch (spec 046).

Revision ID: 0022
Revises: 0021
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0022"
down_revision: str | None = "0021"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "investor_subscriptions",
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("topics", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("locale", sa.String(length=8), nullable=False),
        sa.Column("consent_source", sa.String(length=32), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("unsubscribed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("status IN ('PENDING', 'ACTIVE', 'UNSUBSCRIBED')", name="status"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_table(
        "subscription_requests",
        sa.Column("email_sha256", sa.String(length=64), nullable=False),
        sa.Column("address_sha256", sa.String(length=64), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_subscription_requests_address", "subscription_requests", ["address_sha256", "created_at"], unique=False
    )
    op.create_index(
        "ix_subscription_requests_email", "subscription_requests", ["email_sha256", "created_at"], unique=False
    )
    op.create_table(
        "subscription_links",
        sa.Column("subscription_id", sa.Uuid(), nullable=False),
        sa.Column("purpose", sa.String(length=8), nullable=False),
        sa.Column("token_sha256", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("purpose IN ('confirm', 'manage')", name="purpose"),
        sa.ForeignKeyConstraint(["subscription_id"], ["investor_subscriptions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_sha256"),
    )
    op.create_index(
        op.f("ix_subscription_links_subscription_id"), "subscription_links", ["subscription_id"], unique=False
    )
    op.create_table(
        "subscription_deliveries",
        sa.Column("subscription_id", sa.Uuid(), nullable=False),
        sa.Column("invention_id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.String(length=8), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("kind IN ('ALERT', 'DIGEST')", name="kind"),
        sa.ForeignKeyConstraint(["invention_id"], ["inventions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["subscription_id"], ["investor_subscriptions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("subscription_id", "invention_id"),
    )
    op.create_index(
        "ix_subscription_deliveries_alerts",
        "subscription_deliveries",
        ["subscription_id", "kind", "created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_subscription_deliveries_invention_id"), "subscription_deliveries", ["invention_id"], unique=False
    )
    op.add_column("inventions", sa.Column("investor_digest", sa.Boolean(), server_default="false", nullable=False))
    op.add_column("inventions", sa.Column("investor_digest_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("inventions", "investor_digest_at")
    op.drop_column("inventions", "investor_digest")
    op.drop_index(op.f("ix_subscription_deliveries_invention_id"), table_name="subscription_deliveries")
    op.drop_index("ix_subscription_deliveries_alerts", table_name="subscription_deliveries")
    op.drop_table("subscription_deliveries")
    op.drop_index(op.f("ix_subscription_links_subscription_id"), table_name="subscription_links")
    op.drop_table("subscription_links")
    op.drop_index("ix_subscription_requests_email", table_name="subscription_requests")
    op.drop_index("ix_subscription_requests_address", table_name="subscription_requests")
    op.drop_table("subscription_requests")
    op.drop_table("investor_subscriptions")
