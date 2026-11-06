"""Create demo sessions and their creation operations.

Revision ID: 0005
Revises: 0004
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _execute(sql: str) -> None:
    # asyncpg runs one statement per call.
    for statement in filter(str.strip, sql.split(";")):
        op.execute(statement)


def upgrade() -> None:
    _execute("""
        CREATE TABLE demo_sessions (
            id uuid PRIMARY KEY,
            principal_id uuid NOT NULL UNIQUE REFERENCES principals ON DELETE CASCADE,
            site_id uuid NOT NULL REFERENCES sites ON DELETE CASCADE,
            scenario_id text NOT NULL,
            token_hash bytea NOT NULL UNIQUE,
            key_version text NOT NULL,
            expires_at timestamptz NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_demo_sessions_expires_at ON demo_sessions (expires_at);
        CREATE TABLE demo_create_operations (
            operation_id text PRIMARY KEY,
            session_id uuid REFERENCES demo_sessions ON DELETE SET NULL,
            scenario_id text NOT NULL,
            replay_proof_hash bytea NOT NULL,
            key_version text NOT NULL,
            response jsonb NOT NULL,
            replay_expires_at timestamptz NOT NULL,
            retain_until timestamptz NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_demo_create_operations_retain_until ON demo_create_operations (retain_until);
        CREATE INDEX ix_demo_create_operations_created_at ON demo_create_operations (created_at)
    """)


def downgrade() -> None:
    _execute("DROP TABLE demo_create_operations; DROP TABLE demo_sessions")
