"""The pitch room through HTTP against Postgres: messages, tasks, whose turn, notifications (spec 027)."""

import asyncio
from collections.abc import Awaitable, Callable
from datetime import timedelta
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select, text

import app.discussion.service.notifications as notifications
from app.core import clock
from app.core.database import get_session_factory
from app.identity.service.mailbox_service import NOTIFICATION_DELIVERY
from app.platform.repository.sqlalchemy.models import JobRecord, OutboxEventRecord
from app.platform.service.outbox import publish
from app.worker.loop import dispatch_events, run_jobs
from app.worker.registry import Registry, registry
from tests.integration.mail_relay import LocalRelay
from tests.integration.matching.conftest import World
from tests.integration.pitches.conftest import act, client_of, reread, submitted

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("clean_tables")]

FAKE_SECRET = "sk-fakediscussionsecret777"


async def _deliver(using: Registry = registry) -> None:
    while await dispatch_events(get_session_factory(), using):
        pass


async def _message(client: AsyncClient, pitch: dict[str, Any], text_: str, key: str) -> Any:
    return await client.post(
        f"/api/v1/pitches/{pitch['id']}/messages",
        json={"acting_party_id": client.headers["X-Acting-Party"], "text": text_},
        headers={"Idempotency-Key": key},
    )


async def test_each_party_reads_whose_turn_from_the_server(world: World) -> None:
    """
    Condition:
    - F01 is submitted to A1; both parties read ``next-action`` and their Beranda queue.

    Expected:
    - Mitra A gets "Putuskan pitching ini" as ``you``; Rani gets the same pitch as ``other``, and each queue lists it.
    """
    mitra = world.recipients.clients["A"]
    rani, _ = client_of(world, "F01")
    pitch = await submitted(world)

    theirs = (await mitra.get(f"/api/v1/pitches/{pitch['id']}/next-action")).json()
    mine = (await rani.get(f"/api/v1/pitches/{pitch['id']}/next-action")).json()
    queue = (await mitra.get("/api/v1/me/queue")).json()

    assert (theirs["who"], theirs["title"], theirs["action"], theirs["tab"]) == (
        "you",
        "Putuskan pitching ini",
        "decide",
        "ringkasan",
    )
    assert (mine["who"], mine["title"]) == ("other", "Pitching Anda sedang menunggu keputusan")
    assert [(item["pitch_id"], item["who"]) for item in queue] == [(pitch["id"], "you")]
    assert (await rani.get("/api/v1/me/queue")).json()[0]["who"] == "other"


async def test_messages_poll_with_since_and_a_retry_sends_once(world: World) -> None:
    """
    Condition:
    - Rani sends a message, retries it with the same key, Mitra A replies, and Rani polls with ``since``.

    Expected:
    - Two messages in order, each saying whose it is; the poll returns only the reply.
    """
    mitra = world.recipients.clients["A"]
    rani, _ = client_of(world, "F01")
    pitch = await submitted(world)

    first = await _message(rani, pitch, "Apakah jadwal uji bisa dimajukan?", "m1")
    retry = await _message(rani, pitch, "Apakah jadwal uji bisa dimajukan?", "m1")
    await _message(mitra, pitch, "Bisa, kami cek minggu ini.", "m2")
    listed = (await rani.get(f"/api/v1/pitches/{pitch['id']}/messages")).json()
    polled = (
        await rani.get(f"/api/v1/pitches/{pitch['id']}/messages", params={"since": first.json()["created_at"]})
    ).json()

    assert first.status_code == 201
    assert retry.json()["id"] == first.json()["id"]
    assert [(item["author_name"], item["mine"]) for item in listed] == [("Rani", True), ("Mitra A", False)]
    assert [item["text"] for item in polled] == ["Bisa, kami cek minggu ini."]


async def test_an_empty_message_is_refused_and_message_text_is_never_logged(
    world: World, caplog: pytest.LogCaptureFixture
) -> None:
    """
    Condition:
    - Rani sends only spaces, then a message holding a fake secret.

    Expected:
    - ``VALIDATION_FAILED`` naming ``text``; the second is stored, and its text appears in no log line.
    """
    rani, _ = client_of(world, "F01")
    pitch = await submitted(world)

    empty = await _message(rani, pitch, "   ", "empty")
    await _message(rani, pitch, f"Catatan {FAKE_SECRET}", "secret")

    body = empty.json()["error"]
    assert (empty.status_code, body["code"]) == (422, "VALIDATION_FAILED")
    assert body["details"][0]["loc"] == ["body", "text"]
    assert FAKE_SECRET not in caplog.text


