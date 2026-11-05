"""Support requests, their versions, project budgets and budget lines."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, MutableRow, Row

MONEY = Numeric(20, 4)


class SupportRequestRecord(MutableRow, Base):
    """What support an invention needs for one outcome."""

    __tablename__ = "support_requests"
    __table_args__ = (
        CheckConstraint("relationship_form IN ('PROJECT', 'LICENSE')", name="relationship_form"),
        CheckConstraint("status IN ('DRAFT', 'ACTIVE', 'PAUSED', 'CLOSED', 'EXPIRED')", name="status"),
    )

    invention_id: Mapped[UUID] = mapped_column(ForeignKey("inventions.id", ondelete="RESTRICT"), index=True)
    owner_party_id: Mapped[UUID] = mapped_column(ForeignKey("parties.id", ondelete="RESTRICT"), index=True)
    invention_version_id: Mapped[UUID] = mapped_column(ForeignKey("invention_versions.id", ondelete="RESTRICT"))
    outcome: Mapped[str] = mapped_column(String(200), default="")
    support_forms: Mapped[list[str]] = mapped_column(ARRAY(String(40)), default=list)
    relationship_form: Mapped[str] = mapped_column(String(16), default="PROJECT")
    scope: Mapped[str] = mapped_column(Text, default="")
    months: Mapped[int | None]
    region: Mapped[str] = mapped_column(String(120), default="")
    accepts_partial: Mapped[bool] = mapped_column(default=False)
    accepts_noncash: Mapped[bool] = mapped_column(default=False)
    noncash_description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(16), default="DRAFT")
    expires_at: Mapped[datetime | None]


class SupportRequestVersionRecord(Row, Base):
    """The request as it stood at one version; a sent submission keeps pointing here."""

    __tablename__ = "support_request_versions"
    __table_args__ = (UniqueConstraint("support_request_id", "number"),)

    support_request_id: Mapped[UUID] = mapped_column(ForeignKey("support_requests.id", ondelete="CASCADE"), index=True)
    number: Mapped[int]
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB)


class ProjectBudgetRecord(Row, Base):
    """The cost range of one request version. Unknown money is null with a reason, never zero."""

    __tablename__ = "project_budgets"
    __table_args__ = (
        UniqueConstraint("support_request_id", "version"),
        CheckConstraint("min_amount >= 0", name="min_not_negative"),
        CheckConstraint("max_amount >= min_amount", name="max_not_below_min"),
        CheckConstraint("basis IN ('total_period', 'monthly', 'yearly')", name="basis"),
        CheckConstraint(
            "(min_amount IS NULL AND max_amount IS NULL AND unknown_reason IS NOT NULL) OR "
            "(min_amount IS NOT NULL AND max_amount IS NOT NULL AND currency IS NOT NULL)",
            name="known_or_explained",
        ),
    )

    support_request_id: Mapped[UUID] = mapped_column(ForeignKey("support_requests.id", ondelete="CASCADE"), index=True)
    version: Mapped[int]
    min_amount: Mapped[Decimal | None] = mapped_column(MONEY)
    max_amount: Mapped[Decimal | None] = mapped_column(MONEY)
    currency: Mapped[str | None] = mapped_column(String(3))
    basis: Mapped[str] = mapped_column(String(16), default="total_period")
    period: Mapped[str] = mapped_column(String(80), default="")
    scope: Mapped[str] = mapped_column(Text, default="")
    estimated_on: Mapped[date | None]
    assumptions: Mapped[str] = mapped_column(Text, default="")
    unknown_reason: Mapped[str | None] = mapped_column(String(32))
    financial: Mapped[bool] = mapped_column(default=True)
    lines_explanation: Mapped[str] = mapped_column(Text, default="")


class ProjectBudgetLineRecord(Row, Base):
    """One cost line; its total is quantity times unit cost, in decimal."""

    __tablename__ = "project_budget_lines"

    budget_id: Mapped[UUID] = mapped_column(ForeignKey("project_budgets.id", ondelete="CASCADE"), index=True)
    position: Mapped[int]
    label: Mapped[str] = mapped_column(String(160))
    quantity: Mapped[Decimal] = mapped_column(MONEY)
    unit_cost: Mapped[Decimal] = mapped_column(MONEY)
    explanation: Mapped[str] = mapped_column(Text, default="")
