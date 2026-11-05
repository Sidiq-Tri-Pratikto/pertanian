"""Typed, visible requirements through Postgres (spec 016, US2, FR-003)."""

from copy import deepcopy
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select

from app.core.database import get_session_factory
from app.intake.repository.sqlalchemy.models import RequirementRecord
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
HIDDEN_NOTE = {
    "label": "Catatan tim",
    "field": "authority",
    "operator": "equals",
    "value": "REVIEWED",
    "mandatory": False,
    "visibility": "PARTNER_ONLY",
    "reason": "Catatan internal mitra",
}


def _party(client: AsyncClient) -> str:
    return client.headers["X-Acting-Party"]


async def _requirement_count() -> int:
    async with get_session_factory()() as session:
        return await session.scalar(select(func.count()).select_from(RequirementRecord)) or 0


async def _active(partner: AsyncClient, content: dict[str, Any]) -> dict[str, Any]:
    party = _party(partner)
    await save_profile(partner, party, PROFILES["A"]["content"])
    created = (await create_opportunity(partner, party, content)).json()
    moved = await move_opportunity(partner, party, created["id"], "activate", created["version"])
    assert moved.status_code == 200, moved.text
    return moved.json()


@pytest.mark.parametrize("operator", ["like", "regex", "current", "EQUALS"])
async def test_an_operator_outside_the_list_is_refused(partner: AsyncClient, operator: str) -> None:
    """
    Condition:
    - A requirement uses an operator outside the eight allowed (scenario 1).

    Expected:
    - ``VALIDATION_FAILED``, and nothing is written.
    """
    requirement = {"label": "Syarat", "field": "stage", "operator": operator, "value": ["PILOT"]}

    response = await create_opportunity(partner, _party(partner), {**CONTENT, "requirements": [requirement]})

    assert (response.status_code, response.json()["error"]["code"]) == (422, "VALIDATION_FAILED")
    assert (await partner.get("/api/v1/opportunities")).json() == []
    assert await _requirement_count() == 0


async def test_a_wrong_value_shape_is_refused_per_field(partner: AsyncClient) -> None:
    """
    Condition:
    - A requirement's value does not fit its operator.

    Expected:
    - ``VALIDATION_FAILED`` names the row and ``value``, and nothing is written.
    """
    requirement = {"label": "Syarat", "field": "stage", "operator": "in_set", "value": "PILOT"}

    response = await create_opportunity(partner, _party(partner), {**CONTENT, "requirements": [requirement]})

    assert [item["loc"] for item in response.json()["error"]["details"]] == [["body", "requirements", 0, "value"]]
    assert await _requirement_count() == 0


async def test_a_narrative_requirement_is_a_review_question(partner: AsyncClient, stranger: AsyncClient) -> None:
    """
    Condition:
    - A partner adds a narrative criterion with no typed mapping, and activates (scenario 2, D15).

    Expected:
    - It is stored as a non-mandatory ``manual_review``, so it cannot block; applicants still read it.
    """
    narrative = {"label": "Pengalaman di desa", "mandatory": True, "reason": "Mitra ingin membahasnya."}

    active = await _active(partner, {**CONTENT, "requirements": [*CONTENT["requirements"], narrative]})

    read = (await stranger.get(f"/api/v1/opportunities/{active['id']}")).json()
    row = read["requirements"][-1]
    assert (row["label"], row["field"], row["operator"], row["value"], row["mandatory"]) == (
        "Pengalaman di desa",
        "narrative",
        "manual_review",
        None,
        False,
    )


async def test_an_applicant_reads_every_blocking_requirement_with_its_reason(
    recipients: LoadedRecipients, stranger: AsyncClient
) -> None:
    """
    Condition:
    - An applicant reads each active opportunity (scenario 3).

    Expected:
    - Every mandatory requirement shows its label, reason, stage, verification mode, visibility and version. A1's
      certificate applies at commercialization, and C1's at submission.
    """
    expected_counts = {key: len(item["content"]["requirements"]) for key, item in OPPORTUNITIES.items()}

    for key, opportunity_id in recipients.opportunities.items():
        read = (await stranger.get(f"/api/v1/opportunities/{opportunity_id}")).json()
        assert len(read["requirements"]) == expected_counts[key]
        for row in read["requirements"]:
            assert row["label"] and row["reason"]
            assert row["applies_at"] and row["verification_mode"]
            assert row["visibility"] == "PUBLIC"
            assert row["version"] == read["number"]

    a1 = (await stranger.get(f"/api/v1/opportunities/{recipients.opportunities['A1']}")).json()
    c1 = (await stranger.get(f"/api/v1/opportunities/{recipients.opportunities['C1']}")).json()
    assert next(row for row in a1["requirements"] if "Sertifikat" in row["label"])["applies_at"] == "COMMERCIALIZATION"
    assert next(row for row in c1["requirements"] if "Sertifikat" in row["label"])["applies_at"] == "SUBMISSION"


