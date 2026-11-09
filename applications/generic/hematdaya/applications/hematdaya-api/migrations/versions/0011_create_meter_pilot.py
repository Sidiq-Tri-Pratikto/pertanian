"""Add isolated meter assignments and enrollments.

Revision ID: 0011
Revises: 0010
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add pilot state and admit live source transport."""
    op.execute("ALTER TABLE sources DROP CONSTRAINT sources_transport_status_check")
    op.execute("""
        ALTER TABLE sources ADD CONSTRAINT sources_transport_status_check
        CHECK (transport_status IN ('none', 'simulated_live', 'historical', 'live'))
    """)
    op.execute("""
        CREATE TABLE meter_pilot_assignments (
            meter_id uuid PRIMARY KEY,
            created_at timestamptz NOT NULL DEFAULT now(),
            site_id uuid NOT NULL UNIQUE REFERENCES sites ON DELETE CASCADE,
            owner_id uuid NOT NULL REFERENCES principals ON DELETE CASCADE,
            access_digest varchar(64) UNIQUE,
            access_expires_at timestamptz NOT NULL,
            meter_revoked_at timestamptz,
            source_id uuid REFERENCES sources
        )
    """)
    op.execute("""
        CREATE TABLE meter_pilot_enrollments (
            id uuid PRIMARY KEY,
            site_id uuid NOT NULL REFERENCES meter_pilot_assignments (site_id) ON DELETE CASCADE,
            created_at timestamptz NOT NULL,
            expires_at timestamptz NOT NULL,
            first_measured_at timestamptz,
            first_received_at timestamptz,
            first_energy_wh numeric,
            asset_id uuid REFERENCES assets,
            confirm_key varchar(128),
            asset_name text
        )
    """)
    op.create_index("ix_meter_pilot_enrollments_site_id", "meter_pilot_enrollments", ["site_id"])
    op.execute("""
        CREATE TABLE meter_pilot_start_requests (
            site_id uuid NOT NULL REFERENCES meter_pilot_assignments (site_id) ON DELETE CASCADE,
            key varchar(128) NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now(),
            enrollment_id uuid NOT NULL REFERENCES meter_pilot_enrollments ON DELETE CASCADE,
            PRIMARY KEY (site_id, key)
        )
    """)


def downgrade() -> None:
    """Remove setup state while retaining recorded energy and asset history."""
    op.drop_table("meter_pilot_start_requests")
    op.drop_table("meter_pilot_enrollments")
    op.drop_table("meter_pilot_assignments")
    op.execute("UPDATE sources SET transport_status = 'none' WHERE transport_status = 'live'")
    op.execute("ALTER TABLE sources DROP CONSTRAINT sources_transport_status_check")
    op.execute("""
        ALTER TABLE sources ADD CONSTRAINT sources_transport_status_check
        CHECK (transport_status IN ('none', 'simulated_live', 'historical'))
    """)
