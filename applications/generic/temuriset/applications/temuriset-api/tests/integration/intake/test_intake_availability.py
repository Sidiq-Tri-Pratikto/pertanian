"""What is available now, kept apart from what a partner generally does (spec 016, AC22, AC23, FR-001, FR-004)."""

from copy import deepcopy
from datetime import timedelta
from typing import Any

import pytest
from httpx import AsyncClient

from app.core import clock
from tests.factories.recipients import (
    OPPORTUNITIES,
    PROFILES,
    LoadedRecipients,
    create_opportunity,
    move_opportunity,
    save_profile,
)

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("clean_tables")]

CONTENT = deepcopy(OPPORTUNITIES["A1"]["content"])
PROFILE = PROFILES["A"]["content"]


def _party(client: AsyncClient) -> str:
    return client.headers["X-Acting-Party"]


def _days(offset: int) -> str:
    return (clock.now().date() + timedelta(days=offset)).isoformat()


async def _active(client: AsyncClient, kind: str, key: str = "target") -> dict[str, Any]:
    created = await create_opportunity(client, _party(client), {**CONTENT, "kind": kind}, key=f"create-{key}")
    assert created.status_code == 201, created.text
    moved = await move_opportunity(client, _party(client), created.json()["id"], "activate", 1)
    assert moved.status_code == 200, moved.text
    return moved.json()


async def test_a_directory_entry_claims_no_active_intake(recipients: LoadedRecipients, stranger: AsyncClient) -> None:
    """
    Condition:
    - A source-reported directory profile with unconfirmed intake is read (AC22).

    Expected:
    - It is labelled "Dilaporkan sumber" and "Ketersediaan belum dikonfirmasi", and what the source did not say is
      empty rather than invented.
    """
    read = (await stranger.get(f"/api/v1/partners/{recipients.parties['E']}")).json()

    assert read["availability"]["source"] == "SOURCE_REPORTED"
    assert read["availability"]["source_label"] == "Dilaporkan sumber"
    assert read["availability"]["intake_status"] == "UNCONFIRMED"
    assert read["availability"]["label"] == "Ketersediaan belum dikonfirmasi"
    assert read["stages"] == []
    assert read["regions"] == []
    assert read["check_range"] is None


async def test_closing_intake_stops_general_pitches_and_leaves_specific_targets(recipients: LoadedRecipients) -> None:
    """
    Condition:
    - Mitra A has an active general intake and A1, then closes direct intake (AC23).

    Expected:
    - The general target becomes unavailable; A1 stays available and is evaluated on its own.
    """
    mitra_a, party = recipients.clients["A"], recipients.parties["A"]
    general = await _active(mitra_a, "GENERAL_INTAKE")
    a1 = recipients.opportunities["A1"]
    before = (await mitra_a.get(f"/api/v1/opportunities/{general['id']}")).json()

    closed = await save_profile(mitra_a, party, PROFILE, version=1, key="close-intake", intake_status="CLOSED")

    after_general = (await mitra_a.get(f"/api/v1/opportunities/{general['id']}")).json()
    after_a1 = (await mitra_a.get(f"/api/v1/opportunities/{a1}")).json()
    assert before["target_availability"] == {"available": True, "reason": None}
    assert closed.status_code == 200, closed.text
    assert closed.json()["availability"]["label"] == "Penerimaan ditutup"
    assert after_general["target_availability"] == {"available": False, "reason": "DIRECT_INTAKE_CLOSED"}
    assert after_a1["target_availability"] == {"available": True, "reason": None}


