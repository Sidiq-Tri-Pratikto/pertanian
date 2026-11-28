"""Integration tests for multipart HTML investor emails, subscription locale, and dev preview (spec 060)."""

import re
from collections.abc import AsyncIterator, Awaitable, Callable

import pytest
from httpx import AsyncClient

import app.discovery.service.projection  # noqa: F401
import app.subscriptions.service.follows  # noqa: F401
import app.subscriptions.service.jobs  # noqa: F401
from app.core.database import get_session_factory
from app.worker.loop import dispatch_events
from app.worker.registry import registry
from tests.factories.inventors import publish_invention

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("clean_tables")]

INVESTOR = "investor-html@example.com"
WATER = {"sectors": ["Air dan sanitasi"], "stages": ["PROTOTYPE"]}


async def _deliver() -> None:
    while await dispatch_events(get_session_factory(), registry):
        pass


def _token(body: str, path: str) -> str:
    found = re.search(rf"{path}\?token=([\w-]+)", body)
    assert found, body
    return found.group(1)


@pytest.fixture
async def inventor(
    client: AsyncClient, sign_up: Callable[..., Awaitable[dict]]
) -> AsyncIterator[tuple[AsyncClient, str]]:
    me = await sign_up(client, "rani-html@example.com", name="Rani")
    client.headers["X-Acting-Party"] = me["active_party_id"]
    yield client, me["active_party_id"]


async def test_alert_and_manage_locale_produce_html_in_development_mailbox(
    inventor: tuple[AsyncClient, str], new_client: Callable[[], AsyncClient]
) -> None:
    client, party = inventor
    async with new_client() as visitor:
        res = await visitor.post("/api/v1/subscriptions", json={"email": INVESTOR, "topics": WATER})
        assert res.status_code == 202
        mail = (await visitor.get("/api/v1/dev/mailbox", params={"email": INVESTOR})).json()
        assert mail[0]["html"] and '<html lang="id">' in mail[0]["html"]

        confirm_token = _token(mail[0]["body"], "/langganan/konfirmasi")
        confirmed = await visitor.post("/api/v1/subscriptions/confirm", json={"token": confirm_token})
        assert confirmed.status_code == 200
        manage_token = confirmed.json()["manage_token"]
        assert confirmed.json()["locale"] == "id"

        # Switch email language to English via PUT /subscriptions/manage
        updated = await visitor.put("/api/v1/subscriptions/manage", json={"token": manage_token, "locale": "en"})
        assert updated.status_code == 200
        assert updated.json()["locale"] == "en"

        # Publish a matching water prototype with TKT 4 and enable investor digest
        invention_id = await publish_invention(client, party, "F01")
        current = (await client.get(f"/api/v1/inventions/{invention_id}")).json()
        included = await client.put(
            f"/api/v1/inventions/{invention_id}/investor-digest",
            json={"acting_party_id": party, "expected_version": current["version"], "enabled": True},
        )
        assert included.status_code == 200
        await _deliver()

        inbox = (await visitor.get("/api/v1/dev/mailbox", params={"email": INVESTOR})).json()
        latest = inbox[0]
        assert latest["html"] is not None
        assert '<html lang="en">' in latest["html"]
        assert "View summary" in latest["html"]
        assert "View summary" in latest["body"]


async def test_dev_mail_preview_renders_all_templates_and_404s_unknown(client: AsyncClient) -> None:
    for template in ("confirm", "already", "alert", "digest", "follow_confirm", "follow_already", "follow_update"):
        for lang in ("id", "en"):
            response = await client.get(f"/api/v1/dev/mail-preview/{template}", params={"lang": lang})
            assert response.status_code == 200, (template, lang, response.text)
            assert f'<html lang="{lang}">' in response.text

    unknown = await client.get("/api/v1/dev/mail-preview/does-not-exist")
    assert unknown.status_code == 404
