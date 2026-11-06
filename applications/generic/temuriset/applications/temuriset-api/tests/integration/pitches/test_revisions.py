"""Itemized revision rounds through HTTP against Postgres (spec 025, AC43–AC45)."""

from typing import Any

import pytest
from httpx import AsyncClient

from tests.factories.inventors import upload_document
from tests.integration.matching.conftest import World
from tests.integration.pitches.conftest import REVISION_ITEMS, act, answer, client_of, reread, submitted

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("clean_tables")]

FAKE_SECRET = "sk-fakerevisionsecret654"


async def _in_revision(world: World) -> tuple[AsyncClient, AsyncClient, dict[str, Any]]:
    """Mitra A opens round 1 with the two J03 items; return both clients and Rani's reading."""
    mitra = world.recipients.clients["A"]
    rani, _ = client_of(world, "F01")
    pitch = await submitted(world)
    opened = await act(mitra, pitch, "revision-rounds", "round-1", submission=1, items=REVISION_ITEMS)
    assert opened.status_code == 201, opened.text
    return mitra, rani, await reread(rani, pitch)


def _items(pitch: dict[str, Any], round_number: int = 1) -> list[dict[str, Any]]:
    return pitch["rounds"][round_number - 1]["items"]


async def test_an_honest_cannot_answer_lets_resubmission_through_without_approving(world: World) -> None:
    """
    Condition:
    - Round 1 holds a required budget question and an optional feature question; Rani answers only the required one
      "Belum dapat dipenuhi" and resubmits (AC43).

    Expected:
    - Submission 2 is ``SUBMITTED``, waiting on Mitra A, with no decision; round 1 is closed and keeps its answer.
    """
    mitra, rani, pitch = await _in_revision(world)
    required = _items(pitch)[0]

    saved = await answer(rani, pitch, required["id"], "CANNOT", text="Biaya dua lokasi belum dapat kami penuhi.")
    resubmitted = await act(rani, pitch, "resubmit", "resubmit")
    seen = await reread(mitra, pitch)

    assert saved.status_code == 200, saved.text
    assert (resubmitted.json()["status"], resubmitted.json()["submission"]) == ("SUBMITTED", 2)
    assert seen["decisions"] == []
    assert seen["waiting_on_party_id"] == world.recipients.parties["A"]
    assert seen["rounds"][0]["open"] is False
    assert _items(seen)[0]["answer"]["response"] == "CANNOT"
    assert _items(seen)[1]["answer"] is None
    assert [item["number"] for item in seen["submissions"]] == [1, 2]


async def test_resubmitting_with_a_required_item_unanswered_lists_it(world: World) -> None:
    """
    Condition:
    - Rani answers only the optional item and resubmits.

    Expected:
    - ``REQUIRED_ANSWERS_MISSING`` naming the required item; the pitch stays in revision.
    """
    _, rani, pitch = await _in_revision(world)
    required, optional = _items(pitch)
    await answer(rani, pitch, optional["id"], "DISCUSS", text=f"Perlu diskusi {FAKE_SECRET}")

    response = await act(rani, pitch, "resubmit", "missing")

    body = response.json()["error"]
    assert (response.status_code, body["code"], body["items"]) == (422, "REQUIRED_ANSWERS_MISSING", [required["id"]])
    assert body["message"].startswith("Masih ada pertanyaan wajib yang belum dijawab.")
    assert body["recovery"]["retryable"] is False and body["request_id"]
    assert FAKE_SECRET not in response.text
    assert (await reread(rani, pitch))["status"] == "REVISION_REQUESTED"


async def test_a_planned_feature_in_an_answer_stays_planned(world: World) -> None:
    """
    Condition:
    - Rani answers the feature question with a plan for 20 L/jam and resubmits (AC44).

    Expected:
    - Submission 2 shows the same invention version and facts as submission 1: the answer changed no capability.
    """
    mitra, rani, pitch = await _in_revision(world)
    required, optional = _items(pitch)
    await answer(rani, pitch, required["id"], "CAN", text="Ya, sudah termasuk dua lokasi.")
    await answer(rani, pitch, optional["id"], "CAN", text="Kapasitas 20 L/jam direncanakan pada kuartal depan.")

    await act(rani, pitch, "resubmit", "resubmit")
    first, second = (await reread(mitra, pitch))["submissions"]

    assert second["snapshot"]["inventions"] == first["snapshot"]["inventions"]
    assert all(
        fact["timing"] != "CURRENT" or "20 L/jam" not in str(fact["value"])
        for fact in second["snapshot"]["inventions"][0]["facts"]
    )


