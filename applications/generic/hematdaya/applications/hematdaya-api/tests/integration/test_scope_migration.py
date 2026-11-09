"""A populated 0009 database can round-trip the 028 migration independently of other tests."""

import asyncio
import os
import subprocess
import sys
from uuid import uuid4

import asyncpg
import pytest
from sqlalchemy.engine import make_url

from app.core.settings import get_settings

pytestmark = pytest.mark.integration

TABLES = ("assets", "sources", "measurements", "bindings", "asset_relations", "audit_events")


async def _alembic(database_url: str, operation: str, revision: str) -> None:
    await asyncio.to_thread(
        subprocess.run,
        [sys.executable, "-m", "alembic", operation, revision],
        env=os.environ | {"DATABASE_URL": database_url},
        check=True,
    )


async def test_scope_migration_preserves_preexisting_state() -> None:
    """Check same-site, uniqueness and cascade constraints, plus a populated downgrade and re-upgrade."""
    base_url = make_url(get_settings().database_url.get_secret_value())
    database = f"scope_migration_{uuid4().hex}"
    url = base_url.set(database=database)
    database_url = url.render_as_string(hide_password=False)
    admin = await asyncpg.connect(base_url.set(drivername="postgresql").render_as_string(hide_password=False))
    try:
        await admin.execute(f"CREATE DATABASE {database}")
        await _alembic(database_url, "upgrade", "0009")
        connection = await asyncpg.connect(url.set(drivername="postgresql").render_as_string(hide_password=False))
        try:
            owner, site, other, asset, second, foreign, source = (uuid4() for _ in range(7))
            await connection.execute("INSERT INTO principals (id, kind) VALUES ($1, 'user')", owner)
            await connection.execute(
                "INSERT INTO sites (id, owner_principal_id, kind, name) VALUES "
                "($1, $3, 'standard', 'Rumah'), ($2, $3, 'standard', 'Gudang')",
                site,
                other,
                owner,
            )
            await connection.execute(
                "INSERT INTO assets (id, site_id, name, scope_kind) VALUES "
                "($1, $4, 'Utara', 'device'), ($2, $4, 'Selatan', 'device'), ($3, $5, 'Gudang', 'device')",
                asset,
                second,
                foreign,
                site,
                other,
            )
            await connection.execute(
                "INSERT INTO sources (id, site_id, label, origin, measurement_kind) "
                "VALUES ($1, $2, 'Meter', 'import', 'interval_energy')",
                source,
                site,
            )
            await connection.execute(
                "INSERT INTO bindings (id, site_id, asset_id, source_id, effective_from, authoritative) "
                "VALUES (gen_random_uuid(), $1, $2, $3, now(), true)",
                site,
                asset,
                source,
            )
            await connection.execute(
                "INSERT INTO measurements (source_id, identity_key, kind, interval_start, interval_end, "
                "energy_mwh, quality, received_at) "
                "VALUES ($1, 'seed', 'interval_energy', now() - interval '1 hour', now(), 1000, 'valid', now())",
                source,
            )
            await connection.execute(
                "INSERT INTO asset_relations (id, site_id, from_asset_id, to_asset_id, kind) "
                "VALUES (gen_random_uuid(), $1, $2, $3, 'disjoint')",
                site,
                asset,
                second,
            )
            await connection.execute(
                "INSERT INTO audit_events (id, site_id, actor_principal_id, action, subject_type, subject_id) "
                "VALUES (gen_random_uuid(), $1, $2, 'asset.created', 'asset', $3)",
                site,
                owner,
                asset,
            )
            before = [await connection.fetch(f"SELECT * FROM {table} ORDER BY id") for table in TABLES]

            await _alembic(database_url, "upgrade", "0010")
            assert await connection.fetchval("SELECT version_num FROM alembic_version") == "0010"
            assert await connection.fetchval("SELECT count(*) FROM aggregation_selections") == 0
            add_selection = "INSERT INTO aggregation_selections (site_id, revision) VALUES ($1, $2)"
            add_member = "INSERT INTO aggregation_selection_assets (site_id, asset_id) VALUES ($1, $2)"
            await connection.execute(add_selection, site, 1)
            with pytest.raises(asyncpg.UniqueViolationError):
                await connection.execute(add_selection, site, 2)
            with pytest.raises(asyncpg.CheckViolationError):
                await connection.execute(add_selection, other, 0)
            await connection.execute(add_member, site, asset)
            with pytest.raises(asyncpg.UniqueViolationError):
                await connection.execute(add_member, site, asset)
            with pytest.raises(asyncpg.ForeignKeyViolationError):
                await connection.execute(add_member, site, foreign)
            with pytest.raises(asyncpg.ForeignKeyViolationError):
                await connection.execute(add_member, other, foreign)

            async with connection.transaction():
                await connection.execute("SAVEPOINT test_cascade")
                await connection.execute("DELETE FROM assets WHERE id = $1", asset)
                assert await connection.fetchval("SELECT count(*) FROM aggregation_selection_assets") == 0
                await connection.execute("ROLLBACK TO SAVEPOINT test_cascade")
                await connection.execute("DELETE FROM sites WHERE id = $1", site)
                assert await connection.fetchval("SELECT count(*) FROM aggregation_selections") == 0
                assert await connection.fetchval("SELECT count(*) FROM aggregation_selection_assets") == 0
                await connection.execute("ROLLBACK TO SAVEPOINT test_cascade")

            await _alembic(database_url, "downgrade", "0009")
            assert await connection.fetchval("SELECT to_regclass('aggregation_selections')") is None
            assert [await connection.fetch(f"SELECT * FROM {table} ORDER BY id") for table in TABLES] == before
            await _alembic(database_url, "upgrade", "0010")
            assert await connection.fetchval("SELECT count(*) FROM aggregation_selections") == 0
            assert [await connection.fetch(f"SELECT * FROM {table} ORDER BY id") for table in TABLES] == before
        finally:
            await connection.close()
    finally:
        await admin.execute(f"DROP DATABASE IF EXISTS {database}")
        await admin.close()
