"""API contract and CORS tests."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.settings import Settings
from app.main import app, create_app


def test_document_describes_the_real_error_envelope() -> None:
    """
    Condition:
    - The OpenAPI document is generated.

    Expected:
    - Every operation documents the envelope, and FastAPI's default validation schema is gone.
    """
    document = app.openapi()
    envelope = {"$ref": "#/components/schemas/ErrorEnvelope"}

    for path_item in document["paths"].values():
        for operation in path_item.values():
            assert operation["responses"]["default"]["content"]["application/json"]["schema"] == envelope
    assert "HTTPValidationError" not in document["components"]["schemas"]
    assert "ErrorBody" in document["components"]["schemas"]


def test_document_is_stable_across_calls() -> None:
    """
    Condition:
    - The document is requested twice.

    Expected:
    - The result is identical, so the exported contract is deterministic.
    """
    assert app.openapi() == app.openapi()


def test_cors_headers_survive_failures() -> None:
    """
    Condition:
    - A browser origin is allowed and its request fails.

    Expected:
    - The error envelope still carries the CORS header, so a browser client can read it.
    """
    settings = Settings(
        database_url="postgresql+asyncpg://a:b@localhost/c", cors_allowed_origins=["http://localhost:8081"]
    )

    with patch("app.main.get_settings", return_value=settings):
        client = TestClient(create_app())

    response = client.get("/does-not-exist", headers={"Origin": "http://localhost:8081"})

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"
    assert response.headers["access-control-allow-origin"] == "http://localhost:8081"


def test_no_cors_by_default() -> None:
    """
    Condition:
    - No origin is configured.

    Expected:
    - Responses carry no CORS header.
    """
    response = TestClient(app).get("/health", headers={"Origin": "http://localhost:8081"})

    assert "access-control-allow-origin" not in response.headers
