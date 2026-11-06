"""Opportunity states, retries, readiness and expiry through Postgres (spec 016, D1, D10, D14)."""

from copy import deepcopy
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select

from app.core import clock
from app.core.database import get_session_factory
from app.intake.repository.sqlalchemy.models import OpportunityRecord
from app.intake.service import jobs  # noqa: F401 - registers the expiry job
from app.platform.repository.sqlalchemy.models import AuditEventRecord, OutboxEventRecord
from app.worker.loop import run_jobs
from app.worker.registry import registry
from tests.factories.recipients import (
    OPPORTUNITIES,
    PROFILES,
    create_opportunity,
    move_opportunity,
    save_opportunity,
    save_profile,
)

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("clean_tables")]

CONTENT = deepcopy(OPPORTUNITIES["A1"]["content"])
READY_FIELDS = (
    "title",
    "outcome",
    "included",
    "excluded",
    "support",
    "accepted_stages",
    "relationship_forms",
    "timing",
    "financial",
)
# Close to the wall clock, because sessions signed in by the fixtures stay valid for 30 days of product time.
START = datetime.now(UTC).replace(microsecond=0) + timedelta(hours=1)


def _party(client: AsyncClient) -> str:
    return client.headers["X-Acting-Party"]


def _empty(field: str) -> dict[str, Any]:
    if field == "financial":
        # A range requirement has nothing to compare against without a financial basis, and is refused for that first.
        rows = [row for row in CONTENT["requirements"] if row["operator"] != "range_overlap"]
        return {**CONTENT, "financial": None, "requirements": rows}
    return {**CONTENT, field: [] if field in ("accepted_stages", "relationship_forms") else ""}


@pytest.fixture
async def ready(partner: AsyncClient) -> dict[str, Any]:
    """A complete draft of a partner with a profile."""
    party = _party(partner)
    await save_profile(partner, party, PROFILES["A"]["content"])
    return (await create_opportunity(partner, party, CONTENT)).json()


async def _run_worker() -> None:
    while await run_jobs(get_session_factory(), registry):
        pass


@pytest.mark.parametrize(
    ("path", "statuses"),
    [
        (["activate"], ["ACTIVE"]),
        (["close"], ["CLOSED"]),
        (["activate", "pause"], ["ACTIVE", "PAUSED"]),
        (["activate", "pause", "activate"], ["ACTIVE", "PAUSED", "ACTIVE"]),
        (["activate", "close"], ["ACTIVE", "CLOSED"]),
        (["activate", "pause", "close"], ["ACTIVE", "PAUSED", "CLOSED"]),
    ],
)
async def test_every_allowed_move(
    partner: AsyncClient, ready: dict[str, Any], path: list[str], statuses: list[str]
) -> None:
    """
    Condition:
    - A draft follows each allowed path.

    Expected:
    - Each move lands in the expected status and moves the version once.
    """
    party, version, seen = _party(partner), ready["version"], []

    for action in path:
        moved = (await move_opportunity(partner, party, ready["id"], action, version)).json()
        assert moved["version"] == version + 1
        seen.append(moved["status"])
        version = moved["version"]

    assert seen == statuses


@pytest.mark.parametrize(
    ("setup", "action"),
    [
        ([], "pause"),
        (["activate"], "activate"),
        (["activate", "pause"], "pause"),
        (["close"], "activate"),
        (["close"], "pause"),
        (["close"], "close"),
    ],
)
async def test_every_refused_move(partner: AsyncClient, ready: dict[str, Any], setup: list[str], action: str) -> None:
    """
    Condition:
    - A move the current status does not allow.

    Expected:
    - ``INVALID_TRANSITION``, and nothing changes.
    """
    party, version = _party(partner), ready["version"]
    for step in setup:
        version = (await move_opportunity(partner, party, ready["id"], step, version)).json()["version"]

    response = await move_opportunity(partner, party, ready["id"], action, version)

    read = (await partner.get(f"/api/v1/opportunities/{ready['id']}")).json()
    assert (response.status_code, response.json()["error"]["code"]) == (409, "INVALID_TRANSITION")
    assert read["version"] == version


