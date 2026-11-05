"""Partner intake: profiles, opportunities, versions, typed requirements and external handoffs (spec 016).

Revision ID: 0008
Revises: 0007
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "partner_profiles",
        sa.Column("party_id", sa.Uuid(), nullable=False),
        sa.Column("subtype", sa.String(length=120), nullable=False),
        sa.Column("thesis", sa.Text(), nullable=False),
        sa.Column("sectors", postgresql.ARRAY(sa.String(length=120)), nullable=False),
        sa.Column("stages", postgresql.ARRAY(sa.String(length=16)), nullable=False),
        sa.Column("regions", postgresql.ARRAY(sa.String(length=120)), nullable=False),
        sa.Column("support_forms", postgresql.ARRAY(sa.String(length=120)), nullable=False),
        sa.Column("relationship_forms", postgresql.ARRAY(sa.String(length=16)), nullable=False),
        sa.Column("review_expectations", sa.Text(), nullable=False),
        sa.Column("check_min", sa.Numeric(precision=20, scale=4), nullable=True),
        sa.Column("check_max", sa.Numeric(precision=20, scale=4), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=True),
        sa.Column("range_subject", sa.String(length=16), nullable=True),
        sa.Column("range_basis", sa.String(length=16), nullable=True),
        sa.Column("range_period", sa.String(length=80), nullable=False),
        sa.Column("range_months", sa.Integer(), nullable=True),
        sa.Column("unknown_reason", sa.String(length=32), nullable=True),
        sa.Column("intake_status", sa.String(length=16), nullable=False),
        sa.Column("intake_from", sa.Date(), nullable=True),
        sa.Column("intake_until", sa.Date(), nullable=True),
        sa.Column("source", sa.String(length=16), nullable=False),
        sa.Column("contact_route", sa.String(length=16), nullable=False),
        sa.Column("external_url", sa.String(length=2048), nullable=True),
        sa.Column("general_intake_version_id", sa.Uuid(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("check_max >= check_min", name="check_max_not_below_min"),
        sa.CheckConstraint("check_min >= 0", name="check_min_not_negative"),
        sa.CheckConstraint("contact_route <> 'EXTERNAL' OR external_url IS NOT NULL", name="external_needs_url"),
        sa.CheckConstraint("contact_route IN ('IN_APP', 'EXTERNAL', 'NONE')", name="contact_route"),
        sa.CheckConstraint("intake_status IN ('OPEN', 'CLOSED', 'UNCONFIRMED')", name="intake_status"),
        sa.CheckConstraint(
            "range_basis IN ('total_period', 'monthly', 'yearly', 'per_investment')", name="range_basis"
        ),
        sa.CheckConstraint("range_subject IN ('partner', 'investorCheck', 'license')", name="range_subject"),
        sa.CheckConstraint("source IN ('OWNER_CONFIRMED', 'SOURCE_REPORTED')", name="source"),
        sa.ForeignKeyConstraint(["party_id"], ["parties.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("party_id"),
    )
    op.create_table(
        "opportunities",
        sa.Column("partner_party_id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("current_version_id", sa.Uuid(), nullable=True),
        sa.Column("closes_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("kind IN ('SPECIFIC', 'GENERAL_INTAKE')", name="kind"),
        sa.CheckConstraint("status IN ('DRAFT', 'ACTIVE', 'PAUSED', 'CLOSED', 'EXPIRED')", name="status"),
        sa.ForeignKeyConstraint(["partner_party_id"], ["parties.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_opportunities_partner_party_id"), "opportunities", ["partner_party_id"], unique=False)
    op.create_index(
        "uq_opportunities_open_general_intake",
        "opportunities",
        ["partner_party_id"],
        unique=True,
        postgresql_where=sa.text("kind = 'GENERAL_INTAKE' AND status NOT IN ('CLOSED', 'EXPIRED')"),
    )
    op.create_table(
        "opportunity_versions",
        sa.Column("opportunity_id", sa.Uuid(), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("outcome", sa.Text(), nullable=False),
        sa.Column("included", sa.Text(), nullable=False),
        sa.Column("excluded", sa.Text(), nullable=False),
        sa.Column("support", sa.Text(), nullable=False),
        sa.Column("accepted_stages", postgresql.ARRAY(sa.String(length=16)), nullable=False),
        sa.Column("relationship_forms", postgresql.ARRAY(sa.String(length=16)), nullable=False),
        sa.Column("sectors", postgresql.ARRAY(sa.String(length=120)), nullable=False),
        sa.Column("keywords", postgresql.ARRAY(sa.String(length=120)), nullable=False),
        sa.Column("financial", postgresql.JSONB(none_as_null=True, astext_type=sa.Text()), nullable=True),
        sa.Column("timing", sa.Text(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("opportunity_id", "number"),
    )
    op.create_index(
        op.f("ix_opportunity_versions_opportunity_id"), "opportunity_versions", ["opportunity_id"], unique=False
    )
    op.create_foreign_key(
        "fk_opportunities_current_version",
        "opportunities",
        "opportunity_versions",
        ["current_version_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_partner_profiles_general_intake_version",
        "partner_profiles",
        "opportunity_versions",
        ["general_intake_version_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_table(
        "requirements",
        sa.Column("opportunity_version_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(length=160), nullable=False),
        sa.Column("field", sa.String(length=80), nullable=False),
        sa.Column("operator", sa.String(length=16), nullable=False),
        sa.Column("value", postgresql.JSONB(none_as_null=True, astext_type=sa.Text()), nullable=True),
        sa.Column("mandatory", sa.Boolean(), nullable=False),
        sa.Column("applies_at", sa.String(length=20), nullable=False),
        sa.Column("verification_mode", sa.String(length=20), nullable=False),
        sa.Column("visibility", sa.String(length=16), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("NOT mandatory OR visibility = 'PUBLIC'", name="no_secret_mandatory"),
        sa.CheckConstraint(
            "applies_at IN ('SUBMISSION', 'DISCUSSION', 'PILOT', 'COMMERCIALIZATION')", name="applies_at"
        ),
        sa.CheckConstraint(
            "operator IN ('equals', 'in_set', 'intersects', 'minimum', 'maximum', 'range_overlap', 'exists', "
            "'manual_review')",
            name="operator",
        ),
        sa.CheckConstraint(
            "verification_mode IN ('DECLARATION', 'DOCUMENT_PRESENT', 'REVIEWER_CONFIRMED')", name="verification_mode"
        ),
        sa.CheckConstraint("visibility IN ('PUBLIC', 'PARTNER_ONLY')", name="visibility"),
        sa.ForeignKeyConstraint(["opportunity_version_id"], ["opportunity_versions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_requirements_opportunity_version_id"), "requirements", ["opportunity_version_id"], unique=False
    )
    op.create_table(
        "external_handoffs",
        sa.Column("partner_party_id", sa.Uuid(), nullable=False),
        sa.Column("actor_party_id", sa.Uuid(), nullable=False),
        sa.Column("external_url", sa.String(length=2048), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["actor_party_id"], ["parties.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["partner_party_id"], ["parties.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_external_handoffs_actor_party_id"), "external_handoffs", ["actor_party_id"], unique=False)
    op.create_index(
        op.f("ix_external_handoffs_partner_party_id"), "external_handoffs", ["partner_party_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_external_handoffs_partner_party_id"), table_name="external_handoffs")
    op.drop_index(op.f("ix_external_handoffs_actor_party_id"), table_name="external_handoffs")
    op.drop_table("external_handoffs")
    op.drop_index(op.f("ix_requirements_opportunity_version_id"), table_name="requirements")
    op.drop_table("requirements")
    op.drop_constraint("fk_partner_profiles_general_intake_version", "partner_profiles", type_="foreignkey")
    op.drop_constraint("fk_opportunities_current_version", "opportunities", type_="foreignkey")
    op.drop_index(op.f("ix_opportunity_versions_opportunity_id"), table_name="opportunity_versions")
    op.drop_table("opportunity_versions")
    op.drop_index(
        "uq_opportunities_open_general_intake",
        table_name="opportunities",
        postgresql_where=sa.text("kind = 'GENERAL_INTAKE' AND status NOT IN ('CLOSED', 'EXPIRED')"),
    )
    op.drop_index(op.f("ix_opportunities_partner_party_id"), table_name="opportunities")
    op.drop_table("opportunities")
    op.drop_table("partner_profiles")
