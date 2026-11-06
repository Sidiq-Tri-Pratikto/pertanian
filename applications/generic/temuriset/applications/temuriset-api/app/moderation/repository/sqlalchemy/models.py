"""Private reports, what operators did, suspended listings, privacy requests and the retention policy."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Identity, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, MutableRow, Row


class ReportRecord(MutableRow, Base):
    """A private case. The reporter sees its status only, and nothing here touches public reputation."""

    __tablename__ = "reports"
    __table_args__ = (
        CheckConstraint(
            "category IN ('IMPERSONATION', 'UNSUPPORTED_CLAIM', 'UNWANTED_CONTACT', 'ABUSE', 'OTHER')", name="category"
        ),
        CheckConstraint(
            "subject_type IN ('INVENTION', 'OPPORTUNITY', 'PARTNER_PROFILE', 'FUNDING_REQUEST', 'SUPPORT_REQUEST', "
            "'PITCH', 'MESSAGE', 'OTHER')",
            name="subject_type",
        ),
        CheckConstraint("status IN ('RECEIVED', 'IN_REVIEW', 'RESOLVED', 'DISMISSED')", name="status"),
    )

    case_number: Mapped[int] = mapped_column(BigInteger, Identity(), unique=True)
    reporter_account_id: Mapped[UUID] = mapped_column(ForeignKey("accounts.id", ondelete="RESTRICT"), index=True)
    reporter_party_id: Mapped[UUID] = mapped_column(ForeignKey("parties.id", ondelete="RESTRICT"))
    category: Mapped[str] = mapped_column(String(24))
    subject_type: Mapped[str] = mapped_column(String(24))
    # Never checked on report, so reporting cannot be used to probe for private objects.
    subject_id: Mapped[UUID | None]
    subject_label: Mapped[str] = mapped_column(String(200))
    reason: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), default="RECEIVED", index=True)


class OperatorActionRecord(Row, Base):
    """One thing an operator did on a case, with why. Append-only."""

    __tablename__ = "operator_actions"

    report_id: Mapped[UUID] = mapped_column(ForeignKey("reports.id", ondelete="CASCADE"), index=True)
    operator_account_id: Mapped[UUID] = mapped_column(ForeignKey("accounts.id", ondelete="RESTRICT"))
    action: Mapped[str] = mapped_column(String(24))
    note: Mapped[str] = mapped_column(Text)


class OperatorGrantRecord(Row, Base):
    """A scoped capability held by one account. Being an operator is never a persona."""

    __tablename__ = "operator_grants"
    __table_args__ = (
        Index("uq_operator_grants_active", "account_id", "scope", unique=True, postgresql_where="revoked_at IS NULL"),
    )

    account_id: Mapped[UUID] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"), index=True)
    scope: Mapped[str] = mapped_column(String(32))
    revoked_at: Mapped[datetime | None]


class OperatorFileGrantRecord(Row, Base):
    """A documented reason for one operator to open one file version on one case, until it expires."""

    __tablename__ = "operator_file_grants"

    report_id: Mapped[UUID] = mapped_column(ForeignKey("reports.id", ondelete="CASCADE"), index=True)
    document_version_id: Mapped[UUID] = mapped_column(ForeignKey("document_versions.id", ondelete="CASCADE"))
    operator_account_id: Mapped[UUID] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"))
    purpose: Mapped[str] = mapped_column(Text)
    granted_by: Mapped[str] = mapped_column(String(254))
    expires_at: Mapped[datetime]


class ListingSuspensionRecord(Row, Base):
    """A listing an operator suspended, until it is lifted."""

    __tablename__ = "listing_suspensions"
    __table_args__ = (
        CheckConstraint("subject_type IN ('INVENTION', 'OPPORTUNITY', 'PARTNER_PROFILE')", name="subject_type"),
        Index(
            "uq_listing_suspensions_active",
            "subject_type",
            "subject_id",
            unique=True,
            postgresql_where="lifted_at IS NULL",
        ),
    )

    subject_type: Mapped[str] = mapped_column(String(24))
    subject_id: Mapped[UUID]
    report_id: Mapped[UUID] = mapped_column(ForeignKey("reports.id", ondelete="RESTRICT"), index=True)
    suspended_by_account_id: Mapped[UUID] = mapped_column(ForeignKey("accounts.id", ondelete="RESTRICT"))
    lifted_at: Mapped[datetime | None]


class RetentionPolicyRecord(Row, Base):
    """One category of data and what a deletion request does to it. The answer is generated from these rows."""

    __tablename__ = "retention_policies"
    __table_args__ = (CheckConstraint("decision IN ('REMOVE', 'RETAIN')", name="decision"),)

    key: Mapped[str] = mapped_column(String(32), unique=True)
    position: Mapped[int]
    label: Mapped[str] = mapped_column(String(200))
    decision: Mapped[str] = mapped_column(String(8))
    reason: Mapped[str] = mapped_column(Text, default="")
    period: Mapped[str] = mapped_column(String(200), default="")
    policy_version: Mapped[str] = mapped_column(String(32))


class RetentionHoldRecord(Row, Base):
    """An administrative audit hold for one account and one retention category."""

    __tablename__ = "retention_holds"

    account_id: Mapped[UUID] = mapped_column(ForeignKey("accounts.id", ondelete="RESTRICT"), index=True)
    category_key: Mapped[str] = mapped_column(ForeignKey("retention_policies.key", ondelete="RESTRICT"))
    reason: Mapped[str] = mapped_column(Text)
    period: Mapped[str] = mapped_column(String(200))
    released_at: Mapped[datetime | None]


class PrivacyRequestRecord(MutableRow, Base):
    """A person's export or deletion request, with the answer generated when it was made."""

    __tablename__ = "privacy_requests"
    __table_args__ = (
        CheckConstraint("kind IN ('EXPORT', 'DELETION')", name="kind"),
        CheckConstraint("status IN ('RECEIVED', 'PROCESSING', 'FULFILLED')", name="status"),
        Index(
            "uq_privacy_requests_open_deletion",
            "account_id",
            unique=True,
            postgresql_where="kind = 'DELETION' AND status IN ('RECEIVED', 'PROCESSING')",
        ),
    )

    account_id: Mapped[UUID] = mapped_column(ForeignKey("accounts.id", ondelete="RESTRICT"), index=True)
    kind: Mapped[str] = mapped_column(String(8))
    status: Mapped[str] = mapped_column(String(16), default="RECEIVED", index=True)
    answer: Mapped[dict[str, Any]] = mapped_column(JSONB)
    policy_version: Mapped[str | None] = mapped_column(String(32))
    fulfilled_at: Mapped[datetime | None]
    fulfilled_by_account_id: Mapped[UUID | None] = mapped_column(ForeignKey("accounts.id", ondelete="RESTRICT"))
