"""End-to-end authorization for queued exports and JSON delivery (AC06, AC63)."""

from base64 import b64decode
from collections.abc import Awaitable, Callable
from datetime import timedelta
from pathlib import Path
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import text

from app.core import clock
from app.core.database import get_engine

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("clean_tables")]
Fixture = Callable[..., Awaitable[Any]]
PDF = b"%PDF-1.4 Source evidence bytes"


async def _document(client: AsyncClient, party: str, work: Fixture) -> str:
    intent = await client.post(
        "/api/v1/documents/upload-intents",
        json={
            "acting_party_id": party,
            "title": "Private evidence",
            "kind": "evidence",
            "media_type": "application/pdf",
            "size_bytes": len(PDF),
        },
    )
    assert intent.status_code == 201, intent.text
    uploaded = await client.put(intent.json()["upload_url"], content=PDF)
    assert uploaded.status_code == 202, uploaded.text
    await work(drain=True)
    return uploaded.json()["document_id"]


async def _grant(client: AsyncClient, party: str, recipient: str, document: str, key: str) -> str:
    grant = await client.post(
        f"/api/v1/documents/{document}/grants",
        json={
            "acting_party_id": party,
            "version": 1,
            "grantee_party_id": recipient,
            "purpose": "pitch",
        },
        headers={"Idempotency-Key": key},
    )
    assert grant.status_code == 201, grant.text
    return grant.json()["id"]


async def _export(client: AsyncClient, party: str, selections: list[dict], key: str = "export") -> dict:
    response = await client.post(
        "/api/v1/exports",
        json={"acting_party_id": party, "expected_version": None, "selections": selections},
        headers={"Idempotency-Key": key},
    )
    assert response.status_code == 202, response.text
    return response.json()


@pytest.mark.parametrize("change", ["revoke", "expire"])
@pytest.mark.parametrize("before_generation", [True, False])
async def test_grant_change_expires_export_even_when_replacement_is_valid(
    client: AsyncClient,
    new_client: Callable[[], AsyncClient],
    sign_up: Fixture,
    work: Fixture,
    storage: Path,
    before_generation: bool,
    change: str,
) -> None:
    """
    Condition:
    - The pinned grant is revoked or expires before generation or before delivery.

    Expected:
    - Denial persists expiry, replacement grants cannot revive the result, and private bytes are removed.
    """
    owner = (await sign_up(client, "owner-doc@example.com"))["active_party_id"]
    document = await _document(client, owner, work)
    async with new_client() as recipient:
        party = (await sign_up(recipient, "recipient-doc@example.com"))["active_party_id"]
        grant = await _grant(client, owner, party, document, "grant-1")
        job = await _export(recipient, party, [{"kind": "DOCUMENT", "document_id": document, "version": 1}])
        assert job["status"] == "PENDING"
        path = f"/api/v1/exports/{job['id']}"
        if not before_generation:
            await work(drain=True)
            status = await recipient.get(path)
            assert status.json()["status"] == "SUCCEEDED", status.text
            full = await recipient.get(f"{path}/download")
            assert full.status_code == 200, full.text
            assert full.headers["cache-control"] == "private, no-store"
            assert "attachment" in full.headers["content-disposition"]
            assert b64decode(full.json()["documents"][0]["content_base64"]) == PDF
        if change == "expire":
            async with get_engine().begin() as connection:
                await connection.execute(
                    text("UPDATE document_grants SET expires_at = :at WHERE id = :id"),
                    {"id": grant, "at": clock.now() - timedelta(seconds=1)},
                )
        else:
            revoke = await client.post(
                f"/api/v1/grants/{grant}/revoke",
                json={"acting_party_id": owner},
                headers={"Idempotency-Key": "revoke"},
            )
            assert revoke.status_code == 200, revoke.text
            await _grant(client, owner, party, document, "grant-2")
        if before_generation:
            await work(drain=True)
        denied = await recipient.get(f"{path}/download")
        assert denied.status_code in {403, 409}, denied.text
        assert denied.json()["error"]["code"] in {"GRANT_REVOKED", "FILE_NOT_AVAILABLE"}
        status = await recipient.get(path)
        assert status.json()["status"] == "EXPIRED"
        await work(drain=True)
        assert not list(storage.glob("portability-export-*"))


