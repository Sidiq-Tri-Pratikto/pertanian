"""Deliberate pitch submission through HTTP against Postgres (spec 023)."""

import asyncio
from collections.abc import Awaitable, Callable
from datetime import timedelta
from uuid import UUID

import pytest
from sqlalchemy import func, select, text

from app.core import clock
from app.core.database import get_session_factory
from app.pitches.repository.sqlalchemy.models import PitchRecord
from tests.factories.inventors import F01_BUDGET, SUPPORT_REQUESTS
from tests.factories.recipients import move_opportunity, save_opportunity
from tests.integration.matching.conftest import World
from tests.integration.pitches.conftest import client_of, preflight, submit

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("clean_tables")]

FAKE_SECRET = "sk-fakepitchsecret987"


async def _pitch_count() -> int:
    async with get_session_factory()() as session:
        return await session.scalar(select(func.count()).select_from(PitchRecord)) or 0


async def test_a_fresh_preflight_sends_once_shares_one_version_and_notifies(world: World) -> None:
    """
    Condition:
    - Rani preflights F01 against A1 and submits with the test report, version 1 (scenario 1).

    Expected:
    - One submitted pitch, a grant to Mitra A for version 1 only, a ``pitch.submitted`` event, Mitra A's incoming
      list shows it, and both sides read the frozen submission.
    """
    checked = await preflight(world, "F01", "A1")
    response = await submit(world, "F01", checked)
    pitch = response.json()
    rani, _ = client_of(world, "F01")
    mitra = world.recipients.clients["A"]
    document = (await rani.get(f"/api/v1/documents/{checked['shareable_files'][0]['document_id']}")).json()
    incoming = (await mitra.get("/api/v1/pitches", params={"box": "incoming"})).json()
    detail = (await mitra.get(f"/api/v1/pitches/{pitch['pitch_id']}")).json()
    async with get_session_factory()() as session:
        events = await session.scalar(text("SELECT count(*) FROM outbox_events WHERE topic = 'pitch.submitted'"))

    assert response.status_code == 201, response.text
    assert (pitch["status"], pitch["submission"]) == ("SUBMITTED", 1)
    assert [(grant["version"], grant["grantee_name"], grant["purpose"]) for grant in document["grants"]] == [
        (1, "Mitra A", "pitch")
    ]
    assert events == 1
    assert [item["id"] for item in incoming] == [pitch["pitch_id"]]
    assert (incoming[0]["requester_name"], incoming[0]["subject_title"]) == ("Rani", "ClearSpring")
    assert detail["submissions"][0]["files"] == [
        {"document_id": document["id"], "version": 1, "title": "Laporan uji fungsi ClearSpring"}
    ]
    assert detail["submissions"][0]["brief"] == checked["brief"]["text"]


async def test_a_retried_submission_returns_the_original_once(world: World) -> None:
    """
    Condition:
    - The response is lost and Rani retries with the same key, then sends the same key with another brief (AC37,
      AC38).

    Expected:
    - The retry replays the original pitch and nothing is added; the changed body is ``IDEMPOTENCY_CONFLICT``.
    """
    checked = await preflight(world, "F01", "A1")
    first = await submit(world, "F01", checked, key="lost")
    retry = await submit(world, "F01", checked, key="lost")
    changed = await submit(world, "F01", checked, key="lost", brief="Brief lain")

    assert retry.status_code == 201
    assert retry.json()["pitch_id"] == first.json()["pitch_id"]
    assert changed.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"
    assert await _pitch_count() == 1


async def test_a_second_pitch_of_one_raise_to_one_target_points_at_the_first(world: World) -> None:
    """
    Condition:
    - Bima pitches FRaise01 to B1, then prepares it again, as from its second linked invention (AC39).

    Expected:
    - The new preflight names the existing pitch, and submitting is ``DUPLICATE_PITCH`` with its id.
    """
    first = (await submit(world, "FRaise01", await preflight(world, "FRaise01", "B1"), key="one")).json()
    again = await preflight(world, "FRaise01", "B1")
    duplicate = await submit(world, "FRaise01", again, key="two", brief=f"Coba lagi {FAKE_SECRET}")

    assert again["duplicate_pitch_id"] == first["pitch_id"]
    body = duplicate.json()["error"]
    assert duplicate.status_code == 409
    assert (body["code"], body["pitch_id"]) == ("DUPLICATE_PITCH", first["pitch_id"])
    assert body["message"].startswith("Pitching untuk kebutuhan dan mandat ini sudah ada.")
    assert body["recovery"]["retryable"] is False and body["request_id"]
    assert FAKE_SECRET not in duplicate.text
    assert await _pitch_count() == 1


