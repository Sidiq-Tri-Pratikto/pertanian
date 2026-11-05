"""Partner profiles, opportunities, their versions, typed requirements and external handoffs."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, Numeric, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, MutableRow, Row

MONEY = Numeric(20, 4)


class PartnerProfileRecord(MutableRow, Base):
    """What a party states as a partner. One per party; unknown money is null with a reason."""

    __tablename__ = "partner_profiles"
    __table_args__ = (
        CheckConstraint("intake_status IN ('OPEN', 'CLOSED', 'UNCONFIRMED')", name="intake_status"),
        CheckConstraint("source IN ('OWNER_CONFIRMED', 'SOURCE_REPORTED')", name="source"),
        CheckConstraint("contact_route IN ('IN_APP', 'EXTERNAL', 'NONE')", name="contact_route"),
        CheckConstraint("contact_route <> 'EXTERNAL' OR external_url IS NOT NULL", name="external_needs_url"),
        CheckConstraint("check_min >= 0", name="check_min_not_negative"),
        CheckConstraint("check_max >= check_min", name="check_max_not_below_min"),
        CheckConstraint("range_subject IN ('partner', 'investorCheck', 'license')", name="range_subject"),
        CheckConstraint("range_basis IN ('total_period', 'monthly', 'yearly', 'per_investment')", name="range_basis"),
    )

    party_id: Mapped[UUID] = mapped_column(ForeignKey("parties.id", ondelete="RESTRICT"), unique=True)
    subtype: Mapped[str] = mapped_column(String(120), default="")
    thesis: Mapped[str] = mapped_column(Text, default="")
    sectors: Mapped[list[str]] = mapped_column(ARRAY(String(120)), default=list)
    stages: Mapped[list[str]] = mapped_column(ARRAY(String(16)), default=list)
    regions: Mapped[list[str]] = mapped_column(ARRAY(String(120)), default=list)
    support_forms: Mapped[list[str]] = mapped_column(ARRAY(String(120)), default=list)
    relationship_forms: Mapped[list[str]] = mapped_column(ARRAY(String(16)), default=list)
    review_expectations: Mapped[str] = mapped_column(Text, default="")
    check_min: Mapped[Decimal | None] = mapped_column(MONEY)
    check_max: Mapped[Decimal | None] = mapped_column(MONEY)
    currency: Mapped[str | None] = mapped_column(String(3))
    range_subject: Mapped[str | None] = mapped_column(String(16))
    range_basis: Mapped[str | None] = mapped_column(String(16))
    range_period: Mapped[str] = mapped_column(String(80), default="")
    range_months: Mapped[int | None]
    unknown_reason: Mapped[str | None] = mapped_column(String(32))
    intake_status: Mapped[str] = mapped_column(String(16), default="OPEN")
    intake_from: Mapped[date | None]
    intake_until: Mapped[date | None]
    source: Mapped[str] = mapped_column(String(16), default="OWNER_CONFIRMED")
    contact_route: Mapped[str] = mapped_column(String(16), default="IN_APP")
    external_url: Mapped[str | None] = mapped_column(String(2048))
    general_intake_version_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(
            "opportunity_versions.id",
            ondelete="SET NULL",
            use_alter=True,
            name="fk_partner_profiles_general_intake_version",
        )
    )


class OpportunityRecord(MutableRow, Base):
    """A partner's mandate. ``current_version_id`` names the content others read."""

    __tablename__ = "opportunities"
    __table_args__ = (
        CheckConstraint("kind IN ('SPECIFIC', 'GENERAL_INTAKE')", name="kind"),
        CheckConstraint("status IN ('DRAFT', 'ACTIVE', 'PAUSED', 'CLOSED', 'EXPIRED')", name="status"),
        Index(
            "uq_opportunities_open_general_intake",
            "partner_party_id",
            unique=True,
            postgresql_where=text("kind = 'GENERAL_INTAKE' AND status NOT IN ('CLOSED', 'EXPIRED')"),
        ),
    )

    partner_party_id: Mapped[UUID] = mapped_column(ForeignKey("parties.id", ondelete="RESTRICT"), index=True)
    kind: Mapped[str] = mapped_column(String(16), default="SPECIFIC")
    status: Mapped[str] = mapped_column(String(16), default="DRAFT")
    current_version_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(
            "opportunity_versions.id",
            ondelete="RESTRICT",
            use_alter=True,
            name="fk_opportunities_current_version",
        )
    )
    closes_at: Mapped[datetime | None]