@pytest.mark.parametrize("before_generation", [True, False])
async def test_membership_loss_expires_export_and_context_switch_alone_does_not(
    client: AsyncClient,
    new_client: Callable[[], AsyncClient],
    sign_up: Fixture,
    work: Fixture,
    before_generation: bool,
) -> None:
    """
    Condition:
    - A requester switches to their personal party and returns, then loses organization membership.

    Expected:
    - A valid membership can resume after switching context, while removal expires the original job permanently.
    """
    await sign_up(client, "manager@example.com")
    org = (
        await client.post(
            "/api/v1/organizations",
            json={"name": "Export Workspace", "kind": "company"},
            headers={"Idempotency-Key": "workspace"},
        )
    ).json()
    party = org["party_id"]
    await client.put("/api/v1/me/context", json={"party_id": party})
    document = await _document(client, party, work)
    email = "workspace-member@example.com"
    invited = await client.post(
        f"/api/v1/organizations/{org['id']}/invitations",
        json={"acting_party_id": party, "email": email, "capabilities": ["edit_portfolio"]},
        headers={"Idempotency-Key": "invite"},
    )
    assert invited.status_code == 201, invited.text
    mail = (await client.get("/api/v1/dev/mailbox", params={"email": email})).json()[0]["body"]
    async with new_client() as member:
        me = await sign_up(member, email)
        personal = me["active_party_id"]
        accepted = await member.post(f"/api/v1/invitations/{mail.rsplit('/', 1)[1]}/accept")
        assert accepted.status_code == 200, accepted.text
        await member.put("/api/v1/me/context", json={"party_id": party})
        job = await _export(member, party, [{"kind": "DOCUMENT", "document_id": document, "version": 1}])
        path = f"/api/v1/exports/{job['id']}"
        if not before_generation:
            await work(drain=True)
        # A different account in the same workspace cannot invalidate the result or learn its operation.
        assert (await client.get(path)).status_code == 404
        assert (await client.get(f"/api/v1/operations/{job['operation_id']}")).status_code == 404
        await member.put("/api/v1/me/context", json={"party_id": personal})
        assert (await member.get(f"{path}/download")).status_code == 404
        await member.put("/api/v1/me/context", json={"party_id": party})
        assert (await member.get(path)).json()["status"] == ("PENDING" if before_generation else "SUCCEEDED")
        removed = await client.request(
            "DELETE",
            f"/api/v1/organizations/{org['id']}/members/{me['account']['id']}",
            json={"acting_party_id": party, "expected_version": 1},
        )
        assert removed.status_code == 204, removed.text
        if before_generation:
            await work(drain=True)
        assert (await member.get(f"{path}/download")).status_code == 404
    async with get_engine().connect() as connection:
        state = (
            await connection.execute(
                text("SELECT expired FROM portability_export_jobs WHERE id = :id"),
                {"id": job["id"]},
            )
        ).scalar_one()
    assert state is True


async def test_export_defaults_to_allowlisted_fields_and_expires_after_24_hours(
    client: AsyncClient,
    sign_up: Fixture,
    published_invention: Fixture,
    work: Fixture,
    storage: Path,
) -> None:
    """
    Condition:
    - A portfolio export has a published invention and access is attempted after its lifetime.

    Expected:
    - The valid artifact contains portable fields, then access expires before cleanup runs.
    """
    party = (await sign_up(client, "invention-export@example.com"))["active_party_id"]
    invention = await published_invention(client)
    selected = [{"kind": "INVENTION", "invention_id": invention["id"], "version": "PUBLISHED"}]
    job = await _export(client, party, selected)
    assert await _export(client, party, selected) == job
    await work(drain=True)
    path = f"/api/v1/exports/{job['id']}"
    result = await client.get(f"{path}/download")
    assert result.status_code == 200, result.text
    fields = result.json()["inventions"][0]["fields"]
    assert fields["title"] == invention["published"]["title"]
    assert "private_notes" not in fields and "claims" not in fields
    assert "document_version_id" not in fields["facts"][0]
    with clock.frozen(clock.now() + timedelta(hours=25)):
        assert (await client.get(f"{path}/download")).json()["error"]["code"] == "FILE_NOT_AVAILABLE"
        assert (await client.get(path)).json()["status"] == "EXPIRED"
        await work(drain=True)
    assert not list(storage.glob("portability-export-*"))
