"""Partner profiles through Postgres (spec 016, US1, FR08)."""

import asyncio
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.database import get_session_factory
from app.platform.repository.sqlalchemy.models import AuditEventRecord, OutboxEventRecord
from tests.factories.recipients import INVESTOR_CHECK, PROFILES, save_profile

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("clean_tables")]

CONTENT = PROFILES["A"]["content"]


def _party(client: AsyncClient) -> str:
    return client.headers["X-Acting-Party"]


async def test_investor_b_needs_no_organization_and_money_stays_exact(partner: AsyncClient) -> None:
    """
    Condition:
    - Investor B saves a profile as a personal party, with equity checks of USD 50000–150000 (scenario 1).

    Expected:
    - It is saved with no organization, and the range reads back as exact strings with its subject, basis and period.
    """
    party = _party(partner)

    saved = await save_profile(partner, party, PROFILES["B"]["content"])

    read = (await partner.get(f"/api/v1/partners/{party}")).json()
    assert saved.status_code == 200, saved.text
    assert saved.json()["operation_id"]
    assert read["party_id"] == party
    assert read["party_name"] == "Mitra Uji"
    assert read["version"] == 1
    assert read["check_range"] == {
        "subject": "investorCheck",
        "basis": "per_investment",
        "min": "50000.0000",
        "max": "150000.0000",
        "currency": "USD",
        "period": "per investasi",
        "months": None,
        "unknown_reason": None,
    }
    assert read["availability"]["source"] == "OWNER_CONFIRMED"
    assert read["availability"]["source_label"] == "Dikonfirmasi pemilik profil"
    assert read["availability"]["label"] == "Pitching dibuka"


@pytest.mark.parametrize("invented", ["assets_under_management", "investment_capacity", "credentials"])
async def test_invented_facts_have_nowhere_to_go(partner: AsyncClient, invented: str) -> None:
    """
    Condition:
    - A save states assets under management, capacity or credentials, none of which a profile holds.

    Expected:
    - ``VALIDATION_FAILED``, and no profile exists.
    """
    party = _party(partner)

    response = await save_profile(partner, party, {**CONTENT, invented: "Rp1 triliun"})

    assert (response.status_code, response.json()["error"]["code"]) == (422, "VALIDATION_FAILED")
    assert (await partner.get(f"/api/v1/partners/{party}")).status_code == 404


async def test_unknown_range_stays_null_with_its_reason(partner: AsyncClient) -> None:
    """
    Condition:
    - A partner does not disclose its check range.

    Expected:
    - The amounts are ``null`` with the reason, never zero.
    """
    party = _party(partner)

    saved = await save_profile(
        partner, party, {**CONTENT, "check_range": {"subject": "investorCheck", "unknown_reason": "not_disclosed"}}
    )

    check = saved.json()["check_range"]
    assert (check["min"], check["max"], check["unknown_reason"]) == (None, None, "not_disclosed")


@pytest.mark.parametrize(
    ("change", "field"),
    [
        ({"min": "200000.0000"}, "max"),
        ({"min": "-1"}, "min"),
        ({"min": "banyak"}, "min"),
        ({"max": None}, "max"),
        ({"currency": None}, "currency"),
        ({"currency": "EUR"}, "currency"),
        ({"basis": None}, "basis"),
        ({"period": ""}, "period"),
        ({"basis": "total_period", "period": "6 bulan"}, "months"),
        ({"months": 6}, "months"),
        ({"min": None, "max": None}, "unknown_reason"),
    ],
)
async def test_a_range_that_does_not_say_what_it_means_is_refused(
    partner: AsyncClient, change: dict[str, Any], field: str
) -> None:
    """
    Condition:
    - A range is invalid, or lacks a basis, period, currency or months where they are needed.

    Expected:
    - ``VALIDATION_FAILED`` names the field, and no profile exists.
    """
    party = _party(partner)

    response = await save_profile(partner, party, {**CONTENT, "check_range": {**INVESTOR_CHECK, **change}})

    error = response.json()["error"]
    assert (response.status_code, error["code"]) == (422, "VALIDATION_FAILED")
    assert ["body", "check_range", field] in [item["loc"] for item in error["details"]]
    assert (await partner.get(f"/api/v1/partners/{party}")).status_code == 404


