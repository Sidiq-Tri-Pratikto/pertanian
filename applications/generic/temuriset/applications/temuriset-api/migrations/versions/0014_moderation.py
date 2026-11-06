"""Moderation: reports, operators, suspended listings, privacy requests and the retention policy (spec 034).

Revision ID: 0014
Revises: 0013
"""

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0014"
down_revision: str | None = "0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

POLICY_VERSION = "retention-1"
PERIOD = "Periode final ditetapkan sebelum pilot"
# key, label, decision, reason, period
POLICY = [
    ("sign_in_records", "Kode masuk dan sesi", "REMOVE", "", ""),
    (
        "public_listings",
        "Daftar publik atas nama pribadi: inovasi, kebutuhan, pendanaan, profil mitra, dan mandat",
        "REMOVE",
        "",
        "",
    ),
    ("private_documents", "Isi berkas pribadi", "REMOVE", "", ""),
    ("account_profile", "Nama, email, dan keanggotaan organisasi", "REMOVE", "", ""),
    (
        "listing_history",
        "Riwayat versi inovasi, kebutuhan, dan mandat",
        "RETAIN",
        "Versi yang pernah terbit dapat menjadi rujukan kiriman dan keputusan pihak lain.",
        PERIOD,
    ),
    (
        "audit_events",
        "Catatan audit",
        "RETAIN",
        "Catatan ini tidak dapat diubah dan menjadi bukti siapa melakukan apa.",
        PERIOD,
    ),
    (
        "download_events",
        "Catatan unduhan",
        "RETAIN",
        "Catatan ini membuktikan salinan mana yang sudah keluar dari layanan.",
        PERIOD,
    ),
    (
        "reports",
        "Laporan yang Anda kirim atau yang menyangkut Anda",
        "RETAIN",
        "Kasus yang sudah dibuka perlu ditangani sampai selesai.",
        PERIOD,
    ),
    ("organization_data", "Data organisasi", "RETAIN", "Data ini milik organisasi, bukan milik satu anggota.", PERIOD),
    (
        "backups",
        "Cadangan layanan",
        "RETAIN",
        "Cadangan hanya terhapus saat masa simpannya berakhir.",
        "Sampai cadangan kedaluwarsa",
    ),
]


