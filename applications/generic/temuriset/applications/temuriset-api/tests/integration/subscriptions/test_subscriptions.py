"""Investor quick subscriptions, topic alerts and the weekly digest, through HTTP against Postgres (spec 046)."""

import re
from collections.abc import AsyncIterator, Awaitable, Callable
from datetime import UTC, datetime
from typing import Any

import pytest
from httpx import AsyncClient

import app.discovery.service.projection  # noqa: F401 - registers the projection consumers
import app.subscriptions.service.jobs  # noqa: F401 - registers the alert consumer and the digest job
from app.core.database import get_session_factory
from app.demo.service.data import INVENTIONS
from app.identity.service.mailbox_service import DisabledMailbox
from app.subscriptions.service import service as subscription_service
from app.subscriptions.service.service import next_digest_at
from app.worker.loop import dispatch_events
from app.worker.registry import registry
from tests.factories.inventors import publish_invention

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("clean_tables")]

INVESTOR = "investor-q@example.com"
WATER = {"sectors": ["Air dan sanitasi"], "stages": ["PROTOTYPE"]}


async def _deliver() -> None:
    while await dispatch_events(get_session_factory(), registry):
        pass


async def _mail(client: AsyncClient, email: str = INVESTOR) -> list[dict[str, str]]:
    """The development mailbox for an email, newest first."""
    return (await client.get("/api/v1/dev/mailbox", params={"email": email})).json()


def _token(body: str, path: str) -> str:
    found = re.search(rf"{path}\?token=([\w-]+)", body)
    assert found, body
    return found.group(1)


@pytest.fixture
async def inventor(
    client: AsyncClient, sign_up: Callable[..., Awaitable[dict]]
) -> AsyncIterator[tuple[AsyncClient, str]]:
    """Rani, signed in, acting as herself."""
    me = await sign_up(client, "rani@example.com", name="Rani")
    client.headers["X-Acting-Party"] = me["active_party_id"]
    yield client, me["active_party_id"]


async def _include(client: AsyncClient, party: str, invention_id: str, enabled: bool = True) -> Any:
    current = (await client.get(f"/api/v1/inventions/{invention_id}")).json()
    return await client.put(
        f"/api/v1/inventions/{invention_id}/investor-digest",
        json={"acting_party_id": party, "expected_version": current["version"], "enabled": enabled},
    )


async def _subscribe(client: AsyncClient, topics: dict[str, Any], email: str = INVESTOR) -> Any:
    return await client.post("/api/v1/subscriptions", json={"email": email, "topics": topics})


async def _active(client: AsyncClient, topics: dict[str, Any], email: str = INVESTOR) -> str:
    """Subscribe and confirm; return a manage token."""
    response = await _subscribe(client, topics, email)
    assert response.status_code == 202, response.text
    token = _token((await _mail(client, email))[0]["body"], "/langganan/konfirmasi")
    confirmed = await client.post("/api/v1/subscriptions/confirm", json={"token": token})
    assert confirmed.status_code == 200, confirmed.text
    return confirmed.json()["manage_token"]


async def test_nothing_is_sent_before_confirmation_and_opening_the_link_confirms_nothing(
    inventor: tuple[AsyncClient, str], new_client: Callable[[], AsyncClient]
) -> None:
    """
    Condition:
    - An investor subscribes to water prototypes; ClearSpring is published and included before and after the
      investor confirms with a deliberate POST (US1).

    Expected:
    - One confirmation email at first and no alert; the subscription stays pending until the POST; a used link is
      ``NOT_FOUND``.
    """
    client, party = inventor
    async with new_client() as visitor:
        answer = await _subscribe(visitor, WATER)
        invention = await publish_invention(client, party, "F01")
        await _include(client, party, invention)
        await _deliver()
        before = await _mail(visitor)
        token = _token(before[0]["body"], "/langganan/konfirmasi")
        confirmed = await visitor.post("/api/v1/subscriptions/confirm", json={"token": token})
        again = await visitor.post("/api/v1/subscriptions/confirm", json={"token": token})

    assert (answer.status_code, answer.json()) == (202, {"status": "check_email"})
    assert [mail["subject"] for mail in before] == ["Konfirmasi langganan kabar inovasi TemuRiset"]
    assert (confirmed.json()["status"], confirmed.json()["email"]) == ("ACTIVE", "in***@example.com")
    assert again.status_code == 404


