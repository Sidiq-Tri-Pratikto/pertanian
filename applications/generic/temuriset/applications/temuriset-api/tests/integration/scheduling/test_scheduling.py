"""Race-safe scheduling through HTTP against Postgres, with a frozen product clock (spec 028)."""

import asyncio
from datetime import UTC, datetime
from typing import Any

import pytest
from sqlalchemy import func, select, text

from app.core import clock
from app.core.database import get_session_factory
from app.scheduling.repository.sqlalchemy.models import MeetingRecord
from app.scheduling.service.service import SchedulingService
from tests.integration.matching.conftest import World
from tests.integration.pitches.conftest import act, client_of, preflight, reread, submit
from tests.integration.scheduling.conftest import (
    TEST_ACCESS_TOKEN,
    CalendarRelay,
    accept,
    approved,
    busy,
    connect_calendar,
    disconnect_calendar,
    propose,
    schedule,
)

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("clean_tables")]

# Proposals in the prototype are made on 2 November at 08:00 UTC for slots on 4 November.
MADE = datetime(2026, 11, 2, 8, tzinfo=UTC)
J04 = ["2026-11-04T09:00:00Z", "2026-11-04T11:00:00Z", "2026-11-04T13:00:00Z"]


def at(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


async def _meetings(state: str = "CONFIRMED") -> int:
    async with get_session_factory()() as session:
        query = select(func.count()).select_from(MeetingRecord).where(MeetingRecord.state == state)
        return await session.scalar(query) or 0


async def _bookings() -> list[tuple[str, str]]:
    async with get_session_factory()() as session:
        rows = await session.execute(
            text("SELECT party_id::text, (lower(during) AT TIME ZONE 'UTC')::text FROM bookings ORDER BY 2")
        )
        return [(row[0], row[1]) for row in rows]


async def test_j04_conflicts_keep_the_proposal_and_half_open_intervals_allow_ten_oclock(world: World) -> None:
    """
    Condition:
    - Mitra A is booked 09:00–10:00 on 4 November and proposes 09:00, 11:00 and 13:00; Rani accepts 09:00, then
      counters with 09:30 and 10:00; Mitra A accepts 09:30, then 10:00 (J04, AC50).

    Expected:
    - Both conflicts are ``BOOKING_CONFLICT`` naming the slot, and leave the proposal open with its agenda; the
      counter supersedes the first proposal; 10:00 succeeds, with one confirmed meeting and one booking per party,
      and its calendar file holds the UTC instants (AC68).
    """
    mitra, mitra_party = world.recipients.clients["A"], world.recipients.parties["A"]
    rani, rani_party = client_of(world, "F01")
    pitch = await approved(world)
    await busy(mitra_party, at("2026-11-04T09:00:00Z"), at("2026-11-04T10:00:00Z"))
    with clock.frozen(MADE):
        first = (await propose(mitra, pitch, J04, "p1")).json()
        clash = await accept(rani, first, 1, "a1")
        still = (await schedule(rani, pitch))["proposals"][0]
        counter = (await propose(rani, pitch, ["2026-11-04T09:30:00Z", "2026-11-04T10:00:00Z"], "p2")).json()
        again = await accept(mitra, counter, 1, "a2")
        confirmed = await accept(mitra, counter, 2, "a3")
        read = await schedule(rani, pitch)
        calendar = await rani.get(f"/api/v1/meetings/{confirmed.json()['id']}/calendar.ics")

    body = clash.json()["error"]
    assert (clash.status_code, body["code"], body["slot_id"]) == (409, "BOOKING_CONFLICT", first["slots"][0]["id"])
    assert body["message"].startswith("Waktu ini bentrok dengan jadwal peserta.")
    assert (still["state"], still["agenda"], len(still["slots"])) == ("OPEN", first["agenda"], 3)
    assert again.json()["error"]["code"] == "BOOKING_CONFLICT"
    assert confirmed.status_code == 200, confirmed.text
    assert (confirmed.json()["starts_at"], confirmed.json()["state"]) == ("2026-11-04T10:00:00Z", "CONFIRMED")
    assert sorted(p["state"] for p in read["proposals"]) == ["ACCEPTED", "SUPERSEDED"]
    assert await _meetings() == 1
    assert sorted(party for party, start in await _bookings() if start.startswith("2026-11-04 10")) == sorted(
        [mitra_party, rani_party]
    )
    assert "DTSTART:20261104T100000Z\r\n" in calendar.text and "DTEND:20261104T110000Z\r\n" in calendar.text
    assert calendar.headers["content-type"].startswith("text/calendar")
    assert read["external_calendar"] == "unknown"


async def test_choosing_is_not_booking_and_the_proposer_cannot_accept_its_own(world: World) -> None:
    """
    Condition:
    - Mitra A proposes; nobody accepts; then Mitra A accepts its own proposal.

    Expected:
    - No meeting exists until the other party confirms; accepting one's own is ``FORBIDDEN``.
    """
    mitra = world.recipients.clients["A"]
    pitch = await approved(world)
    with clock.frozen(MADE):
        proposal = (await propose(mitra, pitch, J04, "p")).json()
        own = await accept(mitra, proposal, 2, "own")

    assert await _meetings() == 0
    assert own.json()["error"]["code"] == "FORBIDDEN"


async def test_fifty_parallel_acceptances_book_once(world: World) -> None:
    """
    Condition:
    - Rani accepts the same slot 50 times at once, each with its own key (SC-001).

    Expected:
    - One confirmed meeting and one booking per party; every other answer is ``PROPOSAL_CLOSED``.
    """
    mitra = world.recipients.clients["A"]
    rani, _ = client_of(world, "F01")
    pitch = await approved(world)
    with clock.frozen(MADE):
        proposal = (await propose(mitra, pitch, J04, "p")).json()
        responses = await asyncio.gather(*(accept(rani, proposal, 2, f"race-{n}") for n in range(50)))

    codes = sorted(r.status_code for r in responses)
    assert codes.count(200) == 1
    assert {r.json()["error"]["code"] for r in responses if r.status_code != 200} == {"PROPOSAL_CLOSED"}
    assert await _meetings() == 1
    assert len(await _bookings()) == 2


async def test_two_overlapping_bookings_of_one_party_race_and_one_commits(world: World) -> None:
    """
    Condition:
    - Two inventors concurrently accept overlapping proposals from the same partner (AC50, FR-001).

    Expected:
    - One meeting and its two bookings commit. The other proposal stays open with a slot-specific conflict.
    """
    mitra = world.recipients.clients["A"]
    rani, _ = client_of(world, "F01")
    sinta, _ = client_of(world, "F06")
    first_pitch = await approved(world)
    submitted = await submit(world, "F06", await preflight(world, "F06", "A3"), key="submit-f06")
    assert submitted.status_code == 201, submitted.text
    second_pitch = await reread(mitra, {"id": submitted.json()["pitch_id"]})
    approval = await act(mitra, second_pitch, "decisions", "approve-f06", submission=1, decision="APPROVE")
    assert approval.status_code == 200, approval.text

    with clock.frozen(MADE):
        first = await propose(mitra, first_pitch, J04, "race-proposal-first")
        second = await propose(
            mitra, second_pitch, ["2026-11-04T09:30:00Z", "2026-11-04T12:00:00Z"], "race-proposal-second"
        )
        assert first.status_code == second.status_code == 201, (first.text, second.text)
        first_proposal, second_proposal = first.json(), second.json()
        results = await asyncio.gather(
            accept(rani, first_proposal, 1, "race-accept-first"),
            accept(sinta, second_proposal, 1, "race-accept-second"),
        )
        assert sorted(response.status_code for response in results) == [200, 409]
        losing = next(index for index, response in enumerate(results) if response.status_code == 409)
        rejected_proposal = (first_proposal, second_proposal)[losing]
        error = results[losing].json()["error"]
        assert (error["code"], error["slot_id"]) == ("BOOKING_CONFLICT", rejected_proposal["slots"][0]["id"])
        loser_schedule = await schedule((rani, sinta)[losing], (first_pitch, second_pitch)[losing])
        assert loser_schedule["proposals"][0]["state"] == "OPEN"
        assert loser_schedule["meetings"] == []

    bookings = await _bookings()
    assert await _meetings() == 1
    assert len(bookings) == 2
    assert world.recipients.parties["A"] in {party for party, _ in bookings}


async def test_a_replacement_keeps_the_old_meeting_until_it_is_accepted(world: World) -> None:
    """
    Condition:
    - A meeting at 10:00 on 4 November is confirmed; Rani proposes a replacement on 5 November; Mitra A accepts it
      (AC51). Before that, a plain new proposal without naming the meeting is refused.

    Expected:
    - While pending, the old meeting and its bookings stay; on acceptance it is cancelled and its bookings freed in
      the same transaction, leaving one confirmed meeting.
    """
    mitra = world.recipients.clients["A"]
    rani, _ = client_of(world, "F01")
    pitch = await approved(world)
    with clock.frozen(MADE):
        first = (await propose(mitra, pitch, ["2026-11-04T10:00:00Z", "2026-11-04T11:00:00Z"], "p1")).json()
        old = (await accept(rani, first, 1, "a1")).json()
        plain = await propose(rani, pitch, ["2026-11-05T10:30:00Z", "2026-11-05T11:30:00Z"], "plain")
        pending = (
            await propose(
                rani, pitch, ["2026-11-05T10:30:00Z", "2026-11-05T11:30:00Z"], "p2", replaces_meeting_id=old["id"]
            )
        ).json()
        before = await schedule(mitra, pitch)
        booked_before = await _bookings()
        new = (await accept(mitra, pending, 1, "a2")).json()
        after = await schedule(mitra, pitch)

    assert plain.json()["error"]["details"][0]["loc"] == ["body", "replaces_meeting_id"]
    assert [m["state"] for m in before["meetings"]] == ["CONFIRMED"]
    assert {start[:13] for _, start in booked_before} == {"2026-11-04 10"}
    assert {m["id"]: m["state"] for m in after["meetings"]} == {new["id"]: "CONFIRMED", old["id"]: "CANCELLED"}
    assert {start[:13] for _, start in await _bookings()} == {"2026-11-05 10"}


async def test_a_proposal_expires_at_exactly_seventy_two_hours(world: World) -> None:
    """
    Condition:
    - Slots on 6 November proposed on 2 November at 08:00; read at 07:59 and at 08:00 on 5 November (SCHED-72H).

    Expected:
    - Open one minute before; expired by age at exactly 72 hours, and accepting then is ``PROPOSAL_CLOSED``.
    """
    mitra = world.recipients.clients["A"]
    rani, _ = client_of(world, "F01")
    pitch = await approved(world)
    slots = ["2026-11-06T09:00:00Z", "2026-11-06T11:00:00Z", "2026-11-06T13:00:00Z"]
    with clock.frozen(MADE):
        proposal = (await propose(mitra, pitch, slots, "p")).json()
    with clock.frozen(datetime(2026, 11, 5, 7, 59, tzinfo=UTC)):
        early = (await schedule(rani, pitch))["proposals"][0]
    with clock.frozen(datetime(2026, 11, 5, 8, tzinfo=UTC)):
        late = (await schedule(rani, pitch))["proposals"][0]
        refused = await accept(rani, {**proposal, "version": late["version"]}, 1, "a")

    assert (early["state"], proposal["expires_at"]) == ("OPEN", "2026-11-05T08:00:00Z")
    assert (late["state"], late["expired_reason"]) == ("EXPIRED", "AGE")
    body = refused.json()["error"]
    assert (body["code"], body["reason"]) == (
        "PROPOSAL_CLOSED",
        "Usulan ini sudah kedaluwarsa. Pitching tetap disetujui untuk diskusi.",
    )


async def test_a_proposal_whose_slots_all_passed_expires_and_the_pitch_stays_approved(world: World) -> None:
    """
    Condition:
    - The J04 slots on 4 November are read at 13:00 that day, before 72 hours; the worker's job runs too.

    Expected:
    - Expired with reason ``ALL_PAST``, persisted by the job, and the pitch is still approved for discussion.
    """
    mitra = world.recipients.clients["A"]
    pitch = await approved(world)
    with clock.frozen(MADE):
        proposal = (await propose(mitra, pitch, J04, "p")).json()
    with clock.frozen(datetime(2026, 11, 4, 13, tzinfo=UTC)):
        async with get_session_factory()() as session, session.begin():
            from uuid import UUID  # noqa: PLC0415

            await SchedulingService(session).expire(UUID(proposal["id"]))
        read = (await schedule(mitra, pitch))["proposals"][0]
        status = (await mitra.get(f"/api/v1/pitches/{pitch['id']}")).json()["status"]

    assert (read["state"], read["expired_reason"]) == ("EXPIRED", "ALL_PAST")
    assert status == "APPROVED_FOR_DISCUSSION"


async def test_time_passing_never_completes_a_meeting(world: World) -> None:
    """
    Condition:
    - A meeting at 10:00 on 4 November; an outcome before it starts; then 20 November with no outcome; then Rani
      records "completed" and Mitra A "no show"; then Mitra A changes to "completed" (AC47).

    Expected:
    - The early outcome is ``INVALID_TRANSITION``; the elapsed meeting stays ``CONFIRMED`` and asks both to record;
      different outcomes stay visible as a disagreement; agreeing makes it ``COMPLETED``.
    """
    mitra = world.recipients.clients["A"]
    rani, rani_party = client_of(world, "F01")
    pitch = await approved(world)

    async def outcome(client: Any, meeting: dict[str, Any], result: str, key: str) -> Any:
        return await client.post(
            f"/api/v1/meetings/{meeting['id']}/outcome",
            json={"acting_party_id": client.headers["X-Acting-Party"], "result": result},
            headers={"Idempotency-Key": key},
        )

    with clock.frozen(MADE):
        proposal = (await propose(mitra, pitch, ["2026-11-04T10:00:00Z", "2026-11-04T11:00:00Z"], "p")).json()
        meeting = (await accept(rani, proposal, 1, "a")).json()
        early = await outcome(rani, meeting, "COMPLETED", "early")
    with clock.frozen(datetime(2026, 11, 20, tzinfo=UTC)):
        elapsed = (await schedule(rani, pitch))["meetings"][0]
        turn = (await rani.get(f"/api/v1/pitches/{pitch['id']}/next-action")).json()
        await outcome(rani, meeting, "COMPLETED", "rani")
        split = (await outcome(mitra, meeting, "NO_SHOW", "mitra")).json()
        settled = (await outcome(mitra, meeting, "COMPLETED", "mitra-2")).json()
        done = (await rani.get(f"/api/v1/pitches/{pitch['id']}/next-action")).json()

    assert early.json()["error"]["code"] == "INVALID_TRANSITION"
    assert (elapsed["state"], elapsed["started"], elapsed["outcomes"]) == ("CONFIRMED", True, [])
    assert (turn["who"], turn["title"]) == ("you", "Catat hasil pertemuan")
    assert (split["state"], split["disagreement"]) == ("CONFIRMED", True)
    assert {o["party_id"]: o["result"] for o in split["outcomes"]}[rani_party] == "COMPLETED"
    assert (settled["state"], settled["disagreement"]) == ("COMPLETED", False)
    assert (done["who"], done["title"]) == ("you", "Usulkan ringkasan Kerja Sama")


@pytest.mark.parametrize(
    ("change", "field"),
    [
        ({"slots": ["2026-11-01T09:00:00Z", "2026-11-04T09:00:00Z"]}, "slots"),
        ({"slots": ["2026-11-04T09:00:00Z"]}, "slots"),
        ({"minutes": 45}, "minutes"),
        ({"time_zone": "Jakarta"}, "time_zone"),
        ({"link": "http://meet.example.com/x"}, "link"),
        ({"agenda": " "}, "agenda"),
    ],
)
async def test_a_bad_proposal_names_its_field_and_nothing_is_proposed(
    world: World, change: dict[str, Any], field: str
) -> None:
    """
    Condition:
    - A slot in the past, one slot only, 45 minutes, a zone that is not IANA, an http link, an empty agenda.

    Expected:
    - ``VALIDATION_FAILED`` naming the field; no proposal exists.
    """
    mitra = world.recipients.clients["A"]
    pitch = await approved(world)
    with clock.frozen(MADE):
        rest = {key: value for key, value in change.items() if key != "slots"}
        response = await propose(mitra, pitch, change.get("slots", J04), "bad", **rest)
        read = await schedule(mitra, pitch)

    body = response.json()["error"]
    assert (response.status_code, body["code"]) == (422, "VALIDATION_FAILED")
    assert body["details"][0]["loc"][:2] == ["body", field]
    assert read["proposals"] == []


async def test_scheduling_waits_for_approval(world: World) -> None:
    """
    Condition:
    - Mitra A proposes on a pitch that is only submitted.

    Expected:
    - ``INVALID_TRANSITION``, and the schedule says the reader cannot schedule yet.
    """
    from tests.integration.pitches.conftest import submitted  # noqa: PLC0415

    mitra = world.recipients.clients["A"]
    pitch = await submitted(world)
    with clock.frozen(MADE):
        response = await propose(mitra, pitch, J04, "early")

    assert response.json()["error"]["code"] == "INVALID_TRANSITION"
    assert (await schedule(mitra, pitch))["can_schedule"] is False


async def test_cancelling_a_proposal_keeps_the_meeting_and_cancelling_a_meeting_frees_its_time(world: World) -> None:
    """
    Condition:
    - A confirmed meeting; a pending replacement is cancelled; then the meeting itself is cancelled.

    Expected:
    - The meeting survives the proposal's cancellation; its own cancellation frees both bookings.
    """
    mitra = world.recipients.clients["A"]
    rani, _ = client_of(world, "F01")
    pitch = await approved(world)
    with clock.frozen(MADE):
        first = (await propose(mitra, pitch, ["2026-11-04T10:00:00Z", "2026-11-04T11:00:00Z"], "p1")).json()
        meeting = (await accept(rani, first, 1, "a")).json()
        replacement = (
            await propose(
                rani, pitch, ["2026-11-05T10:00:00Z", "2026-11-05T11:00:00Z"], "p2", replaces_meeting_id=meeting["id"]
            )
        ).json()
        party = rani.headers["X-Acting-Party"]
        await rani.post(
            f"/api/v1/schedule-proposals/{replacement['id']}/cancel",
            json={"acting_party_id": party, "expected_version": replacement["version"]},
            headers={"Idempotency-Key": "c1"},
        )
        kept = await _meetings()
        cancelled = await rani.post(
            f"/api/v1/meetings/{meeting['id']}/cancel",
            json={"acting_party_id": party, "expected_version": meeting["version"]},
            headers={"Idempotency-Key": "c2"},
        )

    assert kept == 1
    assert cancelled.json()["state"] == "CANCELLED"
    assert await _bookings() == []


async def test_connected_viewer_sees_only_own_half_open_advice_and_can_book_busy_slot(
    world: World,
    calendar_relay: CalendarRelay,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Condition:
    - One party connected its calendar. A busy interval touches two slot boundaries and overlaps one slot.

    Expected:
    - Only the viewer who connected sees its own advice, and relay input contains only the exact UTC windows.
    - External busyness leaves internal concurrent booking and ICS unchanged.
    """
    import json

    mitra = world.recipients.clients["A"]
    rani, _ = client_of(world, "F01")
    await connect_calendar(rani)
    monkeypatch.setenv("HTTP_PROXY", "http://127.0.0.1:1")
    monkeypatch.setenv("NO_PROXY", "")
    calendar_relay.busy = {"busy": [{"start": "2026-11-04T10:00:00Z", "end": "2026-11-04T12:30:00Z"}]}
    pitch = await approved(world)
    with clock.frozen(MADE):
        proposal = (await propose(mitra, pitch, J04, "calendar-proposal")).json()
        from_owner = await rani.get(f"/api/v1/pitches/{pitch['id']}/schedule")
        other = await schedule(mitra, pitch)
        first, second = await asyncio.gather(
            accept(rani, proposal, 2, "calendar-accept-1"),
            accept(rani, proposal, 2, "calendar-accept-2"),
        )
        made = next(result for result in (first, second) if result.status_code == 200)
        ics = await rani.get(f"/api/v1/meetings/{made.json()['id']}/calendar.ics")
    assert "no-store" in from_owner.headers["cache-control"]
    assert from_owner.json()["external_calendar"] == "advisory"
    assert [slot["external_availability"] for slot in from_owner.json()["proposals"][0]["slots"]] == [
        "free",
        "busy",
        "free",
    ]
    assert other["external_calendar"] == "unknown"
    assert all("external_availability" not in slot for slot in other["proposals"][0]["slots"])
    assert [request.path for request in calendar_relay.requests] == ["/token", "/freebusy"]
    sent = calendar_relay.requests[-1]
    assert sent.headers["authorization"] == f"Bearer {TEST_ACCESS_TOKEN}"
    assert json.loads(sent.body) == {
        "windows": [
            {"start": "2026-11-04T09:00:00Z", "end": "2026-11-04T10:00:00Z"},
            {"start": "2026-11-04T11:00:00Z", "end": "2026-11-04T12:00:00Z"},
            {"start": "2026-11-04T13:00:00Z", "end": "2026-11-04T14:00:00Z"},
        ]
    }
    assert sorted(result.status_code for result in (first, second)) == [200, 409]
    assert await _meetings() == 1
    assert "DTSTART:20261104T110000Z\r\n" in ics.text


@pytest.mark.parametrize("failure", ["redirect", "oversize", "event_data", "timeout"])
async def test_provider_failure_remains_unknown_and_never_affects_internal_scheduling(
    world: World,
    calendar_relay: CalendarRelay,
    failure: str,
) -> None:
    """
    Condition:
    - A connected calendar returns a redirect, oversize, event details, or fails to respond.

    Expected:
    - The API returns unknown with no annotations, keeps provider data private, and booking and ICS succeed.
    """
    mitra = world.recipients.clients["A"]
    rani, _ = client_of(world, "F01")
    await connect_calendar(rani)
    if failure == "redirect":
        calendar_relay.busy_status = 307
    elif failure == "oversize":
        calendar_relay.busy = {"busy": "x" * 20_000}
    elif failure == "event_data":
        calendar_relay.busy = {
            "busy": [
                {
                    "start": "2026-11-04T09:15:00Z",
                    "end": "2026-11-04T09:45:00Z",
                    "title": "private synthetic event",
                }
            ]
        }
    else:
        calendar_relay.block_busy = True
    pitch = await approved(world)
    with clock.frozen(MADE):
        proposal = (await propose(mitra, pitch, J04, "calendar-failure")).json()
        read = await schedule(rani, pitch)
        calendar_relay.release_busy.set()
        made = await accept(rani, proposal, 1, "calendar-failure-accept")
        assert made.status_code == 200, made.text
        ics = await rani.get(f"/api/v1/meetings/{made.json()['id']}/calendar.ics")
    assert read["external_calendar"] == "unknown"
    assert all("external_availability" not in slot for slot in read["proposals"][0]["slots"])
    assert "private synthetic event" not in str(read)
    assert [request.path for request in calendar_relay.requests] == ["/token", "/freebusy"]
    assert "DTSTART:20261104T090000Z\r\n" in ics.text


async def test_disconnect_during_advisory_lookup_suppresses_the_in_flight_result(
    world: World,
    calendar_relay: CalendarRelay,
) -> None:
    """
    Condition:
    - The viewer disconnects while its private free/busy lookup is waiting on the relay.

    Expected:
    - Disconnect finishes without waiting on the old lookup, and the finished lookup returns unknown.
    """
    mitra = world.recipients.clients["A"]
    rani, _ = client_of(world, "F01")
    await connect_calendar(rani)
    calendar_relay.block_busy = True
    pitch = await approved(world)
    with clock.frozen(MADE):
        await propose(mitra, pitch, J04, "calendar-race")
        reading = asyncio.create_task(schedule(rani, pitch))
        await asyncio.wait_for(calendar_relay.busy_started.wait(), 1)
        disconnected = await asyncio.wait_for(disconnect_calendar(rani), 1)
        assert disconnected.status_code == 200
        assert (await rani.get("/api/v1/me/calendar")).json()["revocation"] == "confirmed"
        calendar_relay.release_busy.set()
        read = await reading
    assert read["external_calendar"] == "unknown"
    assert all("external_availability" not in slot for slot in read["proposals"][0]["slots"])
    assert [request.path for request in calendar_relay.requests] == ["/token", "/freebusy", "/revoke"]


async def test_lookup_rechecks_live_session_after_provider_io(world: World, calendar_relay: CalendarRelay) -> None:
    """
    Condition:
    - The viewer loses the authorized session while its external lookup is waiting on the relay.

    Expected:
    - A stale session cannot receive the pitch projection or calendar advice.
    """
    mitra = world.recipients.clients["A"]
    rani, _ = client_of(world, "F01")
    await connect_calendar(rani)
    calendar_relay.block_busy = True
    pitch = await approved(world)
    with clock.frozen(MADE):
        await propose(mitra, pitch, J04, "calendar-signout")
        reading = asyncio.create_task(rani.get(f"/api/v1/pitches/{pitch['id']}/schedule"))
        await asyncio.wait_for(calendar_relay.busy_started.wait(), 1)
        await rani.post("/api/v1/auth/sign-out")
        calendar_relay.release_busy.set()
        response = await reading
    assert (response.status_code, response.json()["error"]["code"]) == (401, "UNAUTHENTICATED")
    assert "external_availability" not in response.text
