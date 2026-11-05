"""Opportunities and their versions through Postgres (spec 016, US1, FR-002, AC25)."""

from copy import deepcopy
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.database import get_session_factory
from app.platform.repository.sqlalchemy.models import AuditEventRecord, OutboxEventRecord
from tests.factories.recipients import (
    OPPORTUNITIES,
    PROFILES,
    LoadedRecipients,
    create_opportunity,
    move_opportunity,
    save_opportunity,
    save_profile,
)

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("clean_tables")]

CONTENT = deepcopy(OPPORTUNITIES["A1"]["content"])


def _party(client: AsyncClient) -> str:
    return client.headers["X-Acting-Party"]


@pytest.fixture
async def active(partner: AsyncClient) -> dict[str, Any]:
    """An active opportunity at version 1 of a partner with a profile."""
    party = _party(partner)
    await save_profile(partner, party, PROFILES["A"]["content"])
    created = (await create_opportunity(partner, party, CONTENT)).json()
    return (await move_opportunity(partner, party, created["id"], "activate", created["version"])).json()


async def test_each_opportunity_keeps_its_own_version_intake_and_requirements(recipients: LoadedRecipients) -> None:
    """
    Condition:
    - Mitra A publishes A1, A2 and A3, then A1 alone changes and pauses (AC25).

    Expected:
    - Each has its own version, status and requirements, and nothing merges across them.
    """
    client, party = recipients.clients["A"], recipients.parties["A"]
    a1, a2, a3 = (recipients.opportunities[key] for key in ("A1", "A2", "A3"))
    before = (await client.get(f"/api/v1/opportunities/{a1}")).json()

    saved = (await save_opportunity(client, party, a1, {**CONTENT, "title": "A1 baru"}, before["version"])).json()
    await move_opportunity(client, party, a1, "pause", saved["version"])

    read = {key: (await client.get(f"/api/v1/opportunities/{key}")).json() for key in (a1, a2, a3)}
    assert (read[a1]["status"], read[a1]["number"]) == ("PAUSED", 2)
    assert (read[a2]["status"], read[a2]["number"]) == ("ACTIVE", 1)
    assert (read[a3]["status"], read[a3]["number"]) == ("ACTIVE", 1)
    assert [row["label"] for row in read[a1]["requirements"]] == [
        "Tahap inovasi",
        "Berkas uji fungsi",
        "Kisaran biaya pilot",
        "Sertifikat komersialisasi",
    ]
    assert [row["label"] for row in read[a2]["requirements"]] == ["Tahap inovasi", "Wewenang atas inovasi"]
    assert [row["label"] for row in read[a3]["requirements"]] == ["Tahap inovasi"]
    assert read[a1]["financial"]["min"] == "15000.0000"
    assert read[a2]["financial"]["min"] is None
    assert read[a2]["financial"]["noncash"] == "Tanpa dana tunai: fasilitas uji"


async def test_all_of_fr_002_reads_back(active: dict[str, Any]) -> None:
    """
    Condition:
    - A1 is saved and activated.

    Expected:
    - Outcome, scope, support, stages, forms, timing, financial basis and requirements all read back, and money is
      exact.
    """
    for field in ("title", "outcome", "included", "excluded", "support", "timing"):
        assert active[field] == CONTENT[field]
    assert active["accepted_stages"] == CONTENT["accepted_stages"]
    assert active["relationship_forms"] == CONTENT["relationship_forms"]
    assert active["sectors"] == CONTENT["sectors"]
    assert active["keywords"] == CONTENT["keywords"]
    assert active["financial"] == {
        "subject": "partner",
        "basis": "total_period",
        "min": "15000.0000",
        "max": "40000.0000",
        "currency": "USD",
        "period": "6 bulan",
        "months": 6,
        "scope": "biaya pilot enam bulan",
        "noncash": "",
        "terms": "",
        "unknown_reason": None,
    }
    assert active["operation_id"]


async def test_saving_an_active_opportunity_makes_the_next_version_current_at_once(
    partner: AsyncClient, active: dict[str, Any], stranger: AsyncClient
) -> None:
    """
    Condition:
    - An active opportunity is saved (D1).

    Expected:
    - Version 2 is current at once with the status still ``ACTIVE``; the owner still reads version 1 as it stood, and
      others read only the current one.
    """
    party = _party(partner)

    saved = await save_opportunity(partner, party, active["id"], {**CONTENT, "title": "Baru"}, active["version"])

    owner_old = await partner.get(f"/api/v1/opportunities/{active['id']}/versions/1")
    owner_new = await partner.get(f"/api/v1/opportunities/{active['id']}/versions/2")
    other_old = await stranger.get(f"/api/v1/opportunities/{active['id']}/versions/1")
    other_new = await stranger.get(f"/api/v1/opportunities/{active['id']}/versions/2")
    other_read = await stranger.get(f"/api/v1/opportunities/{active['id']}")
    assert saved.status_code == 200, saved.text
    assert (saved.json()["number"], saved.json()["status"], saved.json()["title"]) == (2, "ACTIVE", "Baru")
    assert saved.json()["version"] == active["version"] + 1
    assert (owner_old.json()["number"], owner_old.json()["title"]) == (1, CONTENT["title"])
    assert owner_old.json()["requirements"][0]["version"] == 1
    assert owner_new.json()["requirements"][0]["version"] == 2
    assert other_old.status_code == 404
    assert other_new.status_code == 200
    assert (other_read.json()["number"], other_read.json()["title"]) == (2, "Baru")