def upgrade() -> None:
    op.create_table(
        "reports",
        sa.Column("case_number", sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column("reporter_account_id", sa.Uuid(), nullable=False),
        sa.Column("reporter_party_id", sa.Uuid(), nullable=False),
        sa.Column("category", sa.String(length=24), nullable=False),
        sa.Column("subject_type", sa.String(length=24), nullable=False),
        sa.Column("subject_id", sa.Uuid(), nullable=True),
        sa.Column("subject_label", sa.String(length=200), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "category IN ('IMPERSONATION', 'UNSUPPORTED_CLAIM', 'UNWANTED_CONTACT', 'ABUSE', 'OTHER')", name="category"
        ),
        sa.CheckConstraint("status IN ('RECEIVED', 'IN_REVIEW', 'RESOLVED', 'DISMISSED')", name="status"),
        sa.CheckConstraint(
            "subject_type IN ('INVENTION', 'OPPORTUNITY', 'PARTNER_PROFILE', 'FUNDING_REQUEST', 'SUPPORT_REQUEST', "
            "'PITCH', 'MESSAGE', 'OTHER')",
            name="subject_type",
        ),
        sa.ForeignKeyConstraint(["reporter_account_id"], ["accounts.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["reporter_party_id"], ["parties.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("case_number"),
    )
    op.create_index(op.f("ix_reports_reporter_account_id"), "reports", ["reporter_account_id"], unique=False)
    op.create_index(op.f("ix_reports_status"), "reports", ["status"], unique=False)
    op.create_table(
        "operator_actions",
        sa.Column("report_id", sa.Uuid(), nullable=False),
        sa.Column("operator_account_id", sa.Uuid(), nullable=False),
        sa.Column("action", sa.String(length=24), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["operator_account_id"], ["accounts.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["report_id"], ["reports.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_operator_actions_report_id"), "operator_actions", ["report_id"], unique=False)
    op.create_table(
        "operator_grants",
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("scope", sa.String(length=32), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_operator_grants_account_id"), "operator_grants", ["account_id"], unique=False)
    op.create_index(
        "uq_operator_grants_active",
        "operator_grants",
        ["account_id", "scope"],
        unique=True,
        postgresql_where="revoked_at IS NULL",
    )
    op.create_table(
        "operator_file_grants",
        sa.Column("report_id", sa.Uuid(), nullable=False),
        sa.Column("document_version_id", sa.Uuid(), nullable=False),
        sa.Column("operator_account_id", sa.Uuid(), nullable=False),
        sa.Column("purpose", sa.Text(), nullable=False),
        sa.Column("granted_by", sa.String(length=254), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["document_version_id"], ["document_versions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["operator_account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["report_id"], ["reports.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_operator_file_grants_report_id"), "operator_file_grants", ["report_id"], unique=False)
    op.create_table(
        "listing_suspensions",
        sa.Column("subject_type", sa.String(length=24), nullable=False),
        sa.Column("subject_id", sa.Uuid(), nullable=False),
        sa.Column("report_id", sa.Uuid(), nullable=False),
        sa.Column("suspended_by_account_id", sa.Uuid(), nullable=False),
        sa.Column("lifted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("subject_type IN ('INVENTION', 'OPPORTUNITY', 'PARTNER_PROFILE')", name="subject_type"),
        sa.ForeignKeyConstraint(["report_id"], ["reports.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["suspended_by_account_id"], ["accounts.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_listing_suspensions_report_id"), "listing_suspensions", ["report_id"], unique=False)
    op.create_index(
        "uq_listing_suspensions_active",
        "listing_suspensions",
        ["subject_type", "subject_id"],
        unique=True,
        postgresql_where="lifted_at IS NULL",
    )
    policies = op.create_table(
        "retention_policies",
        sa.Column("key", sa.String(length=32), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(length=200), nullable=False),
        sa.Column("decision", sa.String(length=8), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("period", sa.String(length=200), nullable=False),
        sa.Column("policy_version", sa.String(length=32), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("decision IN ('REMOVE', 'RETAIN')", name="decision"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key"),
    )
    now = datetime.now(UTC)
    op.bulk_insert(
        policies,
        [
            {
                "id": uuid.uuid4(),
                "created_at": now,
                "key": key,
                "position": position,
                "label": label,
                "decision": decision,
                "reason": reason,
                "period": period,
                "policy_version": POLICY_VERSION,
            }
            for position, (key, label, decision, reason, period) in enumerate(POLICY)
        ],
    )
    op.create_table(
        "retention_holds",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("account_id", sa.Uuid(), sa.ForeignKey("accounts.id", ondelete="RESTRICT"), nullable=False),
        sa.Column(
            "category_key",
            sa.String(length=32),
            sa.ForeignKey("retention_policies.key", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("period", sa.String(length=200), nullable=False),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(op.f("ix_retention_holds_account_id"), "retention_holds", ["account_id"])
    op.drop_constraint("file_state", "document_versions", type_="check")
    op.create_check_constraint(
        "file_state",
        "document_versions",
        "file_state IN ('CREATED', 'UPLOADING', 'QUARANTINED', 'AVAILABLE', 'REJECTED', 'ERASURE_PENDING', 'ERASED')",
    )
    op.create_table(
        "privacy_requests",
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.String(length=8), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("answer", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("policy_version", sa.String(length=32), nullable=True),
        sa.Column("fulfilled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fulfilled_by_account_id", sa.Uuid(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("kind IN ('EXPORT', 'DELETION')", name="kind"),
        sa.CheckConstraint("status IN ('RECEIVED', 'PROCESSING', 'FULFILLED')", name="status"),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["fulfilled_by_account_id"], ["accounts.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_privacy_requests_account_id"), "privacy_requests", ["account_id"], unique=False)
    op.create_index(op.f("ix_privacy_requests_status"), "privacy_requests", ["status"], unique=False)
    op.create_index(
        "uq_privacy_requests_open_deletion",
        "privacy_requests",
        ["account_id"],
        unique=True,
        postgresql_where="kind = 'DELETION' AND status IN ('RECEIVED', 'PROCESSING')",
    )


def downgrade() -> None:
    op.drop_table("privacy_requests")
    op.drop_table("retention_holds")
    op.drop_table("retention_policies")
    op.execute("UPDATE document_versions SET file_state = 'REJECTED' WHERE file_state IN ('ERASURE_PENDING', 'ERASED')")
    op.drop_constraint("file_state", "document_versions", type_="check")
    op.create_check_constraint(
        "file_state",
        "document_versions",
        "file_state IN ('CREATED', 'UPLOADING', 'QUARANTINED', 'AVAILABLE', 'REJECTED')",
    )
    op.drop_table("listing_suspensions")
    op.drop_table("operator_file_grants")
    op.drop_table("operator_grants")
    op.drop_table("operator_actions")
    op.drop_table("reports")
