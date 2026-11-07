"""Create insight feedback and its idempotent operations.

Revision ID: 0007
Revises: 0006
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _execute(sql: str) -> None:
    # asyncpg runs one statement per call.
    for statement in filter(str.strip, sql.split(";")):
        op.execute(statement)


def upgrade() -> None:
    _execute("""
        CREATE TABLE insight_feedback (
            insight_id uuid NOT NULL,
            revision integer NOT NULL,
            principal_id uuid NOT NULL REFERENCES principals ON DELETE CASCADE,
            rating text CHECK (rating IN ('useful', 'not_relevant')),
            visibility text NOT NULL CHECK (visibility IN ('visible', 'hidden', 'snoozed')),
            until timestamptz,
            updated_at timestamptz NOT NULL DEFAULT now(),
            PRIMARY KEY (insight_id, revision, principal_id),
            FOREIGN KEY (insight_id, revision) REFERENCES insight_revisions (insight_id, revision) ON DELETE CASCADE,
            CHECK ((visibility = 'snoozed') = (until IS NOT NULL))
        );
        CREATE TABLE feedback_operations (
            principal_id uuid NOT NULL REFERENCES principals ON DELETE CASCADE,
            key text NOT NULL,
            insight_id uuid NOT NULL REFERENCES insights ON DELETE CASCADE,
            revision integer NOT NULL,
            action text NOT NULL,
            response jsonb,
            created_at timestamptz NOT NULL DEFAULT now(),
            PRIMARY KEY (principal_id, key)
        )
    """)


def downgrade() -> None:
    _execute("DROP TABLE feedback_operations; DROP TABLE insight_feedback")
