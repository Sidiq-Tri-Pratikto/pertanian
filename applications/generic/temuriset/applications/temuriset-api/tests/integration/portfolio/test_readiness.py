"""TKT readiness on invention drafts, published versions, projections and privacy (spec 055)."""

from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Any
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import update

from app.core.database import get_session_factory
from app.discovery.service.projection import refresh_invention
from app.documents.repository.sqlalchemy.models import DocumentVersionRecord
from tests.factories.inventors import INVENTIONS, upload_document

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("clean_tables")]


@pytest.fixture
async def inventor(
    client: AsyncClient, sign_up: Callable[..., Awaitable[dict]]
) -> AsyncIterator[tuple[AsyncClient, str]]:
    """Rani, signed in, acting as herself."""
    me = await sign_up(client, "rani-tkt@example.com", name="Rani")
    client.headers["X-Acting-Party"] = me["active_party_id"]
    yield client, me["active_party_id"]


@pytest.fixture
async def stranger(
    new_client: Callable[[], AsyncClient], sign_up: Callable[..., Awaitable[dict]]
) -> AsyncIterator[tuple[AsyncClient, str]]:
    """Another signed-in party who does not manage Rani's invention."""
    async with new_client() as other:
        me = await sign_up(other, "stranger-tkt@example.com", persona="mitra", name="Investor")
        other.headers["X-Acting-Party"] = me["active_party_id"]
        yield other, me["active_party_id"]


async def _upload_pdf(client: AsyncClient, party: str, title: str = "Laporan uji TKT") -> dict[str, Any]:
    await upload_document(client, party, title)
    document = next(item for item in (await client.get("/api/v1/documents")).json() if item["title"] == title)
    return {"document_id": document["id"], "version": max(version["number"] for version in document["versions"])}


async def _create_draft(client: AsyncClient, party: str, readiness: Any = ..., *, key: str = "inv-1") -> dict[str, Any]:
    created = (
        await client.post("/api/v1/inventions", json={"acting_party_id": party}, headers={"Idempotency-Key": key})
    ).json()
    content = dict(INVENTIONS["F01"]["content"])
    body: dict[str, Any] = {
        "acting_party_id": party,
        "expected_version": created["version"],
        **content,
    }
    if readiness is not ...:
        body["readiness"] = readiness
    saved = await client.put(
        f"/api/v1/inventions/{created['id']}/draft",
        json=body,
        headers={"Idempotency-Key": f"{key}-draft"},
    )
    assert saved.status_code == 200, saved.text
    return saved.json()


async def test_readiness_saves_freezes_on_publish_and_copies_to_new_draft(
    inventor: tuple[AsyncClient, str],
) -> None:
    """AC73: save TKT 6 with note and evidence, publish freezes it, new draft copies it, clearing removes it."""
    client, party = inventor
    evidence = await _upload_pdf(client, party)
    saved = await _create_draft(
        client,
        party,
        readiness={"tkt_level": 6, "note": "Diuji di dua koperasi", "evidence": evidence},
    )
    assert saved["draft"]["readiness"] == {
        "tkt_level": 6,
        "note": "Diuji di dua koperasi",
        "provenance": "SELF_DECLARED",
        "has_evidence": True,
        "evidence": evidence,
    }

    pub = await client.post(
        f"/api/v1/inventions/{saved['id']}/publish",
        json={"acting_party_id": party, "expected_version": saved["version"]},
        headers={"Idempotency-Key": "pub-tkt-1"},
    )
    assert pub.status_code == 200, pub.text
    owner = (await client.get(f"/api/v1/inventions/{saved['id']}")).json()
    assert owner["published"]["readiness"] == saved["draft"]["readiness"]
    assert owner["draft"] is None

    # Starting a new draft successor without touching readiness copies the published version's readiness row.
    content = dict(INVENTIONS["F01"]["content"])
    content["summary"] = "Ringkasan diperbarui untuk draf versi 2."
    successor = await client.put(
        f"/api/v1/inventions/{saved['id']}/draft",
        json={"acting_party_id": party, "expected_version": owner["version"], **content},
        headers={"Idempotency-Key": "draft-successor-1"},
    )
    assert successor.status_code == 200, successor.text
    assert successor.json()["draft"]["readiness"] == owner["published"]["readiness"]

    # Explicitly setting readiness to null clears TKT on the draft while leaving published version frozen.
    cleared = await client.put(
        f"/api/v1/inventions/{saved['id']}/draft",
        json={"acting_party_id": party, "expected_version": successor.json()["version"], **content, "readiness": None},
        headers={"Idempotency-Key": "draft-clear-1"},
    )
    assert cleared.status_code == 200, cleared.text
    assert cleared.json()["draft"]["readiness"] is None
    assert cleared.json()["published"]["readiness"]["tkt_level"] == 6


