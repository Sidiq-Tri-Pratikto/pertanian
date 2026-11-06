"""Relationship records confirmed on the same version, through HTTP against Postgres (spec 030)."""

from collections.abc import Awaitable, Callable

import pytest
from httpx import AsyncClient

from tests.integration.matching.conftest import World
from tests.integration.pitches.conftest import client_of, submitted
from tests.integration.relationships.conftest import (
    ALL,
    VALUES,
    confirm,
    met,
    partnership_action,
    propose_partnership,
)

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("clean_tables")]

FAKE_SECRET = "sk-fakepartnershipsecret111"


async def test_one_confirmation_shows_nothing_and_a_correction_starts_over(world: World) -> None:
    """
    Condition:
    - Rani proposes version 1; Mitra A requests a scope correction; Mitra A then tries to confirm with version 1's
      checksum (AC52, AC53).

    Expected:
    - Version 1 is pending with no public field; after the correction it is ``CHANGES_REQUESTED`` and version 2 has
      no confirmations; the old checksum is ``STALE_VERSION``; Mitra A's next action asks to confirm version 2.
    """
    mitra = world.recipients.clients["A"]
    rani, _ = client_of(world, "F01")
    pitch = await met(world)

    proposed = (await propose_partnership(rani, pitch)).json()
    corrected = await partnership_action(
        mitra, proposed, "corrections", "fix", version=1, values={**VALUES, "scope": "Validasi enam bulan"}
    )
    stale = await confirm(mitra, proposed, ["name"], "old")
    record = corrected.json()
    turn = (await mitra.get(f"/api/v1/pitches/{pitch['id']}/next-action")).json()
    rani_turn = (await rani.get(f"/api/v1/pitches/{pitch['id']}/next-action")).json()

    assert (proposed["current"]["status"], proposed["effective"]) == (
        "PENDING_COUNTERPARTY",
        {"version": None, "fields": [], "values": {}},
    )
    assert corrected.status_code == 201, corrected.text
    assert [(v["number"], v["status"], len(v["confirmations"])) for v in record["versions"]] == [
        (1, "CHANGES_REQUESTED", 1),
        (2, "PENDING_COUNTERPARTY", 0),
    ]
    assert (stale.json()["error"]["code"], stale.json()["error"]["current_version"]) == ("STALE_VERSION", 2)
    assert (turn["who"], turn["title"]) == ("you", "Konfirmasi ringkasan Kerja Sama versi 2")
    assert rani_turn["who"] == "you"


async def test_both_confirming_version_two_shows_only_what_both_allowed(world: World) -> None:
    """
    Condition:
    - Version 2 after a correction; Rani allows name, type, scope, date and amount, Mitra A all but amount.

    Expected:
    - ``CONFIRMED``; effective fields exclude amount, evidence never appears, and both next actions wait on no one.
    """
    mitra = world.recipients.clients["A"]
    rani, _ = client_of(world, "F01")
    pitch = await met(world)
    proposed = (await propose_partnership(rani, pitch)).json()
    v2 = (
        await partnership_action(mitra, proposed, "corrections", "fix", version=1, values={**VALUES, "scope": "Enam"})
    ).json()

    await confirm(rani, v2, ALL, "r")
    done = (await confirm(mitra, v2, ["name", "type", "scope", "date"], "m")).json()
    turn = (await rani.get(f"/api/v1/pitches/{pitch['id']}/next-action")).json()

    assert done["current"]["status"] == "CONFIRMED"
    assert done["effective"]["version"] == 2
    assert done["effective"]["fields"] == ["name", "type", "scope", "date"]
    assert "amount" not in done["effective"]["values"]
    assert "Catatan pertemuan" not in str(done["effective"])
    assert (turn["who"], turn["title"]) == (None, "Kerja Sama dikonfirmasi kedua pihak")


async def test_a_project_amount_creates_no_share(world: World) -> None:
    """
    Condition:
    - A PROJECT with a percent, then a PROJECT with an amount both parties allow (AC54).

    Expected:
    - The percent is ``VALIDATION_FAILED``; the amount shows with its currency and no percent or ownership field.
    """
    mitra = world.recipients.clients["A"]
    rani, _ = client_of(world, "F01")
    pitch = await met(world)

    share = await propose_partnership(
        rani, pitch, key="share", values={**VALUES, "percent": "10", "percent_date": "2026-12-01"}
    )
    proposed = (await propose_partnership(rani, pitch)).json()
    done = (await confirm(mitra, proposed, ALL, "m")).json()

    assert share.json()["error"]["details"][0]["loc"] == ["body", "values", "percent"]
    assert done["effective"]["values"]["amount"] == {"amount": "25000", "currency": "USD"}
    assert "percent" not in done["effective"]["values"]


