"""Inventors F01–F06 and FRaise01 from the fixtures, as plain data and as a loader through the API (specs 019, 021).

The data lives in ``app/demo/service/data.py`` so demo seeding (021) uses the same values.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from app.demo.service.data import (  # noqa: F401 - re-exported for tests
    ACCOUNTS,
    F01_BUDGET,
    F01_GAP_BUDGET,
    FRAISE01,
    INVENTIONS,
    SUPPORT_REQUESTS,
)


@dataclass
class LoadedInventors:
    """What ``load_inventors`` made.

    Attributes:
        parties (dict[str, str]): Party id per account, such as ``rani``.
        inventions (dict[str, str]): Invention id per fixture, such as ``F01``.
        support_requests (dict[str, str]): Support request id per fixture.
        funding (str): FRaise01's id.
        clients (dict[str, Any]): A signed-in client per account. The caller closes them.
    """

    parties: dict[str, str] = field(default_factory=dict)
    inventions: dict[str, str] = field(default_factory=dict)
    support_requests: dict[str, str] = field(default_factory=dict)
    funding: str = ""
    clients: dict[str, Any] = field(default_factory=dict)

    async def close(self) -> None:
        """Close every client."""
        for client in self.clients.values():
            await client.aclose()


def _ok(response: Any, status: int = 200) -> dict[str, Any]:
    assert response.status_code == status, response.text  # noqa: S101 - a test fixture stops on a broken setup
    return response.json()


async def _account(client: Any, key: str, sign_up: Callable[..., Awaitable[dict]]) -> str:
    account = ACCOUNTS[key]
    me = await sign_up(client, f"{key}@example.com", name=account["name"])
    if account["organization"] is None:
        client.headers["X-Acting-Party"] = me["active_party_id"]
        return me["active_party_id"]
    organization = _ok(
        await client.post(
            "/api/v1/organizations",
            json={"name": account["organization"], "kind": "company"},
            headers={"Idempotency-Key": f"organization-{key}"},
        ),
        201,
    )
    await client.put("/api/v1/me/context", json={"party_id": organization["party_id"]})
    client.headers["X-Acting-Party"] = organization["party_id"]
    return organization["party_id"]


async def _document(client: Any, party_id: str, title: str) -> str:
    """Upload a small PDF, let the scanner pass it, and return its version id."""
    # Imported here so that reading the plain data above needs no application or database.
    from uuid import UUID  # noqa: PLC0415

    from sqlalchemy import select  # noqa: PLC0415

    import app.documents.service.jobs  # noqa: F401, PLC0415 - registers the scanner job
    from app.core.database import get_session_factory  # noqa: PLC0415
    from app.documents.repository.sqlalchemy.models import DocumentVersionRecord  # noqa: PLC0415
    from app.worker.loop import run_jobs  # noqa: PLC0415
    from app.worker.registry import registry  # noqa: PLC0415

    content = b"%PDF-1.4\n" + title.encode() + b"\n%%EOF\n"
    intent = _ok(
        await client.post(
            "/api/v1/documents/upload-intents",
            json={
                "acting_party_id": party_id,
                "title": title,
                "kind": "evidence",
                "media_type": "application/pdf",
                "size_bytes": len(content),
            },
        ),
        201,
    )
    uploaded = _ok(await client.put(intent["upload_url"], content=content), 202)
    while await run_jobs(get_session_factory(), registry):
        pass
    async with get_session_factory()() as session:
        version = await session.scalar(
            select(DocumentVersionRecord.id).where(DocumentVersionRecord.document_id == UUID(uploaded["document_id"]))
        )
    return str(version)


async def publish_invention(client: Any, party_id: str, key: str) -> str:
    """Create, fill and publish one fixture invention through the API.

    Args:
        client (Any): A client acting for the party.
        party_id (str): The managing party.
        key (str): Fixture, such as ``F01``.

    Returns:
        str: The invention id.
    """
    fixture = INVENTIONS[key]
    content = {**fixture["content"], "facts": [dict(fact) for fact in fixture["content"]["facts"]]}
    for fact in content["facts"]:
        if fact["key"] in fixture.get("documents", {}):
            fact["document_version_id"] = await _document(client, party_id, fixture["documents"][fact["key"]])
    created = _ok(
        await client.post(
            "/api/v1/inventions", json={"acting_party_id": party_id}, headers={"Idempotency-Key": f"create-{key}"}
        ),
        201,
    )
    saved = _ok(
        await client.put(
            f"/api/v1/inventions/{created['id']}/draft",
            json={"acting_party_id": party_id, "expected_version": created["version"], **content},
            headers={"Idempotency-Key": f"draft-{key}"},
        )
    )
    _ok(
        await client.post(
            f"/api/v1/inventions/{created['id']}/publish",
            json={"acting_party_id": party_id, "expected_version": saved["version"]},
            headers={"Idempotency-Key": f"publish-{key}"},
        )
    )
    return created["id"]


async def _activate(client: Any, path: str, party_id: str, version: int, key: str) -> dict[str, Any]:
    return _ok(
        await client.post(
            f"{path}/activate",
            json={"acting_party_id": party_id, "expected_version": version},
            headers={"Idempotency-Key": key},
        )
    )


async def load_inventors(
    new_client: Callable[[], Any],
    sign_up: Callable[..., Awaitable[dict]],
    *,
    gap: bool = False,
    proposed_entity: bool = False,
) -> LoadedInventors:
    """Create F01–F06, their needs and FRaise01 through the API, all active.

    Args:
        new_client (Callable[[], Any]): Makes a client with its own cookie jar.
        sign_up (Callable[..., Awaitable[dict]]): Signs a client up.
        gap (bool, optional): F01-GAP: F01's range is not filled in yet. Defaults to False.
        proposed_entity (bool, optional): FRaise01 for a company not founded yet. Defaults to False.

    Returns:
        LoadedInventors: Parties, inventions, needs, the raise and a client per account.
    """
    loaded = LoadedInventors()
    for key in ACCOUNTS:
        client = new_client()
        loaded.clients[key] = client
        loaded.parties[key] = await _account(client, key, sign_up)
    for key, fixture in INVENTIONS.items():
        account = fixture["account"]
        loaded.inventions[key] = await publish_invention(loaded.clients[account], loaded.parties[account], key)
    for key, content in SUPPORT_REQUESTS.items():
        account = INVENTIONS[key]["account"]
        client, party_id = loaded.clients[account], loaded.parties[account]
        body = {**content, "budget": F01_GAP_BUDGET if key == "F01" and gap else content["budget"]}
        created = _ok(
            await client.post(
                "/api/v1/support-requests",
                json={"acting_party_id": party_id, "invention_id": loaded.inventions[key], **body},
                headers={"Idempotency-Key": f"support-{key}"},
            ),
            201,
        )
        await _activate(client, f"/api/v1/support-requests/{created['id']}", party_id, created["version"], f"a-{key}")
        loaded.support_requests[key] = created["id"]
    client, party_id = loaded.clients["bima"], loaded.parties["bima"]
    subject: dict[str, Any] = {"subject_type": "PROPOSED_ENTITY", "proposed_name": FRAISE01["entity"]["name"]}
    if not proposed_entity:
        entity = _ok(
            await client.post(
                "/api/v1/legal-entities",
                json={"acting_party_id": party_id, **FRAISE01["entity"]},
                headers={"Idempotency-Key": "entity-dcm"},
            ),
            201,
        )
        subject = {"subject_type": "EXISTING_ENTITY", "legal_entity_id": entity["id"]}
    raise_ = _ok(
        await client.post(
            "/api/v1/funding-requests",
            json={
                "acting_party_id": party_id,
                **subject,
                **FRAISE01["content"],
                "invention_ids": [loaded.inventions[key] for key in FRAISE01["inventions"]],
            },
            headers={"Idempotency-Key": "fraise01"},
        ),
        201,
    )
    await _activate(client, f"/api/v1/funding-requests/{raise_['id']}", party_id, raise_["version"], "a-fraise01")
    loaded.funding = raise_["id"]
    return loaded
