"""Create measurements and the current-revision view.

Revision ID: 0004
Revises: 0003
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _execute(sql: str) -> None:
    # asyncpg runs one statement per call.
    for statement in filter(str.strip, sql.split(";")):
        op.execute(statement)


def upgrade() -> None:
    _execute("""
        ALTER TABLE sites ADD COLUMN measurement_revision bigint NOT NULL DEFAULT 0;
        CREATE TABLE measurements (
            id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            source_id uuid NOT NULL REFERENCES sources ON DELETE CASCADE,
            identity_key text NOT NULL,
            source_record_id text,
            kind text NOT NULL CHECK (kind IN (
                'interval_energy', 'average_power', 'instantaneous_power', 'counter_point', 'counter_delta'
            )),
            interval_start timestamptz,
            interval_end timestamptz,
            measured_at timestamptz,
            energy_mwh bigint CHECK (energy_mwh >= 0),
            raw_value text,
            raw_unit text,
            counter_segment integer,
            quality text NOT NULL CHECK (quality IN ('valid', 'long_gap')),
            provenance jsonb NOT NULL DEFAULT '{}',
            received_at timestamptz NOT NULL,
            revision integer NOT NULL DEFAULT 1 CHECK (revision >= 1),
            created_at timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT measurements_shape CHECK (
                CASE WHEN kind IN ('interval_energy', 'average_power', 'counter_delta')
                    THEN interval_start IS NOT NULL AND interval_end > interval_start AND measured_at IS NULL
                        AND energy_mwh IS NOT NULL
                    ELSE measured_at IS NOT NULL AND interval_start IS NULL AND interval_end IS NULL
                        AND energy_mwh IS NULL
                END
            ),
            UNIQUE (source_id, identity_key, revision)
        );
        CREATE INDEX ix_measurements_interval ON measurements (source_id, interval_start);
        CREATE INDEX ix_measurements_point ON measurements (source_id, measured_at) WHERE measured_at IS NOT NULL;
        CREATE VIEW current_measurements AS
            SELECT DISTINCT ON (source_id, identity_key) *
            FROM measurements
            ORDER BY source_id, identity_key, revision DESC
    """)


def downgrade() -> None:
    _execute("""
        DROP VIEW current_measurements;
        DROP TABLE measurements;
        ALTER TABLE sites DROP COLUMN measurement_revision
    """)
