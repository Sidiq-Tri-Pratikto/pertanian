"""Recipient decisions through HTTP against Postgres (spec 025, AC40–AC42)."""

import asyncio
from collections.abc import Awaitable, Callable

import pytest
from httpx import AsyncClient
from sqlalchemy import text

from app.core.database import get_session_factory
from tests.integration.matching.conftest import World
from tests.integration.pitches.conftest import REVISION_ITEMS, act, client_of, reread, submitted

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("clean_tables")]

FAKE_SECRET = "sk-fakedecisionsecret321"


async def _topics() -> list[str]:
    async with get_session_factory()() as session:
        return list(await session.scalars(text("SELECT topic FROM outbox_events ORDER BY created_at")))


async def test_approval_opens_discussion_and_nothing_else(world: World) -> None:
    """
    Condition:
    - Mitra A begins review, then approves F01 for discussion on submission 1 (AC40).

    Expected:
    - ``APPROVED_FOR_DISCUSSION`` with one stored decision both sides read; the only new events are the pitch's own,
      so no funding, partnership or commitment record is made; nobody is waiting, and closing is all that is left.
    """
    mitra = world.recipients.clients["A"]
    rani, _ = client_of(world, "F01")
    pitch = await submitted(world)
    before = len(await _topics())

    reviewing = await act(mitra, pitch, "begin-review", "review")
    approved = await act(mitra, await reread(mitra, pitch), "decisions", "approve", submission=1, decision="APPROVE")
    seen = await reread(rani, pitch)

    assert reviewing.json()["status"] == "UNDER_REVIEW"
    assert approved.status_code == 200, approved.text
    assert (approved.json()["status"], approved.json()["version"]) == ("APPROVED_FOR_DISCUSSION", 3)
    assert [(item["decision"], item["submission_number"]) for item in seen["decisions"]] == [("APPROVE", 1)]
    assert seen["waiting_on_party_id"] is None
    assert seen["allowed_actions"] == ["close"]
    assert (await _topics())[before:] == ["pitch.begin_review", "pitch.approve"]


async def test_two_decisions_on_one_version_commit_once(world: World) -> None:
    """
    Condition:
    - Mitra A approves and rejects the same version at once, with two keys (AC41).

    Expected:
    - One commits; the other is ``STALE_VERSION`` with the stored version, and only one decision is stored.
    """
    mitra = world.recipients.clients["A"]
    pitch = await submitted(world)

    responses = await asyncio.gather(
        act(mitra, pitch, "decisions", "approve", submission=1, decision="APPROVE"),
        act(mitra, pitch, "decisions", "reject", submission=1, decision="REJECT", reason="Belum sesuai fokus kami."),
    )

    codes = sorted(response.status_code for response in responses)
    loser = next(response for response in responses if response.status_code == 409).json()["error"]
    assert codes == [200, 409]
    assert (loser["code"], loser["current_version"]) == ("STALE_VERSION", 2)
    assert loser["recovery"]["retryable"] is False and loser["request_id"]
    assert len((await reread(mitra, pitch))["decisions"]) == 1


async def test_a_withdrawn_pitch_takes_no_decision_and_never_reopens(world: World) -> None:
    """
    Condition:
    - Rani withdraws F01; Mitra A then approves against the current version (AC42).

    Expected:
    - ``INVALID_TRANSITION``; the pitch stays withdrawn with no decision, and a new pitch to A1 is possible again.
    """
    mitra = world.recipients.clients["A"]
    rani, _ = client_of(world, "F01")
    pitch = await submitted(world)

    withdrawn = await act(rani, pitch, "withdraw", "withdraw")
    decided = await act(mitra, await reread(mitra, pitch), "decisions", "late", submission=1, decision="APPROVE")
    after = await reread(mitra, pitch)

    body = decided.json()["error"]
    assert withdrawn.json()["status"] == "WITHDRAWN"
    assert (decided.status_code, body["code"]) == (409, "INVALID_TRANSITION")
    assert body["message"].startswith("Status ini tidak dapat diubah dengan cara itu.")
    assert (after["status"], after["decisions"], after["allowed_actions"]) == ("WITHDRAWN", [], [])


async def test_a_rejection_needs_a_short_private_reason(world: World) -> None:
    """
    Condition:
    - Mitra A rejects without a reason, then with one.

    Expected:
    - First ``VALIDATION_FAILED`` naming ``reason`` and nothing changes; then ``REJECTED`` and Rani reads the reason.
    """
    mitra = world.recipients.clients["A"]
    rani, _ = client_of(world, "F01")
    pitch = await submitted(world)

    empty = await act(mitra, pitch, "decisions", "empty", submission=1, decision="REJECT", reason="  ")
    rejected = await act(mitra, pitch, "decisions", "reject", submission=1, decision="REJECT", reason="Di luar fokus.")

    body = empty.json()["error"]
    assert (empty.status_code, body["code"]) == (422, "VALIDATION_FAILED")
    assert body["details"][0]["loc"] == ["body", "reason"]
    assert "hanya terlihat oleh pengirim pitching" in body["details"][0]["msg"]
    assert rejected.json()["status"] == "REJECTED"
    assert (await reread(rani, pitch))["decisions"][0]["reason"] == "Di luar fokus."


