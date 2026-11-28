"""Integration tests for GET /api/v1/fit and discovery best_fit ordering (spec 059)."""

import pytest
from httpx import AsyncClient

from app.core.settings import get_settings
from app.demo.service import scenario
from tests.factories.inventors import INVENTIONS
from tests.factories.recipients import create_opportunity, move_opportunity, save_profile
from tests.integration.matching.conftest import World

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("clean_tables")]


async def test_fit_endpoint_scores_by_investor_by_product_preview_and_isolation(world: World) -> None:
    """
    Condition:
    - Rani has F01 (with active need) and publishes a second product WITHOUT a need; Galih queries /fit with Rani's id.

    Expected:
    - Filtering by partner returns both of Rani's products × Mitra A's mandates; need-less product is labelled
      preview=True with money/form UNKNOWN and no_need recommendation first; Galih gets [] for Rani's product.
    """
    rani = world.inventors.clients["rani"]
    rani_party = world.inventors.parties["rani"]
    galih = world.inventors.clients["galih"]
    mitra_a_party = world.recipients.parties["A"]

    # Create a second published invention for Rani with no support need (preview mode).
    created = (
        await rani.post("/api/v1/inventions", json={"acting_party_id": rani_party}, headers={"Idempotency-Key": "p2"})
    ).json()
    saved = (
        await rani.put(
            f"/api/v1/inventions/{created['id']}/draft",
            json={
                "acting_party_id": rani_party,
                "expected_version": created["version"],
                **INVENTIONS["F06"]["content"],
                "title": "Preview Solar",
            },
            headers={"Idempotency-Key": "p2-draft"},
        )
    ).json()
    pub = await rani.post(
        f"/api/v1/inventions/{created['id']}/publish",
        json={"acting_party_id": rani_party, "expected_version": saved["version"]},
        headers={"Idempotency-Key": "p2-pub"},
    )
    assert pub.status_code == 200, pub.text

    by_investor = await rani.get("/api/v1/fit", params={"partner_party_id": mitra_a_party})
    assert by_investor.status_code == 200, by_investor.text
    items = by_investor.json()
    assert {item["invention"]["id"] for item in items} == {world.inventors.inventions["F01"], created["id"]}
    assert all(item["opportunity"]["partner_party_id"] == mitra_a_party for item in items)

    preview_item = next(item for item in items if item["invention"]["id"] == created["id"])
    assert preview_item["preview"] is True
    assert preview_item["source"] is None
    dims = {d["id"]: d for d in preview_item["result"]["breakdown"]}
    assert dims["money"]["status"] == "UNKNOWN" and dims["form"]["status"] == "UNKNOWN"
    assert preview_item["result"]["recommendations"][0]["kind"] == "no_need"

    # By product filter returns only F01 across all partners.
    by_product = await rani.get("/api/v1/fit", params={"invention_id": world.inventors.inventions["F01"]})
    assert by_product.status_code == 200
    assert all(item["invention"]["id"] == world.inventors.inventions["F01"] for item in by_product.json())

    # Isolation: Galih cannot see Rani's invention.
    stranger = await galih.get("/api/v1/fit", params={"invention_id": world.inventors.inventions["F01"]})
    assert stranger.status_code == 200 and stranger.json() == []


async def test_discovery_partners_orders_by_fit_for_chosen_product(
    client: AsyncClient, new_client, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    Condition:
    - Demo scenario with Investor A (agriculture) and Investor B (solar energy), and Inovator A's Produk B (SolarBox).

    Expected:
    - GET /api/v1/discovery?type=partners&produk=<Produk B> ranks Investor B first with best_fit "Kecocokan kuat".
    """
    import app.discovery.service.projection  # noqa: F401, PLC0415
    from app.core.database import get_session_factory  # noqa: PLC0415
    from app.worker.loop import dispatch_events  # noqa: PLC0415
    from app.worker.registry import registry  # noqa: PLC0415

    monkeypatch.setattr(get_settings(), "demo_mode", True)
    assert (await client.post("/api/v1/demo/reset")).status_code == 200
    async with new_client() as investor:
        sign = await investor.post("/api/v1/demo/sign-in", json={"key": "investor-b"})
        party_b = sign.json()["active_party_id"]
        investor.headers["X-Acting-Party"] = party_b
        assert (await save_profile(investor, party_b, scenario.INVESTOR_B["profile"])).status_code == 200
        opp = (await create_opportunity(investor, party_b, scenario.INVESTOR_B["opportunity"])).json()
        assert (await move_opportunity(investor, party_b, opp["id"], "activate", opp["version"])).status_code == 200

    sign_inv = await client.post("/api/v1/demo/sign-in", json={"key": "inovator-a"})
    party_inv = sign_inv.json()["active_party_id"]
    client.headers["X-Acting-Party"] = party_inv
    created = (
        await client.post("/api/v1/inventions", json={"acting_party_id": party_inv}, headers={"Idempotency-Key": "b"})
    ).json()
    saved = (
        await client.put(
            f"/api/v1/inventions/{created['id']}/draft",
            json={
                "acting_party_id": party_inv,
                "expected_version": created["version"],
                **scenario.PRODUCT_B["content"],
            },
            headers={"Idempotency-Key": "b-draft"},
        )
    ).json()
    await client.post(
        f"/api/v1/inventions/{created['id']}/publish",
        json={"acting_party_id": party_inv, "expected_version": saved["version"]},
        headers={"Idempotency-Key": "b-pub"},
    )
    need = (
        await client.post(
            "/api/v1/support-requests",
            json={"acting_party_id": party_inv, "invention_id": created["id"], **scenario.PRODUCT_B["need"]},
            headers={"Idempotency-Key": "b-need"},
        )
    ).json()
    await client.post(
        f"/api/v1/support-requests/{need['id']}/activate",
        json={"acting_party_id": party_inv, "expected_version": need["version"]},
        headers={"Idempotency-Key": "b-act"},
    )
    while await dispatch_events(get_session_factory(), registry):
        pass

    resp = await client.get("/api/v1/discovery", params={"type": "partners", "produk": created["id"]})
    assert resp.status_code == 200, resp.text
    partners = [item for section in resp.json()["sections"] for item in section["items"]]
    assert len(partners) >= 2
    assert partners[0]["title"] == "Investor B"
    assert partners[0]["best_fit"]["label"] == "Kecocokan kuat"

    all_resp = await client.get("/api/v1/discovery", params={"type": "partners", "produk": "all"})
    assert all_resp.status_code == 200, all_resp.text
    all_partners = [item for section in all_resp.json()["sections"] for item in section["items"]]
    assert all_partners[0]["best_fit"]["matching_products"] >= 1