async def test_a_task_after_approval_keeps_the_approval_and_completes_once(world: World) -> None:
    """
    Condition:
    - Mitra A approves, then gives Rani a task with a due date and a reference; Rani completes it, then repeats
      with the old version.

    Expected:
    - The decision stays; the task is done at version 2, and the stale completion is ``STALE_VERSION``.
    """
    mitra, party = world.recipients.clients["A"], world.recipients.parties["A"]
    rani, rani_party = client_of(world, "F01")
    pitch = await submitted(world)
    await act(mitra, pitch, "decisions", "approve", submission=1, decision="APPROVE")

    task = await mitra.post(
        f"/api/v1/pitches/{pitch['id']}/tasks",
        json={
            "acting_party_id": party,
            "title": "Kirim rincian biaya per lokasi",
            "owner_party_id": rani_party,
            "due_date": "2026-11-20",
            "reference": "Revisi putaran 1, butir 1",
        },
        headers={"Idempotency-Key": "task"},
    )
    done = await rani.post(
        f"/api/v1/tasks/{task.json()['id']}/complete",
        json={"acting_party_id": rani_party, "expected_version": 1},
        headers={"Idempotency-Key": "done"},
    )
    stale = await rani.post(
        f"/api/v1/tasks/{task.json()['id']}/complete",
        json={"acting_party_id": rani_party, "expected_version": 1},
        headers={"Idempotency-Key": "again"},
    )
    tasks = (await mitra.get(f"/api/v1/pitches/{pitch['id']}/tasks")).json()

    assert task.status_code == 201, task.text
    assert (task.json()["owner_name"], task.json()["reference"]) == ("Rani", "Revisi putaran 1, butir 1")
    assert (done.json()["status"], done.json()["version"]) == ("DONE", 2)
    assert stale.json()["error"]["code"] == "STALE_VERSION"
    assert [item["status"] for item in tasks] == ["DONE"]
    assert [item["decision"] for item in (await reread(mitra, pitch))["decisions"]] == ["APPROVE"]


async def test_a_task_owner_must_be_one_of_the_two_parties(world: World) -> None:
    """
    Condition:
    - Mitra A gives a task to Mitra B, who is not part of the pitch.

    Expected:
    - ``VALIDATION_FAILED`` naming ``owner_party_id``, and no task.
    """
    mitra, party = world.recipients.clients["A"], world.recipients.parties["A"]
    pitch = await submitted(world)

    response = await mitra.post(
        f"/api/v1/pitches/{pitch['id']}/tasks",
        json={"acting_party_id": party, "title": "Tugas", "owner_party_id": world.recipients.parties["B"]},
        headers={"Idempotency-Key": "task"},
    )

    assert response.json()["error"]["details"][0]["loc"] == ["body", "owner_party_id"]
    assert (await mitra.get(f"/api/v1/pitches/{pitch['id']}/tasks")).json() == []


async def test_an_ended_pitch_takes_no_new_messages(world: World) -> None:
    """
    Condition:
    - Rani withdraws, then sends a message.

    Expected:
    - ``INVALID_TRANSITION``; the room stays readable.
    """
    rani, _ = client_of(world, "F01")
    pitch = await submitted(world)
    await act(rani, await reread(rani, pitch), "withdraw", "withdraw")

    response = await _message(rani, pitch, "Halo", "late")

    assert response.json()["error"]["code"] == "INVALID_TRANSITION"
    assert (await rani.get(f"/api/v1/pitches/{pitch['id']}/messages")).status_code == 200


async def test_each_event_notifies_the_party_that_acts_once_and_read_state_is_its_own(world: World) -> None:
    """
    Condition:
    - Submission, then a revision request; the worker delivers twice; Mitra A marks its notification read and Rani
      tries to mark it too.

    Expected:
    - Mitra A gets "Pitching baru" and Rani "Revisi diminta", each once and linking to the right tab; only Mitra A's
      read state changes, and Rani's attempt is ``NOT_FOUND``.
    """
    mitra = world.recipients.clients["A"]
    rani, _ = client_of(world, "F01")
    pitch = await submitted(world)
    item = {"category": "Anggaran", "question": "Berapa?", "reason": "Perlu.", "required": True}
    await act(mitra, pitch, "revision-rounds", "round", submission=1, items=[item])
    await _deliver()
    await _deliver()

    theirs = (await mitra.get("/api/v1/notifications")).json()
    mine = (await rani.get("/api/v1/notifications")).json()
    read = await mitra.put(f"/api/v1/notifications/{theirs[0]['id']}/read")
    foreign = await rani.put(f"/api/v1/notifications/{theirs[0]['id']}/read")

    assert [(n["text"], n["tab"]) for n in theirs] == [
        ("Pitching baru: ClearSpring → Validasi prototipe enam bulan", "ringkasan")
    ]
    assert [(n["text"], n["tab"], n["read"]) for n in mine] == [
        ("Revisi diminta: ClearSpring → Validasi prototipe enam bulan", "revisi", False)
    ]
    assert read.json()["read"] is True
    assert foreign.status_code == 404
    assert (await rani.get("/api/v1/notifications", params={"unread": True})).json()[0]["read"] is False


