"""Create the append-only audit trail.

Revision ID: 0003
Revises: 0002
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE audit_events (
            id uuid PRIMARY KEY,
            site_id uuid NOT NULL REFERENCES sites ON DELETE CASCADE,
            actor_principal_id uuid NOT NULL,
            action text NOT NULL,
            subject_type text NOT NULL,
            subject_id uuid NOT NULL,
            affected_from timestamptz,
            affected_to timestamptz,
            detail jsonb NOT NULL DEFAULT '{}',
            created_at timestamptz NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX ix_audit_events_site ON audit_events (site_id, created_at)")
    # Rows leave only with their site (purge, deletion); nothing may rewrite one.
    op.execute("""
        CREATE FUNCTION audit_events_append_only() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION 'audit_events is append-only';
        END $$
    """)
    op.execute("""
        CREATE TRIGGER audit_events_no_update BEFORE UPDATE ON audit_events
        FOR EACH ROW EXECUTE FUNCTION audit_events_append_only()
    """)


def downgrade() -> None:
    op.execute("DROP TABLE audit_events")
    op.execute("DROP FUNCTION audit_events_append_only")
