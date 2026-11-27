"""Public updates on the invention page, through HTTP against Postgres (spec 052)."""

from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Any

import pytest
from httpx import AsyncClient, Response
from sqlalchemy import select

from app.core.database import get_session_factory
from app.platform.repository.sqlalchemy.models import OutboxEventRecord
from tests.factories.inventors import publish_invention

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("clean_tables")]


@pytest.fixture
async def inventor(
    client: AsyncClient, sign_up: Callable[..., Awaitable[dict]]
) -> AsyncIterator[tuple[AsyncClient, str]]:
    """Rani, signed in, acting as herself."""
    me = await sign_up(client, "rani@example.com", name="Rani")
    client.headers["X-Acting-Party"] = me["active_party_id"]
    yield client, me["active_party_id"]


async def _page(client: AsyncClient, party: str, invention: str, enabled: bool = True) -> None:
    current = (await client.get(f"/api/v1/inventions/{invention}")).json()
    body = {"acting_party_id": party, "expected_version": current["version"], "enabled": enabled}
    assert (await client.put(f"/api/v1/inventions/{invention}/public-page", json=body)).status_code == 200


async def _write(client: AsyncClient, party: str, invention: str, title: str, key: str) -> dict[str, Any]:
    response = await client.post(
        f"/api/v1/inventions/{invention}/updates",
        json={"acting_party_id": party, "title": title, "body": f"{title}: hasil uji kedua."},
        headers={"Idempotency-Key": key},
    )
    assert response.status_code == 201, response.text
    return response.json()


async def _act(client: AsyncClient, party: str, invention: str, update: dict, action: str, key: str) -> Response:
    return await client.post(
        f"/api/v1/inventions/{invention}/updates/{update['id']}/{action}",
        json={"acting_party_id": party, "expected_version": update["version"]},
        headers={"Idempotency-Key": key},
    )


async def _announced() -> list[dict]:
    async with get_session_factory()() as session:
        rows = await session.scalars(
            select(OutboxEventRecord.payload).where(OutboxEventRecord.topic == "invention.update_published")
        )
        return list(rows)


async def test_a_published_update_shows_on_the_page_and_is_announced_once(
    inventor: tuple[AsyncClient, str], new_client: Callable[[], AsyncClient]
) -> None:
    """
    Condition:
    - Rani turns on ClearSpring's public page, writes an update, publishes it, corrects it, withdraws it and
      publishes it again; a second draft stays unpublished.

    Expected:
    - A visitor sees only the published update, with the corrected text, and never the draft; withdrawn, it is
      gone from the page. ``invention.update_published`` fires once, on the first publication, and
      ``published_at`` never changes.
    """
    client, party = inventor
    invention = await publish_invention(client, party, "F01")
    await _page(client, party, invention)
    update = await _write(client, party, invention, "Uji lapangan kedua", "u1")
    await _write(client, party, invention, "Draf rahasia", "u2")

    published = (await _act(client, party, invention, update, "publish", "p1")).json()
    corrected = await client.put(
        f"/api/v1/inventions/{invention}/updates/{update['id']}",
        json={
            "acting_party_id": party,
            "expected_version": published["version"],
            "title": "Uji lapangan kedua selesai",
            "body": "Tiga keluarga memakai saringan selama dua minggu.",
            "content_locale": "id",
        },
    )
    assert corrected.status_code == 200, corrected.text
    async with new_client() as visitor:
        shown = (await visitor.get(f"/api/v1/teasers/inventions/{invention}")).json()["latest_updates"]
        withdrawn = (await _act(client, party, invention, corrected.json(), "withdraw", "w1")).json()
        hidden = (await visitor.get(f"/api/v1/teasers/inventions/{invention}")).json()["latest_updates"]
        again = (await _act(client, party, invention, withdrawn, "publish", "p2")).json()

    assert [(item["title"], item["body"]) for item in shown] == [
        ("Uji lapangan kedua selesai", "Tiga keluarga memakai saringan selama dua minggu.")
    ]
    assert hidden == []
    assert (withdrawn["status"], again["status"]) == ("WITHDRAWN", "PUBLISHED")
    assert again["published_at"] == published["published_at"]
    assert await _announced() == [{"invention_id": invention, "update_id": update["id"]}]
    listed = (await client.get(f"/api/v1/inventions/{invention}/updates")).json()
    assert [item["status"] for item in listed] == ["DRAFT", "PUBLISHED"]


async def test_an_update_cannot_be_published_without_a_public_page(inventor: tuple[AsyncClient, str]) -> None:
    """
    Condition:
    - ClearSpring is published but its public page is off, or only investor news is on; then the page is on but the
      invention is archived.

    Expected:
    - ``INVALID_TRANSITION`` with a message naming the public page, nothing announced; once archived, a new update
      is refused with ``CONFLICT`` and the page's updates are gone with the page.
    """
    client, party = inventor
    invention = await publish_invention(client, party, "F01")
    update = await _write(client, party, invention, "Kabar pertama", "u1")

    refused = await _act(client, party, invention, update, "publish", "p1")
    withdraw_draft = await _act(client, party, invention, update, "withdraw", "w1")
    current = (await client.get(f"/api/v1/inventions/{invention}")).json()
    await client.post(
        f"/api/v1/inventions/{invention}/archive",
        json={"acting_party_id": party, "expected_version": current["version"]},
        headers={"Idempotency-Key": "archive"},
    )
    archived = await client.post(
        f"/api/v1/inventions/{invention}/updates",
        json={"acting_party_id": party, "title": "x", "body": "x"},
        headers={"Idempotency-Key": "u3"},
    )

    assert (refused.status_code, refused.json()["error"]["code"]) == (409, "INVALID_TRANSITION")
    assert "halaman publik" in refused.json()["error"]["message"]
    assert refused.json()["error"]["recovery"]["retryable"] is False
    assert withdraw_draft.json()["error"]["code"] == "INVALID_TRANSITION"
    assert archived.json()["error"]["code"] == "CONFLICT"
    assert await _announced() == []


async def test_a_stale_correction_is_refused_and_the_text_is_bounded(inventor: tuple[AsyncClient, str]) -> None:
    """
    Condition:
    - Rani corrects an update with an old ``expected_version``, then sends a body over 1,200 characters.

    Expected:
    - ``STALE_VERSION``, then ``VALIDATION_FAILED`` on ``body``; the update keeps its text.
    """
    client, party = inventor
    invention = await publish_invention(client, party, "F01")
    update = await _write(client, party, invention, "Kabar pertama", "u1")
    path = f"/api/v1/inventions/{invention}/updates/{update['id']}"

    stale = await client.put(
        path, json={"acting_party_id": party, "expected_version": 9, "title": "Baru", "body": "Baru"}
    )
    too_long = await client.put(
        path, json={"acting_party_id": party, "expected_version": 1, "title": "Baru", "body": "x" * 1201}
    )

    assert stale.json()["error"]["code"] == "STALE_VERSION"
    assert too_long.json()["error"]["code"] == "VALIDATION_FAILED"
    assert too_long.json()["error"]["details"][0]["loc"] == ["body", "body"]
    listed = (await client.get(f"/api/v1/inventions/{invention}/updates")).json()
    assert listed[0]["title"] == "Kabar pertama"