async def test_a_failing_delivery_never_repeats_the_decision_or_its_notification(world: World) -> None:
    """
    Condition:
    - Mitra A approves; a fake email consumer on ``pitch.approve`` fails twice, then works (AC46).

    Expected:
    - One decision and one in-app notification for Rani, though the event was delivered three times.
    """
    mitra = world.recipients.clients["A"]
    rani, _ = client_of(world, "F01")
    pitch = await submitted(world)
    await act(mitra, pitch, "decisions", "approve", submission=1, decision="APPROVE")
    failures = {"left": 2}

    async def email(_session: Any, _payload: dict[str, Any]) -> None:
        if failures["left"]:
            failures["left"] -= 1
            raise RuntimeError(f"smtp down {FAKE_SECRET}")

    flaky = Registry(consumers={topic: dict(handlers) for topic, handlers in registry.consumers.items()})
    flaky.consumer("pitch.approve", "email.fake")(email)
    later = clock.now()
    for _ in range(3):
        later += timedelta(hours=2)
        with clock.frozen(later):
            await _deliver(flaky)
    async with get_session_factory()() as session:
        decisions = await session.scalar(text("SELECT count(*) FROM pitch_decisions"))
        sent = await session.scalar(text("SELECT count(*) FROM notifications WHERE event_key LIKE 'pitch.approve:%'"))

    assert failures["left"] == 0
    assert (decisions, sent) == (1, 1)
    assert [n["text"] for n in (await rani.get("/api/v1/notifications")).json()][0].startswith(
        "Pitching disetujui untuk diskusi"
    )


async def test_a_stranger_reaches_no_room(
    world: World, new_client: Callable[[], AsyncClient], sign_up: Callable[..., Awaitable[dict]]
) -> None:
    """
    Condition:
    - An unrelated account reads messages, tasks and the next action of F01's pitch, and posts a message (AC48).

    Expected:
    - Every answer is ``NOT_FOUND`` with no pitch metadata.
    """
    pitch = await submitted(world)
    async with new_client() as stranger:
        me = await sign_up(stranger, "stranger@example.com", name="Stranger")
        stranger.headers["X-Acting-Party"] = me["active_party_id"]
        answers = [
            await stranger.get(f"/api/v1/pitches/{pitch['id']}/messages"),
            await stranger.get(f"/api/v1/pitches/{pitch['id']}/tasks"),
            await stranger.get(f"/api/v1/pitches/{pitch['id']}/next-action"),
            await _message(stranger, pitch, "Halo", "s"),
        ]

    assert [answer.status_code for answer in answers] == [404, 404, 404, 404]
    assert all("ClearSpring" not in answer.text for answer in answers)


def test_notification_keys_name_the_event() -> None:
    """
    Condition:
    - A pitch event and a scheduling event.

    Expected:
    - The key carries the topic, pitch and version, or the meeting it is about.
    """
    assert notifications.event_key("pitch.approve", {"pitch_id": "p", "version": 3}) == "pitch.approve:p:3"
    assert notifications.event_key("meeting.confirmed", {"pitch_id": "p", "meeting_id": "m"}) == "meeting.confirmed:p:m"


async def _email_preference(client: AsyncClient, enabled: bool) -> dict[str, Any]:
    account = (await client.get("/api/v1/me")).json()["account"]
    changed = await client.patch(
        "/api/v1/me", json={"email_notifications": enabled, "expected_version": account["version"]}
    )
    assert changed.status_code == 200
    saved = changed.json()["account"]
    assert saved["email_notifications"] == enabled and saved["version"] == account["version"] + 1
    return saved


