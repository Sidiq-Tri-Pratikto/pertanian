"""Capability guard tests through the real error boundary."""

import json
import logging
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.capabilities.service.guard import require_capability
from app.core.errors.handlers import ErrorBoundaryMiddleware, register_exception_handlers
from app.core.settings import Settings

MESSAGE = "Fitur ini tidak tersedia pada layanan ini. Hubungi pengelola layanan bila Anda memerlukannya."


class FundingRequest(BaseModel):
    """Body of the test-only guarded route."""

    amount: int


@pytest.fixture
def effects() -> list[int]:
    """What the guarded route changed."""
    return []


@pytest.fixture
def client(effects: list[int]) -> TestClient:
    """Application with one route guarded by the optional ``company_funding`` capability."""
    app = FastAPI()
    app.add_middleware(ErrorBoundaryMiddleware)
    register_exception_handlers(app)

    @app.post("/funding", dependencies=[require_capability("company_funding")])
    async def create_funding(body: FundingRequest) -> dict[str, int]:
        effects.append(body.amount)
        return {"amount": body.amount}

    return TestClient(app)


def _settings(composition: str, overrides: dict[str, bool] | None = None) -> Settings:
    return Settings(
        database_url="postgresql+asyncpg://a:b@localhost/c",
        composition=composition,
        composition_overrides=overrides or {},
    )


def test_selected_capability_passes(client: TestClient, effects: list[int]) -> None:
    """
    Condition:
    - ``generic-base`` selects company funding.

    Expected:
    - The guard passes and the route runs.
    """
    with patch("app.capabilities.service.guard.get_settings", return_value=_settings("generic-base")):
        response = client.post("/funding", json={"amount": 5})

    assert response.status_code == 200
    assert effects == [5]


def test_absent_capability_is_refused_and_changes_nothing(
    client: TestClient, effects: list[int], caplog: pytest.LogCaptureFixture
) -> None:
    """
    Condition:
    - ``project-support-only`` leaves company funding out.

    Expected:
    - HTTP 403 ``CAPABILITY_UNAVAILABLE`` with the Indonesian message, not retryable, a request ID that resolves
      to one failure record, and no effect.
    """
    with (
        patch("app.capabilities.service.guard.get_settings", return_value=_settings("project-support-only")),
        caplog.at_level(logging.WARNING),
    ):
        response = client.post("/funding", json={"amount": 5})

    assert response.status_code == 403
    error = response.json()["error"]
    assert error["code"] == "CAPABILITY_UNAVAILABLE"
    assert error["message"] == MESSAGE
    assert error["recovery"] == {"retryable": False}
    assert "Retry-After" not in response.headers
    assert effects == []
    records = [
        json.loads(r.getMessage().split(" ", 2)[2]) for r in caplog.records if "Application failure" in r.getMessage()
    ]
    assert [(r["reference_id"], r["code"], r["http_status"]) for r in records] == [
        (error["request_id"], "APP-CAPABILITY-UNAVAILABLE", 403)
    ]


def test_refusal_comes_before_body_validation(client: TestClient) -> None:
    """
    Condition:
    - A disabled capability receives a body with invalid fields.

    Expected:
    - The refusal, never field errors.
    """
    with patch("app.capabilities.service.guard.get_settings", return_value=_settings("project-support-only")):
        response = client.post("/funding", json={"amount": "not a number"})

    assert response.status_code == 403
    assert "details" not in response.json()["error"]


def test_override_switches_a_capability_off(client: TestClient, effects: list[int]) -> None:
    """
    Condition:
    - ``generic-base`` with ``company_funding`` switched off by an override.

    Expected:
    - The guard refuses, as for a composition without it.
    """
    settings = _settings("generic-base", {"company_funding": False})
    with patch("app.capabilities.service.guard.get_settings", return_value=settings):
        response = client.post("/funding", json={"amount": 5})

    assert response.status_code == 403
    assert effects == []


def test_unknown_capability_fails_at_import() -> None:
    """
    Condition:
    - A route names a capability outside the catalog.

    Expected:
    - Wiring fails immediately instead of refusing every request later.
    """
    with pytest.raises(ValueError, match="Unknown capability: escrow"):
        require_capability("escrow")