@pytest.mark.parametrize("claim", [{"source": "SOURCE_REPORTED"}, {"intake_status": "UNCONFIRMED"}])
async def test_an_owner_cannot_claim_a_source_or_an_unconfirmed_state(partner: AsyncClient, claim: dict) -> None:
    """
    Condition:
    - An owner's save sets the source, or marks its own intake unconfirmed (D6).

    Expected:
    - ``VALIDATION_FAILED``; an owner's save is always owner-confirmed.
    """
    response = await save_profile(partner, _party(partner), CONTENT, **claim)

    assert (response.status_code, response.json()["error"]["code"]) == (422, "VALIDATION_FAILED")


async def test_external_route_needs_a_url(partner: AsyncClient) -> None:
    """
    Condition:
    - A partner chooses an external route with no address.

    Expected:
    - ``VALIDATION_FAILED`` names ``external_url``.
    """
    response = await save_profile(partner, _party(partner), {**CONTENT, "contact_route": "EXTERNAL"})

    error = response.json()["error"]
    assert (response.status_code, error["code"]) == (422, "VALIDATION_FAILED")
    assert ["body", "external_url"] in [item["loc"] for item in error["details"]]


async def test_a_strangers_save_reveals_nothing(partner: AsyncClient, stranger: AsyncClient) -> None:
    """
    Condition:
    - An unrelated party saves another party's profile, acting as itself.

    Expected:
    - ``NOT_FOUND``, and the profile is unchanged.
    """
    party = _party(partner)
    await save_profile(partner, party, CONTENT)

    response = await stranger.put(
        f"/api/v1/partners/{party}",
        json={"acting_party_id": _party(stranger), "expected_version": 1, **CONTENT, "thesis": "Bukan milik saya"},
        headers={"Idempotency-Key": "steal"},
    )

    assert (response.status_code, response.json()["error"]["code"]) == (404, "NOT_FOUND")
    assert (await partner.get(f"/api/v1/partners/{party}")).json()["thesis"] == CONTENT["thesis"]


async def test_a_member_without_edit_capability_cannot_save(limited_member: tuple[AsyncClient, str]) -> None:
    """
    Condition:
    - A member with only ``schedule`` saves the organization's profile.

    Expected:
    - ``FORBIDDEN``, and no profile exists.
    """
    member, party = limited_member

    response = await save_profile(member, party, CONTENT)

    assert (response.status_code, response.json()["error"]["code"]) == (403, "FORBIDDEN")
    assert (await member.get(f"/api/v1/partners/{party}")).status_code == 404


async def test_others_read_a_saved_profile_and_nobody_reads_a_missing_one(
    partner: AsyncClient, stranger: AsyncClient
) -> None:
    """
    Condition:
    - Another party reads a party with no profile, then the same party once it has saved one (D4).

    Expected:
    - ``NOT_FOUND`` first, then the profile.
    """
    party = _party(partner)

    missing = await stranger.get(f"/api/v1/partners/{party}")
    await save_profile(partner, party, CONTENT)
    found = await stranger.get(f"/api/v1/partners/{party}")

    assert missing.status_code == 404
    assert found.status_code == 200
    assert found.json()["thesis"] == CONTENT["thesis"]


async def test_first_save_creates_version_one_and_later_saves_need_the_version(partner: AsyncClient) -> None:
    """
    Condition:
    - A first save with ``expected_version`` null, then saves with null, the current and an old version (D17).

    Expected:
    - Version 1 is created; null and an old version are ``STALE_VERSION`` and overwrite nothing; the current one saves.
    """
    party = _party(partner)

    first = await save_profile(partner, party, CONTENT, key="first")
    with_null = await save_profile(partner, party, {**CONTENT, "thesis": "Null"}, key="null")
    current = await save_profile(partner, party, {**CONTENT, "thesis": "Baru"}, version=1, key="current")
    old = await save_profile(partner, party, {**CONTENT, "thesis": "Lama"}, version=1, key="old")

    read = (await partner.get(f"/api/v1/partners/{party}")).json()
    assert first.json()["version"] == 1
    assert (with_null.status_code, with_null.json()["error"]["code"]) == (409, "STALE_VERSION")
    assert with_null.json()["error"]["current_version"] == 1
    assert current.json()["version"] == 2
    assert (old.status_code, old.json()["error"]["code"]) == (409, "STALE_VERSION")
    assert old.json()["error"]["current_version"] == 2
    assert (read["thesis"], read["version"]) == ("Baru", 2)


