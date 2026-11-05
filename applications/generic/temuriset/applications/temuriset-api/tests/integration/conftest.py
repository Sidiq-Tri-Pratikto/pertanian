"""Integration fixtures: one migrated Postgres for the session, empty platform tables per test."""

import subprocess
import sys
from collections.abc import AsyncIterator, Iterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.core.database import get_engine
from app.main import app

PLATFORM_TABLES = "idempotency_records, audit_events, outbox_deliveries, outbox_events, jobs"


@pytest.fixture(scope="session", autouse=True)
def migrated_database() -> Iterator[None]:
    """Apply migrations once; a failure here means Postgres is not running (``make run-dependencies``)."""
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True)
    yield


@pytest.fixture
async def clean_tables() -> AsyncIterator[None]:
    """Start each test with empty platform tables. TRUNCATE bypasses the audit table's row trigger."""
    async with get_engine().begin() as connection:
        await connection.execute(text(f"TRUNCATE {PLATFORM_TABLES}"))
    yield


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    """Client bound to the real application."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as async_client:
        yield async_client
