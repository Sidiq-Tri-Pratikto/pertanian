"""Full-stack fixtures over real Postgres. Start it with ``make run-dependencies``."""

import asyncio
import json
import logging
import secrets
import subprocess
import sys
from collections.abc import AsyncIterator, Callable, Iterator
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from fastapi import Request
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.database import get_session_factory
from app.core.settings import get_settings
from app.identity.dependencies import get_current_principal
from app.identity.model.models import PrincipalKind, PrincipalModel
from app.main import app

TEST_PRINCIPAL_HEADER = "x-test-principal"
COMMITTED_RESULT = {
    "import_id": "00000000-0000-0000-0000-000000000000",
    "status": "committed",
    "rows_added": 0,
    "rows_skipped": 1,
    "rows_duplicate": 0,
    "assets_created": [],
    "assets_mapped": [],
    "period": None,
    "affected_from": None,
    "affected_to": None,
    "rows_after_site_clock": 0,
    "acknowledge_skipped": True,
    "committed_at": "2026-11-07T00:00:00Z",
}
"""A valid stored result, because a committed import must carry one."""


@pytest.fixture(scope="session", autouse=True)
def migrated_database() -> Iterator[None]:
    """Apply migrations once; a failure here means Postgres is not running.

    Tests share the development database, so demo sessions they create are expired afterwards. The next real
    creation purges them, and test runs never use up the local demo capacity.
    """
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True)
    started = datetime.now(UTC)
    yield
    asyncio.run(_expire_demo_sessions_since(started))


async def _expire_demo_sessions_since(started: datetime) -> None:
    engine = create_async_engine(get_settings().database_url.get_secret_value())
    async with engine.begin() as connection:
        await connection.execute(
            text("UPDATE demo_sessions SET expires_at = now() WHERE created_at >= :started"), {"started": started}
        )
    await engine.dispose()


@pytest.fixture(autouse=True)
def roomy_demo_limits(monkeypatch: pytest.MonkeyPatch) -> None:
    """Sessions persist between runs, so tests lift the demo limits; capacity tests set their own."""
    monkeypatch.setattr(get_settings(), "demo_max_active_sessions", 10**9)
    monkeypatch.setattr(get_settings(), "demo_create_max_per_minute", 10**9)


@pytest.fixture
def capture_app_logs(caplog: pytest.LogCaptureFixture) -> Iterator[None]:
    """Capture the application logger, which does not propagate once configured."""
    logger = logging.getLogger("app")
    original_level = logger.level
    logger.addHandler(caplog.handler)
    logger.setLevel(logging.INFO)
    try:
        yield
    finally:
        logger.removeHandler(caplog.handler)
        logger.setLevel(original_level)