async def test_a_version_before_any_profile_exists_is_stale(partner: AsyncClient) -> None:
    """
    Condition:
    - A save names a version, but the party has no profile (D17).

    Expected:
    - ``STALE_VERSION``, and no profile exists.
    """
    party = _party(partner)

    response = await save_profile(partner, party, CONTENT, version=3)

    assert (response.status_code, response.json()["error"]["code"]) == (409, "STALE_VERSION")
    assert (await partner.get(f"/api/v1/partners/{party}")).status_code == 404


async def test_the_loser_of_two_first_saves_overwrites_nothing(partner: AsyncClient) -> None:
    """
    Condition:
    - Two tabs send a first save at the same time, with different keys and content (D17).

    Expected:
    - One saves, the other is ``STALE_VERSION``, and the stored thesis is the winner's.
    """
    party = _party(partner)

    responses = await asyncio.gather(
        save_profile(partner, party, {**CONTENT, "thesis": "Tab satu"}, key="tab-1"),
        save_profile(partner, party, {**CONTENT, "thesis": "Tab dua"}, key="tab-2"),
    )

    winner = next(response for response in responses if response.status_code == 200)
    loser = next(response for response in responses if response.status_code != 200)
    read = (await partner.get(f"/api/v1/partners/{party}")).json()
    assert (loser.status_code, loser.json()["error"]["code"]) == (409, "STALE_VERSION")
    assert (read["thesis"], read["version"]) == (winner.json()["thesis"], 1)


async def test_a_save_from_a_stale_context_is_refused(partner: AsyncClient) -> None:
    """
    Condition:
    - A save claims to act as a party other than the session's.

    Expected:
    - ``STALE_CONTEXT``.
    """
    party = _party(partner)

    response = await partner.put(
        f"/api/v1/partners/{party}",
        json={"acting_party_id": "00000000-0000-4000-8000-000000000009", "expected_version": None, **CONTENT},
        headers={"Idempotency-Key": "context"},
    )

    assert (response.status_code, response.json()["error"]["code"]) == (409, "STALE_CONTEXT")


async def test_retried_save_replays_and_another_body_conflicts(partner: AsyncClient) -> None:
    """
    Condition:
    - A save is retried with its key, then the key is reused with another body; a save has no key at all.

    Expected:
    - The retry replays; the reuse is ``IDEMPOTENCY_CONFLICT``; no key is ``BAD_REQUEST``.
    """
    party = _party(partner)

    first = await save_profile(partner, party, CONTENT, key="same")
    retry = await save_profile(partner, party, CONTENT, key="same")
    other = await save_profile(partner, party, {**CONTENT, "thesis": "Lain"}, key="same")
    no_key = await partner.put(
        f"/api/v1/partners/{party}", json={"acting_party_id": party, "expected_version": 1, **CONTENT}
    )

    assert retry.headers["Idempotent-Replayed"] == "true"
    assert retry.json() == first.json()
    assert (other.status_code, other.json()["error"]["code"]) == (409, "IDEMPOTENCY_CONFLICT")
    assert (no_key.status_code, no_key.json()["error"]["code"]) == (400, "BAD_REQUEST")


async def test_a_save_audits_and_publishes_with_the_change(partner: AsyncClient) -> None:
    """
    Condition:
    - A profile is saved twice.

    Expected:
    - Two audit events and two ``partner.changed`` events, for 018's projection.
    """
    party = _party(partner)

    await save_profile(partner, party, CONTENT, key="one")
    await save_profile(partner, party, CONTENT, version=1, key="two")

    async with get_session_factory()() as session:
        topics = list(
            await session.scalars(select(OutboxEventRecord.topic).where(OutboxEventRecord.topic == "partner.changed"))
        )
        actions = list(
            await session.scalars(select(AuditEventRecord.action).where(AuditEventRecord.subject_id == party))
        )
    assert topics == ["partner.changed", "partner.changed"]
    assert actions == ["partner.saved", "partner.saved"]
