"""Following one invention by email and receiving its public updates, through HTTP against Postgres (spec 053)."""

import asyncio
import re
from collections.abc import AsyncIterator, Awaitable, Callable

import pytest
from httpx import AsyncClient

import app.subscriptions.service.follows  # noqa: F401 - registers the update fan-out
import app.subscriptions.service.jobs  # noqa: F401 - registers the alert consumer
from app.core.database import get_session_factory
from app.worker.loop import dispatch_events, run_jobs
from app.worker.registry import registry
from tests.factories.inventors import publish_invention
from tests.integration.mail_relay import LocalRelay

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("clean_tables")]

FOLLOWER = "pengikut@example.com"


@pytest.fixture
async def inventor(
    client: AsyncClient, sign_up: Callable[..., Awaitable[dict]]
) -> AsyncIterator[tuple[AsyncClient, str]]:
    """Rani, signed in, acting as herself."""
    me = await sign_up(client, "rani@example.com", name="Rani")
    client.headers["X-Acting-Party"] = me["active_party_id"]
    yield client, me["active_party_id"]


async def _deliver() -> None:
    while await dispatch_events(get_session_factory(), registry):
        pass


async def _mail(client: AsyncClient, email: str = FOLLOWER) -> list[dict[str, str]]:
    return (await client.get("/api/v1/dev/mailbox", params={"email": email})).json()


def _token(body: str, path: str) -> str:
    found = re.search(rf"{path}\?token=([\w-]+)", body)
    assert found, body
    return found.group(1)


async def _public(client: AsyncClient, party: str, key: str, *, page: bool = True, digest: bool = False) -> str:
    """Publish a fixture invention with its public page (and optionally investor news) on."""
    invention = await publish_invention(client, party, key)
    current = (await client.get(f"/api/v1/inventions/{invention}")).json()
    body = {"acting_party_id": party, "expected_version": current["version"], "enabled": page}
    assert (await client.put(f"/api/v1/inventions/{invention}/public-page", json=body)).status_code == 200
    if digest:
        current = (await client.get(f"/api/v1/inventions/{invention}")).json()
        body = {"acting_party_id": party, "expected_version": current["version"], "enabled": True}
        assert (await client.put(f"/api/v1/inventions/{invention}/investor-digest", json=body)).status_code == 200
    return invention


async def _update(client: AsyncClient, party: str, invention: str, title: str) -> dict:
    """Write and publish an update."""
    written = await client.post(
        f"/api/v1/inventions/{invention}/updates",
        json={"acting_party_id": party, "title": title, "body": f"{title}: dua unit siap diuji."},
        headers={"Idempotency-Key": f"write-{title}"},
    )
    assert written.status_code == 201, written.text
    published = await client.post(
        f"/api/v1/inventions/{invention}/updates/{written.json()['id']}/publish",
        json={"acting_party_id": party, "expected_version": written.json()["version"]},
        headers={"Idempotency-Key": f"publish-{title}"},
    )
    assert published.status_code == 200, published.text
    return published.json()


async def _following(visitor: AsyncClient, invention: str, locale: str = "id") -> str:
    """Follow and confirm; return a manage token."""
    response = await visitor.post(
        "/api/v1/follows", json={"invention_id": invention, "email": FOLLOWER, "locale": locale}
    )
    assert response.status_code == 202, response.text
    token = _token((await _mail(visitor))[0]["body"], "/en/follow/confirm" if locale == "en" else "/ikuti/konfirmasi")
    confirmed = await visitor.post("/api/v1/follows/confirm", json={"token": token})
    assert confirmed.status_code == 200, confirmed.text
    return confirmed.json()["manage_token"]


async def test_a_follower_gets_each_update_once_and_unfollowing_one_invention_keeps_the_other(
    inventor: tuple[AsyncClient, str], new_client: Callable[[], AsyncClient]
) -> None:
    """
    Condition:
    - One email follows ClearSpring and a second invention, and confirms both after opening the preview.
    - Rani publishes an update on each; the worker runs twice. The follower unfollows ClearSpring, switches the other
      to English, and Rani publishes one more update on each.

    Expected:
    - The preview confirms nothing. Each update arrives once, with the update's text and a manage link; nothing
      arrives twice. After unfollowing, ClearSpring's update is not sent, while the other arrives in English.
    """
    client, party = inventor
    first = await _public(client, party, "F01")
    second = await _public(client, party, "F02")
    async with new_client() as visitor:
        await visitor.post("/api/v1/follows", json={"invention_id": first, "email": FOLLOWER})
        pending = _token((await _mail(visitor))[0]["body"], "/ikuti/konfirmasi")
        preview = (await visitor.post("/api/v1/follows/preview", json={"token": pending})).json()
        manage_first = (await visitor.post("/api/v1/follows/confirm", json={"token": pending})).json()["manage_token"]
        manage_second = await _following(visitor, second)

        await _update(client, party, first, "Jadwal pilot dikonfirmasi")
        await _update(client, party, second, "Uji kedua selesai")
        await _deliver()
        await _deliver()
        after_two = await _mail(visitor)

        assert (await visitor.post("/api/v1/follows/unfollow", json={"token": manage_first})).status_code == 200
        english = await visitor.put("/api/v1/follows/manage", json={"token": manage_second, "locale": "en"})
        await _update(client, party, first, "Unit ketiga")
        await _update(client, party, second, "Unit keempat")
        await _deliver()
        latest = await _mail(visitor)

    assert (preview["status"], preview["email"]) == ("PENDING", "pe***@example.com")
    updates = [message for message in after_two if message["subject"].startswith("Pembaruan dari")]
    assert len(updates) == 2
    assert any("Jadwal pilot dikonfirmasi: dua unit siap diuji." in message["body"] for message in updates)
    assert all("/ikuti/atur?token=" in message["body"] for message in updates)
    assert english.json()["locale"] == "en"
    new = latest[: len(latest) - len(after_two)]
    assert [message["subject"].split(" ")[0:3] for message in new] == [["An", "update", "from"]]
    assert "Unit keempat" in new[0]["body"] and "/en/follow/manage?token=" in new[0]["body"]