@pytest.mark.parametrize(("action", "needs_active"), [("activate", False), ("pause", True), ("close", True)])
async def test_retried_status_change_replays_and_happens_once(
    partner: AsyncClient, ready: dict[str, Any], action: str, needs_active: bool
) -> None:
    """
    Condition:
    - A status change is retried with its key after its response was lost (D14).

    Expected:
    - The stored response replays instead of a stale version, the version moves once, one audit event exists, and the
      response carries the operation.
    """
    party, version = _party(partner), ready["version"]
    if needs_active:
        version = (await move_opportunity(partner, party, ready["id"], "activate", version, key="setup")).json()[
            "version"
        ]

    first = await move_opportunity(partner, party, ready["id"], action, version, key="retry")
    retry = await move_opportunity(partner, party, ready["id"], action, version, key="retry")

    read = (await partner.get(f"/api/v1/opportunities/{ready['id']}")).json()
    operation = (await partner.get(f"/api/v1/operations/{first.json()['operation_id']}")).json()
    async with get_session_factory()() as session:
        audited = await session.scalar(
            select(func.count())
            .select_from(AuditEventRecord)
            .where(AuditEventRecord.action == f"opportunity.{action}", AuditEventRecord.subject_id == ready["id"])
        )
    assert first.status_code == 200, first.text
    assert retry.headers["Idempotent-Replayed"] == "true"
    assert retry.json() == first.json()
    assert read["version"] == version + 1
    assert audited == 1
    assert operation["result"] == {"type": "opportunity", "id": ready["id"]}


@pytest.mark.parametrize("action", ["activate", "pause", "close"])
async def test_status_change_without_a_key_is_refused(partner: AsyncClient, ready: dict[str, Any], action: str) -> None:
    """
    Condition:
    - A status change arrives with no ``Idempotency-Key`` (D14).

    Expected:
    - ``BAD_REQUEST`` names the header, and nothing changes.
    """
    response = await partner.post(
        f"/api/v1/opportunities/{ready['id']}/{action}",
        json={"acting_party_id": _party(partner), "expected_version": ready["version"]},
    )

    read = (await partner.get(f"/api/v1/opportunities/{ready['id']}")).json()
    assert (response.status_code, response.json()["error"]["code"]) == (400, "BAD_REQUEST")
    assert response.json()["error"]["details"][0]["loc"] == ["header", "Idempotency-Key"]
    assert read["status"] == "DRAFT"


async def test_status_change_key_at_a_later_version_is_a_conflict(partner: AsyncClient, ready: dict[str, Any]) -> None:
    """
    Condition:
    - The key that activated version 1 is reused to activate at a later version (D14).

    Expected:
    - ``IDEMPOTENCY_CONFLICT``, and the opportunity stays paused.
    """
    party = _party(partner)
    active = (await move_opportunity(partner, party, ready["id"], "activate", ready["version"], key="reused")).json()
    paused = (await move_opportunity(partner, party, ready["id"], "pause", active["version"], key="pause")).json()

    response = await move_opportunity(partner, party, ready["id"], "activate", paused["version"], key="reused")

    read = (await partner.get(f"/api/v1/opportunities/{ready['id']}")).json()
    assert (response.status_code, response.json()["error"]["code"]) == (409, "IDEMPOTENCY_CONFLICT")
    assert read["status"] == "PAUSED"


@pytest.mark.parametrize("field", READY_FIELDS)
async def test_activation_needs_every_readiness_field(partner: AsyncClient, field: str) -> None:
    """
    Condition:
    - A draft lacking one field a partner must state is activated (D1).

    Expected:
    - ``VALIDATION_FAILED`` names the field, and it stays a draft.
    """
    party = _party(partner)
    await save_profile(partner, party, PROFILES["A"]["content"])
    draft = (await create_opportunity(partner, party, _empty(field))).json()

    response = await move_opportunity(partner, party, draft["id"], "activate", draft["version"])

    error = response.json()["error"]
    read = (await partner.get(f"/api/v1/opportunities/{draft['id']}")).json()
    assert (response.status_code, error["code"]) == (422, "VALIDATION_FAILED")
    assert ["body", field] in [item["loc"] for item in error["details"]]
    assert read["status"] == "DRAFT"


