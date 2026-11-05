"""Fixtures for partner intake: a signed-in partner, an unrelated party, and Recipients A–E."""

from collections.abc import AsyncIterator, Callable

import pytest
from httpx import AsyncClient

from tests.factories.recipients import LoadedRecipients, load_recipients


@pytest.fixture
async def partner(client: AsyncClient, sign_up) -> AsyncIterator[AsyncClient]:
    """A partner acting as its personal party, with no profile yet."""
    me = await sign_up(client, "mitra@example.com", persona="mitra", name="Mitra Uji")
    client.headers["X-Acting-Party"] = me["active_party_id"]
    yield client


@pytest.fixture
async def stranger(new_client: Callable[[], AsyncClient], sign_up) -> AsyncIterator[AsyncClient]:
    """An unrelated party, signed in from another browser."""
    async with new_client() as other:
        me = await sign_up(other, "stranger@example.com", name="Stranger")
        other.headers["X-Acting-Party"] = me["active_party_id"]
        yield other


@pytest.fixture
async def recipients(new_client: Callable[[], AsyncClient], sign_up) -> AsyncIterator[LoadedRecipients]:
    """Recipients A–E with their opportunities active."""
    loaded = await load_recipients(new_client, sign_up)
    yield loaded
    await loaded.close()


@pytest.fixture
async def limited_member(
    client: AsyncClient, new_client: Callable[[], AsyncClient], sign_up
) -> AsyncIterator[tuple[AsyncClient, str]]:
    """A member who holds only ``schedule``, acting as an organization, with that organization's party."""
    await sign_up(client, "owner@example.com", persona="mitra", name="Owner")
    organization = (
        await client.post(
            "/api/v1/organizations", json={"name": "Org", "kind": "company"}, headers={"Idempotency-Key": "o"}
        )
    ).json()
    party = organization["party_id"]
    await client.put("/api/v1/me/context", json={"party_id": party})
    await client.post(
        f"/api/v1/organizations/{organization['id']}/invitations",
        json={"acting_party_id": party, "email": "eve@example.com", "capabilities": ["schedule"]},
        headers={"Idempotency-Key": "i"},
    )
    mail = (await client.get("/api/v1/dev/mailbox", params={"email": "eve@example.com"})).json()
    token = mail[0]["body"].rsplit("/", 1)[1]
    async with new_client() as eve:
        await sign_up(eve, "eve@example.com", name="Eve")
        await eve.post(f"/api/v1/invitations/{token}/accept")
        await eve.put("/api/v1/me/context", json={"party_id": party})
        yield eve, party
