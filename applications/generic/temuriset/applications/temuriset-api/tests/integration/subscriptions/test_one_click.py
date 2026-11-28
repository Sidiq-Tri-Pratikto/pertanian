"""Integration tests for RFC 8058 one-click unsubscribe, loopback relay HTML/headers, and recheck (spec 060)."""

import re
from collections.abc import AsyncIterator, Awaitable, Callable

import pytest
from httpx import AsyncClient

import app.discovery.service.projection  # noqa: F401
import app.identity.service.mail_jobs  # noqa: F401
import app.subscriptions.service.follows  # noqa: F401
import app.subscriptions.service.jobs  # noqa: F401
from app.core.database import get_session_factory
from app.worker.loop import dispatch_events, run_jobs
from app.worker.registry import registry
from tests.factories.inventors import publish_invention
from tests.integration.mail_relay import LocalRelay

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("clean_tables")]

SUBSCRIBER = "oneclick-sub@example.com"
FOLLOWER = "oneclick-follow@example.com"
WATER = {"sectors": ["Air dan sanitasi"], "stages": ["PROTOTYPE"]}


async def _drain() -> None:
    while await dispatch_events(get_session_factory(), registry):
        pass
    while await run_jobs(get_session_factory(), registry):
        pass


def _token(body: str, path: str) -> str:
    found = re.search(rf"{path}\?token=([\w-]+)", body)
    assert found, body
    return found.group(1)


def _one_click_token(list_unsubscribe_header: str) -> str:
    found = re.search(r"/api/v1/unsubscribe/one-click\?t=([\w-]+)", list_unsubscribe_header)
    assert found, list_unsubscribe_header
    return found.group(1)


@pytest.fixture
async def inventor(
    client: AsyncClient, sign_up: Callable[..., Awaitable[dict]]
) -> AsyncIterator[tuple[AsyncClient, str]]:
    me = await sign_up(client, "rani-oc@example.com", name="Rani")
    client.headers["X-Acting-Party"] = me["active_party_id"]
    yield client, me["active_party_id"]


