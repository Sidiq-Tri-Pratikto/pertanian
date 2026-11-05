"""Fixtures for preflight and pitches: the matching world, plus helpers that preflight and submit."""

from typing import Any

from httpx import AsyncClient, Response

from tests.factories.inventors import INVENTIONS
from tests.integration.matching.conftest import World, make_world, world  # noqa: F401 - shared fixtures


def client_of(loaded: World, fixture: str) -> tuple[AsyncClient, str]:
    """The client and party of the account that holds a fixture such as ``F01`` or ``FRaise01``."""
    account = "bima" if fixture == "FRaise01" else INVENTIONS[fixture]["account"]
    return loaded.inventors.clients[account], loaded.inventors.parties[account]


def source_of(loaded: World, fixture: str) -> tuple[str, str]:
    """Source type and id of a fixture."""
    if fixture == "FRaise01":
        return "FUNDING_REQUEST", loaded.inventors.funding
    return "SUPPORT_REQUEST", loaded.inventors.support_requests[fixture]


async def preflight(loaded: World, fixture: str, target: str) -> dict[str, Any]:
    """Preflight a fixture's source against a target such as ``A1``."""
    client, party = client_of(loaded, fixture)
    source_type, source_id = source_of(loaded, fixture)
    response = await client.post(
        "/api/v1/pitches/preflight",
        json={
            "acting_party_id": party,
            "source_type": source_type,
            "source_id": source_id,
            "opportunity_id": loaded.opportunity(target),
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


async def submit(
    loaded: World,
    fixture: str,
    checked: dict[str, Any],
    *,
    files: list[dict[str, Any]] | None = None,
    brief: str | None = None,
    key: str = "submit",
) -> Response:
    """Submit a preflight; by default with every shareable file and the template brief."""
    client, party = client_of(loaded, fixture)
    chosen = (
        [{"document_id": item["document_id"], "version": item["version"]} for item in checked["shareable_files"]]
        if files is None
        else files
    )
    return await client.post(
        "/api/v1/pitches",
        json={
            "acting_party_id": party,
            "preflight_token": checked["token"],
            "brief": checked["brief"]["text"] if brief is None else brief,
            "files": chosen,
        },
        headers={"Idempotency-Key": key},
    )