async def test_approval_cannot_be_followed_by_a_revision_request(world: World) -> None:
    """
    Condition:
    - Mitra A approves, then requests a revision round.

    Expected:
    - ``INVALID_TRANSITION``; clarification after approval belongs to discussion tasks, and no round exists.
    """
    mitra = world.recipients.clients["A"]
    pitch = await submitted(world)
    await act(mitra, pitch, "decisions", "approve", submission=1, decision="APPROVE")

    revision = await act(
        mitra, await reread(mitra, pitch), "revision-rounds", "revise", submission=1, items=REVISION_ITEMS
    )

    assert revision.json()["error"]["code"] == "INVALID_TRANSITION"
    assert (await reread(mitra, pitch))["rounds"] == []


async def test_a_decision_on_an_older_submission_or_version_is_stale(world: World) -> None:
    """
    Condition:
    - Mitra A decides naming submission 2, which does not exist, then with an old version.

    Expected:
    - Both are ``STALE_VERSION`` with the stored version; nothing is decided.
    """
    mitra = world.recipients.clients["A"]
    pitch = await submitted(world)

    wrong_submission = await act(mitra, pitch, "decisions", "a", submission=2, decision="APPROVE")
    old = await act(mitra, {**pitch, "version": 0}, "decisions", "b", submission=1, decision="APPROVE")

    assert [r.json()["error"]["code"] for r in (wrong_submission, old)] == ["STALE_VERSION", "STALE_VERSION"]
    assert (await reread(mitra, pitch))["status"] == "SUBMITTED"


async def test_a_retried_decision_returns_the_original_once(world: World) -> None:
    """
    Condition:
    - Mitra A's approval response is lost and the same key is sent again.

    Expected:
    - The retry replays the original response and one decision is stored.
    """
    mitra = world.recipients.clients["A"]
    pitch = await submitted(world)

    first = await act(mitra, pitch, "decisions", "lost", submission=1, decision="APPROVE")
    retry = await act(mitra, pitch, "decisions", "lost", submission=1, decision="APPROVE")

    assert retry.status_code == 200
    assert retry.json() == first.json()
    assert len((await reread(mitra, pitch))["decisions"]) == 1


async def test_the_requester_cannot_decide_and_a_stranger_sees_nothing(
    world: World, new_client: Callable[[], AsyncClient], sign_up: Callable[..., Awaitable[dict]]
) -> None:
    """
    Condition:
    - Rani approves her own pitch; a stranger approves it as itself.

    Expected:
    - Rani is ``FORBIDDEN``; the stranger is ``NOT_FOUND``; the pitch stays submitted.
    """
    rani, _ = client_of(world, "F01")
    pitch = await submitted(world)
    async with new_client() as stranger:
        me = await sign_up(stranger, "stranger@example.com", name="Stranger")
        stranger.headers["X-Acting-Party"] = me["active_party_id"]

        own = await act(rani, pitch, "decisions", "own", submission=1, decision="APPROVE")
        foreign = await act(stranger, pitch, "decisions", "foreign", submission=1, decision="APPROVE")

    assert own.json()["error"]["code"] == "FORBIDDEN"
    assert foreign.status_code == 404
    assert (await reread(rani, pitch))["status"] == "SUBMITTED"


async def test_a_member_without_decide_pitch_reads_but_cannot_decide(
    world: World, new_client: Callable[[], AsyncClient], sign_up: Callable[..., Awaitable[dict]]
) -> None:
    """
    Condition:
    - A Mitra A member who holds only ``schedule`` opens the pitch and approves it.

    Expected:
    - It reads the pitch with no allowed actions, and approving is ``FORBIDDEN``.
    """
    mitra, party = world.recipients.clients["A"], world.recipients.parties["A"]
    pitch = await submitted(world)
    me = (await mitra.get("/api/v1/me")).json()
    organization = {"id": next(item["organization_id"] for item in me["organizations"] if item["party_id"] == party)}
    await mitra.post(
        f"/api/v1/organizations/{organization['id']}/invitations",
        json={"acting_party_id": party, "email": "viewer@example.com", "capabilities": ["schedule"]},
        headers={"Idempotency-Key": "invite-viewer"},
    )
    mail = (await mitra.get("/api/v1/dev/mailbox", params={"email": "viewer@example.com"})).json()
    async with new_client() as viewer:
        await sign_up(viewer, "viewer@example.com", name="Viewer")
        await viewer.post(f"/api/v1/invitations/{mail[0]['body'].rsplit('/', 1)[1]}/accept")
        await viewer.put("/api/v1/me/context", json={"party_id": party})
        viewer.headers["X-Acting-Party"] = party

        read = await reread(viewer, pitch)
        decided = await act(viewer, pitch, "decisions", "viewer", submission=1, decision="APPROVE")

    assert (read["status"], read["allowed_actions"]) == ("SUBMITTED", [])
    assert decided.json()["error"]["code"] == "FORBIDDEN"


async def test_an_approved_discussion_closes_with_a_reason(world: World) -> None:
    """
    Condition:
    - After approval, Rani closes without a reason, then with one.

    Expected:
    - First ``VALIDATION_FAILED``; then ``CLOSED``, ended, so a new pitch is no longer blocked by it.
    """
    mitra = world.recipients.clients["A"]
    rani, _ = client_of(world, "F01")
    pitch = await submitted(world)
    await act(mitra, pitch, "decisions", "approve", submission=1, decision="APPROVE")
    approved = await reread(rani, pitch)

    empty = await act(rani, approved, "close", "empty", reason="")
    closed = await act(rani, approved, "close", "close", reason=f"Kami lanjut dengan mitra lain {FAKE_SECRET}")

    assert empty.json()["error"]["code"] == "VALIDATION_FAILED"
    assert closed.json()["status"] == "CLOSED"
    assert FAKE_SECRET not in empty.text
    assert (await reread(mitra, pitch))["allowed_actions"] == []
