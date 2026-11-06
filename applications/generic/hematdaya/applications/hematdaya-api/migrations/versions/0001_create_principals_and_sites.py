"""Create principals and sites.

Revision ID: 0001
Revises:
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _execute(sql: str) -> None:
    # asyncpg runs one statement per call.
    for statement in filter(str.strip, sql.split(";")):
        op.execute(statement)


def upgrade() -> None:
    _execute("""
        CREATE TABLE principals (
            id uuid PRIMARY KEY,
            kind text NOT NULL CHECK (kind IN ('demo', 'user')),
            created_at timestamptz NOT NULL DEFAULT now()
        );
        CREATE TABLE sites (
            id uuid PRIMARY KEY,
            owner_principal_id uuid NOT NULL REFERENCES principals,
            kind text NOT NULL CHECK (kind IN ('demo', 'standard')),
            name text NOT NULL CHECK (char_length(name) BETWEEN 1 AND 60),
            context text NOT NULL DEFAULT 'unspecified'
                CHECK (context IN ('household', 'business', 'industry', 'unspecified')),
            timezone text NOT NULL DEFAULT 'Asia/Jakarta',
            currency text NOT NULL DEFAULT 'IDR',
            virtual_now timestamptz,
            created_at timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT sites_virtual_now_only_for_demo CHECK (
                (kind = 'demo' AND virtual_now IS NOT NULL) OR (kind = 'standard' AND virtual_now IS NULL)
            )
        );
        CREATE INDEX ix_sites_owner_principal_id ON sites (owner_principal_id);
    """)


def downgrade() -> None:
    _execute("DROP TABLE sites; DROP TABLE principals")