async def test_subscription_relay_html_headers_and_idempotent_one_click_unsubscribe(
    inventor: tuple[AsyncClient, str], new_client: Callable[[], AsyncClient], local_relay: LocalRelay
) -> None:
    client, party = inventor
    local_relay.enable()

    async with new_client() as visitor:
        assert (
            await visitor.post("/api/v1/subscriptions", json={"email": SUBSCRIBER, "topics": WATER})
        ).status_code == 202
        await _drain()
        confirm_msg = local_relay.requests[-1][1]
        assert confirm_msg["html"] and "<!DOCTYPE html>" in confirm_msg["html"]
        confirm_token = _token(confirm_msg["body"], "/langganan/konfirmasi")

        confirmed = await visitor.post("/api/v1/subscriptions/confirm", json={"token": confirm_token})
        assert confirmed.status_code == 200
        manage_token = confirmed.json()["manage_token"]

        # Trigger an alert through the loopback relay
        invention_id = await publish_invention(client, party, "F01")
        current = (await client.get(f"/api/v1/inventions/{invention_id}")).json()
        assert (
            await client.put(
                f"/api/v1/inventions/{invention_id}/investor-digest",
                json={"acting_party_id": party, "expected_version": current["version"], "enabled": True},
            )
        ).status_code == 200
        await _drain()

        alert_msg = local_relay.requests[-1][1]
        assert alert_msg["html"] and "<!DOCTYPE html>" in alert_msg["html"]
        headers = alert_msg["headers"]
        assert headers["List-Unsubscribe-Post"] == "List-Unsubscribe=One-Click"
        oc_token = _one_click_token(headers["List-Unsubscribe"])

        # Cookie-less RFC 8058 POST works and is idempotent
        first = await visitor.post(
            f"/api/v1/unsubscribe/one-click?t={oc_token}",
            content="List-Unsubscribe=One-Click",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert first.status_code == 200, first.text
        assert first.json() == {"status": "unsubscribed"}

        second = await visitor.post(
            f"/api/v1/unsubscribe/one-click?t={oc_token}",
            content="List-Unsubscribe=One-Click",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert second.status_code == 200
        assert second.json() == {"status": "unsubscribed"}

        read_back = await visitor.post("/api/v1/subscriptions/manage", json={"token": manage_token})
        assert read_back.status_code == 200
        assert read_back.json()["status"] == "UNSUBSCRIBED"

        # Unknown token returns 404
        missing = await visitor.post(
            "/api/v1/unsubscribe/one-click?t=unknown-token-that-does-not-exist-12345",
            content="List-Unsubscribe=One-Click",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert missing.status_code == 404


async def test_follow_one_click_unsubscribe_and_relay_recheck_drops_queued_mail(
    inventor: tuple[AsyncClient, str], new_client: Callable[[], AsyncClient], local_relay: LocalRelay
) -> None:
    client, party = inventor
    local_relay.enable()

    invention_id = await publish_invention(client, party, "F01")
    current = (await client.get(f"/api/v1/inventions/{invention_id}")).json()
    assert (
        await client.put(
            f"/api/v1/inventions/{invention_id}/public-page",
            json={"acting_party_id": party, "expected_version": current["version"], "enabled": True},
        )
    ).status_code == 200

    async with new_client() as visitor:
        assert (
            await visitor.post(
                "/api/v1/follows", json={"invention_id": invention_id, "email": FOLLOWER, "locale": "id"}
            )
        ).status_code == 202
        await _drain()
        confirm_token = _token(local_relay.requests[-1][1]["body"], "/ikuti/konfirmasi")
        confirmed = await visitor.post("/api/v1/follows/confirm", json={"token": confirm_token})
        assert confirmed.status_code == 200
        manage_token = confirmed.json()["manage_token"]

        # Publish first update -> delivers with one-click token
        u1 = (
            await client.post(
                f"/api/v1/inventions/{invention_id}/updates",
                json={"acting_party_id": party, "title": "Kabar 1", "body": "Isi kabar pertama."},
                headers={"Idempotency-Key": "oc-u1"},
            )
        ).json()
        assert (
            await client.post(
                f"/api/v1/inventions/{invention_id}/updates/{u1['id']}/publish",
                json={"acting_party_id": party, "expected_version": u1["version"]},
                headers={"Idempotency-Key": "oc-u1-pub"},
            )
        ).status_code == 200
        await _drain()
        update_msg = local_relay.requests[-1][1]
        assert update_msg["html"] and "Kabar 1" in update_msg["html"]
        oc_token = _one_click_token(update_msg["headers"]["List-Unsubscribe"])

        # Publish second update, fan out to queue the relay job, then one-click unsubscribe BEFORE relay job runs
        u2 = (
            await client.post(
                f"/api/v1/inventions/{invention_id}/updates",
                json={"acting_party_id": party, "title": "Kabar 2", "body": "Isi kabar kedua."},
                headers={"Idempotency-Key": "oc-u2"},
            )
        ).json()
        assert (
            await client.post(
                f"/api/v1/inventions/{invention_id}/updates/{u2['id']}/publish",
                json={"acting_party_id": party, "expected_version": u2["version"]},
                headers={"Idempotency-Key": "oc-u2-pub"},
            )
        ).status_code == 200
        while await dispatch_events(get_session_factory(), registry):
            pass

        before_count = len(local_relay.requests)
        unsub = await visitor.post(
            f"/api/v1/unsubscribe/one-click?t={oc_token}",
            content="List-Unsubscribe=One-Click",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert unsub.status_code == 200

        # Now run queued relay jobs -> recheck must drop the queued email!
        while await run_jobs(get_session_factory(), registry):
            pass
        assert len(local_relay.requests) == before_count

        status_check = await visitor.post("/api/v1/follows/manage", json={"token": manage_token})
        assert status_check.status_code == 200
        assert status_check.json()["status"] == "UNSUBSCRIBED"