async def test_saving_a_paused_opportunity_keeps_it_paused(partner: AsyncClient, active: dict[str, Any]) -> None:
    """
    Condition:
    - A paused opportunity is saved (D1).

    Expected:
    - The next version is current and the status is still ``PAUSED``.
    """
    party = _party(partner)
    paused = (await move_opportunity(partner, party, active["id"], "pause", active["version"])).json()

    saved = await save_opportunity(partner, party, active["id"], CONTENT, paused["version"])

    assert (saved.json()["number"], saved.json()["status"]) == (2, "PAUSED")


async def test_editing_a_draft_keeps_version_one_and_replaces_its_requirements(partner: AsyncClient) -> None:
    """
    Condition:
    - A draft is started empty and then saved with content twice.

    Expected:
    - It stays version 1, with the latest requirements only.
    """
    party = _party(partner)
    created = (await create_opportunity(partner, party, {"title": "Draf"})).json()

    first = (await save_opportunity(partner, party, created["id"], CONTENT, created["version"], key="one")).json()
    second = (
        await save_opportunity(
            partner,
            party,
            created["id"],
            {**CONTENT, "requirements": CONTENT["requirements"][:1]},
            first["version"],
            key="two",
        )
    ).json()

    assert created["status"] == "DRAFT"
    assert (first["number"], second["number"]) == (1, 1)
    assert [row["label"] for row in second["requirements"]] == ["Tahap inovasi"]


async def test_others_never_reach_a_draft(partner: AsyncClient, stranger: AsyncClient) -> None:
    """
    Condition:
    - A partner has a draft and an active opportunity, and another party reads and lists them.

    Expected:
    - The draft is ``NOT_FOUND`` by id and by version, and the partner's list shows only the active one. With no filter
      the other party's own list is empty.
    """
    party = _party(partner)
    await save_profile(partner, party, PROFILES["A"]["content"])
    draft = (await create_opportunity(partner, party, {"title": "Rahasia"}, key="draft")).json()
    live = (await create_opportunity(partner, party, CONTENT, key="live")).json()
    await move_opportunity(partner, party, live["id"], "activate", live["version"])

    by_id = await stranger.get(f"/api/v1/opportunities/{draft['id']}")
    by_version = await stranger.get(f"/api/v1/opportunities/{draft['id']}/versions/1")
    listed = (await stranger.get("/api/v1/opportunities", params={"partner_party_id": party})).json()
    own = (await stranger.get("/api/v1/opportunities")).json()
    mine = (await partner.get("/api/v1/opportunities")).json()

    assert by_id.status_code == 404
    assert by_version.status_code == 404
    assert [item["id"] for item in listed] == [live["id"]]
    assert "Rahasia" not in str(listed)
    assert own == []
    assert {item["id"] for item in mine} == {draft["id"], live["id"]}


async def test_a_strangers_changes_reveal_nothing(
    partner: AsyncClient, active: dict[str, Any], stranger: AsyncClient
) -> None:
    """
    Condition:
    - Another party saves and closes a visible active opportunity, acting as itself.

    Expected:
    - Both are ``NOT_FOUND``, and nothing changes.
    """
    other = _party(stranger)

    saved = await save_opportunity(stranger, other, active["id"], CONTENT, active["version"])
    closed = await move_opportunity(stranger, other, active["id"], "close", active["version"])

    read = (await partner.get(f"/api/v1/opportunities/{active['id']}")).json()
    assert saved.status_code == 404
    assert closed.status_code == 404
    assert (read["status"], read["version"]) == ("ACTIVE", active["version"])


async def test_a_member_without_edit_capability_cannot_start_one(limited_member: tuple[AsyncClient, str]) -> None:
    """
    Condition:
    - A member with only ``schedule`` starts an opportunity for the organization.

    Expected:
    - ``FORBIDDEN``.
    """
    member, party = limited_member

    response = await create_opportunity(member, party, CONTENT)

    assert (response.status_code, response.json()["error"]["code"]) == (403, "FORBIDDEN")