def failure_records(caplog: pytest.LogCaptureFixture) -> list[dict]:
    """Read the sanitized records written by the application failure recorder."""
    prefix = "Application failure "
    return [
        json.loads(record.getMessage().removeprefix(prefix))
        for record in caplog.records
        if record.getMessage().startswith(prefix)
    ]


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    """Client bound to the real application and its real credential resolvers."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as async_client:
        yield async_client


@pytest.fixture
def acting() -> Iterator[Callable[[UUID], dict[str, str]]]:
    """Let a test act as any principal, standing in for credentials that arrive in later specs.

    Yields:
        Callable[[UUID], dict[str, str]]: Builds the headers that act as a principal.
    """

    async def as_header_principal(request: Request) -> PrincipalModel:
        return PrincipalModel(id=UUID(request.headers[TEST_PRINCIPAL_HEADER]), kind=PrincipalKind.DEMO)

    app.dependency_overrides[get_current_principal] = as_header_principal
    yield lambda principal_id: {TEST_PRINCIPAL_HEADER: str(principal_id)}
    app.dependency_overrides.pop(get_current_principal, None)


async def execute(sql: str, **params: object) -> list:
    """Run SQL in its own committed transaction.

    Args:
        sql (str): Statement.
        **params (object): Bound parameters.

    Returns:
        list: Returned rows, if any.
    """
    async with get_session_factory()() as session:
        result = await session.execute(text(sql), params)
        rows = list(result) if result.returns_rows else []
        await session.commit()
        return rows


async def make_principal() -> UUID:
    """Insert a demo principal.

    Returns:
        UUID: Its ID.
    """
    rows = await execute("INSERT INTO principals (id, kind) VALUES (gen_random_uuid(), 'demo') RETURNING id")
    return rows[0][0]


async def make_site(
    owner: UUID, *, kind: str = "demo", virtual_now: datetime | None = None, name: str = "Rumah"
) -> UUID:
    """Insert a site.

    Args:
        owner (UUID): Owner principal.
        kind (str, optional): Site kind. Defaults to demo.
        virtual_now (datetime | None, optional): Demo clock; demo sites default to 2026-10-26 00.00 WIB.
        name (str, optional): Name. Defaults to Rumah.

    Returns:
        UUID: Its ID.
    """
    if kind == "demo" and virtual_now is None:
        virtual_now = datetime.fromisoformat("2026-10-25T17:00:00+00:00")
    rows = await execute(
        "INSERT INTO sites (id, owner_principal_id, kind, name, virtual_now)"
        " VALUES (gen_random_uuid(), :owner, :kind, :name, :virtual_now) RETURNING id",
        owner=owner,
        kind=kind,
        name=name,
        virtual_now=virtual_now,
    )
    return rows[0][0]


async def make_asset(site: UUID, name: str = "Kulkas", scope_kind: str = "device") -> UUID:
    """Insert an asset.

    Args:
        site (UUID): Its site.
        name (str, optional): Name. Defaults to Kulkas.
        scope_kind (str, optional): Scope kind. Defaults to device.

    Returns:
        UUID: Its ID.
    """
    rows = await execute(
        "INSERT INTO assets (id, site_id, name, scope_kind)"
        " VALUES (gen_random_uuid(), :site, :name, :kind) RETURNING id",
        site=site,
        name=name,
        kind=scope_kind,
    )
    return rows[0][0]


async def make_source(site: UUID, label: str = "Sumber demo") -> UUID:
    """Insert a simulated interval-energy source.

    Args:
        site (UUID): Its site.
        label (str, optional): Label. Defaults to Sumber demo.

    Returns:
        UUID: Its ID.
    """
    rows = await execute(
        "INSERT INTO sources (id, site_id, label, origin, measurement_kind, cadence_seconds, resolution_mwh)"
        " VALUES (gen_random_uuid(), :site, :label, 'simulated', 'interval_energy', 3600, 1000) RETURNING id",
        site=site,
        label=label,
    )
    return rows[0][0]


async def make_binding(site: UUID, asset: UUID, source: UUID, effective_from: str = "2026-09-27T17:00:00Z") -> UUID:
    """Insert an open authoritative binding.

    Args:
        site (UUID): The site.
        asset (UUID): The asset.
        source (UUID): The source.
        effective_from (str, optional): Start. Defaults to 2026-09-28 00.00 WIB.

    Returns:
        UUID: Its ID.
    """
    rows = await execute(
        "INSERT INTO bindings (id, site_id, source_id, asset_id, effective_from, authoritative)"
        " VALUES (gen_random_uuid(), :site, :source, :asset, :start, true) RETURNING id",
        site=site,
        source=source,
        asset=asset,
        start=datetime.fromisoformat(effective_from),
    )
    return rows[0][0]


async def make_import(site: UUID, *, status: str = "previewed", expires_at: datetime | None = None) -> UUID:
    """Insert one import with reconciled counts and one invalid row.

    Args:
        site (UUID): Its site.
        status (str, optional): Its status. Defaults to previewed.
        expires_at (datetime | None, optional): Its expiry. Defaults to a day after the wall clock.

    Returns:
        UUID: Its ID.
    """
    committed = status == "committed"
    rows = await execute(
        "INSERT INTO imports (id, site_id, status, file_name, content_sha256, mapping, total_rows, accepted_rows,"
        " invalid_rows, duplicate_rows, conflict_rows, pending_rows, blocked, block_reasons, needs_acknowledgment,"
        " questions, assumptions, measurement_revision, binding_revision, expires_at, idempotency_key, commit_result)"
        " VALUES (gen_random_uuid(), :site, :status, 'data.csv', :digest, '{}', 1, 0, 1, 0, 0, 0, true,"
        " '[\"Impor diblokir: 1 dari 1 baris tidak valid.\"]', false, '[]', '[]', 0, 0, :expires_at, :key,"
        " CAST(:result AS jsonb)) RETURNING id",
        site=site,
        status=status,
        digest="0" * 64,
        expires_at=expires_at or datetime.now(UTC) + timedelta(hours=24),
        key=secrets.token_urlsafe(16) if committed else None,
        result=json.dumps(COMMITTED_RESULT) if committed else None,
    )
    await execute(
        "INSERT INTO import_rows (import_id, data_row, file_line, status, reason, field, message)"
        " VALUES (:id, 1, 2, 'invalid', 'negative', 'energi_wh',"
        " 'Baris data 1, energi_wh: gunakan angka 0 atau lebih.')",
        id=rows[0][0],
    )
    return rows[0][0]


def demo_headers(**overrides: str) -> dict[str, str]:
    """Fresh random creation headers.

    Args:
        **overrides (str): Replace ``key`` or ``proof``.

    Returns:
        dict[str, str]: ``Idempotency-Key`` and ``X-Demo-Replay-Proof``.
    """
    return {
        "Idempotency-Key": overrides.get("key", secrets.token_urlsafe(16)),
        "X-Demo-Replay-Proof": overrides.get("proof", secrets.token_urlsafe(32)),
    }


async def start_demo(client: AsyncClient, scenario_id: str = "h-base") -> dict:
    """Create a demo session.

    Args:
        client (AsyncClient): The client.
        scenario_id (str, optional): The scenario. Defaults to h-base.

    Returns:
        dict: The session response, with ``auth`` headers added.
    """
    response = await client.post("/api/v1/demo/sessions", json={"scenario_id": scenario_id}, headers=demo_headers())
    assert response.status_code == 201, response.text
    body = response.json()
    return body | {"auth": {"Authorization": f"Bearer {body['token']}"}}


async def summary(client: AsyncClient, session: dict, path: str | None = None, **params: str) -> dict:
    """Read a summary as a demo session.

    Args:
        client (AsyncClient): The client.
        session (dict): A ``start_demo`` result.
        path (str | None, optional): Route; defaults to the session site's summary.
        **params (str): Query parameters.

    Returns:
        dict: The response body.
    """
    response = await client.get(
        path or f"/api/v1/sites/{session['site_id']}/summary", params=params, headers=session["auth"]
    )
    assert response.status_code == 200, response.text
    return response.json()


def scope_path(site_id: str) -> str:
    """Return the site's scope route."""
    return f"/api/v1/sites/{site_id}/aggregation-selection"