async def test_the_answer_is_the_same_for_every_address_and_an_active_follower_gets_a_manage_link(
    inventor: tuple[AsyncClient, str], new_client: Callable[[], AsyncClient]
) -> None:
    """
    Condition:
    - A new address follows, follows again while pending, confirms, and follows a third time; an invention whose
      public page is off is followed too.

    Expected:
    - Each answer is ``202 check_email``. The third email is a manage link, not a new confirmation. A page that is
      off answers ``NOT_FOUND``; a confirmation link works once even when two requests race.
    """
    client, party = inventor
    invention = await _public(client, party, "F01")
    hidden = await _public(client, party, "F02", page=False, digest=True)
    async with new_client() as visitor:
        body = {"invention_id": invention, "email": FOLLOWER}
        answers = [(await visitor.post("/api/v1/follows", json=body)).json()]
        answers.append((await visitor.post("/api/v1/follows", json=body)).json())
        token = _token((await _mail(visitor))[0]["body"], "/ikuti/konfirmasi")
        raced = await asyncio.gather(
            *(visitor.post("/api/v1/follows/confirm", json={"token": token}) for _ in range(2))
        )
        answers.append((await visitor.post("/api/v1/follows", json=body)).json())
        latest = (await _mail(visitor))[0]
        off = await visitor.post("/api/v1/follows", json={"invention_id": hidden, "email": "lain@example.com"})

    assert answers == [{"status": "check_email"}] * 3
    assert sorted(response.status_code for response in raced) == [200, 404]
    assert latest["subject"].startswith("Anda sudah mengikuti") and "/ikuti/atur?token=" in latest["body"]
    assert (off.status_code, off.json()["error"]["code"]) == (404, "NOT_FOUND")


async def test_a_follower_confirmed_after_an_update_does_not_get_it(
    inventor: tuple[AsyncClient, str], new_client: Callable[[], AsyncClient]
) -> None:
    """
    Condition:
    - Rani publishes an update; an email asks to follow, then confirms before the worker runs.

    Expected:
    - The update published before the confirmation is not sent.
    """
    client, party = inventor
    invention = await _public(client, party, "F01")
    await _update(client, party, invention, "Sebelum mengikuti")
    async with new_client() as visitor:
        await _following(visitor, invention)
        await _deliver()
        mail = await _mail(visitor)

    assert [message for message in mail if message["subject"].startswith("Pembaruan dari")] == []


async def test_queued_mail_is_dropped_when_the_follower_leaves_or_the_invention_is_withdrawn(
    inventor: tuple[AsyncClient, str], new_client: Callable[[], AsyncClient], local_relay: LocalRelay
) -> None:
    """
    Condition:
    - Through the real relay: a follower is confirmed and an update's email is queued, then the follower unfollows
      before the relay job runs. Separately, an investor alert is queued, then the invention leaves investor news.

    Expected:
    - Neither queued message reaches the relay; the confirmation sent earlier did. The sealed job never holds the
      address in plain text.
    """
    client, party = inventor
    invention = await _public(client, party, "F01", digest=True)
    factory = get_session_factory()
    local_relay.enable()
    async with new_client() as visitor:
        await visitor.post("/api/v1/follows", json={"invention_id": invention, "email": FOLLOWER})
        assert await run_jobs(factory, registry) == 1
        [confirmation] = local_relay.accepted.values()
        token = _token(confirmation["body"], "/ikuti/konfirmasi")
        manage = (await visitor.post("/api/v1/follows/confirm", json={"token": token})).json()["manage_token"]

        await _update(client, party, invention, "Antre lalu batal")
        await _deliver()
        await visitor.post("/api/v1/follows/unfollow", json={"token": manage})
        await run_jobs(factory, registry)

        subscribed = await visitor.post(
            "/api/v1/subscriptions", json={"email": "investor@example.com", "topics": {"keywords": ["air"]}}
        )
        assert subscribed.status_code == 202
        await run_jobs(factory, registry)
        sub_token = _token(list(local_relay.accepted.values())[-1]["body"], "/langganan/konfirmasi")
        await visitor.post("/api/v1/subscriptions/confirm", json={"token": sub_token})
        current = (await client.get(f"/api/v1/inventions/{invention}")).json()
        await client.put(
            f"/api/v1/inventions/{invention}/investor-digest",
            json={"acting_party_id": party, "expected_version": current["version"], "enabled": False},
        )
        current = (await client.get(f"/api/v1/inventions/{invention}")).json()
        await client.put(
            f"/api/v1/inventions/{invention}/investor-digest",
            json={"acting_party_id": party, "expected_version": current["version"], "enabled": True},
        )
        await _deliver()
        current = (await client.get(f"/api/v1/inventions/{invention}")).json()
        await client.put(
            f"/api/v1/inventions/{invention}/investor-digest",
            json={"acting_party_id": party, "expected_version": current["version"], "enabled": False},
        )
        await run_jobs(factory, registry)

    subjects = [message["subject"] for message in local_relay.accepted.values()]
    assert not any(subject.startswith("Pembaruan dari") for subject in subjects), subjects
    assert not any(subject.startswith("Inovasi sesuai minat Anda") for subject in subjects), subjects
    assert len(subjects) == 2
