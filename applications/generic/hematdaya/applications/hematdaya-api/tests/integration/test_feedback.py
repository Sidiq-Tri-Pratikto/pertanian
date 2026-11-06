"""Insight feedback: AT-39, idempotency, visibility per revision, and no effect on measurements."""

import asyncio
import secrets
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient

from tests.integration.conftest import execute, start_demo
from tests.integration.test_insights import WEEK, _correct_tv_19h, _insights

pytestmark = pytest.mark.integration


def _key() -> str:
    return secrets.token_urlsafe(16)


async def _feedback(client: AsyncClient, session: dict, insight: dict, action: str, key: str | None = None, **body):
    return await client.post(
        f"/api/v1/insights/{insight['id']}/feedback",
        json={"action": action, "revision": insight["revision"]} | body,
        headers=session["auth"] | {"Idempotency-Key": key or _key()},
    )


async def _tv(client: AsyncClient) -> tuple[dict, dict]:
    session = await start_demo(client, "h-change")
    body = await _insights(client, session)
    return session, body["observations"][0]


async def _measurements(site_id: str) -> list:
    return await execute(
        "SELECT count(*), sum(m.energy_mwh), string_agg(m.identity_key, ',' ORDER BY m.id) FROM measurements m"
        " JOIN sources s ON s.id = m.source_id WHERE s.site_id = :site",
        site=UUID(site_id),
    )


async def test_every_action_is_confirmed_and_leaves_measurements_alone(client: AsyncClient) -> None:
    """
    Condition:
    - AT-39: useful, not relevant, snooze, hide and restore on the TV observation, each sent twice.

    Expected:
    - Each is confirmed with the state it produced; measurement identities, values and the summary are unchanged.
    """
    session, tv = await _tv(client)
    before = await _measurements(session["site_id"])
    summary_before = (
        await client.get(f"/api/v1/sites/{session['site_id']}/summary", params=WEEK, headers=session["auth"])
    ).json()

    expected = {
        "useful": ("useful", "visible"),
        "not_relevant": ("not_relevant", "visible"),
        "snooze": ("not_relevant", "snoozed"),
        "hide": ("not_relevant", "hidden"),
        "restore": ("not_relevant", "visible"),
    }
    for action, (rating, visibility) in expected.items():
        key = _key()
        first = await _feedback(client, session, tv, action, key)
        again = await _feedback(client, session, tv, action, key)
        assert first.status_code == 200, first.text
        assert first.json() == again.json()
        assert (first.json()["rating"], first.json()["visibility"]) == (rating, visibility)

    assert await _measurements(session["site_id"]) == before
    summary_after = (
        await client.get(f"/api/v1/sites/{session['site_id']}/summary", params=WEEK, headers=session["auth"])
    ).json()
    assert summary_after == summary_before
    rows = await execute("SELECT count(*) FROM feedback_operations WHERE insight_id = :id", id=UUID(tv["id"]))
    assert rows[0][0] == 5


async def test_concurrent_retries_apply_once(client: AsyncClient) -> None:
    """
    Condition:
    - A lost response retried at the same time with the same key.

    Expected:
    - Both answer the same outcome and one operation is stored.
    """
    session, tv = await _tv(client)
    key = _key()

    first, second = await asyncio.gather(
        _feedback(client, session, tv, "hide", key), _feedback(client, session, tv, "hide", key)
    )

    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    rows = await execute("SELECT count(*) FROM feedback_operations WHERE insight_id = :id", id=UUID(tv["id"]))
    assert rows[0][0] == 1


async def test_reused_key_for_another_payload_is_refused(client: AsyncClient) -> None:
    """
    Condition:
    - A key used for "useful" is sent again for "hide", then for a newer revision.

    Expected:
    - CONFLICT, not retryable, and the observation stays visible with its first rating.
    """
    session, tv = await _tv(client)
    key = _key()
    assert (await _feedback(client, session, tv, "useful", key)).status_code == 200

    other_action = await _feedback(client, session, tv, "hide", key)
    await _correct_tv_19h(session["site_id"], 300)
    newer = (await _insights(client, session))["observations"][0]
    other_revision = await _feedback(client, session, newer, "useful", key)

    for response in (other_action, other_revision):
        assert response.status_code == 409
        error = response.json()["error"]
        assert error["code"] == "CONFLICT"
        assert error["recovery"]["retryable"] is False
        assert error["request_id"]
    state = await execute(
        "SELECT revision, rating, visibility FROM insight_feedback WHERE insight_id = :id", id=UUID(tv["id"])
    )
    assert state == [(1, "useful", "visible")]


