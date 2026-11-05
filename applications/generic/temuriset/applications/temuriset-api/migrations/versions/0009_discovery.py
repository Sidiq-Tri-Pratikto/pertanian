"""Discovery: search projection, saved items, relevance feedback and the alias table (spec 018).

Revision ID: 0009
Revises: 0008
"""

from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import NAMESPACE_URL, uuid5

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# English words people type, and the Indonesian words they also match (the prototype's EN_ALIAS).
ALIASES = {
    "water": "air",
    "clean": "bersih",
    "energy": "energi",
    "software": "perangkat lunak",
    "agriculture": "pertanian",
    "farming": "pertanian",
    "packaging": "kemasan",
    "manufacturing": "manufaktur",
    "material": "material",
    "funding": "pendanaan",
    "investment": "investasi",
    "license": "lisensi",
    "distribution": "distribusi",
    "mentoring": "pendampingan",
    "community": "komunitas",
}

SEEDED_AT = datetime(2026, 11, 5, tzinfo=UTC)


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    ]


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.create_table(
        "search_documents",
        sa.Column("subject_type", sa.String(length=16), nullable=False),
        sa.Column("subject_id", sa.Uuid(), nullable=False),
        sa.Column("version_id", sa.Uuid(), nullable=True),
        sa.Column("owner_party_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column(
            "tsv",
            postgresql.TSVECTOR(),
            sa.Computed("to_tsvector('simple', title || ' ' || body)", persisted=True),
            nullable=True,
        ),
        sa.Column("filters", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("card", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("curated", sa.Boolean(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        *_timestamps(),
        sa.CheckConstraint("subject_type IN ('INVENTION', 'FUNDING_REQUEST', 'PARTNER')", name="subject_type"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("subject_type", "subject_id"),
    )
    op.create_index("ix_search_documents_owner_party_id", "search_documents", ["owner_party_id"])
    op.create_index("ix_search_documents_order", "search_documents", ["subject_type", "published_at", "id"])
    op.create_index("ix_search_documents_tsv", "search_documents", ["tsv"], postgresql_using="gin")
    op.create_index(
        "ix_search_documents_title_trgm",
        "search_documents",
        ["title"],
        postgresql_using="gin",
        postgresql_ops={"title": "gin_trgm_ops"},
    )
    for table in ("saved_items", "relevance_feedback"):
        op.create_table(
            table,
            sa.Column("party_id", sa.Uuid(), nullable=False),
            sa.Column("subject_type", sa.String(length=16), nullable=False),
            sa.Column("subject_id", sa.Uuid(), nullable=False),
            *_timestamps(),
            sa.ForeignKeyConstraint(["party_id"], ["parties.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("party_id", "subject_type", "subject_id"),
        )
        op.create_index(f"ix_{table}_party_id", table, ["party_id"])
    aliases = op.create_table(
        "alias_terms",
        sa.Column("term", sa.String(length=80), nullable=False),
        sa.Column("canonical", sa.String(length=80), nullable=False),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("term"),
    )
    op.bulk_insert(
        aliases,
        [
            {
                "id": uuid5(NAMESPACE_URL, f"temuriset:alias:{term}"),
                "term": term,
                "canonical": canonical,
                "created_at": SEEDED_AT,
            }
            for term, canonical in ALIASES.items()
        ],
    )


def downgrade() -> None:
    op.drop_table("alias_terms")
    for table in ("relevance_feedback", "saved_items"):
        op.drop_index(f"ix_{table}_party_id", table_name=table)
        op.drop_table(table)
    op.drop_index("ix_search_documents_title_trgm", table_name="search_documents")
    op.drop_index("ix_search_documents_tsv", table_name="search_documents")
    op.drop_index("ix_search_documents_order", table_name="search_documents")
    op.drop_index("ix_search_documents_owner_party_id", table_name="search_documents")
    op.drop_table("search_documents")
