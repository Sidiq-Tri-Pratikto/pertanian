"""External handoffs through Postgres (spec 016, AC24, D3)."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.database import get_session_factory
from app.intake.repository.sqlalchemy.models import ExternalHandoffRecord
from app.platform.repository.sqlalchemy.models import AuditEventRecord
from tests.factories.recipients import PROFILES, LoadedRecipients, save_profile

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("clean_tables")]

URL = "https://example.org/formulir-demo"


def _party(client: AsyncClient) -> str:
    return client.headers["X-Acting-Party"]


async def _handoff(client: AsyncClient, party_id: str, key: str = "handoff", **extra: str) -> object:
    return await client.post(
        f"/api/v1/partners/{party_id}/handoffs",
        json={"acting_party_id": _party(client), **extra},
        headers={"Idempotency-Key": key},
    )


async def _stored() -> list[ExternalHandoffRecord]:
    async with get_session_factory()() as session:
        return list(await session.scalars(select(ExternalHandoffRecord)))


async def test_following_an_external_route_is_a_handoff_and_never_a_pitch(
    recipients: LoadedRecipients, stranger: AsyncClient
) -> None:
    """
    Condition:
    - An applicant follows Recipient E's external route (AC24).

    Expected:
    - One event is recorded with the party and the URL, the response says nothing was submitted, and it is audited as a
      handoff.
    """
    partner = recipients.parties["E"]

    response = await _handoff(stranger, partner)

    stored = await _stored()
    async with get_session_factory()() as session:
        actions = list(
            await session.scalars(select(AuditEventRecord.action).where(AuditEventRecord.subject_id == partner))
        )
    assert response.status_code == 201, response.text
    assert response.json()["external_url"] == URL
    assert response.json()["submitted"] is False
    assert response.json()["operation_id"]
    assert [(str(row.partner_party_id), str(row.actor_party_id), row.external_url) for row in stored] == [
        (partner, _party(stranger), URL)
    ]
    assert "external_handoff.recorded" in actions


async def test_a_retried_handoff_records_one_event(recipients: LoadedRecipients, stranger: AsyncClient) -> None:
    """
    Condition:
    - The same click is retried with its key.

    Expected:
    - The response replays and one event exists.
    """
    first = await _handoff(stranger, recipients.parties["E"])
    retry = await _handoff(stranger, recipients.parties["E"])

    assert retry.headers["Idempotent-Replayed"] == "true"
    assert retry.json() == first.json()
    assert len(await _stored()) == 1


@pytest.mark.parametrize("route", ["IN_APP", "NONE"])
async def test_only_an_external_route_can_be_followed(partner: AsyncClient, stranger: AsyncClient, route: str) -> None:
    """
    Condition:
    - A partner's route is in-app or none.

    Expected:
    - ``CONFLICT`` with a two-clause message, and no event.
    """
    party = _party(partner)
    await save_profile(partner, party, {**PROFILES["A"]["content"], "contact_route": route})

    response = await _handoff(stranger, party)

    error = response.json()["error"]
    assert (response.status_code, error["code"]) == (409, "CONFLICT")
    assert error["message"] == "Mitra ini tidak memakai jalur eksternal. Gunakan jalur yang tersedia pada profilnya."
    assert await _stored() == []


async def test_a_party_with_no_profile_is_not_found(partner: AsyncClient, stranger: AsyncClient) -> None:
    """
    Condition:
    - The party has no profile.

    Expected:
    - ``NOT_FOUND``.
    """
    response = await _handoff(stranger, _party(partner))

    assert (response.status_code, response.json()["error"]["code"]) == (404, "NOT_FOUND")


@pytest.mark.parametrize("url", ["javascript:alert(1)", "ftp://example.org/x", "bukan alamat"])
async def test_an_unsafe_external_url_is_refused_on_save(partner: AsyncClient, url: str) -> None:
    """
    Condition:
    - A partner saves an external route that is not ``http`` or ``https``.

    Expected:
    - ``VALIDATION_FAILED``, and no profile exists.
    """
    party = _party(partner)

    response = await save_profile(
        partner, party, {**PROFILES["A"]["content"], "contact_route": "EXTERNAL", "external_url": url}
    )

    assert (response.status_code, response.json()["error"]["code"]) == (422, "VALIDATION_FAILED")
    assert (await partner.get(f"/api/v1/partners/{party}")).status_code == 404


async def test_a_handoff_names_no_opportunity(recipients: LoadedRecipients, stranger: AsyncClient) -> None:
    """
    Condition:
    - A handoff body names an ``opportunity_id`` (D3).

    Expected:
    - ``VALIDATION_FAILED``, so a draft's existence can never be probed this way, and no event.
    """
    response = await _handoff(stranger, recipients.parties["E"], opportunity_id=recipients.opportunities["A1"])

    assert (response.status_code, response.json()["error"]["code"]) == (422, "VALIDATION_FAILED")
    assert await _stored() == []
