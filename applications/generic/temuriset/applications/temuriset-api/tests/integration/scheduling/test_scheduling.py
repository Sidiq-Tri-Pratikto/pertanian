"""Race-safe scheduling through HTTP against Postgres, with a frozen product clock (spec 028)."""

import asyncio
from datetime import UTC, datetime
from typing import Any

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.dialects.postgresql import Range
from sqlalchemy.exc import IntegrityError

from app.core import clock
from app.core.database import get_session_factory
from app.scheduling.repository.sqlalchemy.models import BookingRecord, MeetingRecord
from app.scheduling.service.service import SchedulingService
from tests.integration.matching.conftest import World
from tests.integration.pitches.conftest import client_of
from tests.integration.scheduling.conftest import accept, approved, busy, propose, schedule

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
    - Two transactions book overlapping hours for one party at the same moment (AC50, FR-001).

    Expected:
    - The exclusion constraint lets exactly one commit; the other fails with an integrity error.
    """
    party = world.recipients.parties["A"]

    async def book(start: str, end: str) -> str:
        try:
            async with get_session_factory()() as session, session.begin():
                session.add(BookingRecord(party_id=party, title="x", during=Range(at(start), at(end), bounds="[)")))
                await session.flush()
                await asyncio.sleep(0.2)
            return "committed"
        except IntegrityError:
            return "conflict"

    results = await asyncio.gather(
        book("2026-11-04T09:00:00Z", "2026-11-04T10:00:00Z"), book("2026-11-04T09:30:00Z", "2026-11-04T10:30:00Z")
    )

    assert sorted(results) == ["committed", "conflict"]


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
