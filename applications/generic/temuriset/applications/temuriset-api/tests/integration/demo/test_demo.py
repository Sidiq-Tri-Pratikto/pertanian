"""The labelled demo through HTTP against Postgres: picker, sign-in, reset, variants and goldens (spec 021)."""

import json
from collections.abc import Iterator
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import text

from app.core.database import get_session_factory
from app.core.settings import get_settings
from tests.integration.matching.test_matches import GOLDEN, _golden_text

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("clean_tables")]


@pytest.fixture
def demo_on(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Demo mode for this test only."""
    monkeypatch.setattr(get_settings(), "demo_mode", True)
    yield


async def _reset(client: AsyncClient, **variants: bool) -> dict[str, Any]:
    response = await client.post("/api/v1/demo/reset", json=variants)
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


async def _match_first_need(client: AsyncClient) -> dict[str, Any]:
    need = (await client.get("/api/v1/support-requests")).json()[0]
    response = await client.post(
        "/api/v1/matches",
        json={
            "acting_party_id": client.headers["X-Acting-Party"],
            "source_type": "SUPPORT_REQUEST",
            "source_id": need["id"],
        },
        headers={"Idempotency-Key": f"demo-{need['id']}-{need['version']}"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def _a1(run: dict[str, Any]) -> dict[str, Any]:
    return next(item for item in run["results"] + run["excluded"] if item["title"] == "Validasi prototipe enam bulan")


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
        await client.post("/api/v1/demo/sign-in", json={"key": "rani"}),
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
    - Ten accounts labelled "Akun demo · data fiktif"; signing in as Rani gives a demo account; asking for an email
      code for her sends nothing; an unknown key is NOT_FOUND.
    """
    await _reset(client)
    accounts = (await client.get("/api/v1/demo/accounts")).json()
    me = await _sign_in(client, "rani")
    code = await client.post("/api/v1/auth/code", json={"email": "rani@demo.invalid", "purpose": "sign_in"})
    unknown = await client.post("/api/v1/demo/sign-in", json={"key": "nobody"})

    assert {account["label"] for account in accounts} == {"Akun demo · data fiktif"}
    assert [account["key"] for account in accounts][:5] == ["rani", "dewi", "galih", "bima", "sinta"]
    assert len(accounts) == 10
    assert (me["account"]["kind"], me["account"]["display_name"]) == ("demo", "Rani")
    assert code.status_code == 202
    assert (await client.get("/api/v1/dev/mailbox", params={"email": "rani@demo.invalid"})).json() == []
    assert unknown.status_code == 404
    assert (await client.get("/api/v1/capabilities")).json()["demo"] is True


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
    await _sign_in(client, "rani")
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
    await _sign_in(client, "rani")
    assert (await client.get("/api/v1/reports")).json() == []
    assert (await client.get("/api/v1/privacy-requests")).json() == []
    async with new_client() as real:
        await sign_up(real, "real@example.com", name="Pengguna Nyata")
        assert (await real.get(f"/api/v1/inventions/{kept['id']}")).status_code == 200
        assert (await real.get(f"/api/v1/reports/{report.json()['id']}")).status_code == 200


@pytest.mark.usefixtures("demo_on")
async def test_goldens_hold_on_seeded_data_and_variants_are_selectable(client: AsyncClient) -> None:
    """
    Condition:
    - Rani matches F01 against A1 on the baseline demo, then on F01-GAP and F01-SCAN (FR-003, SC-001).

    Expected:
    - The baseline equals ``match-f01-a1.json`` byte for byte; GAP equals ``match-f01gap-a1.json``; SCAN still passes
      the file, whose text needs a person.
    """
    await _reset(client)
    await _sign_in(client, "rani")
    assert _golden_text(_a1(await _match_first_need(client))) == (GOLDEN / "match-f01-a1.json").read_text()

    await _reset(client, gap=True)
    await _sign_in(client, "rani")
    assert _golden_text(_a1(await _match_first_need(client))) == (GOLDEN / "match-f01gap-a1.json").read_text()

    await _reset(client, scan=True)
    await _sign_in(client, "rani")
    scanned = _a1(await _match_first_need(client))
    documents = (await client.get("/api/v1/documents")).json()
    assert next(row for row in scanned["rows"] if row["label"] == "Berkas uji fungsi")["result"] == "PASS"
    assert documents[0]["versions"][0]["extraction_state"] == "NEEDS_MANUAL_INPUT"


@pytest.mark.usefixtures("demo_on")
async def test_proposed_entity_variant_fails_b1(client: AsyncClient) -> None:
    """
    Condition:
    - The demo reset with FRaise01 for a company not founded yet; Bima matches it.

    Expected:
    - B1's entity requirement fails.
    """
    await _reset(client, proposed_entity=True)
    await _sign_in(client, "bima")
    raise_ = (await client.get("/api/v1/funding-requests")).json()[0]
    run = (
        await client.post(
            "/api/v1/matches",
            json={
                "acting_party_id": client.headers["X-Acting-Party"],
                "source_type": "FUNDING_REQUEST",
                "source_id": raise_["id"],
            },
            headers={"Idempotency-Key": "demo-raise"},
        )
    ).json()
    b1 = next(item for item in run["results"] + run["excluded"] if item["title"] == "Investasi ekuitas pre-seed")

    assert next(row for row in b1["rows"] if row["label"] == "Badan usaha yang sudah berdiri")["result"] == "FAIL"


@pytest.mark.usefixtures("demo_on")
async def test_demo_activity_counts_nowhere(client: AsyncClient, new_client, sign_up) -> None:
    """
    Condition:
    - A real partner reads discovery; then demo accounts save and view an invention many times (AC03).

    Expected:
    - The real partner's discovery is unchanged: no count, trend or ranking moves; F06 stays curated by the
      operator's flag, not by activity.
    """
    await _reset(client)
    async with new_client() as partner:
        me = await sign_up(partner, "mitra-nyata@example.com", persona="mitra", name="Mitra Nyata")
        partner.headers["X-Acting-Party"] = me["active_party_id"]
        before = (await partner.get("/api/v1/discovery")).json()
        await _sign_in(client, "mitra-a")
        target = before["sections"][1]["items"][0]
        for _ in range(20):
            await client.get(f"/api/v1/inventions/{target['subject_id']}/public")
        await client.put(
            f"/api/v1/saved-items/INVENTION/{target['subject_id']}",
            json={"acting_party_id": client.headers["X-Acting-Party"]},
        )
        after = (await partner.get("/api/v1/discovery")).json()

    assert after == before
    assert [item["title"] for item in before["sections"][2]["items"]] == ["GridShare"]
    assert "trend" not in json.dumps(before).lower()
