"""Suspension hides a listing while leaving the owner and the case operational."""

from collections.abc import Awaitable, Callable
from uuid import UUID

import pytest
from httpx import AsyncClient

from app.core.database import get_session_factory
from app.moderation.repository.sqlalchemy.models import OperatorGrantRecord
from tests.integration.conftest import SignUp

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("clean_tables")]


async def test_suspension_hides_public_listing_and_lift_restores_it(
    client: AsyncClient,
    sign_up: SignUp,
    new_client: Callable[[], AsyncClient],
    published_invention: Callable[..., Awaitable[dict]],
) -> None:
    """
    Condition:
    - A published invention is reported and a scoped operator suspends it.

    Expected:
    - Public reads are hidden, private owner reads still work, and lifting restores public access.
    """
    owner = await sign_up(client, "listing-owner@example.test")
    invention = await published_invention(client)
    invention_id = invention["id"]
    request = await client.post(
        "/api/v1/support-requests",
        json={
            "acting_party_id": owner["active_party_id"],
            "invention_id": invention_id,
            "outcome": "Uji lapangan",
            "support_forms": ["project_funding"],
        },
        headers={"Idempotency-Key": "before-suspension"},
    )
    assert request.status_code == 201, request.text
    draft = request.json()
    public_url = f"/api/v1/inventions/{invention_id}/public"

    async with new_client() as operator:
        actor = await sign_up(operator, "listing-operator@example.test")
        async with get_session_factory()() as session:
            session.add(OperatorGrantRecord(account_id=UUID(actor["account"]["id"]), scope="moderation"))
            await session.commit()
        assert (await operator.get(public_url)).status_code == 200
        case = await operator.post(
            "/api/v1/reports",
            json={
                "acting_party_id": actor["active_party_id"],
                "expected_version": None,
                "subject_type": "INVENTION",
                "subject_id": invention_id,
                "reason": "A disputed public claim",
            },
            headers={"Idempotency-Key": "listing-report"},
        )
        assert case.status_code == 201, case.text
        url = f"/api/v1/operator/reports/{case.json()['id']}/actions"
        action = {"acting_party_id": actor["active_party_id"], "expected_version": 1, "note": "Review required"}
        suspended = await operator.post(
            url, json={**action, "action": "SUSPEND_LISTING"}, headers={"Idempotency-Key": "suspend"}
        )
        assert suspended.status_code == 200, suspended.text
        assert suspended.json()["suspended"]
        assert (await operator.get(public_url)).status_code == 404
        assert (await client.get(f"/api/v1/inventions/{invention_id}")).status_code == 200
        blocked = await client.post(
            "/api/v1/support-requests",
            json={"acting_party_id": owner["active_party_id"], "invention_id": invention_id},
            headers={"Idempotency-Key": "blocked-need"},
        )
        assert blocked.json()["error"]["code"] == "LISTING_SUSPENDED", blocked.text
        activation = await client.post(
            f"/api/v1/support-requests/{draft['id']}/activate",
            json={"acting_party_id": owner["active_party_id"], "expected_version": draft["version"]},
            headers={"Idempotency-Key": "blocked-activation"},
        )
        assert activation.json()["error"]["code"] == "LISTING_SUSPENDED", activation.text

        lifted = await operator.post(
            url,
            json={**action, "expected_version": suspended.json()["version"], "action": "LIFT_SUSPENSION"},
            headers={"Idempotency-Key": "lift"},
        )
        assert lifted.status_code == 200, lifted.text
        assert not lifted.json()["suspended"]
        assert (await operator.get(public_url)).status_code == 200


async def test_suspended_mandate_is_hidden_and_owner_can_wind_down(
    client: AsyncClient, sign_up: SignUp, new_client: Callable[[], AsyncClient]
) -> None:
    """
    Condition:
    - A partner's active mandate is suspended by a scoped operator.

    Expected:
    - Other parties cannot read it. The owner sees the suspension reason and can pause.
    """
    from tests.factories.recipients import PROFILES, save_profile
    from tests.integration.intake.test_intake_availability import _active

    owner = await sign_up(client, "mandate-owner@example.test", persona="mitra")
    party = owner["active_party_id"]
    client.headers["X-Acting-Party"] = party
    profile = await save_profile(client, party, PROFILES["A"]["content"], version=None, key="profile")
    assert profile.status_code == 200, profile.text
    opportunity = await _active(client, "SPECIFIC")
    target = opportunity["id"]
    async with new_client() as operator:
        actor = await sign_up(operator, "mandate-operator@example.test")
        async with get_session_factory()() as session, session.begin():
            session.add(OperatorGrantRecord(account_id=UUID(actor["account"]["id"]), scope="moderation"))
        report = await operator.post(
            "/api/v1/reports",
            json={
                "acting_party_id": actor["active_party_id"],
                "expected_version": None,
                "subject_type": "OPPORTUNITY",
                "subject_id": target,
                "reason": "Perlu ditinjau",
            },
            headers={"Idempotency-Key": "mandate-report"},
        )
        assert report.status_code == 201, report.text
        suspended = await operator.post(
            f"/api/v1/operator/reports/{report.json()['id']}/actions",
            json={
                "acting_party_id": actor["active_party_id"],
                "expected_version": 1,
                "action": "SUSPEND_LISTING",
                "note": "Ditinjau",
            },
            headers={"Idempotency-Key": "mandate-suspend"},
        )
        assert suspended.status_code == 200, suspended.text
        assert (await operator.get(f"/api/v1/opportunities/{target}")).status_code == 404
        public = await operator.get("/api/v1/opportunities", params={"partner_party_id": party})
        assert public.json() == []

    private = await client.get(f"/api/v1/opportunities/{target}")
    assert private.json()["target_availability"] == {"available": False, "reason": "SUSPENDED"}
    paused = await client.post(
        f"/api/v1/opportunities/{target}/pause",
        json={"acting_party_id": party, "expected_version": opportunity["version"]},
        headers={"Idempotency-Key": "wind-down"},
    )
    assert paused.status_code == 200, paused.text