async def test_readiness_privacy_on_public_view_discovery_card_and_teaser(
    inventor: tuple[AsyncClient, str],
    stranger: tuple[AsyncClient, str],
    new_client: Callable[[], AsyncClient],
) -> None:
    """AC74: non-owner, discovery card and signed-out teaser see level/note/has_evidence, never evidence file id."""
    client, party = inventor
    other, _ = stranger
    evidence = await _upload_pdf(client, party)
    saved = await _create_draft(
        client,
        party,
        readiness={"tkt_level": 6, "note": "Prototipe teruji di dua desa", "evidence": evidence},
        key="inv-privacy",
    )
    pub = await client.post(
        f"/api/v1/inventions/{saved['id']}/publish",
        json={"acting_party_id": party, "expected_version": saved["version"]},
        headers={"Idempotency-Key": "pub-privacy"},
    )
    assert pub.status_code == 200, pub.text
    current = (await client.get(f"/api/v1/inventions/{saved['id']}")).json()
    page = await client.put(
        f"/api/v1/inventions/{saved['id']}/public-page",
        json={"acting_party_id": party, "expected_version": current["version"], "enabled": True},
    )
    assert page.status_code == 200, page.text

    # Public view for another signed-in party strips evidence reference, keeps has_evidence=True.
    public_resp = await other.get(f"/api/v1/inventions/{saved['id']}/public")
    assert public_resp.status_code == 200, public_resp.text
    public_data = public_resp.json()
    assert public_data["readiness"] == {
        "tkt_level": 6,
        "note": "Prototipe teruji di dua desa",
        "provenance": "SELF_DECLARED",
        "has_evidence": True,
        "evidence": None,
    }
    assert evidence["document_id"] not in public_resp.text

    # Discovery projection card includes tkt_level and never evidence.
    async with get_session_factory()() as session, session.begin():
        await refresh_invention(session, UUID(saved["id"]))
    disc = await other.get("/api/v1/discovery", params={"type": "inventions"})
    assert disc.status_code == 200, disc.text
    cards = [
        item for section in disc.json()["sections"] for item in section["items"] if item["subject_id"] == saved["id"]
    ]
    assert len(cards) == 1
    assert cards[0]["card"]["tkt_level"] == 6
    assert evidence["document_id"] not in disc.text

    # Signed-out teaser includes tkt_level and never evidence.
    async with new_client() as visitor:
        teaser = await visitor.get(f"/api/v1/teasers/inventions/{saved['id']}")
    assert teaser.status_code == 200, teaser.text
    assert teaser.json()["tkt_level"] == 6
    assert evidence["document_id"] not in teaser.text


async def test_readiness_validation_and_evidence_ownership_errors(
    inventor: tuple[AsyncClient, str],
    stranger: tuple[AsyncClient, str],
) -> None:
    """Invalid tkt_level, >500-char note, or another party's / unavailable evidence is rejected."""
    client, party = inventor
    other, other_party = stranger
    created = (
        await client.post("/api/v1/inventions", json={"acting_party_id": party}, headers={"Idempotency-Key": "inv-err"})
    ).json()
    base = {"acting_party_id": party, "expected_version": created["version"], **INVENTIONS["F01"]["content"]}

    for bad_level in (0, 10):
        resp = await client.put(
            f"/api/v1/inventions/{created['id']}/draft",
            json={**base, "readiness": {"tkt_level": bad_level}},
            headers={"Idempotency-Key": f"bad-level-{bad_level}"},
        )
        assert resp.status_code == 422
        assert resp.json()["error"]["code"] == "VALIDATION_FAILED"

    long_note = await client.put(
        f"/api/v1/inventions/{created['id']}/draft",
        json={**base, "readiness": {"tkt_level": 5, "note": "x" * 501}},
        headers={"Idempotency-Key": "long-note"},
    )
    assert long_note.status_code == 422
    assert long_note.json()["error"]["code"] == "VALIDATION_FAILED"

    # Another party's available document must be refused with FILE_NOT_AVAILABLE.
    other_doc = await _upload_pdf(other, other_party, "Dokumen pihak lain")
    foreign = await client.put(
        f"/api/v1/inventions/{created['id']}/draft",
        json={**base, "readiness": {"tkt_level": 5, "evidence": other_doc}},
        headers={"Idempotency-Key": "foreign-doc"},
    )
    assert foreign.status_code in (400, 409, 422)
    assert foreign.json()["error"]["code"] == "FILE_NOT_AVAILABLE"

    # Optional everywhere: omitting readiness leaves readiness as None.
    saved = await client.put(
        f"/api/v1/inventions/{created['id']}/draft",
        json=base,
        headers={"Idempotency-Key": "omit-readiness"},
    )
    assert saved.status_code == 200
    assert saved.json()["draft"]["readiness"] is None


async def test_erased_evidence_clears_reference_while_keeping_tkt_and_note(
    inventor: tuple[AsyncClient, str],
) -> None:
    """Edge case: if the linked evidence file is erased later, evidence becomes null while TKT and note stay."""
    client, party = inventor
    evidence = await _upload_pdf(client, party, "Bukti akan dihapus")
    saved = await _create_draft(
        client,
        party,
        readiness={"tkt_level": 5, "note": "Catatan tetap ada", "evidence": evidence},
        key="inv-erase",
    )
    assert saved["draft"]["readiness"]["has_evidence"] is True

    async with get_session_factory()() as session, session.begin():
        await session.execute(
            update(DocumentVersionRecord)
            .where(DocumentVersionRecord.document_id == UUID(evidence["document_id"]))
            .values(file_state="ERASED")
        )

    after = (await client.get(f"/api/v1/inventions/{saved['id']}")).json()
    assert after["draft"]["readiness"] == {
        "tkt_level": 5,
        "note": "Catatan tetap ada",
        "provenance": "SELF_DECLARED",
        "has_evidence": False,
        "evidence": None,
    }