async def test_parallel_submissions_with_different_keys_make_one_pitch(world: World) -> None:
    """
    Condition:
    - Five submissions of one preflight race, each with its own key (FR-001).

    Expected:
    - Exactly one pitch; every other answer is ``DUPLICATE_PITCH`` naming it.
    """
    checked = await preflight(world, "F01", "A1")
    responses = await asyncio.gather(*(submit(world, "F01", checked, key=f"race-{n}") for n in range(5)))
    created = [response for response in responses if response.status_code == 201]
    others = {response.json()["error"]["code"] for response in responses if response.status_code != 201}

    assert len(created) == 1
    assert others <= {"DUPLICATE_PITCH"}
    assert await _pitch_count() == 1


async def test_twenty_identical_submissions_create_one_pitch(world: World) -> None:
    """
    Condition:
    - Twenty identical submissions with one key arrive together (SC-001).

    Expected:
    - One pitch.
    """
    checked = await preflight(world, "F01", "A1")
    await asyncio.gather(*(submit(world, "F01", checked, key="same") for _ in range(20)))

    assert await _pitch_count() == 1


async def test_a_closed_target_stops_new_pitches(world: World) -> None:
    """
    Condition:
    - Rani preflights against A1, then Mitra A closes it (AC26).

    Expected:
    - ``TARGET_CLOSED`` saying new pitches stop and discussions remain, with the reason; no pitch.
    """
    checked = await preflight(world, "F01", "A1")
    mitra, party = world.recipients.clients["A"], world.recipients.parties["A"]
    current = (await mitra.get(f"/api/v1/opportunities/{world.opportunity('A1')}")).json()
    closed = await move_opportunity(mitra, party, world.opportunity("A1"), "close", current["version"])
    assert closed.status_code == 200, closed.text
    response = await submit(world, "F01", checked)

    body = response.json()["error"]
    assert (response.status_code, body["code"]) == (409, "TARGET_CLOSED")
    assert "Diskusi yang sudah berjalan tetap berlanjut" in body["message"]
    assert body["reason"] == "Mandat ini sudah ditutup, dijeda atau berakhir."
    assert await _pitch_count() == 0


async def test_a_changed_mandate_makes_the_preflight_stale(world: World) -> None:
    """
    Condition:
    - Mitra A saves A1 as version 2 after Rani's preflight (AC34, scenario 6).

    Expected:
    - ``PREFLIGHT_STALE`` saying the mandate changed; a fresh preflight pins version 2 and submits.
    """
    from tests.factories.recipients import OPPORTUNITIES  # noqa: PLC0415

    checked = await preflight(world, "F01", "A1")
    mitra, party = world.recipients.clients["A"], world.recipients.parties["A"]
    current = (await mitra.get(f"/api/v1/opportunities/{world.opportunity('A1')}")).json()
    content = {**OPPORTUNITIES["A1"]["content"], "timing": "Dibuka sampai 15 Desember 2026"}
    saved = await save_opportunity(mitra, party, world.opportunity("A1"), content, current["version"])
    assert saved.status_code == 200, saved.text
    stale = await submit(world, "F01", checked, key="stale")
    fresh = await preflight(world, "F01", "A1")

    assert (stale.status_code, stale.json()["error"]["code"]) == (409, "PREFLIGHT_STALE")
    assert stale.json()["error"]["reason"] == "Mandat berubah setelah pemeriksaan."
    assert fresh["opportunity"]["version"] == 2
    assert (await submit(world, "F01", fresh, key="fresh")).status_code == 201


async def test_an_expired_preflight_is_stale_and_another_partys_token_is_not_found(world: World) -> None:
    """
    Condition:
    - Rani's preflight passes 30 minutes; Galih sends Rani's token.

    Expected:
    - ``PREFLIGHT_STALE`` for Rani; NOT_FOUND for Galih.
    """
    checked = await preflight(world, "F01", "A1")
    async with get_session_factory()() as session, session.begin():
        await session.execute(
            text("UPDATE preflights SET expires_at = :at"), {"at": clock.now() - timedelta(seconds=1)}
        )
    expired = await submit(world, "F01", checked, key="late")
    galih, party = client_of(world, "F03")
    foreign = await galih.post(
        "/api/v1/pitches",
        json={"acting_party_id": party, "preflight_token": checked["token"], "brief": "x", "files": []},
        headers={"Idempotency-Key": "foreign"},
    )

    assert expired.json()["error"]["reason"] == "Pemeriksaan sudah lebih dari 30 menit."
    assert foreign.status_code == 404


