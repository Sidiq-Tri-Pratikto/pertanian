"""Platform pieces that need no database: versions, request digest, actor placeholder, backoff, registry."""

import json
import logging
from datetime import timedelta
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.core.errors.handlers import ErrorBoundaryMiddleware, register_exception_handlers
from app.identity.model.models import Principal
from app.platform.actor import current_actor_party_id
from app.platform.service.idempotency import request_digest
from app.platform.service.versions import check_expected
from app.worker.loop import backoff
from app.worker.registry import Registry

ACTOR = UUID("00000000-0000-4000-8000-000000000001")


class Rename(BaseModel):
    """A change to a versioned resource."""

    expected_version: int


@pytest.fixture
def client() -> TestClient:
    """A versioned resource stored at version 3."""
    app = FastAPI()
    app.add_middleware(ErrorBoundaryMiddleware)
    register_exception_handlers(app)

    @app.post("/things/1")
    async def rename(body: Rename) -> dict[str, int]:
        check_expected(3, body.expected_version)
        return {"version": 4}

    return TestClient(app)


def test_current_version_passes(client: TestClient) -> None:
    """
    Condition:
    - The client sends the stored version.

    Expected:
    - The change goes through.
    """
    assert client.post("/things/1", json={"expected_version": 3}).json() == {"version": 4}


def test_stale_version_is_refused_with_the_current_version(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    """
    Condition:
    - The client changes version 2 while version 3 is stored.

    Expected:
    - 409 ``STALE_VERSION`` with ``current_version`` 3, an Indonesian message, not retryable, recorded once.
    """
    with caplog.at_level(logging.WARNING):
        response = client.post("/things/1", json={"expected_version": 2})

    assert response.status_code == 409
    error = response.json()["error"]
    assert error["code"] == "STALE_VERSION"
    assert error["current_version"] == 3
    assert (
        error["message"]
        == "Data ini sudah diubah sejak Anda membukanya. Muat ulang versi terbaru lalu ulangi perubahan Anda."
    )
    assert error["recovery"] == {"retryable": False}
    records = [line for line in caplog.text.splitlines() if "Application failure" in line]
    assert len(records) == 1
    assert json.loads(records[0].split("Application failure ", 1)[1])["reference_id"] == error["request_id"]


def test_request_digest_ignores_formatting_but_not_content() -> None:
    """
    Condition:
    - Bodies that differ only in key order or spacing, in content, in operation or in actor.

    Expected:
    - Only formatting leaves the digest unchanged.
    """
    base = request_digest(ACTOR, "notes", b'{"a":1,"b":2}')

    assert request_digest(ACTOR, "notes", b'{ "b": 2, "a": 1 }') == base
    assert request_digest(ACTOR, "notes", b'{"a":1,"b":3}') != base
    assert request_digest(ACTOR, "other", b'{"a":1,"b":2}') != base
    assert request_digest(UUID(int=7), "notes", b'{"a":1,"b":2}') != base
    assert request_digest(ACTOR, "notes", b"not json") == request_digest(ACTOR, "notes", b"not json")


async def test_actor_is_the_principals_active_party() -> None:
    """
    Condition:
    - A signed-in principal acting as an organization.

    Expected:
    - The idempotency actor is that active party, not the personal one.
    """
    principal = Principal(
        account_id=UUID(int=1), session_id=UUID(int=2), personal_party_id=UUID(int=3), active_party_id=ACTOR
    )

    assert await current_actor_party_id(principal) == ACTOR


@pytest.mark.parametrize(
    ("attempts", "delay"),
    [(1, timedelta(seconds=5)), (2, timedelta(seconds=10)), (4, timedelta(seconds=40)), (20, timedelta(hours=1))],
)
def test_backoff_doubles_up_to_an_hour(attempts: int, delay: timedelta) -> None:
    """
    Condition:
    - A side effect failed ``attempts`` times.

    Expected:
    - The next try waits five seconds doubled per failure, capped at an hour.
    """
    assert backoff(attempts) == delay


def test_registry_keeps_consumers_per_topic_and_jobs_per_kind() -> None:
    """
    Condition:
    - Two consumers on one topic and one job kind are registered.

    Expected:
    - Both consumers are kept by name; the job handler by kind.
    """
    registry = Registry()

    async def handler(*_: object) -> None:
        return None

    registry.consumer("note.created", "a")(handler)
    registry.consumer("note.created", "b")(handler)
    registry.job("export")(handler)

    assert list(registry.consumers["note.created"]) == ["a", "b"]
    assert registry.jobs == {"export": handler}
