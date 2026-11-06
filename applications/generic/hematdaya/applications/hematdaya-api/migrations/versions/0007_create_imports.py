"""Create imports and their staged row results.

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
        CREATE TABLE imports (
            id uuid PRIMARY KEY,
            site_id uuid NOT NULL REFERENCES sites ON DELETE CASCADE,
            status text NOT NULL CHECK (status IN ('previewed', 'committed', 'rejected')),
            file_name text NOT NULL CHECK (char_length(file_name) BETWEEN 1 AND 255),
            content_sha256 text NOT NULL,
            mapping jsonb NOT NULL,
            total_rows integer NOT NULL,
            accepted_rows integer NOT NULL,
            invalid_rows integer NOT NULL,
            duplicate_rows integer NOT NULL,
            conflict_rows integer NOT NULL,
            pending_rows integer NOT NULL,
            blocked boolean NOT NULL,
            block_reasons jsonb NOT NULL,
            needs_acknowledgment boolean NOT NULL,
            questions jsonb NOT NULL,
            assumptions jsonb NOT NULL,
            period_start timestamptz,
            period_end timestamptz,
            measurement_revision bigint NOT NULL,
            binding_revision bigint NOT NULL,
            idempotency_key text,
            expires_at timestamptz NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT imports_counts_reconcile CHECK (
                accepted_rows + invalid_rows + duplicate_rows + conflict_rows + pending_rows = total_rows
            )
        );
        CREATE UNIQUE INDEX ux_imports_site_idempotency ON imports (site_id, idempotency_key)
            WHERE idempotency_key IS NOT NULL;
        CREATE INDEX ix_imports_site_created ON imports (site_id, created_at);
        CREATE INDEX ix_imports_expiry ON imports (expires_at) WHERE status = 'previewed';
        CREATE TABLE import_rows (
            import_id uuid NOT NULL REFERENCES imports ON DELETE CASCADE,
            data_row integer NOT NULL,
            file_line integer NOT NULL,
            status text NOT NULL CHECK (status IN ('accepted', 'invalid', 'duplicate', 'conflict')),
            reason text,
            field text,
            message text,
            parsed jsonb,
            PRIMARY KEY (import_id, data_row),
            CONSTRAINT import_rows_message CHECK ((status IN ('invalid', 'conflict')) = (message IS NOT NULL))
        );
        CREATE INDEX ix_import_rows_errors ON import_rows (import_id, data_row)
            WHERE status IN ('invalid', 'conflict')
    """)


def downgrade() -> None:
    _execute("""
        DROP TABLE import_rows;
        DROP TABLE imports
    """)
