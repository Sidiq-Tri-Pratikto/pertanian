"""The public invention page and its photo, through HTTP against Postgres (spec 051)."""

from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Any
from uuid import UUID

import pytest
from httpx import AsyncClient

from app.core.database import get_session_factory
from app.subscriptions.service.service import SubscriptionService
from tests.factories.inventors import publish_invention, upload_document
from tests.unit.documents.test_public_image import SECRET, _jpeg

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("clean_tables")]

FIELD_TEST = "Dua siklus pengeringan selesai di satu koperasi. Hasil dilaporkan oleh inovator."


@pytest.fixture
async def inventor(
    client: AsyncClient, sign_up: Callable[..., Awaitable[dict]]
) -> AsyncIterator[tuple[AsyncClient, str]]:
    """Rani, signed in, acting as herself."""
    me = await sign_up(client, "rani@example.com", name="Rani")
    client.headers["X-Acting-Party"] = me["active_party_id"]
    yield client, me["active_party_id"]


async def _photo(client: AsyncClient, party: str) -> dict[str, Any]:
    """Upload a JPEG that carries a fake location; return the choice the page form sends."""
    await upload_document(client, party, "Foto prototipe", content=_jpeg(), media_type="image/jpeg")
    document = next(
        item for item in (await client.get("/api/v1/documents")).json() if item["title"] == "Foto prototipe"
    )
    return {"document_id": document["id"], "version": max(version["number"] for version in document["versions"])}


async def _set(client: AsyncClient, party: str, invention: str, **fields: Any) -> Any:
    current = (await client.get(f"/api/v1/inventions/{invention}")).json()
    body = {"acting_party_id": party, "expected_version": current["version"], "enabled": True, **fields}
    return await client.put(f"/api/v1/inventions/{invention}/public-page", json=body)


async def test_the_owner_publishes_a_page_with_a_clean_photo_and_investor_alerts_stay_off(
    inventor: tuple[AsyncClient, str], new_client: Callable[[], AsyncClient]
) -> None:
    """
    Condition:
    - Rani publishes ClearSpring, uploads a JPEG whose EXIF holds a location, and publishes the public page with the
      photo, a description and a field-test summary in Indonesian. The investor-alert switch stays off.

    Expected:
    - Signed out, the summary shows the field test, the photo's address and size (orientation 6 kept), and that
      following is on; the photo is served without the location and with safe headers; investor alerts still
      cannot see the invention; the owner's view echoes the choices.
    """
    client, party = inventor
    invention = await publish_invention(client, party, "F01")
    choice = await _photo(client, party)
    saved = await _set(
        client, party, invention, photo=choice, photo_alt="Prototipe di meja kerja", field_test=FIELD_TEST
    )
    assert saved.status_code == 200, saved.text

    async with new_client() as visitor:
        teaser = (await visitor.get(f"/api/v1/teasers/inventions/{invention}")).json()
        photo = await visitor.get(teaser["photo"]["url"])
    async with get_session_factory()() as session:
        for_alerts = await SubscriptionService(session)._public(UUID(invention))  # noqa: SLF001 - the alert gate

    assert teaser["follow_enabled"] is True and teaser["field_test_summary"] == FIELD_TEST
    assert teaser["photo"] | {"url": None} == {
        "url": None,
        "alt": "Prototipe di meja kerja",
        "width": 640,
        "height": 480,
        "orientation": 6,
    }
    assert photo.status_code == 200 and photo.headers["content-type"] == "image/jpeg"
    assert SECRET not in photo.content
    assert photo.headers["x-content-type-options"] == "nosniff"
    assert "sandbox" in photo.headers["content-security-policy"]
    assert for_alerts is None
    page = saved.json()["public_page"]
    assert (page["enabled"], page["field_test"], page["photo"]["version"], page["content_locale"]) == (
        True,
        FIELD_TEST,
        choice["version"],
        "id",
    )


async def test_the_page_and_its_photo_disappear_when_switched_off_or_archived(
    inventor: tuple[AsyncClient, str], new_client: Callable[[], AsyncClient]
) -> None:
    """
    Condition:
    - A published page with a photo; the owner switches the page off, then on, then archives the invention.

    Expected:
    - Off: the summary and the photo are not found. Archived: both are not found again.
    """
    client, party = inventor
    invention = await publish_invention(client, party, "F01")
    choice = await _photo(client, party)
    assert (await _set(client, party, invention, photo=choice, photo_alt="Foto")).status_code == 200
    async with new_client() as visitor:
        url = (await visitor.get(f"/api/v1/teasers/inventions/{invention}")).json()["photo"]["url"]
        assert (await _set(client, party, invention, enabled=False, photo=choice, photo_alt="Foto")).status_code == 200
        off = [
            (await visitor.get(f"/api/v1/teasers/inventions/{invention}")).status_code,
            (await visitor.get(url)).status_code,
        ]
        assert (await _set(client, party, invention, photo=choice, photo_alt="Foto")).status_code == 200
        current = (await client.get(f"/api/v1/inventions/{invention}")).json()
        archived = await client.post(
            f"/api/v1/inventions/{invention}/archive",
            json={"acting_party_id": party, "expected_version": current["version"]},
            headers={"Idempotency-Key": "archive-public-page"},
        )
        assert archived.status_code in (200, 201), archived.text
        gone = [
            (await visitor.get(f"/api/v1/teasers/inventions/{invention}")).status_code,
            (await visitor.get(url)).status_code,
        ]

    assert off == [404, 404]
    assert gone == [404, 404]


async def test_a_photo_needs_a_description_and_must_be_the_owners_own_image(
    inventor: tuple[AsyncClient, str], new_client: Callable[[], AsyncClient], sign_up: Callable[..., Awaitable[dict]]
) -> None:
    """
    Condition:
    - Rani picks a photo without a description, then a PDF, then a file of another party.

    Expected:
    - ``VALIDATION_FAILED`` naming ``photo_alt``, then ``FILE_TYPE_UNSUPPORTED``, then ``FILE_NOT_AVAILABLE``; nothing
      is saved.
    """
    client, party = inventor
    invention = await publish_invention(client, party, "F01")
    choice = await _photo(client, party)
    pdf_version = await upload_document(client, party, "Laporan")
    pdf = next(item for item in (await client.get("/api/v1/documents")).json() if item["title"] == "Laporan")
    async with new_client() as other:
        stranger = await sign_up(other, "dewi@example.com", name="Dewi")
        other.headers["X-Acting-Party"] = stranger["active_party_id"]
        foreign = await _photo(other, stranger["active_party_id"])

    no_alt = await _set(client, party, invention, photo=choice)
    not_image = await _set(client, party, invention, photo={"document_id": pdf["id"], "version": 1}, photo_alt="x")
    not_mine = await _set(client, party, invention, photo=foreign, photo_alt="x")

    assert pdf_version
    assert (no_alt.status_code, no_alt.json()["error"]["code"]) == (422, "VALIDATION_FAILED")
    assert no_alt.json()["error"]["details"][0]["loc"] == ["body", "photo_alt"]
    assert not_image.json()["error"]["code"] == "FILE_TYPE_UNSUPPORTED"
    assert not_mine.json()["error"]["code"] == "FILE_NOT_AVAILABLE"
    assert (await client.get(f"/api/v1/inventions/{invention}")).json()["public_page"]["enabled"] is False