async def test_a_new_file_version_is_shared_while_the_first_submission_stays(world: World) -> None:
    """
    Condition:
    - Rani uploads version 2 of the test report, attaches it to her answer, and resubmits choosing it (AC45).

    Expected:
    - Submission 2 shares version 2 once, submission 1 still shows version 1, round 1 keeps the answer and its file,
      and Mitra A holds grants for both versions.
    """
    mitra, rani, pitch = await _in_revision(world)
    _, party = client_of(world, "F01")
    first_file = pitch["submissions"][0]["files"][0]
    await upload_document(rani, party, "Laporan uji fungsi ClearSpring", first_file["document_id"])
    newer = {"document_id": first_file["document_id"], "version": 2}

    saved = await answer(rani, pitch, _items(pitch)[0]["id"], "CAN", text="Rincian terlampir.", files=[newer])
    resubmitted = await act(rani, pitch, "resubmit", "resubmit", files=[newer])
    seen = await reread(mitra, pitch)
    document = (await rani.get(f"/api/v1/documents/{first_file['document_id']}")).json()

    assert saved.json()["files"] == [{**newer, "title": "Laporan uji fungsi ClearSpring"}]
    assert resubmitted.status_code == 200, resubmitted.text
    assert [[f["version"] for f in item["files"]] for item in seen["submissions"]] == [[1], [2]]
    assert _items(seen)[0]["answer"]["files"][0]["version"] == 2
    assert sorted(grant["version"] for grant in document["grants"]) == [1, 2]


async def test_draft_answers_are_versioned_and_hidden_until_resubmission(world: World) -> None:
    """
    Condition:
    - Rani saves an answer, saves it again with its version, then once more with the old version; Mitra A reads the
      open round.

    Expected:
    - Versions 1 then 2, the stale save is ``STALE_VERSION`` with version 2, and Mitra A sees the items but no answer.
    """
    mitra, rani, pitch = await _in_revision(world)
    item = _items(pitch)[0]

    first = await answer(rani, pitch, item["id"], "DISCUSS", text="Perlu dibahas.")
    second = await answer(rani, pitch, item["id"], "CAN", version=1, text="Bisa.")
    stale = await answer(rani, pitch, item["id"], "CANNOT", version=1)
    first_again = await answer(rani, pitch, item["id"], "CANNOT")

    assert (first.json()["version"], second.json()["version"]) == (1, 2)
    assert (stale.json()["error"]["code"], stale.json()["error"]["current_version"]) == ("STALE_VERSION", 2)
    assert first_again.json()["error"]["code"] == "STALE_VERSION"
    assert _items(await reread(rani, pitch))[0]["answer"]["text"] == "Bisa."
    assert _items(await reread(mitra, pitch))[0]["answer"] is None


async def test_a_failed_attachment_keeps_the_other_answers(world: World) -> None:
    """
    Condition:
    - Rani answers the optional item, then saves the required one with a file version that does not exist.

    Expected:
    - ``VALIDATION_FAILED`` naming the file; the optional answer is untouched and the required one stays unsaved.
    """
    _, rani, pitch = await _in_revision(world)
    required, optional = _items(pitch)
    await answer(rani, pitch, optional["id"], "DISCUSS", text="Perlu diskusi.")
    missing = {"document_id": pitch["submissions"][0]["files"][0]["document_id"], "version": 9}

    failed = await answer(rani, pitch, required["id"], "CAN", text="Terlampir.", files=[missing])
    after = _items(await reread(rani, pitch))

    body = failed.json()["error"]
    assert (failed.status_code, body["code"]) == (422, "VALIDATION_FAILED")
    assert body["details"][0]["loc"] == ["body", "files", 0]
    assert (after[0]["answer"], after[1]["answer"]["text"]) == (None, "Perlu diskusi.")