async def test_equity_without_an_identified_company_is_refused_and_discussion_stays(world: World) -> None:
    """
    Condition:
    - Rani's F01 has no legal entity; she proposes EQUITY (AC21).

    Expected:
    - ``ENTITY_REQUIRED``; the pitch stays approved and a PROJECT can still be proposed.
    """
    rani, _ = client_of(world, "F01")
    pitch = await met(world)

    refused = await propose_partnership(rani, pitch, key="equity", type="EQUITY")
    status = (await rani.get(f"/api/v1/pitches/{pitch['id']}")).json()["status"]
    project = await propose_partnership(rani, pitch, key="project")

    body = refused.json()["error"]
    assert (refused.status_code, body["code"]) == (422, "ENTITY_REQUIRED")
    assert body["message"].startswith("Kerja Sama ekuitas memerlukan badan usaha")
    assert body["recovery"]["retryable"] is False and body["request_id"]
    assert status == "APPROVED_FOR_DISCUSSION"
    assert project.status_code == 201


async def test_one_equity_relationship_references_both_inventions_once(world: World) -> None:
    """
    Condition:
    - Bima's FRaise01 (an existing company, two inventions) reaches B1, meets, and proposes EQUITY with a percent.

    Expected:
    - One relationship naming both inventions once, with the percent and its effective date.
    """
    bima, _ = client_of(world, "FRaise01")
    pitch = await met(world, "FRaise01", "B1", "B")

    proposed = await propose_partnership(
        bima,
        pitch,
        type="EQUITY",
        values={**VALUES, "name": "Demo Circular Materials Ltd", "percent": "12.5", "percent_date": "2027-01-01"},
        ceiling=["name", "type", "percent"],
        subset=["name", "type", "percent"],
    )

    record = proposed.json()
    assert proposed.status_code == 201, proposed.text
    assert len(record["invention_ids"]) == len(set(record["invention_ids"])) == 2
    assert record["current"]["values"]["percent"] == "12.5"


async def test_no_relationship_before_a_completed_meeting(world: World) -> None:
    """
    Condition:
    - A pitch that is only submitted, then one approved with no meeting.

    Expected:
    - ``INVALID_TRANSITION`` before approval and ``MEETING_NOT_COMPLETED`` after.
    """
    from tests.integration.pitches.conftest import act  # noqa: PLC0415

    mitra = world.recipients.clients["A"]
    rani, _ = client_of(world, "F01")
    pitch = await submitted(world)
    early = await propose_partnership(rani, pitch, key="early")
    await act(mitra, pitch, "decisions", "approve", submission=1, decision="APPROVE")
    no_meeting = await propose_partnership(rani, pitch, key="later", values={**VALUES, "evidence": FAKE_SECRET})

    assert early.json()["error"]["code"] == "INVALID_TRANSITION"
    body = no_meeting.json()["error"]
    assert (no_meeting.status_code, body["code"]) == (409, "MEETING_NOT_COMPLETED")
    assert FAKE_SECRET not in no_meeting.text


async def test_restrictions_narrow_at_once_and_expansion_needs_both(world: World) -> None:
    """
    Condition:
    - A confirmed version 1 without amount; Rani restricts date; then Mitra A proposes version 2 to add amount, and
      only Mitra A confirms it.

    Expected:
    - Date disappears on the next read while versions and confirmations stay; version 1 stays effective while
      version 2 is pending, so amount is still hidden.
    """
    mitra = world.recipients.clients["A"]
    rani, _ = client_of(world, "F01")
    pitch = await met(world)
    proposed = (await propose_partnership(rani, pitch)).json()
    await confirm(mitra, proposed, ["name", "type", "scope", "date"], "m")

    narrowed = (await partnership_action(rani, proposed, "restrictions", "hide", field="date")).json()
    v2 = (await partnership_action(mitra, narrowed, "corrections", "more", version=1, values=VALUES)).json()
    pending = (await confirm(mitra, v2, ALL, "m2")).json()

    assert narrowed["effective"]["fields"] == ["name", "type", "scope"]
    assert [r["field"] for r in narrowed["restrictions"]] == ["date"]
    assert [v["status"] for v in narrowed["versions"]] == ["CONFIRMED"]
    assert [(v["number"], v["status"]) for v in pending["versions"]] == [(1, "CONFIRMED"), (2, "PENDING_COUNTERPARTY")]
    assert pending["effective"]["version"] == 1
    assert "amount" not in pending["effective"]["fields"]