async def test_the_answer_never_reveals_an_account_or_a_subscription(
    inventor: tuple[AsyncClient, str], new_client: Callable[[], AsyncClient]
) -> None:
    """
    Condition:
    - Rani's account email subscribes; an active subscriber subscribes again with other topics (US1.2).

    Expected:
    - Both answers are ``check_email``; the active subscriber's topics stay and it gets a manage link instead.
    """
    client, _ = inventor
    async with new_client() as visitor:
        account = await _subscribe(visitor, WATER, "rani@example.com")
        manage = await _active(visitor, WATER)
        repeat = await _subscribe(visitor, {"sectors": ["Energi"]})
        latest = (await _mail(visitor))[0]
        topics = (await visitor.post("/api/v1/subscriptions/manage", json={"token": manage})).json()["topics"]

    assert account.json() == repeat.json() == {"status": "check_email"}
    assert latest["subject"] == "Anda sudah berlangganan kabar inovasi TemuRiset"
    assert topics["sectors"] == ["Air dan sanitasi"]


async def test_a_specific_match_alerts_directly_with_the_reason_and_no_private_field(
    inventor: tuple[AsyncClient, str], new_client: Callable[[], AsyncClient]
) -> None:
    """
    Condition:
    - An active water-prototype subscriber; Rani publishes ClearSpring, which has private notes, and includes it
      (US3.1, SC-001).

    Expected:
    - One alert naming the invention, its introduction, "Inovator di TemuRiset" (no public profile), the reason,
      the teaser link and a manage link; the private notes appear nowhere.
    """
    client, party = inventor
    async with new_client() as visitor:
        await _active(visitor, WATER)
        invention = await publish_invention(client, party, "F01")
        await _include(client, party, invention)
        await _deliver()
        alert = (await _mail(visitor))[0]

    assert alert["subject"] == "Inovasi sesuai minat Anda: ClearSpring"
    assert "Inovator: Inovator di TemuRiset" in alert["body"]
    assert "cocok dengan minat Anda, sektor Air dan sanitasi, tahap Prototipe" in alert["body"]
    assert f"/temuan/{invention}" in alert["body"] and "/langganan/atur?token=" in alert["body"]
    assert INVENTIONS["F01"]["content"]["private_notes"] not in alert["body"]


async def test_an_invention_reaches_a_subscriber_once_and_a_switched_off_one_never(
    inventor: tuple[AsyncClient, str], new_client: Callable[[], AsyncClient]
) -> None:
    """
    Condition:
    - ClearSpring published but not included; then included, excluded and included again; then the digest runs.

    Expected:
    - No alert and a ``NOT_FOUND`` teaser while excluded; exactly one alert overall, and the digest adds nothing.
    """
    client, party = inventor
    async with new_client() as visitor:
        await _active(visitor, WATER)
        invention = await publish_invention(client, party, "F01")
        await _deliver()
        hidden = await visitor.get(f"/api/v1/teasers/inventions/{invention}")
        silent = len(await _mail(visitor))
        for enabled in (True, False, True):
            await _include(client, party, invention, enabled)
            await _deliver()
        digest = (await visitor.post("/api/v1/dev/digest")).json()
        subjects = [mail["subject"] for mail in await _mail(visitor)]

    assert (hidden.status_code, silent) == (404, 1)
    assert subjects.count("Inovasi sesuai minat Anda: ClearSpring") == 1
    assert digest == {"sent": 0}


async def test_a_partial_match_waits_for_the_digest_and_an_empty_week_sends_nothing(
    inventor: tuple[AsyncClient, str], new_client: Callable[[], AsyncClient]
) -> None:
    """
    Condition:
    - A subscriber for water inventions at market stage; ClearSpring (a prototype) is included; the digest runs
      twice (US3.2, US3.5).

    Expected:
    - No direct alert; the first digest lists ClearSpring with the sector reason; the second sends nothing.
    """
    client, party = inventor
    async with new_client() as visitor:
        await _active(visitor, {"sectors": ["Air dan sanitasi"], "stages": ["MARKET"]})
        invention = await publish_invention(client, party, "F01")
        await _include(client, party, invention)
        await _deliver()
        after_alerts = len(await _mail(visitor))
        first = (await visitor.post("/api/v1/dev/digest")).json()
        second = (await visitor.post("/api/v1/dev/digest")).json()
        digest = (await _mail(visitor))[0]

    assert after_alerts == 1
    assert (first, second) == ({"sent": 1}, {"sent": 0})
    assert digest["subject"] == "Kabar inovasi mingguan TemuRiset: 1 inovasi sesuai minat Anda"
    assert "cocok dengan minat Anda, sektor Air dan sanitasi." in digest["body"]


