"""Full-stack tests over real Postgres. Start it with ``make run-dependencies``."""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration


async def test_ready_reaches_database(client: AsyncClient) -> None:
    """
    Condition:
    - Postgres is running.

    Expected:
    - Readiness reports ready.
    """
    response = await client.get("/health/ready")

    assert response.status_code == 200
