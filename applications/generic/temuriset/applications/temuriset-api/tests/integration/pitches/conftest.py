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


# The two J03 items from the prototype: a required pilot-budget question and an optional planned-feature question.
REVISION_ITEMS: list[dict[str, Any]] = [
    {
        "category": "Anggaran",
        "question": "Apakah biaya pilot sudah mencakup pengujian di dua lokasi?",
        "reason": "Kami perlu memastikan cakupan biaya sebelum menyiapkan uji.",
        "required": True,
        "due_date": "2026-11-09",
        "expected_evidence": "Rincian biaya per lokasi",
    },
    {
        "category": "Fitur",
        "question": "Kapan kapasitas 20 L/jam direncanakan tersedia?",
        "reason": "Membantu kami menyusun tahap uji berikutnya.",
        "required": False,
    },
]


async def submitted(loaded: World) -> dict[str, Any]:
    """Send F01 to A1 with its test report and return Mitra A's reading of it."""
    response = await submit(loaded, "F01", await preflight(loaded, "F01", "A1"))
    assert response.status_code == 201, response.text
    return (await loaded.recipients.clients["A"].get(f"/api/v1/pitches/{response.json()['pitch_id']}")).json()


async def act(client: AsyncClient, pitch: dict[str, Any], action: str, key: str, **body: Any) -> Response:
    """POST a pitch action as the client's acting party, against the version read."""
    return await client.post(
        f"/api/v1/pitches/{pitch['id']}/{action}",
        json={
            "acting_party_id": client.headers["X-Acting-Party"],
            "expected_version": pitch["version"],
            **body,
        },
        headers={"Idempotency-Key": key},
    )


async def reread(client: AsyncClient, pitch: dict[str, Any]) -> dict[str, Any]:
    """Read a pitch again."""
    return (await client.get(f"/api/v1/pitches/{pitch['id']}")).json()


async def answer(
    client: AsyncClient, pitch: dict[str, Any], item_id: str, response: str, version: int | None = None, **body: Any
) -> Response:
    """Save a draft answer as the requester."""
    return await client.put(
        f"/api/v1/pitches/{pitch['id']}/revision-items/{item_id}/answer",
        json={
            "acting_party_id": client.headers["X-Acting-Party"],
            "expected_version": version,
            "response": response,
            **body,
        },
    )