async def test_more_than_three_direct_matches_in_a_day_fold_into_the_digest(
    inventor: tuple[AsyncClient, str], new_client: Callable[[], AsyncClient]
) -> None:
    """
    Condition:
    - A subscriber for four sectors; four matching inventions are included the same day (FR-005).

    Expected:
    - Three alerts; the fourth arrives in the digest.
    """
    client, party = inventor
    keys = ["F01", "F02", "F04", "F05"]
    sectors = [INVENTIONS[key]["content"]["sector"] for key in keys]
    async with new_client() as visitor:
        await _active(visitor, {"sectors": sectors})
        for key in keys:
            await _include(client, party, await publish_invention(client, party, key))
            await _deliver()
        alerts = [mail for mail in await _mail(visitor) if mail["subject"].startswith("Inovasi sesuai minat")]
        digest = (await visitor.post("/api/v1/dev/digest")).json()
        latest = (await _mail(visitor))[0]

    assert len(alerts) == 3
    assert digest == {"sent": 1}
    assert "1 inovasi" in latest["subject"]


async def test_manage_links_change_topics_and_unsubscribe_stops_everything(
    inventor: tuple[AsyncClient, str], new_client: Callable[[], AsyncClient]
) -> None:
    """
    Condition:
    - An active subscriber changes topics to energy, then unsubscribes; then ClearSpring is included (US4).

    Expected:
    - Topics change; after unsubscribing nothing more is sent, and an unknown token is ``NOT_FOUND``.
    """
    client, party = inventor
    async with new_client() as visitor:
        manage = await _active(visitor, WATER)
        changed = await visitor.put(
            "/api/v1/subscriptions/manage", json={"token": manage, "topics": {"sectors": ["Air dan sanitasi"]}}
        )
        left = await visitor.post("/api/v1/subscriptions/unsubscribe", json={"token": manage})
        before = len(await _mail(visitor))
        await _include(client, party, await publish_invention(client, party, "F01"))
        await _deliver()
        after = len(await _mail(visitor))
        unknown = await visitor.post("/api/v1/subscriptions/manage", json={"token": "x" * 43})

    assert changed.json()["topics"] == {"sectors": ["Air dan sanitasi"], "stages": [], "keywords": []}
    assert left.json()["status"] == "UNSUBSCRIBED"
    assert before == after
    assert unknown.status_code == 404


async def test_the_teaser_shows_only_the_brief_public_summary(
    inventor: tuple[AsyncClient, str], new_client: Callable[[], AsyncClient]
) -> None:
    """
    Condition:
    - ClearSpring is included; a signed-out visitor reads its teaser before and after Rani publishes her profile.

    Expected:
    - Title, summary, sector, stage and keywords; the inventor name only once the profile is published; no private
      field.
    """
    client, party = inventor
    invention = await publish_invention(client, party, "F01")
    await _include(client, party, invention)
    async with new_client() as visitor:
        anonymous = await visitor.get(f"/api/v1/teasers/inventions/{invention}")
        mine = (await client.get("/api/v1/profiles/me")).json()
        await client.put(
            "/api/v1/profiles/me",
            json={"acting_party_id": party, "expected_version": mine["version"], "bio": "Inovator", "published": True},
        )
        named = (await visitor.get(f"/api/v1/teasers/inventions/{invention}")).json()

    body = anonymous.json()
    assert anonymous.status_code == 200
    assert (body["title"], body["sector"], body["stage"], body["inventor_name"]) == (
        "ClearSpring",
        "Air dan sanitasi",
        "PROTOTYPE",
        "Inovator di TemuRiset",
    )
    assert named["inventor_name"] == "Rani"
    assert INVENTIONS["F01"]["content"]["private_notes"] not in anonymous.text
    assert set(body) == {
        "id",
        "title",
        "summary",
        "sector",
        "stage",
        "keywords",
        "inventor_name",
        "published_at",
        "follow_enabled",
        "field_test_summary",
        "photo",
        "content_locale",
        "latest_updates",
    }
    # Investor news alone opens no public page: no field test, photo or updates, not indexable (specs 051, 052).
    assert (body["follow_enabled"], body["field_test_summary"], body["photo"], body["latest_updates"]) == (
        False,
        None,
        None,
        [],
    )


@pytest.mark.parametrize(
    ("body", "code"),
    [
        ({"email": INVESTOR, "topics": {}}, "VALIDATION_FAILED"),
        ({"email": "bukan-email", "topics": WATER}, "VALIDATION_FAILED"),
    ],
)
async def test_a_subscription_without_topics_or_email_is_refused(
    new_client: Callable[[], AsyncClient], body: dict[str, Any], code: str
) -> None:
    """
    Condition:
    - No topic at all, or an invalid email.

    Expected:
    - ``VALIDATION_FAILED`` and no email.
    """
    async with new_client() as visitor:
        response = await visitor.post("/api/v1/subscriptions", json=body)
        mailed = await _mail(visitor)

    assert (response.status_code, response.json()["error"]["code"]) == (422, code)
    assert mailed == []


