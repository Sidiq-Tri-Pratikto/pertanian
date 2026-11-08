"""Request language is isolated and defaults to Indonesian."""

import asyncio

from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from app.main import app


async def test_parallel_requests_choose_their_own_language() -> None:
    """
    Condition:
    - Concurrent requests to an absent route select English, Indonesian, or an unsupported locale.

    Expected:
    - Each response carries its own locale and the same failure contract.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        english, indonesian, fallback = await asyncio.gather(
            client.get("/api/v1/missing", headers={"X-HematDaya-Locale": "en"}),
            client.get("/api/v1/missing", headers={"X-HematDaya-Locale": "id"}),
            client.get("/api/v1/missing", headers={"X-HematDaya-Locale": "fr"}),
        )
    assert [response.headers["Content-Language"] for response in (english, indonesian, fallback)] == ["en", "id", "id"]
    for response in (english, indonesian, fallback):
        assert response.status_code == 404
        assert "X-HematDaya-Locale" in response.headers["Vary"]
        assert response.json()["error"]["code"] == "NOT_FOUND"
    assert english.json()["error"]["message"].startswith("We could not")
    assert indonesian.json()["error"]["message"] == fallback.json()["error"]["message"]


def test_old_client_receives_indonesian() -> None:
    """
    Condition:
    - The client has no language header.

    Expected:
    - The API preserves Indonesian copy and the status.
    """
    response = TestClient(app).get("/api/v1/missing")
    assert response.status_code == 404
    assert response.headers["Content-Language"] == "id"
    assert response.json()["error"]["message"].startswith("Data yang diminta")