async def test_contest_decline_and_retries(world: World) -> None:
    """
    Condition:
    - Mitra A confirms twice with one key, then again with another; Rani contests; a second relationship for the
      pitch is proposed; on another pitch a pending version is declined.

    Expected:
    - The retry replays; the second key is ``INVALID_TRANSITION``; contested is recorded; the duplicate is
      ``CONFLICT``.
    """
    mitra = world.recipients.clients["A"]
    rani, _ = client_of(world, "F01")
    pitch = await met(world)
    proposed = (await propose_partnership(rani, pitch)).json()

    first = await confirm(mitra, proposed, ["name"], "same")
    retry = await confirm(mitra, proposed, ["name"], "same")
    again = await confirm(mitra, proposed, ["name"], "other")
    contested = (await partnership_action(rani, proposed, "request-review", "review", reason="Tidak sesuai")).json()
    duplicate = await propose_partnership(rani, pitch, key="dup")

    assert retry.json() == first.json()
    assert again.json()["error"]["code"] == "INVALID_TRANSITION"
    assert contested["contested"] is True
    assert duplicate.json()["error"]["code"] == "CONFLICT"


async def test_declining_a_pending_version(world: World) -> None:
    """
    Condition:
    - Mitra A declines version 1.

    Expected:
    - ``DECLINED``, nothing public, and nobody is waiting.
    """
    mitra = world.recipients.clients["A"]
    rani, _ = client_of(world, "F01")
    pitch = await met(world)
    proposed = (await propose_partnership(rani, pitch)).json()

    declined = (await partnership_action(mitra, proposed, "decline", "no", version=1)).json()
    turn = (await rani.get(f"/api/v1/pitches/{pitch['id']}/next-action")).json()

    assert (declined["current"]["status"], declined["effective"]["fields"]) == ("DECLINED", [])
    assert turn["who"] is None


async def test_a_member_without_confirm_relationship_and_a_stranger(
    world: World, new_client: Callable[[], AsyncClient], sign_up: Callable[..., Awaitable[dict]]
) -> None:
    """
    Condition:
    - A Mitra A member holding only ``schedule`` confirms; a stranger reads and confirms (FR-003).

    Expected:
    - The member is ``FORBIDDEN``; the stranger gets ``NOT_FOUND`` for both.
    """
    mitra, party = world.recipients.clients["A"], world.recipients.parties["A"]
    rani, _ = client_of(world, "F01")
    pitch = await met(world)
    proposed = (await propose_partnership(rani, pitch)).json()
    me = (await mitra.get("/api/v1/me")).json()
    organization = next(item["organization_id"] for item in me["organizations"] if item["party_id"] == party)
    await mitra.post(
        f"/api/v1/organizations/{organization}/invitations",
        json={"acting_party_id": party, "email": "viewer@example.com", "capabilities": ["schedule"]},
        headers={"Idempotency-Key": "invite"},
    )
    mail = (await mitra.get("/api/v1/dev/mailbox", params={"email": "viewer@example.com"})).json()
    async with new_client() as viewer, new_client() as stranger:
        await sign_up(viewer, "viewer@example.com", name="Viewer")
        await viewer.post(f"/api/v1/invitations/{mail[0]['body'].rsplit('/', 1)[1]}/accept")
        await viewer.put("/api/v1/me/context", json={"party_id": party})
        viewer.headers["X-Acting-Party"] = party
        other = await sign_up(stranger, "stranger@example.com", name="Stranger")
        stranger.headers["X-Acting-Party"] = other["active_party_id"]

        member = await confirm(viewer, proposed, ["name"], "viewer")
        read = await stranger.get(f"/api/v1/partnerships/{proposed['id']}")
        foreign = await confirm(stranger, proposed, ["name"], "stranger")

    assert member.json()["error"]["code"] == "FORBIDDEN"
    assert (read.status_code, foreign.status_code) == (404, 404)


async def test_concurrent_proposals_share_one_completed_pitch(world: World) -> None:
    """Two authorized parties racing to propose get one version and one safe conflict."""
    from asyncio import gather  # noqa: PLC0415

    rani, _ = client_of(world, "F01")
    mitra = world.recipients.clients["A"]
    pitch = await met(world)
    options = await rani.get(f"/api/v1/pitches/{pitch['id']}/partnership-options")
    assert options.status_code == 200, options.text
    assert options.json()["types"] == ["PROJECT", "LICENSE"]
    one, two = await gather(propose_partnership(rani, pitch), propose_partnership(mitra, pitch))
    assert sorted((one.status_code, two.status_code)) == [201, 409]