async def test_one_email_asking_too_often_is_rate_limited(new_client: Callable[[], AsyncClient]) -> None:
    """
    Condition:
    - The same email subscribes four times within an hour.

    Expected:
    - The fourth is ``RATE_LIMITED`` with a wait time.
    """
    async with new_client() as visitor:
        answers = [await _subscribe(visitor, WATER) for _ in range(4)]

    body = answers[-1].json()["error"]
    assert [answer.status_code for answer in answers] == [202, 202, 202, 429]
    assert body["code"] == "RATE_LIMITED" and body["recovery"]["retry_after_seconds"] > 0


async def test_a_deployment_without_email_refuses_honestly(
    new_client: Callable[[], AsyncClient], monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    Condition:
    - Outbound email is disabled (US1.5).

    Expected:
    - ``MAIL_UNAVAILABLE`` and nothing stored.
    """
    monkeypatch.setattr(subscription_service, "mailbox_for", lambda _settings: DisabledMailbox())
    async with new_client() as visitor:
        response = await _subscribe(visitor, WATER)

    assert response.json()["error"]["code"] == "MAIL_UNAVAILABLE"


async def test_only_the_managing_party_switches_inclusion(
    inventor: tuple[AsyncClient, str], new_client: Callable[[], AsyncClient], sign_up: Callable[..., Awaitable[dict]]
) -> None:
    """
    Condition:
    - Another party flips Rani's switch.

    Expected:
    - ``NOT_FOUND``, and the invention stays excluded.
    """
    client, party = inventor
    invention = await publish_invention(client, party, "F01")
    async with new_client() as other:
        me = await sign_up(other, "dewi@example.com", name="Dewi")
        other.headers["X-Acting-Party"] = me["active_party_id"]
        version = (await client.get(f"/api/v1/inventions/{invention}")).json()["version"]
        response = await other.put(
            f"/api/v1/inventions/{invention}/investor-digest",
            json={"acting_party_id": me["active_party_id"], "expected_version": version, "enabled": True},
        )

    assert response.status_code == 404
    assert (await client.get(f"/api/v1/inventions/{invention}")).json()["investor_digest"] is False


def test_the_digest_runs_on_monday_at_nine_in_jakarta() -> None:
    """
    Condition:
    - Sunday 15 November 2026, then exactly Monday 16 November at 02:00 UTC.

    Expected:
    - The next run is Monday 16 November 02:00 UTC (09:00 WIB); at that instant, the following Monday.
    """
    assert next_digest_at(datetime(2026, 11, 15, 10, tzinfo=UTC)) == datetime(2026, 11, 16, 2, tzinfo=UTC)
    assert next_digest_at(datetime(2026, 11, 16, 2, tzinfo=UTC)) == datetime(2026, 11, 23, 2, tzinfo=UTC)


async def test_an_english_subscriber_gets_english_mail_with_english_links_and_errors_follow_the_header(
    inventor: tuple[AsyncClient, str], new_client: Callable[[], AsyncClient]
) -> None:
    """
    Condition:
    - A visitor subscribes from the English page (locale ``en``) and confirms; Rani publishes a matching invention.
      The same visitor then sends an empty topic list with the English header (spec 050).

    Expected:
    - The confirmation and the alert are in English with ``/en/...`` links, the anonymous inventor reads "An inventor
      on TemuRiset", and the error message is English with ``Content-Language: en`` while the code stays the same.
    """
    client, party = inventor
    async with new_client() as visitor:
        sent = await visitor.post("/api/v1/subscriptions", json={"email": INVESTOR, "topics": WATER, "locale": "en"})
        assert sent.status_code == 202, sent.text
        confirmation = (await _mail(visitor))[0]
        token = _token(confirmation["body"], "/en/subscribe/confirm")
        assert (await visitor.post("/api/v1/subscriptions/confirm", json={"token": token})).status_code == 200
        invention = await publish_invention(client, party, "F01")
        await _include(client, party, invention)
        await _deliver()
        alert = (await _mail(visitor))[0]
        refused = await visitor.post(
            "/api/v1/subscriptions",
            json={"email": "other@example.com", "topics": {}, "locale": "en"},
            headers={"X-TemuRiset-Locale": "en"},
        )

    assert confirmation["subject"] == "Confirm your TemuRiset invention news subscription"
    assert "sector Air dan sanitasi; stage Prototype" in confirmation["body"]
    assert alert["subject"] == "An invention that matches your interests: ClearSpring"
    assert "Inventor: An inventor on TemuRiset" in alert["body"]
    assert "it matches your interests, sector Air dan sanitasi, stage Prototype" in alert["body"]
    assert f"/en/inventions/{invention}" in alert["body"] and "/en/subscribe/manage?token=" in alert["body"]
    assert refused.headers["content-language"] == "en"
    assert refused.json()["error"]["code"] == "VALIDATION_FAILED"
    assert refused.json()["error"]["message"].isascii()