async def test_item_review_comes_after_resubmission_and_is_stored_per_item(world: World) -> None:
    """
    Condition:
    - Mitra A marks an item while the round is open, then after resubmission accepts one and asks detail on another.

    Expected:
    - The early mark is ``INVALID_TRANSITION``; then each item keeps its own mark and the pitch is not approved.
    """
    mitra, rani, pitch = await _in_revision(world)
    required, optional = _items(pitch)
    for item in (required, optional):
        await answer(rani, pitch, item["id"], "CAN", text="Ya.")

    def review(item: dict[str, Any], result: str, version: int = 1) -> Any:
        return mitra.put(
            f"/api/v1/pitches/{pitch['id']}/revision-items/{item['id']}/review",
            json={"acting_party_id": world.recipients.parties["A"], "expected_version": version, "result": result},
        )

    early = await review(required, "ACCEPTED")
    await act(rani, pitch, "resubmit", "resubmit")
    accepted = await review(required, "ACCEPTED")
    detail = await review(optional, "NEEDS_DETAIL")
    seen = await reread(mitra, pitch)

    assert early.json()["error"]["code"] == "INVALID_TRANSITION"
    assert (accepted.json()["review"], accepted.json()["version"]) == ("ACCEPTED", 2)
    assert detail.json()["review"] == "NEEDS_DETAIL"
    assert [item["review"] for item in _items(seen)] == ["ACCEPTED", "NEEDS_DETAIL"]
    assert (seen["status"], seen["decisions"]) == ("SUBMITTED", [])


async def test_a_closed_round_takes_no_more_answers_and_the_recipient_cannot_answer(world: World) -> None:
    """
    Condition:
    - Mitra A answers an item; Rani resubmits and then edits her answer.

    Expected:
    - Mitra A is ``FORBIDDEN``; Rani's late edit is ``INVALID_TRANSITION`` and round 1 keeps what was sent.
    """
    mitra, rani, pitch = await _in_revision(world)
    item = _items(pitch)[0]
    await answer(rani, pitch, item["id"], "CAN", text="Terkirim.")

    recipient = await answer(mitra, pitch, item["id"], "CAN")
    await act(rani, pitch, "resubmit", "resubmit")
    late = await answer(rani, pitch, item["id"], "CANNOT", version=1)

    assert recipient.json()["error"]["code"] == "FORBIDDEN"
    assert late.json()["error"]["code"] == "INVALID_TRANSITION"
    assert _items(await reread(mitra, pitch))[0]["answer"]["text"] == "Terkirim."


async def test_a_second_round_numbers_itself_and_keeps_the_first(world: World) -> None:
    """
    Condition:
    - After a first resubmission, Mitra A opens round 2 on submission 2, naming submission 1 first.

    Expected:
    - Naming submission 1 is ``STALE_VERSION``; round 2 opens on submission 2 and round 1 keeps its answer.
    """
    mitra, rani, pitch = await _in_revision(world)
    await answer(rani, pitch, _items(pitch)[0]["id"], "CANNOT", text="Belum.")
    await act(rani, pitch, "resubmit", "resubmit")
    current = await reread(mitra, pitch)

    old = await act(mitra, current, "revision-rounds", "old", submission=1, items=REVISION_ITEMS[:1])
    second = await act(mitra, current, "revision-rounds", "round-2", submission=2, items=REVISION_ITEMS[:1])
    seen = await reread(rani, pitch)

    assert old.json()["error"]["code"] == "STALE_VERSION"
    assert (second.status_code, second.json()["round"]) == (201, 2)
    assert [(r["number"], r["submission_number"], r["open"]) for r in seen["rounds"]] == [(1, 1, False), (2, 2, True)]
    assert _items(seen)[0]["answer"]["text"] == "Belum."
    assert "answer" in seen["allowed_actions"] and "resubmit" in seen["allowed_actions"]