def scope_confirmation(proposal: dict, preview: dict) -> dict:
    """Confirm the exact preview period and scope revisions."""
    window = preview["summary"]["window"]
    return proposal | {
        "expected_selection_revision": preview["selection_revision"],
        "expected_binding_revision": preview["binding_revision"],
        "resolved_period": {key: window[key] for key in ("timezone", "start_date", "end_date")},
    }


async def scope_state(site_id: str) -> list:
    """Read persisted scope state in a separate transaction for preview and rollback assertions."""
    return await execute(
        """
        SELECT binding_revision, measurement_revision,
               ARRAY(SELECT to_jsonb(t) FROM aggregation_selections t WHERE t.site_id = s.id),
               ARRAY(SELECT to_jsonb(t) FROM aggregation_selection_assets t WHERE t.site_id = s.id ORDER BY asset_id),
               ARRAY(SELECT to_jsonb(t) FROM bindings t WHERE t.site_id = s.id ORDER BY id),
               ARRAY(SELECT to_jsonb(t) FROM asset_relations t WHERE t.site_id = s.id ORDER BY id),
               ARRAY(SELECT to_jsonb(t) FROM audit_events t WHERE t.site_id = s.id ORDER BY id)
        FROM sites s WHERE s.id = CAST(:site AS uuid)
        """,
        site=site_id,
    )


async def make_switchable_scope_site() -> tuple[UUID, UUID, UUID, UUID, UUID]:
    owner = await make_principal()
    site = await make_site(owner)
    asset = await make_asset(site, "Meter")
    current, candidate = await make_source(site, "Sumber lama"), await make_source(site, "Sumber baru")
    await execute(
        "INSERT INTO bindings (id, site_id, asset_id, source_id, effective_from, authoritative) VALUES "
        "(gen_random_uuid(), :site, :asset, :current, '2026-10-24T17:00:00Z', true), "
        "(gen_random_uuid(), :site, :asset, :candidate, '2026-10-24T17:00:00Z', false)",
        site=site,
        asset=asset,
        current=current,
        candidate=candidate,
    )
    await execute(
        "INSERT INTO measurements (source_id, identity_key, kind, interval_start, interval_end, "
        "energy_mwh, quality, received_at) VALUES "
        "(:current, 'test', 'interval_energy', '2026-10-24T17:00:00Z', '2026-10-24T18:00:00Z', "
        "1000000, 'valid', now()), "
        "(:candidate, 'test', 'interval_energy', '2026-10-24T17:00:00Z', '2026-10-24T18:00:00Z', "
        "2000000, 'valid', now())",
        current=current,
        candidate=candidate,
    )
    return owner, site, asset, current, candidate