async def test_a_required_file_must_be_chosen(world: World) -> None:
    """
    Condition:
    - Rani submits F01 to A1 without choosing the test report, then with a file not in the preflight (scenario 7).

    Expected:
    - ``NOT_READY`` naming "Berkas uji fungsi"; the unknown file is refused per field; no pitch.
    """
    checked = await preflight(world, "F01", "A1")
    missing = await submit(world, "F01", checked, files=[], key="none")
    unknown = await submit(
        world, "F01", checked, files=[{"document_id": checked["preflight_id"], "version": 1}], key="unknown"
    )

    assert (missing.status_code, missing.json()["error"]["code"]) == (422, "NOT_READY")
    assert missing.json()["error"]["requirement"] == "Berkas uji fungsi"
    assert unknown.json()["error"]["code"] == "VALIDATION_FAILED"
    assert await _pitch_count() == 0


async def test_needs_information_cannot_be_submitted(make_world: Callable[..., Awaitable[World]]) -> None:
    """
    Condition:
    - F01-GAP, whose range is still open, against A1.

    Expected:
    - ``NOT_READY`` naming "Kisaran biaya pilot".
    """
    gap = await make_world(gap=True)
    try:
        response = await submit(gap, "F01", await preflight(gap, "F01", "A1"))
    finally:
        await gap.recipients.close()
        await gap.inventors.close()

    assert response.json()["error"]["requirement"] == "Kisaran biaya pilot"


async def test_later_edits_never_change_a_submission(world: World) -> None:
    """
    Condition:
    - After submitting, Rani changes F01's outcome.

    Expected:
    - The frozen submission still shows the outcome that was sent.
    """
    pitch = (await submit(world, "F01", await preflight(world, "F01", "A1"))).json()
    rani, party = client_of(world, "F01")
    request_id = world.inventors.support_requests["F01"]
    current = (await rani.get(f"/api/v1/support-requests/{request_id}")).json()
    changed = await rani.put(
        f"/api/v1/support-requests/{request_id}",
        json={
            "acting_party_id": party,
            "expected_version": current["version"],
            **SUPPORT_REQUESTS["F01"],
            "outcome": "Hasil yang diubah",
            "budget": F01_BUDGET,
        },
        headers={"Idempotency-Key": "edit-after"},
    )
    assert changed.status_code == 200, changed.text
    detail = (await rani.get(f"/api/v1/pitches/{pitch['pitch_id']}")).json()

    assert detail["submissions"][0]["snapshot"]["source"]["outcome"] == "Validasi prototipe enam bulan"


async def test_the_sixth_pitch_in_a_day_is_rate_limited(world: World) -> None:
    """
    Condition:
    - Rani's party already started five pitches today (policy ``pitch-rate-limit`` v1).

    Expected:
    - ``RATE_LIMITED`` naming the limit, retryable with a wait; no pitch is added.
    """
    rani_party = UUID(world.inventors.parties["rani"])
    other = UUID(world.recipients.parties["A"])
    async with get_session_factory()() as session, session.begin():
        for n in range(5):
            session.add(
                PitchRecord(
                    requester_party_id=rani_party,
                    recipient_party_id=other,
                    opportunity_id=UUID(int=n + 1),
                    opportunity_version_id=UUID(int=n + 1),
                    subject_type="SUPPORT_REQUEST",
                    subject_id=UUID(int=n + 1),
                    status="WITHDRAWN",
                    active=False,
                )
            )
    response = await submit(world, "F01", await preflight(world, "F01", "A1"))

    body = response.json()["error"]
    assert (response.status_code, body["code"]) == (429, "RATE_LIMITED")
    assert body["message"].startswith("Batas 5 pitching baru per hari sudah tercapai.")
    assert body["recovery"]["retryable"] is True and body["recovery"]["retry_after_seconds"] > 0
    assert await _pitch_count() == 5


async def test_only_the_two_sides_read_a_pitch(world: World) -> None:
    """
    Condition:
    - A submitted pitch, read by Galih, and listed by Galih.

    Expected:
    - NOT_FOUND and an empty list.
    """
    pitch = (await submit(world, "F01", await preflight(world, "F01", "A1"))).json()
    galih, _ = client_of(world, "F03")

    assert (await galih.get(f"/api/v1/pitches/{pitch['pitch_id']}")).status_code == 404
    assert (await galih.get("/api/v1/pitches", params={"box": "incoming"})).json() == []
