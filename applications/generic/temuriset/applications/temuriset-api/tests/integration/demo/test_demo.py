"""The labelled demo through HTTP against Postgres: picker, sign-in, reset and activity (spec 021)."""

import json
from collections.abc import Iterator
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import text

from app.core.database import get_session_factory
from app.core.settings import get_settings

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("clean_tables")]


@pytest.fixture
def demo_on(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Demo mode for this test only."""
    monkeypatch.setattr(get_settings(), "demo_mode", True)
    yield


async def _reset(client: AsyncClient) -> dict[str, Any]:
    response = await client.post("/api/v1/demo/reset")
    assert response.status_code == 200, response.text
    return response.json()


async def _sign_in(client: AsyncClient, key: str) -> dict[str, Any]:
    response = await client.post("/api/v1/demo/sign-in", json={"key": key})
    assert response.status_code == 200, response.text
    me = response.json()
    party = me["organizations"][0]["party_id"] if me["organizations"] else me["active_party_id"]
    await client.put("/api/v1/me/context", json={"party_id": party})
    client.headers["X-Acting-Party"] = party
    return me


async def _snapshot() -> dict[str, list[tuple[Any, ...]]]:
    async with get_session_factory()() as session:
        return {
            table: [tuple(row) for row in await session.execute(text(f"SELECT id, version FROM {table} ORDER BY id"))]  # noqa: S608 - fixed table names
            for table in ("inventions", "support_requests", "funding_requests", "opportunities", "partner_profiles")
        }


async def test_demo_routes_do_not_exist_outside_demo_mode(client: AsyncClient) -> None:
    """
    Condition:
    - Demo mode is off.

    Expected:
    - Every demo route answers NOT_FOUND and the manifest says no demo.
    """
    responses = [
        await client.get("/api/v1/demo/accounts"),
        await client.post("/api/v1/demo/sign-in", json={"key": "inovator-a"}),
        await client.post("/api/v1/demo/reset", json={}),
    ]

    assert [response.status_code for response in responses] == [404, 404, 404]
    assert (await client.get("/api/v1/capabilities")).json()["demo"] is False


@pytest.mark.usefixtures("demo_on")
async def test_the_picker_lists_labelled_accounts_and_signs_in_without_email(client: AsyncClient) -> None:
    """
    Condition:
    - Demo mode is on and the demo is seeded (scenario 1).

    Expected:
    - Three accounts labelled "Akun demo · data fiktif"; signing in as Inovator A gives a demo account; asking for an
      email code for it sends nothing; an unknown key is NOT_FOUND.
    """
    await _reset(client)
    accounts = (await client.get("/api/v1/demo/accounts")).json()
    me = await _sign_in(client, "inovator-a")
    code = await client.post("/api/v1/auth/code", json={"email": "inovator-a@demo.invalid", "purpose": "sign_in"})
    unknown = await client.post("/api/v1/demo/sign-in", json={"key": "nobody"})

    assert {account["label"] for account in accounts} == {"Akun demo · data fiktif"}
    assert all(account["summary"] for account in accounts)
    assert accounts[0]["summary"].startswith("Inovator perorangan")
    assert [account["key"] for account in accounts] == ["inovator-a", "investor-a", "investor-b"]
    assert (me["account"]["kind"], me["account"]["display_name"]) == ("demo", "Inovator A")
    assert code.status_code == 202
    assert (await client.get("/api/v1/dev/mailbox", params={"email": "inovator-a@demo.invalid"})).json() == []
    assert unknown.status_code == 404
    assert (await client.get("/api/v1/capabilities")).json()["demo"] is True


@pytest.mark.usefixtures("demo_on")
async def test_signing_in_before_anyone_seeded_the_demo_seeds_it_first(client: AsyncClient) -> None:
    """
    Condition:
    - Demo mode is on but nobody ran the seed or a reset yet, as on a fresh demo deployment.

    Expected:
    - Signing in as Inovator A seeds the demo and succeeds, and Produk A is there.
    """
    me = await _sign_in(client, "inovator-a")

    assert (me["account"]["kind"], me["account"]["display_name"]) == ("demo", "Inovator A")
    titles = [invention["title"] for invention in (await client.get("/api/v1/inventions")).json()]
    assert "ClearSpring" in titles


@pytest.mark.usefixtures("demo_on")
async def test_reset_twice_keeps_ids_and_versions_and_spares_real_accounts(
    client: AsyncClient, new_client, sign_up, published_invention
) -> None:
    """
    Condition:
    - Real and demo accounts create records; the demo is reset, used, then reset again (scenario 3, SC-001).

    Expected:
    - Resets yield identical ids and versions. Demo reports and privacy requests are removed. Real records stay.
    """
    async with new_client() as real:
        me = await sign_up(real, "real@example.com", name="Pengguna Nyata")
        real.headers["X-Acting-Party"] = me["active_party_id"]
        kept = await published_invention(real, "Inovasi pengguna nyata")
        report = await real.post(
            "/api/v1/reports",
            json={"acting_party_id": me["active_party_id"], "expected_version": None, "reason": "Laporan nyata"},
            headers={"Idempotency-Key": "real-report"},
        )
        assert report.status_code == 201, report.text
    await _reset(client)
    first = await _snapshot()
    await _sign_in(client, "inovator-a")
    invention = (await client.get("/api/v1/inventions")).json()[0]
    await client.post(
        f"/api/v1/inventions/{invention['id']}/archive",
        json={"acting_party_id": client.headers["X-Acting-Party"], "expected_version": invention["version"]},
        headers={"Idempotency-Key": "demo-archive"},
    )
    demo_party = client.headers["X-Acting-Party"]
    demo_report = await client.post(
        "/api/v1/reports",
        json={"acting_party_id": demo_party, "expected_version": None, "reason": "Laporan demo"},
        headers={"Idempotency-Key": "demo-report"},
    )
    demo_export = await client.post(
        "/api/v1/privacy-requests",
        json={"acting_party_id": demo_party, "expected_version": None, "kind": "EXPORT"},
        headers={"Idempotency-Key": "demo-export"},
    )
    assert demo_report.status_code == demo_export.status_code == 201
    await _reset(client)

    assert await _snapshot() == first
    await _sign_in(client, "inovator-a")
    assert (await client.get("/api/v1/reports")).json() == []
    assert (await client.get("/api/v1/privacy-requests")).json() == []
    async with new_client() as real:
        await sign_up(real, "real@example.com", name="Pengguna Nyata")
        assert (await real.get(f"/api/v1/inventions/{kept['id']}")).status_code == 200
        assert (await real.get(f"/api/v1/reports/{report.json()['id']}")).status_code == 200


@pytest.mark.usefixtures("demo_on")
async def test_demo_activity_counts_nowhere(client: AsyncClient, new_client, sign_up) -> None:
    """
    Condition:
    - A real partner reads discovery; then demo accounts save and view an invention many times (AC03).

    Expected:
    - The real partner's discovery is unchanged: no count, trend or ranking moves.
    """
    await _reset(client)
    async with new_client() as partner:
        me = await sign_up(partner, "mitra-nyata@example.com", persona="mitra", name="Mitra Nyata")
        partner.headers["X-Acting-Party"] = me["active_party_id"]
        before = (await partner.get("/api/v1/discovery")).json()
        await _sign_in(client, "inovator-a")
        target = {"subject_id": (await client.get("/api/v1/inventions")).json()[0]["id"]}
        await _sign_in(client, "investor-a")
        for _ in range(20):
            await client.get(f"/api/v1/inventions/{target['subject_id']}/public")
        await client.put(
            f"/api/v1/saved-items/INVENTION/{target['subject_id']}",
            json={"acting_party_id": client.headers["X-Acting-Party"]},
        )
        after = (await partner.get("/api/v1/discovery")).json()

    assert after == before
    assert "trend" not in json.dumps(before).lower()