async def test_a_mandatory_requirement_cannot_be_hidden(partner: AsyncClient) -> None:
    """
    Condition:
    - A mandatory requirement is ``PARTNER_ONLY`` (D9).

    Expected:
    - ``VALIDATION_FAILED`` names ``visibility``; no secret criterion can reject a pitch.
    """
    requirement = {**HIDDEN_NOTE, "mandatory": True}

    response = await create_opportunity(partner, _party(partner), {**CONTENT, "requirements": [requirement]})

    assert [item["loc"] for item in response.json()["error"]["details"]] == [["body", "requirements", 0, "visibility"]]


async def test_partner_only_rows_reach_the_owner_only(partner: AsyncClient, stranger: AsyncClient) -> None:
    """
    Condition:
    - An active opportunity has a non-mandatory ``PARTNER_ONLY`` note.

    Expected:
    - The owner reads it; another party finds it in no read, version read or list.
    """
    active = await _active(partner, {**CONTENT, "requirements": [*CONTENT["requirements"], HIDDEN_NOTE]})
    party = _party(partner)

    owner = (await partner.get(f"/api/v1/opportunities/{active['id']}")).json()
    read = await stranger.get(f"/api/v1/opportunities/{active['id']}")
    version = await stranger.get(f"/api/v1/opportunities/{active['id']}/versions/1")
    listed = await stranger.get("/api/v1/opportunities", params={"partner_party_id": party})

    assert "Catatan tim" in [row["label"] for row in owner["requirements"]]
    for response in (read, version, listed):
        assert response.status_code == 200
        assert "Catatan tim" not in response.text
        assert "Catatan internal mitra" not in response.text


async def test_a_blocking_requirement_needs_a_reason_to_go_live(partner: AsyncClient) -> None:
    """
    Condition:
    - A draft has a mandatory requirement with no reason, and is activated. The same is saved on a live opportunity
      (D1).

    Expected:
    - Both are ``VALIDATION_FAILED`` naming the row's ``reason``; the draft stays a draft, and the live version stays.
    """
    party = _party(partner)
    await save_profile(partner, party, PROFILES["A"]["content"])
    no_reason = {"label": "Syarat", "field": "authority", "operator": "equals", "value": "REVIEWED"}
    draft = (await create_opportunity(partner, party, {**CONTENT, "requirements": [no_reason]}, key="draft")).json()
    live = (await create_opportunity(partner, party, CONTENT, key="live")).json()
    live = (await move_opportunity(partner, party, live["id"], "activate", live["version"])).json()

    activated = await move_opportunity(partner, party, draft["id"], "activate", draft["version"])
    saved = await save_opportunity(
        partner, party, live["id"], {**CONTENT, "requirements": [no_reason]}, live["version"]
    )

    for response in (activated, saved):
        error = response.json()["error"]
        assert (response.status_code, error["code"]) == (422, "VALIDATION_FAILED")
        assert ["body", "requirements", 0, "reason"] in [item["loc"] for item in error["details"]]
    assert (await partner.get(f"/api/v1/opportunities/{draft['id']}")).json()["status"] == "DRAFT"
    read = (await partner.get(f"/api/v1/opportunities/{live['id']}")).json()
    assert (read["number"], len(read["requirements"])) == (1, len(CONTENT["requirements"]))


async def test_a_new_version_leaves_the_old_requirements_alone(partner: AsyncClient) -> None:
    """
    Condition:
    - A live opportunity is saved with fewer requirements.

    Expected:
    - The new version has fewer; version 1 keeps all of them, so a pitch's target does not change.
    """
    active = await _active(partner, CONTENT)
    party = _party(partner)

    saved = await save_opportunity(
        partner, party, active["id"], {**CONTENT, "requirements": CONTENT["requirements"][:1]}, active["version"]
    )

    old = (await partner.get(f"/api/v1/opportunities/{active['id']}/versions/1")).json()
    assert len(saved.json()["requirements"]) == 1
    assert len(old["requirements"]) == len(CONTENT["requirements"])