async def test_decision_email_reuses_the_key_after_acceptance_and_duplicate_event(
    world: World, local_relay: LocalRelay, caplog: pytest.LogCaptureFixture
) -> None:
    """
    Condition:
    - An opted-in requester receives a pitch decision. The relay accepts the mail but loses its acknowledgement.

    Expected:
    - Two workers, an idempotent route replay, and a repeated logical event preserve one decision, one in-app
      notice, and one accepted email. The relay sees a generic message, and the failure record omits private data.
    """
    mitra = world.recipients.clients["A"]
    rani, _ = client_of(world, "F01")
    local_relay.enable()
    saved = await _email_preference(rani, True)
    stale = await rani.patch(
        "/api/v1/me", json={"email_notifications": False, "expected_version": saved["version"] - 1}
    )
    assert (stale.status_code, stale.json()["error"]["code"]) == (409, "STALE_VERSION")
    local_relay.outcomes.append(None)
    with clock.frozen(clock.now()):
        when = clock.now()
        pitch = await submitted(world)
        decision = await act(
            mitra, pitch, "decisions", "approve-email", submission=1, decision="APPROVE", reason=FAKE_SECRET
        )
        repeated = await act(
            mitra, pitch, "decisions", "approve-email", submission=1, decision="APPROVE", reason=FAKE_SECRET
        )
        assert decision.status_code == 200 and repeated.headers["Idempotent-Replayed"] == "true"
        await _deliver()
        assert not local_relay.requests
        assert await run_jobs(get_session_factory(), registry) == 1
        async with get_session_factory().begin() as session:
            event = await session.scalar(select(OutboxEventRecord).where(OutboxEventRecord.topic == "pitch.approve"))
            assert event is not None
            await publish(session, event.topic, event.payload)
        await _deliver()

    with clock.frozen(when + timedelta(seconds=5)):
        counts = await asyncio.gather(*(run_jobs(get_session_factory(), registry) for _ in range(2)))
        assert sorted(counts) == [0, 1]

    assert len(local_relay.requests) == 2 and len(local_relay.accepted) == 1
    assert local_relay.requests[0] == local_relay.requests[1]
    message = local_relay.requests[0][1]
    assert message["to"] == saved["email"] and message["subject"] == "Pemberitahuan TemuRiset"
    assert message["body"].endswith("http://localhost:3020/home")
    assert all(private not in message["body"] for private in (FAKE_SECRET, "ClearSpring", "Validasi prototipe"))
    assert FAKE_SECRET not in caplog.text and saved["email"] not in caplog.text
    assert "APP-MAIL-RELAY-RETRY" in caplog.text and "ref_" in caplog.text
    assert len((await rani.get("/api/v1/notifications")).json()) == 1
    assert len((await reread(mitra, pitch))["decisions"]) == 1


@pytest.mark.parametrize("change", ["opt_out", "remove_member"])
async def test_organization_email_retry_rechecks_consent_and_membership(
    world: World,
    local_relay: LocalRelay,
    new_client: Callable[[], AsyncClient],
    sign_up: Callable[..., Awaitable[dict]],
    change: str,
) -> None:
    """
    Condition:
    - Two opted-in organization members differ in pitch authority and delivery to the authorized one fails.

    Expected:
    - Only the authorized member is ever attempted. Opting out or losing membership cancels further mail attempts,
      while the organization's in-app notice remains.
    """
    owner = world.recipients.clients["A"]
    party_id = world.recipients.parties["A"]
    org = next(item for item in (await owner.get("/api/v1/me")).json()["organizations"] if item["party_id"] == party_id)
    organization_id = org["organization_id"]

    async def add_member(client: AsyncClient, email: str, permission: str) -> dict[str, Any]:
        await sign_up(client, email)
        invited = await owner.post(
            f"/api/v1/organizations/{organization_id}/invitations",
            json={"acting_party_id": party_id, "email": email, "capabilities": [permission]},
            headers={"Idempotency-Key": permission},
        )
        assert invited.status_code == 201
        messages = (await client.get("/api/v1/dev/mailbox", params={"email": email})).json()
        token = messages[0]["body"].rsplit("/", 1)[1]
        assert (await client.post(f"/api/v1/invitations/{token}/accept")).status_code == 200
        return await _email_preference(client, True)

    async with new_client() as reviewer, new_client() as other:
        account = await add_member(reviewer, "reviewer@example.test", "decide_pitch")
        await add_member(other, "other@example.test", "schedule")
        local_relay.enable()
        local_relay.outcomes.append(503)
        with clock.frozen(clock.now()):
            when = clock.now()
            await submitted(world)
            await _deliver()
            assert await run_jobs(get_session_factory(), registry) == 1
            if change == "opt_out":
                await _email_preference(reviewer, False)
            else:
                removed = await owner.request(
                    "DELETE",
                    f"/api/v1/organizations/{organization_id}/members/{account['id']}",
                    json={"acting_party_id": party_id, "expected_version": 1},
                )
                assert removed.status_code == 204, removed.text

        with clock.frozen(when + timedelta(seconds=5)):
            assert await run_jobs(get_session_factory(), registry) == 1

    [(_, attempted)] = local_relay.requests
    assert attempted["to"] == account["email"]
    assert not local_relay.accepted
    assert len((await owner.get("/api/v1/notifications")).json()) == 1
    async with get_session_factory()() as session:
        jobs = list(await session.scalars(select(JobRecord).where(JobRecord.kind == NOTIFICATION_DELIVERY)))
        assert len(jobs) == 1 and jobs[0].status == "SUCCEEDED"
