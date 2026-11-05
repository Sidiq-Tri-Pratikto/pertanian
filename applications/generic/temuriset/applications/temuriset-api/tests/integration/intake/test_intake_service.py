"""The service paths other specs call, and the race and missing-record paths HTTP alone does not reach (spec 016)."""

from datetime import timedelta
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient

from app.core import clock
from app.core.database import get_session_factory
from app.core.errors.base import ConflictError, NotFoundError
from app.intake.model.schema import PartnerProfileContent
from app.intake.repository.sqlalchemy.repository import SqlAlchemyIntakeRepository
from app.intake.service.service import IntakeService
from tests.factories.recipients import OPPORTUNITIES, PROFILES, LoadedRecipients, move_opportunity, save_profile

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("clean_tables")]

CONTENT = PROFILES["A"]["content"]


def _party(client: AsyncClient) -> str:
    return client.headers["X-Acting-Party"]


async def test_target_availability_is_the_same_answer_for_other_specs(recipients: LoadedRecipients) -> None:
    """
    Condition:
    - Matching and submission ask the service directly, for an active target and for one just closed (D8).

    Expected:
    - The answer matches what the API shows, and a missing target is ``NotFoundError``.
    """
    client, party = recipients.clients["A"], recipients.parties["A"]
    a1 = recipients.opportunities["A1"]

    async with get_session_factory()() as session:
        open_answer = await IntakeService(session).target_availability(UUID(a1))
    await move_opportunity(client, party, a1, "close", 2)
    async with get_session_factory()() as session:
        closed_answer = await IntakeService(session).target_availability(UUID(a1))
        with pytest.raises(NotFoundError):
            await IntakeService(session).target_availability(uuid4())

    assert (open_answer.available, open_answer.reason) == (True, None)
    assert (closed_answer.available, closed_answer.reason) == (False, "TARGET_NOT_ACTIVE")


async def test_a_directory_entry_never_replaces_a_profile(recipients: LoadedRecipients) -> None:
    """
    Condition:
    - A directory entry is recorded for a party that already has a profile (D6).

    Expected:
    - ``ConflictError``, and the owner's profile stays owner-confirmed.
    """
    client, party = recipients.clients["A"], recipients.parties["A"]

    async with get_session_factory()() as session:
        with pytest.raises(ConflictError):
            await IntakeService(session).record_directory_profile(
                UUID(party), PartnerProfileContent.model_validate(PROFILES["E"]["content"])
            )

    assert (await client.get(f"/api/v1/partners/{party}")).json()["availability"]["source"] == "OWNER_CONFIRMED"


async def test_the_loser_of_a_first_save_race_is_told_the_stored_version(
    partner: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    Condition:
    - A first save read no profile, and another request committed one before it inserted (D17). HTTP tests cannot pick
      this interleaving, so the read before the insert is made to miss.

    Expected:
    - ``STALE_VERSION`` with the stored version, and the winner's content stays.
    """
    party = _party(partner)
    await save_profile(partner, party, CONTENT, key="winner")
    real_profile = SqlAlchemyIntakeRepository.profile

    async def missed_locked_read(self: SqlAlchemyIntakeRepository, party_id: UUID, *, lock: bool = False) -> object:
        return None if lock else await real_profile(self, party_id)

    monkeypatch.setattr(SqlAlchemyIntakeRepository, "profile", missed_locked_read)

    response = await save_profile(partner, party, {**CONTENT, "thesis": "Kalah"}, key="loser")

    monkeypatch.undo()
    read = (await partner.get(f"/api/v1/partners/{party}")).json()
    assert (response.status_code, response.json()["error"]["code"]) == (409, "STALE_VERSION")
    assert response.json()["error"]["current_version"] == 1
    assert read["thesis"] == CONTENT["thesis"]


async def test_intake_dates_must_be_in_order(partner: AsyncClient) -> None:
    """
    Condition:
    - An intake ends before it starts.

    Expected:
    - ``VALIDATION_FAILED`` names ``intake_until``.
    """
    today = clock.now().date().isoformat()
    earlier = (clock.now().date() - timedelta(days=1)).isoformat()

    response = await save_profile(partner, _party(partner), {**CONTENT, "intake_from": today, "intake_until": earlier})

    assert ["body", "intake_until"] in [item["loc"] for item in response.json()["error"]["details"]]


async def test_an_opportunity_that_does_not_exist_is_not_found(partner: AsyncClient) -> None:
    """
    Condition:
    - A read, a version read and a status change name an unknown opportunity.

    Expected:
    - ``NOT_FOUND``, the same as another party's draft.
    """
    party, unknown = _party(partner), uuid4()

    read = await partner.get(f"/api/v1/opportunities/{unknown}")
    version = await partner.get(f"/api/v1/opportunities/{unknown}/versions/1")
    moved = await move_opportunity(partner, party, str(unknown), "pause", 1)

    assert [response.status_code for response in (read, version, moved)] == [404, 404, 404]


async def test_a_version_number_that_does_not_exist_is_not_found(recipients: LoadedRecipients) -> None:
    """
    Condition:
    - The owner reads a version number that was never saved.

    Expected:
    - ``NOT_FOUND``.
    """
    client = recipients.clients["A"]

    response = await client.get(f"/api/v1/opportunities/{recipients.opportunities['A1']}/versions/9")

    assert response.status_code == 404


async def test_a_list_honors_its_limit(recipients: LoadedRecipients, stranger: AsyncClient) -> None:
    """
    Condition:
    - Another party lists Mitra A's three opportunities with a limit, and asks for more than the maximum.

    Expected:
    - The limit is honored, and a limit above the maximum is ``VALIDATION_FAILED``.
    """
    party = recipients.parties["A"]
    count = sum(item["partner"] == "A" for item in OPPORTUNITIES.values())

    everything = await stranger.get("/api/v1/opportunities", params={"partner_party_id": party})
    limited = await stranger.get("/api/v1/opportunities", params={"partner_party_id": party, "limit": 2})
    too_many = await stranger.get("/api/v1/opportunities", params={"partner_party_id": party, "limit": 101})

    assert len(everything.json()) == count
    assert len(limited.json()) == 2
    assert too_many.status_code == 422
