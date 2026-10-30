"""Liveness and readiness tests."""

from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.main import app


def test_health_needs_no_dependencies() -> None:
    """
    Condition:
    - No database is reachable.

    Expected:
    - Liveness still reports ok.
    """
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_reports_unreachable_database() -> None:
    """
    Condition:
    - The database refuses connections, so the driver raises a raw socket error.

    Expected:
    - The client gets the retryable unavailable envelope with a Retry-After header, not the fallback 500.
    """
    engine = create_async_engine("postgresql+asyncpg://nobody:nothing@127.0.0.1:1/none")

    with patch("app.core.database.get_session_factory", return_value=async_sessionmaker(engine)):
        response = TestClient(app).get("/ready")

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "DATABASE_UNAVAILABLE"
    assert response.json()["error"]["recovery"]["retryable"] is True
    assert response.headers["retry-after"] == "30"
