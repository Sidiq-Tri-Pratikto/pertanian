"""Create insights and their immutable evidence revisions.

Revision ID: 0006
Revises: 0005
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _execute(sql: str) -> None:
    # asyncpg runs one statement per call.
    for statement in filter(str.strip, sql.split(";")):
        op.execute(statement)


def upgrade() -> None:
    _execute("""
        CREATE TABLE insights (
            id uuid PRIMARY KEY,
            site_id uuid NOT NULL REFERENCES sites ON DELETE CASCADE,
            kind text NOT NULL,
            asset_id uuid NOT NULL REFERENCES assets ON DELETE CASCADE,
            period_start timestamptz NOT NULL,
            period_end timestamptz NOT NULL,
            identity_key text NOT NULL,
            current_revision integer NOT NULL,
            active boolean NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now(),
            UNIQUE (site_id, identity_key)
        );
        CREATE INDEX ix_insights_site_period ON insights (site_id, period_start, period_end);
        CREATE TABLE insight_revisions (
            id uuid PRIMARY KEY,
            insight_id uuid NOT NULL REFERENCES insights ON DELETE CASCADE,
            revision integer NOT NULL CHECK (revision >= 1),
            evidence jsonb NOT NULL,
            evidence_hash text NOT NULL,
            policy_id text NOT NULL,
            policy_version integer NOT NULL,
            generated_at timestamptz NOT NULL,
            superseded_at timestamptz,
            created_at timestamptz NOT NULL DEFAULT now(),
            UNIQUE (insight_id, revision)
        )
    """)
    # Evidence never changes; only supersession may be recorded on a revision.
    op.execute("""
        CREATE FUNCTION insight_revisions_frozen() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            IF NEW.evidence IS DISTINCT FROM OLD.evidence OR NEW.evidence_hash IS DISTINCT FROM OLD.evidence_hash
                OR NEW.revision IS DISTINCT FROM OLD.revision OR NEW.generated_at IS DISTINCT FROM OLD.generated_at
            THEN
                RAISE EXCEPTION 'insight evidence is immutable';
            END IF;
            RETURN NEW;
        END $$
    """)
    op.execute("""
        CREATE TRIGGER insight_revisions_frozen BEFORE UPDATE ON insight_revisions
        FOR EACH ROW EXECUTE FUNCTION insight_revisions_frozen()
    """)


def downgrade() -> None:
    _execute("DROP TABLE insight_revisions; DROP TABLE insights; DROP FUNCTION insight_revisions_frozen")
