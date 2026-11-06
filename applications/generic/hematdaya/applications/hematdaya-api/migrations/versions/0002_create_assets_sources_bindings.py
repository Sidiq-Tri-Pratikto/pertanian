"""Create assets, sources, bindings and relations.

Revision ID: 0002
Revises: 0001
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _execute(sql: str) -> None:
    # asyncpg runs one statement per call.
    for statement in filter(str.strip, sql.split(";")):
        op.execute(statement)


def upgrade() -> None:
    _execute("""
        CREATE EXTENSION IF NOT EXISTS btree_gist;
        ALTER TABLE sites ADD COLUMN binding_revision bigint NOT NULL DEFAULT 0;
        CREATE TABLE assets (
            id uuid PRIMARY KEY,
            site_id uuid NOT NULL REFERENCES sites ON DELETE CASCADE,
            name text NOT NULL CHECK (char_length(name) BETWEEN 1 AND 60),
            category text,
            location text,
            scope_kind text NOT NULL CHECK (scope_kind IN ('device', 'group', 'circuit', 'site_total')),
            parent_asset_id uuid,
            expected_use text NOT NULL DEFAULT 'unknown'
                CHECK (expected_use IN ('unknown', 'continuous', 'scheduled', 'intermittent')),
            archived_at timestamptz,
            created_at timestamptz NOT NULL DEFAULT now(),
            UNIQUE (site_id, id),
            FOREIGN KEY (site_id, parent_asset_id) REFERENCES assets (site_id, id) ON DELETE CASCADE,
            CHECK (parent_asset_id <> id)
        );
        CREATE INDEX ix_assets_site_name ON assets (site_id, name, id);
        CREATE TABLE sources (
            id uuid PRIMARY KEY,
            site_id uuid NOT NULL REFERENCES sites ON DELETE CASCADE,
            label text NOT NULL CHECK (char_length(label) BETWEEN 1 AND 120),
            origin text NOT NULL CHECK (origin IN ('live', 'import', 'dataset_replay', 'simulated')),
            measurement_kind text NOT NULL
                CHECK (measurement_kind IN ('interval_energy', 'average_power', 'instantaneous_power', 'counter')),
            cadence_seconds integer CHECK (cadence_seconds > 0),
            resolution_mwh bigint CHECK (resolution_mwh > 0),
            transport_status text NOT NULL DEFAULT 'none'
                CHECK (transport_status IN ('none', 'simulated_live', 'historical')),
            created_at timestamptz NOT NULL DEFAULT now(),
            UNIQUE (site_id, id)
        );
        CREATE TABLE bindings (
            id uuid PRIMARY KEY,
            site_id uuid NOT NULL,
            source_id uuid NOT NULL,
            asset_id uuid NOT NULL,
            effective_from timestamptz NOT NULL,
            effective_to timestamptz,
            authoritative boolean NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now(),
            FOREIGN KEY (site_id, source_id) REFERENCES sources (site_id, id) ON DELETE CASCADE,
            FOREIGN KEY (site_id, asset_id) REFERENCES assets (site_id, id) ON DELETE CASCADE,
            CONSTRAINT bindings_nonempty_range CHECK (effective_to IS NULL OR effective_to > effective_from),
            CONSTRAINT bindings_one_authority EXCLUDE USING gist (
                asset_id WITH =, tstzrange(effective_from, effective_to, '[)') WITH &&
            ) WHERE (authoritative)
        );
        CREATE INDEX ix_bindings_asset ON bindings (asset_id);
        CREATE INDEX ix_bindings_source ON bindings (source_id);
        CREATE TABLE asset_relations (
            id uuid PRIMARY KEY,
            site_id uuid NOT NULL,
            from_asset_id uuid NOT NULL,
            to_asset_id uuid NOT NULL,
            kind text NOT NULL CHECK (kind IN ('contains', 'unknown_overlap', 'disjoint')),
            created_at timestamptz NOT NULL DEFAULT now(),
            FOREIGN KEY (site_id, from_asset_id) REFERENCES assets (site_id, id) ON DELETE CASCADE,
            FOREIGN KEY (site_id, to_asset_id) REFERENCES assets (site_id, id) ON DELETE CASCADE,
            CHECK (from_asset_id <> to_asset_id),
            UNIQUE (from_asset_id, to_asset_id, kind)
        );
        CREATE INDEX ix_asset_relations_site ON asset_relations (site_id)
    """)


def downgrade() -> None:
    _execute("""
        DROP TABLE asset_relations;
        DROP TABLE bindings;
        DROP TABLE sources;
        DROP TABLE assets;
        ALTER TABLE sites DROP COLUMN binding_revision
    """)
