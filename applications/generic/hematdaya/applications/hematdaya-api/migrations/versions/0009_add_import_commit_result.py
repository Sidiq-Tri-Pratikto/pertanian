"""Add the stored first result of an import commit.

Revision ID: 0009
Revises: 0008
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _execute(sql: str) -> None:
    # asyncpg runs one statement per call.
    for statement in filter(str.strip, sql.split(";")):
        op.execute(statement)


def upgrade() -> None:
    # NOT VALID enforces both rules on every new write and skips existing rows. 025's tests leave committed rows with
    # no result in the shared development database, and a downgrade and upgrade does the same.
    _execute("""
        ALTER TABLE imports ADD COLUMN commit_result jsonb;
        ALTER TABLE imports ADD CONSTRAINT imports_commit_result
            CHECK ((status = 'committed') = (commit_result IS NOT NULL)) NOT VALID;
        ALTER TABLE imports ADD CONSTRAINT imports_commit_key
            CHECK (status <> 'committed' OR idempotency_key IS NOT NULL) NOT VALID
    """)


def downgrade() -> None:
    _execute("""
        ALTER TABLE imports DROP CONSTRAINT imports_commit_key;
        ALTER TABLE imports DROP CONSTRAINT imports_commit_result;
        ALTER TABLE imports DROP COLUMN commit_result
    """)