async def test_hide_and_restore_through_the_hidden_list(client: AsyncClient) -> None:
    """
    Condition:
    - P10: hide the TV observation, read the hidden list, restore it.

    Expected:
    - It leaves the list with a hidden count, appears in the hidden list, and returns after restore.
    """
    session, tv = await _tv(client)
    assert (await _feedback(client, session, tv, "hide")).status_code == 200

    listed = await _insights(client, session)
    hidden = await client.get(
        f"/api/v1/sites/{session['site_id']}/insights/hidden", params=WEEK, headers=session["auth"]
    )
    assert (listed["observations"], listed["hidden_count"]) == ([], 1)
    assert hidden.status_code == 200
    assert [item["id"] for item in hidden.json()["observations"]] == [tv["id"]]
    assert hidden.json()["observations"][0]["feedback"]["visibility"] == "hidden"

    assert (await _feedback(client, session, tv, "restore")).status_code == 200
    restored = await _insights(client, session)
    assert [item["id"] for item in restored["observations"]] == [tv["id"]]
    assert restored["hidden_count"] == 0


async def test_snooze_lasts_until_the_next_local_midnight_of_the_site_clock(client: AsyncClient) -> None:
    """
    Condition:
    - Snooze on a demo site whose virtual clock is 26 Oktober 00.00 WIB, then move the clock past midnight.

    Expected:
    - Until 27 Oktober 00.00 WIB; hidden while the clock is frozen, back once the site clock passes it.
    """
    session, tv = await _tv(client)
    response = await _feedback(client, session, tv, "snooze")

    assert response.json()["until"] == "2026-10-26T17:00:00Z"
    assert (await _insights(client, session))["hidden_count"] == 1
    await execute("UPDATE sites SET virtual_now = '2026-10-26T17:00:00Z' WHERE id = :id", id=UUID(session["site_id"]))
    back = await _insights(client, session)
    assert [item["id"] for item in back["observations"]] == [tv["id"]]
    assert back["observations"][0]["feedback"]["visibility"] == "snoozed"


async def test_feedback_stays_with_its_revision(client: AsyncClient) -> None:
    """
    Condition:
    - Hide revision 1, re-read unchanged data, then correct the data so revision 2 appears.

    Expected:
    - Equal evidence keeps it hidden; revision 2 is visible and says earlier feedback exists; revision 1 keeps it.
    """
    session, tv = await _tv(client)
    await _feedback(client, session, tv, "hide")
    assert (await _insights(client, session))["hidden_count"] == 1

    await _correct_tv_19h(session["site_id"], 300)
    newer = (await _insights(client, session))["observations"][0]
    old = await client.get(f"/api/v1/insights/{tv['id']}", params={"revision": 1}, headers=session["auth"])

    assert (newer["revision"], newer["feedback"], newer["earlier_feedback"]) == (2, None, True)
    assert old.json()["feedback"]["visibility"] == "hidden"
    assert old.json()["superseded"] is True


async def test_foreign_or_unknown_targets_look_missing(client: AsyncClient) -> None:
    """
    Condition:
    - Another owner's insight, an unknown revision and an unknown insight.

    Expected:
    - NOT_FOUND each time, and no feedback stored.
    """
    owner, tv = await _tv(client)
    intruder = await start_demo(client, "h-change")

    foreign = await _feedback(client, intruder, tv, "hide")
    unknown_revision = await _feedback(client, owner, tv | {"revision": 9}, "hide")
    unknown_insight = await _feedback(client, owner, tv | {"id": str(uuid4())}, "hide")

    for response in (foreign, unknown_revision, unknown_insight):
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "NOT_FOUND"
    assert (await execute("SELECT count(*) FROM insight_feedback WHERE insight_id = :id", id=UUID(tv["id"])))[0][0] == 0


@pytest.mark.parametrize("headers", [{}, {"Idempotency-Key": "short"}])
async def test_feedback_needs_a_strong_key(client: AsyncClient, headers: dict) -> None:
    """
    Condition:
    - No key, or a key below 128 bits.

    Expected:
    - VALIDATION_FAILED and nothing stored.
    """
    session, tv = await _tv(client)
    response = await client.post(
        f"/api/v1/insights/{tv['id']}/feedback",
        json={"action": "hide", "revision": 1},
        headers=session["auth"] | headers,
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_FAILED"
    assert (await execute("SELECT count(*) FROM feedback_operations WHERE insight_id = :id", id=UUID(tv["id"])))[0][
        0
    ] == 0