@pytest.mark.parametrize(
    ("change", "field"),
    [
        ({"basis": None}, "basis"),
        ({"period": ""}, "period"),
        ({"months": None}, "months"),
        ({"basis": "monthly"}, "months"),
        ({"min": "50000.0000"}, "max"),
        ({"min": "-1"}, "min"),
        ({"currency": None}, "currency"),
    ],
)
async def test_a_cash_range_that_does_not_say_what_it_means_is_refused(
    partner: AsyncClient, change: dict[str, Any], field: str
) -> None:
    """
    Condition:
    - A cash range lacks a basis, period or months where needed, or is not a valid range (D13).

    Expected:
    - ``VALIDATION_FAILED`` names the field, and nothing is stored.
    """
    party = _party(partner)
    financial = {**CONTENT["financial"], **change}

    response = await create_opportunity(partner, party, {**CONTENT, "financial": financial})

    error = response.json()["error"]
    assert (response.status_code, error["code"]) == (422, "VALIDATION_FAILED")
    assert ["body", "financial", field] in [item["loc"] for item in error["details"]]
    assert (await partner.get("/api/v1/opportunities")).json() == []


async def test_a_financial_basis_with_nothing_stated_is_refused(partner: AsyncClient) -> None:
    """
    Condition:
    - ``financial`` states no range, no non-cash support, no terms and no reason.

    Expected:
    - ``VALIDATION_FAILED`` asks for the reason; unknown is explained, never implied.
    """
    response = await create_opportunity(partner, _party(partner), {**CONTENT, "financial": {"subject": "partner"}})

    assert ["body", "financial", "unknown_reason"] in [item["loc"] for item in response.json()["error"]["details"]]


async def test_stale_save_keeps_the_stored_content(partner: AsyncClient, active: dict[str, Any]) -> None:
    """
    Condition:
    - Two saves are sent against the same version.

    Expected:
    - The second is ``STALE_VERSION`` with the current version, and only the first took effect.
    """
    party = _party(partner)
    await save_opportunity(partner, party, active["id"], {**CONTENT, "title": "Tab satu"}, active["version"], key="a")

    stale = await save_opportunity(
        partner, party, active["id"], {**CONTENT, "title": "Tab dua"}, active["version"], key="b"
    )

    read = (await partner.get(f"/api/v1/opportunities/{active['id']}")).json()
    assert (stale.status_code, stale.json()["error"]["code"]) == (409, "STALE_VERSION")
    assert stale.json()["error"]["current_version"] == read["version"]
    assert read["title"] == "Tab satu"


async def test_retried_create_and_save_replay_and_another_body_conflicts(partner: AsyncClient) -> None:
    """
    Condition:
    - A create and a save are each retried with their key, then reused with another body.

    Expected:
    - One opportunity and one change; retries replay; the reuse is ``IDEMPOTENCY_CONFLICT``.
    """
    party = _party(partner)

    created = await create_opportunity(partner, party, CONTENT, key="c")
    created_again = await create_opportunity(partner, party, CONTENT, key="c")
    created_other = await create_opportunity(partner, party, {**CONTENT, "title": "Lain"}, key="c")
    opportunity = created.json()
    saved = await save_opportunity(partner, party, opportunity["id"], CONTENT, 1, key="s")
    saved_again = await save_opportunity(partner, party, opportunity["id"], CONTENT, 1, key="s")
    saved_other = await save_opportunity(partner, party, opportunity["id"], {**CONTENT, "title": "Lain"}, 1, key="s")

    assert created_again.headers["Idempotent-Replayed"] == "true"
    assert created_again.json() == created.json()
    assert created_other.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"
    assert saved_again.headers["Idempotent-Replayed"] == "true"
    assert saved_again.json() == saved.json()
    assert saved_other.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"
    assert len((await partner.get("/api/v1/opportunities")).json()) == 1


async def test_one_open_general_intake_per_partner(partner: AsyncClient) -> None:
    """
    Condition:
    - A partner starts a second general intake while one is open, then closes the first (D7).

    Expected:
    - The second is ``CONFLICT``; after closing, a new one can start.
    """
    party = _party(partner)
    first = (await create_opportunity(partner, party, {"kind": "GENERAL_INTAKE"}, key="one")).json()

    second = await create_opportunity(partner, party, {"kind": "GENERAL_INTAKE"}, key="two")
    await move_opportunity(partner, party, first["id"], "close", first["version"])
    third = await create_opportunity(partner, party, {"kind": "GENERAL_INTAKE"}, key="three")

    assert (second.status_code, second.json()["error"]["code"]) == (409, "CONFLICT")
    assert third.status_code == 201


async def test_changes_audit_and_publish_with_the_change(partner: AsyncClient, active: dict[str, Any]) -> None:
    """
    Condition:
    - An opportunity is created, activated and saved.

    Expected:
    - Each change has an audit event and an ``opportunity.changed`` event, for 018's projection.
    """
    await save_opportunity(partner, _party(partner), active["id"], CONTENT, active["version"])

    async with get_session_factory()() as session:
        topics = list(
            await session.scalars(
                select(OutboxEventRecord.topic).where(OutboxEventRecord.topic == "opportunity.changed")
            )
        )
        actions = set(
            await session.scalars(select(AuditEventRecord.action).where(AuditEventRecord.subject_id == active["id"]))
        )
    assert len(topics) == 3
    assert actions == {"opportunity.created", "opportunity.activate", "opportunity.saved"}
