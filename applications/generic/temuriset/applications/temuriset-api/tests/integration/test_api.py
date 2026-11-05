"""Full-stack tests over real Postgres. Start it with ``make run-dependencies``."""

import subprocess
import sys
from collections.abc import AsyncIterator, Iterator

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module", autouse=True)
def migrated_database() -> Iterator[None]:
    """Apply migrations once; a failure here means Postgres is not running."""
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True)
    yield


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    """Client bound to the real application."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as async_client:
        yield async_client


async def test_ready_reaches_database(client: AsyncClient) -> None:
    """
    Condition:
    - Postgres is running.

    Expected:
    - Readiness reports ready.
    """
    response = await client.get("/health/ready")

    assert response.status_code == 200