class OpportunityVersionRecord(Row, Base):
    """One opportunity's content at one number. Frozen once the opportunity has gone live."""

    __tablename__ = "opportunity_versions"
    __table_args__ = (UniqueConstraint("opportunity_id", "number"),)

    opportunity_id: Mapped[UUID] = mapped_column(ForeignKey("opportunities.id", ondelete="CASCADE"), index=True)
    number: Mapped[int]
    title: Mapped[str] = mapped_column(String(200), default="")
    outcome: Mapped[str] = mapped_column(Text, default="")
    included: Mapped[str] = mapped_column(Text, default="")
    excluded: Mapped[str] = mapped_column(Text, default="")
    support: Mapped[str] = mapped_column(Text, default="")
    accepted_stages: Mapped[list[str]] = mapped_column(ARRAY(String(16)), default=list)
    relationship_forms: Mapped[list[str]] = mapped_column(ARRAY(String(16)), default=list)
    sectors: Mapped[list[str]] = mapped_column(ARRAY(String(120)), default=list)
    keywords: Mapped[list[str]] = mapped_column(ARRAY(String(120)), default=list)
    financial: Mapped[dict[str, Any] | None] = mapped_column(JSONB(none_as_null=True))
    timing: Mapped[str] = mapped_column(Text, default="")


class RequirementRecord(Row, Base):
    """One typed requirement of one opportunity version."""

    __tablename__ = "requirements"
    __table_args__ = (
        CheckConstraint(
            "operator IN ('equals', 'in_set', 'intersects', 'minimum', 'maximum', 'range_overlap', 'exists', "
            "'manual_review')",
            name="operator",
        ),
        CheckConstraint("applies_at IN ('SUBMISSION', 'DISCUSSION', 'PILOT', 'COMMERCIALIZATION')", name="applies_at"),
        CheckConstraint(
            "verification_mode IN ('DECLARATION', 'DOCUMENT_PRESENT', 'REVIEWER_CONFIRMED')", name="verification_mode"
        ),
        CheckConstraint("visibility IN ('PUBLIC', 'PARTNER_ONLY')", name="visibility"),
        CheckConstraint("NOT mandatory OR visibility = 'PUBLIC'", name="no_secret_mandatory"),
    )

    opportunity_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("opportunity_versions.id", ondelete="CASCADE"), index=True
    )
    position: Mapped[int]
    label: Mapped[str] = mapped_column(String(160))
    field: Mapped[str] = mapped_column(String(80))
    operator: Mapped[str] = mapped_column(String(16))
    value: Mapped[Any] = mapped_column(JSONB(none_as_null=True), nullable=True)
    mandatory: Mapped[bool] = mapped_column(default=True)
    applies_at: Mapped[str] = mapped_column(String(20))
    verification_mode: Mapped[str] = mapped_column(String(20))
    visibility: Mapped[str] = mapped_column(String(16), default="PUBLIC")
    reason: Mapped[str] = mapped_column(Text, default="")


class ExternalHandoffRecord(Row, Base):
    """Someone followed a partner's external route. Append-only, with the URL as it was followed; never a pitch."""

    __tablename__ = "external_handoffs"

    partner_party_id: Mapped[UUID] = mapped_column(ForeignKey("parties.id", ondelete="RESTRICT"), index=True)
    actor_party_id: Mapped[UUID] = mapped_column(ForeignKey("parties.id", ondelete="RESTRICT"), index=True)
    external_url: Mapped[str] = mapped_column(String(2048))