async def test_activation_needs_a_saved_partner_profile(partner: AsyncClient) -> None:
    """
    Condition:
    - A complete draft is activated by a partner with no profile (D1). A draft itself needs no profile.

    Expected:
    - ``VALIDATION_FAILED`` naming ``partner_profile``; once the profile is saved, activation works.
    """
    party = _party(partner)
    draft = (await create_opportunity(partner, party, CONTENT)).json()

    refused = await move_opportunity(partner, party, draft["id"], "activate", draft["version"], key="no-profile")
    await save_profile(partner, party, PROFILES["A"]["content"])
    activated = await move_opportunity(partner, party, draft["id"], "activate", draft["version"], key="profile")

    error = refused.json()["error"]
    assert (refused.status_code, error["code"]) == (422, "VALIDATION_FAILED")
    assert ["partner_profile"] in [item["loc"] for item in error["details"]]
    assert activated.json()["status"] == "ACTIVE"


@pytest.mark.parametrize("status", ["ACTIVE", "PAUSED"])
@pytest.mark.parametrize("field", READY_FIELDS)
async def test_a_live_save_cannot_publish_what_activation_would_refuse(
    partner: AsyncClient, ready: dict[str, Any], status: str, field: str
) -> None:
    """
    Condition:
    - An active or paused opportunity is saved without a field a partner must state (D1).

    Expected:
    - ``VALIDATION_FAILED`` names the field, and the current version stays.
    """
    party = _party(partner)
    live = (await move_opportunity(partner, party, ready["id"], "activate", ready["version"])).json()
    if status == "PAUSED":
        live = (await move_opportunity(partner, party, ready["id"], "pause", live["version"])).json()

    response = await save_opportunity(partner, party, ready["id"], _empty(field), live["version"])

    error = response.json()["error"]
    read = (await partner.get(f"/api/v1/opportunities/{ready['id']}")).json()
    assert (response.status_code, error["code"]) == (422, "VALIDATION_FAILED")
    assert ["body", field] in [item["loc"] for item in error["details"]]
    assert (read["number"], read["version"], read["title"]) == (1, live["version"], CONTENT["title"])


async def test_a_draft_may_stay_incomplete(partner: AsyncClient) -> None:
    """
    Condition:
    - A draft is saved with nothing filled in.

    Expected:
    - It saves.
    """
    party = _party(partner)
    draft = (await create_opportunity(partner, party, {})).json()

    saved = await save_opportunity(partner, party, draft["id"], {"title": ""}, draft["version"])

    assert saved.status_code == 200, saved.text


async def test_activation_refuses_a_closing_time_already_past(partner: AsyncClient) -> None:
    """
    Condition:
    - A complete draft closes before now.

    Expected:
    - ``VALIDATION_FAILED`` names ``closes_at``, and it stays a draft.
    """
    party = _party(partner)
    await save_profile(partner, party, PROFILES["A"]["content"])
    with clock.frozen(START):
        draft = (
            await create_opportunity(partner, party, {**CONTENT, "closes_at": (START - timedelta(days=1)).isoformat()})
        ).json()

        response = await move_opportunity(partner, party, draft["id"], "activate", draft["version"])

    assert ["body", "closes_at"] in [item["loc"] for item in response.json()["error"]["details"]]


async def _closing(partner: AsyncClient, closes_at: datetime) -> dict[str, Any]:
    party = _party(partner)
    await save_profile(partner, party, PROFILES["A"]["content"])
    draft = (await create_opportunity(partner, party, {**CONTENT, "closes_at": closes_at.isoformat()})).json()
    return (await move_opportunity(partner, party, draft["id"], "activate", draft["version"])).json()


async def _stored_status(opportunity_id: str) -> tuple[str, int]:
    async with get_session_factory()() as session:
        row = (
            await session.execute(
                select(OpportunityRecord.status, OpportunityRecord.version).where(
                    OpportunityRecord.id == opportunity_id
                )
            )
        ).one()
    return row.status, row.version


async def test_a_read_after_closing_shows_expired_and_writes_nothing(partner: AsyncClient) -> None:
    """
    Condition:
    - An active opportunity is read after ``closes_at``, before the worker has run (D10).

    Expected:
    - The read says ``EXPIRED`` and not available; the stored row is untouched.
    """
    with clock.frozen(START):
        active = await _closing(partner, START + timedelta(days=1))
    with clock.frozen(START + timedelta(days=2)):
        read = (await partner.get(f"/api/v1/opportunities/{active['id']}")).json()
        listed = (await partner.get("/api/v1/opportunities")).json()

    assert read["status"] == "EXPIRED"
    assert listed[0]["status"] == "EXPIRED"
    assert read["target_availability"] == {"available": False, "reason": "TARGET_NOT_ACTIVE"}
    assert await _stored_status(active["id"]) == ("ACTIVE", active["version"])


