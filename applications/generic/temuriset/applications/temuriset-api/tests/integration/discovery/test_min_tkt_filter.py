"""Discovery minimum TKT filter and preflight TKT evidence pre-tick (spec 056)."""

from collections.abc import Awaitable, Callable
from uuid import UUID

import pytest
from httpx import AsyncClient

from app.core.database import get_session_factory
from app.discovery.service.projection import refresh_invention
from tests.factories.inventors import INVENTIONS, SUPPORT_REQUESTS, upload_document
from tests.factories.recipients import OPPORTUNITIES, create_opportunity, move_opportunity, save_profile

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("clean_tables")]


async def _publish_with_tkt(
    client: AsyncClient, party: str, key: str, title: str, tkt_level: int | None, *, attach_evidence: bool = False
) -> str:
    created = (
        await client.post("/api/v1/inventions", json={"acting_party_id": party}, headers={"Idempotency-Key": key})
    ).json()
    content = {**INVENTIONS["F01"]["content"], "title": title}
    readiness = None
    if tkt_level is not None:
        evidence = None
        if attach_evidence:
            await upload_document(client, party, f"Bukti TKT {title}")
            doc = next(
                item for item in (await client.get("/api/v1/documents")).json() if item["title"] == f"Bukti TKT {title}"
            )
            evidence = {"document_id": doc["id"], "version": max(v["number"] for v in doc["versions"])}
        readiness = {"tkt_level": tkt_level, "note": f"Catatan TKT {tkt_level}", "evidence": evidence}
    saved = await client.put(
        f"/api/v1/inventions/{created['id']}/draft",
        json={"acting_party_id": party, "expected_version": created["version"], **content, "readiness": readiness},
        headers={"Idempotency-Key": f"{key}-draft"},
    )
    assert saved.status_code == 200, saved.text
    pub = await client.post(
        f"/api/v1/inventions/{created['id']}/publish",
        json={"acting_party_id": party, "expected_version": saved.json()["version"]},
        headers={"Idempotency-Key": f"{key}-pub"},
    )
    assert pub.status_code == 200, pub.text
    async with get_session_factory()() as session, session.begin():
        await refresh_invention(session, UUID(created["id"]))
    return created["id"]


async def test_discovery_min_tkt_filters_inventions_and_offers_relaxation(
    client: AsyncClient,
    new_client: Callable[[], AsyncClient],
    sign_up: Callable[..., Awaitable[dict]],
) -> None:
    """FR-003: min_tkt=5 keeps TKT >= 5, excludes lower and missing TKT, and offers 'Hapus filter TKT' relaxation."""
    me = await sign_up(client, "inv-filter@example.com", name="Inovator")
    party = me["active_party_id"]
    client.headers["X-Acting-Party"] = party

    await _publish_with_tkt(client, party, "i-none", "Tanpa TKT", None)
    await _publish_with_tkt(client, party, "i-low", "Produk TKT 4", 4)
    high_id = await _publish_with_tkt(client, party, "i-high", "Produk TKT 6", 6)

    async with new_client() as investor:
        inv_me = await sign_up(investor, "mitra-filter@example.com", persona="mitra", name="Mitra")
        investor.headers["X-Acting-Party"] = inv_me["active_party_id"]

        filtered = (await investor.get("/api/v1/discovery", params={"type": "inventions", "min_tkt": 5})).json()
        items = [item for section in filtered["sections"] for item in section["items"]]
        assert [item["subject_id"] for item in items] == [high_id]
        assert items[0]["card"]["tkt_level"] == 6
        assert filtered["filters"]["min_tkt"] == 5

        empty = (await investor.get("/api/v1/discovery", params={"type": "inventions", "min_tkt": 9})).json()
        assert empty["total_estimate"] == 0
        assert empty["relaxation"] is not None
        assert empty["relaxation"]["remove"] == "min_tkt"
        assert empty["relaxation"]["label"] == "Hapus filter TKT"
        assert empty["relaxation"]["total_estimate"] == 3


async def test_preflight_marks_and_preselects_tkt_evidence_file(
    client: AsyncClient,
    new_client: Callable[[], AsyncClient],
    sign_up: Callable[..., Awaitable[dict]],
) -> None:
    """FR-004: preflight includes the invention's TKT evidence file with kind='tkt' and selected=True."""
    me = await sign_up(client, "inv-preflight-tkt@example.com", name="Inovator")
    party = me["active_party_id"]
    client.headers["X-Acting-Party"] = party

    inv_id = await _publish_with_tkt(client, party, "i-pre", "ClearSpring TKT", 6, attach_evidence=True)
    need = (
        await client.post(
            "/api/v1/support-requests",
            json={"acting_party_id": party, "invention_id": inv_id, **SUPPORT_REQUESTS["F01"]},
            headers={"Idempotency-Key": "need-pre-1"},
        )
    ).json()
    await client.post(
        f"/api/v1/support-requests/{need['id']}/activate",
        json={"acting_party_id": party, "expected_version": need["version"]},
        headers={"Idempotency-Key": "need-pre-act"},
    )

    async with new_client() as investor:
        inv_me = await sign_up(investor, "mitra-pre-tkt@example.com", persona="mitra", name="Mitra")
        m_party = inv_me["active_party_id"]
        investor.headers["X-Acting-Party"] = m_party
        await save_profile(
            investor, m_party, {"subtype": "Investor", "thesis": "Uji", "contact_route": "IN_APP"}, key="prof-pre"
        )
        opp = (
            await create_opportunity(
                investor, m_party, {"kind": "SPECIFIC", **OPPORTUNITIES["A1"]["content"]}, key="opp-pre"
            )
        ).json()
        await move_opportunity(investor, m_party, opp["id"], "activate", opp["version"], key="opp-pre-act")

    preflight = await client.post(
        "/api/v1/pitches/preflight",
        json={
            "acting_party_id": party,
            "source_type": "SUPPORT_REQUEST",
            "source_id": need["id"],
            "opportunity_id": opp["id"],
        },
    )
    assert preflight.status_code == 200, preflight.text
    tkt_files = [item for item in preflight.json()["shareable_files"] if item["kind"] == "tkt"]
    assert len(tkt_files) == 1
    assert tkt_files[0]["selected"] is True
    assert tkt_files[0]["title"] == "Bukti TKT ClearSpring TKT"
