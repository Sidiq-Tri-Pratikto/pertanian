"""Create the optional confirmed aggregation selection of a site.

Revision ID: 0010
Revises: 0009
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add site selections without backfilling legacy sites."""
    op.execute("""
        CREATE TABLE aggregation_selections (
            site_id uuid PRIMARY KEY REFERENCES sites ON DELETE CASCADE,
            revision bigint NOT NULL CONSTRAINT aggregation_selections_positive_revision CHECK (revision > 0),
            created_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now()
        )
    """)
    op.execute("""
        CREATE TABLE aggregation_selection_assets (
            site_id uuid NOT NULL REFERENCES aggregation_selections ON DELETE CASCADE,
            asset_id uuid NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now(),
            PRIMARY KEY (site_id, asset_id),
            FOREIGN KEY (site_id, asset_id) REFERENCES assets (site_id, id) ON DELETE CASCADE
        )
    """)
    op.execute("CREATE INDEX ix_aggregation_selection_assets_asset ON aggregation_selection_assets (asset_id)")


def downgrade() -> None:
    """Remove selections and membership while retaining the site's existing data."""
    op.drop_table("aggregation_selection_assets")
    op.drop_table("aggregation_selections")