async def test_the_worker_persists_expiry_audits_and_publishes(partner: AsyncClient) -> None:
    """
    Condition:
    - The worker runs after ``closes_at``.

    Expected:
    - The row is ``EXPIRED``, once, with an audit event and an ``opportunity.changed`` event.
    """
    with clock.frozen(START):
        active = await _closing(partner, START + timedelta(days=1))
        await _run_worker()
        before = await _stored_status(active["id"])
    with clock.frozen(START + timedelta(days=1, minutes=1)):
        await _run_worker()
        await _run_worker()

    async with get_session_factory()() as session:
        audited = await session.scalar(
            select(func.count())
            .select_from(AuditEventRecord)
            .where(AuditEventRecord.action == "opportunity.expired", AuditEventRecord.subject_id == active["id"])
        )
        events = await session.scalar(
            select(func.count()).select_from(OutboxEventRecord).where(OutboxEventRecord.topic == "opportunity.changed")
        )
    assert before == ("ACTIVE", active["version"])
    assert await _stored_status(active["id"]) == ("EXPIRED", active["version"] + 1)
    assert audited == 1
    assert events == 3


async def test_a_job_for_a_moved_closing_time_does_nothing(partner: AsyncClient) -> None:
    """
    Condition:
    - ``closes_at`` moves later, and the job queued for the old time comes due.

    Expected:
    - The opportunity stays active until the new time, when the new job expires it.
    """
    party = _party(partner)
    with clock.frozen(START):
        active = await _closing(partner, START + timedelta(days=1))
        moved = await save_opportunity(
            partner,
            party,
            active["id"],
            {**CONTENT, "closes_at": (START + timedelta(days=5)).isoformat()},
            active["version"],
        )
    version = moved.json()["version"]

    with clock.frozen(START + timedelta(days=2)):
        await _run_worker()
        early = await _stored_status(active["id"])
    with clock.frozen(START + timedelta(days=6)):
        await _run_worker()
        late = await _stored_status(active["id"])

    assert moved.status_code == 200, moved.text
    assert early == ("ACTIVE", version)
    assert late == ("EXPIRED", version + 1)


async def test_a_mutation_after_closing_is_an_invalid_transition(partner: AsyncClient) -> None:
    """
    Condition:
    - Before the worker runs, an opportunity past ``closes_at`` is saved and paused (D10).

    Expected:
    - Both are ``INVALID_TRANSITION``.
    """
    party = _party(partner)
    with clock.frozen(START):
        active = await _closing(partner, START + timedelta(days=1))
    with clock.frozen(START + timedelta(days=2)):
        saved = await save_opportunity(partner, party, active["id"], CONTENT, active["version"])
        paused = await move_opportunity(partner, party, active["id"], "pause", active["version"])

    assert (saved.status_code, saved.json()["error"]["code"]) == (409, "INVALID_TRANSITION")
    assert (paused.status_code, paused.json()["error"]["code"]) == (409, "INVALID_TRANSITION")


async def test_closing_a_general_intake_clears_the_pointer(partner: AsyncClient) -> None:
    """
    Condition:
    - A general intake is activated, saved while active, and closed (D7).

    Expected:
    - The profile's pointer follows the current version, then is cleared.
    """
    from app.intake.repository.sqlalchemy.models import OpportunityVersionRecord, PartnerProfileRecord  # noqa: PLC0415

    party = _party(partner)
    await save_profile(partner, party, PROFILES["A"]["content"])
    draft = (await create_opportunity(partner, party, {**CONTENT, "kind": "GENERAL_INTAKE"})).json()

    async def pointed_number() -> int | None:
        async with get_session_factory()() as session:
            return await session.scalar(
                select(OpportunityVersionRecord.number)
                .join(
                    PartnerProfileRecord, PartnerProfileRecord.general_intake_version_id == OpportunityVersionRecord.id
                )
                .where(OpportunityVersionRecord.opportunity_id == draft["id"])
            )

    before = await pointed_number()
    active = (await move_opportunity(partner, party, draft["id"], "activate", draft["version"])).json()
    activated = await pointed_number()
    saved = (await save_opportunity(partner, party, draft["id"], CONTENT, active["version"])).json()
    after_save = await pointed_number()
    await move_opportunity(partner, party, draft["id"], "close", saved["version"])
    after_close = await pointed_number()

    assert (before, activated, after_save, after_close) == (None, 1, 2, None)