@pytest.mark.parametrize(
    ("kind", "profile", "paused", "expected"),
    [
        ("SPECIFIC", {}, False, (True, None)),
        ("GENERAL_INTAKE", {}, False, (True, None)),
        ("SPECIFIC", {}, True, (False, "TARGET_NOT_ACTIVE")),
        ("GENERAL_INTAKE", {}, True, (False, "TARGET_NOT_ACTIVE")),
        (
            "SPECIFIC",
            {"contact_route": "EXTERNAL", "external_url": "https://example.org/x"},
            False,
            (False, "EXTERNAL_ROUTE"),
        ),
        (
            "GENERAL_INTAKE",
            {"contact_route": "EXTERNAL", "external_url": "https://example.org/x"},
            False,
            (False, "EXTERNAL_ROUTE"),
        ),
        ("SPECIFIC", {"contact_route": "NONE"}, False, (False, "NO_NEW_APPROACHES")),
        ("GENERAL_INTAKE", {"contact_route": "NONE"}, False, (False, "NO_NEW_APPROACHES")),
        ("SPECIFIC", {"intake_status": "CLOSED"}, False, (True, None)),
        ("GENERAL_INTAKE", {"intake_status": "CLOSED"}, False, (False, "DIRECT_INTAKE_CLOSED")),
        ("SPECIFIC", {"intake_until": -1}, False, (True, None)),
        ("GENERAL_INTAKE", {"intake_until": -1}, False, (False, "INTAKE_UNCONFIRMED")),
        ("GENERAL_INTAKE", {"intake_from": 1}, False, (False, "INTAKE_UNCONFIRMED")),
        ("GENERAL_INTAKE", {"intake_from": -1, "intake_until": 1}, False, (True, None)),
    ],
)
async def test_every_row_of_the_availability_table_over_http(
    partner: AsyncClient,
    stranger: AsyncClient,
    kind: str,
    profile: dict[str, Any],
    paused: bool,
    expected: tuple[bool, str | None],
) -> None:
    """
    Condition:
    - A specific or general target is read by another party under each contact route, intake state and date (D16).

    Expected:
    - ``target_availability`` matches the table, with its reason, in the read and in the partner's list.
    """
    party = _party(partner)
    extra = {
        name: _days(value) if name in ("intake_from", "intake_until") else value for name, value in profile.items()
    }
    status = extra.pop("intake_status", "OPEN")
    saved = await save_profile(partner, party, {**PROFILE, **extra}, intake_status=status)
    assert saved.status_code == 200, saved.text
    target = await _active(partner, kind)
    if paused:
        await move_opportunity(partner, party, target["id"], "pause", target["version"])

    read = (await stranger.get(f"/api/v1/opportunities/{target['id']}")).json()
    listed = (await stranger.get("/api/v1/opportunities", params={"partner_party_id": party})).json()

    wanted = {"available": expected[0], "reason": expected[1]}
    assert read["target_availability"] == wanted
    assert [item["target_availability"] for item in listed] == [wanted]


async def test_a_lapsed_intake_date_is_not_shown_as_open(partner: AsyncClient) -> None:
    """
    Condition:
    - A partner's intake is stored as open, but ``intake_until`` has passed.

    Expected:
    - The stored state stays for the owner's form, and the current state and label say it is unconfirmed.
    """
    party = _party(partner)

    saved = await save_profile(partner, party, {**PROFILE, "intake_until": _days(-1)})

    availability = saved.json()["availability"]
    assert availability["intake_status"] == "OPEN"
    assert availability["current_intake_status"] == "UNCONFIRMED"
    assert availability["label"] == "Ketersediaan belum dikonfirmasi"


async def test_a_general_target_says_so_and_a_specific_one_does_not(partner: AsyncClient) -> None:
    """
    Condition:
    - A partner has a specific opportunity and a general intake (FR-004).

    Expected:
    - Only the general one is labelled "berdasarkan profil umum mitra".
    """
    await save_profile(partner, _party(partner), PROFILE)

    specific = await _active(partner, "SPECIFIC", "specific")
    general = await _active(partner, "GENERAL_INTAKE", "general")

    assert specific["general_intake_label"] is None
    assert general["general_intake_label"] == "berdasarkan profil umum mitra"


async def test_thesis_and_availability_are_separate(partner: AsyncClient) -> None:
    """
    Condition:
    - A partner with a thesis closes its intake (FR-001).

    Expected:
    - The thesis still reads as before, and availability says intake is closed.
    """
    saved = await save_profile(partner, _party(partner), PROFILE, intake_status="CLOSED")

    assert saved.json()["thesis"] == PROFILE["thesis"]
    assert saved.json()["availability"]["current_intake_status"] == "CLOSED"
    assert "thesis" not in saved.json()["availability"]
