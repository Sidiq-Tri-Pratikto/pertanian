"""Portability worker and upload fixtures."""

import json
from collections.abc import Awaitable, Callable
from typing import Any

import pytest
from httpx import AsyncClient

import app.documents.service.jobs  # noqa: F401 - register the document worker for real uploads
import app.portability.service.jobs  # noqa: F401 - register the portability worker
from app.core.database import get_session_factory
from app.worker.loop import run_jobs
from app.worker.registry import registry


@pytest.fixture
def work() -> Callable[..., Awaitable[int]]:
    """Run one batch or drain due jobs, leaving scheduled expiry jobs alone."""

    async def run(*, drain: bool = False) -> int:
        count = await run_jobs(get_session_factory(), registry)
        if drain:
            while await run_jobs(get_session_factory(), registry):
                pass
        return count

    return run


@pytest.fixture
def upload() -> Callable[..., Awaitable[dict[str, Any]]]:
    """Stage a real version 1 JSON upload with optional explicit mapping."""

    async def stage(
        client: AsyncClient,
        party: str,
        key: str,
        rows: list[dict],
        *,
        map_private: bool = False,
        profile: dict | None = None,
    ) -> dict:
        file = {
            "schema_version": 1,
            "external_system": "example-registry",
            "provenance": {"source": "Private source"},
            "inventions": [{"provenance": {"source": "Private source"}, **row} for row in rows],
            "partner_profile": {"provenance": {"source": "Private source"}, **profile} if profile else None,
        }
        response = await client.post(
            "/api/v1/imports/validate",
            params={"acting_party_id": party, "map_private_notes": str(map_private).lower()},
            content=json.dumps(file),
            headers={"Content-Type": "application/json", "Idempotency-Key": key},
        )
        assert response.status_code == 202, response.text
        return response.json()

    return stage
