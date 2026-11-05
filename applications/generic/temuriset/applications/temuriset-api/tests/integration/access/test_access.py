"""Organizations, memberships, invitations and the acting context (spec 007)."""

from collections.abc import AsyncIterator, Callable
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import pytest
from fastapi import APIRouter
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.access.model.models import Capability
from app.access.repository.sqlalchemy.models import InvitationRecord
from app.access.service.policy import require
from app.access.service.service import assert_can_act
from app.core import clock
from app.core.database import get_session_factory
from app.core.security import PrincipalDep
from app.main import create_app
from app.platform.repository.sqlalchemy.models import JobRecord
from app.platform.service.outbox import enqueue_job
from app.worker.loop import run_jobs
from app.worker.registry import Registry

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("clean_tables")]

WEB_ORIGIN = "http://localhost:3020"
ORGANIZATION = "Demo Circular Materials Ltd"

probe = APIRouter()


@probe.post("/test/organizations/{party_id}/{action}")
async def act(party_id: UUID, action: Capability, principal: PrincipalDep) -> dict[str, str]:
    """Test-only route: asks the policy whether the active party may take an action on a party's resource."""
    require(principal, action, party_id)
    return {"allowed": action}


app = create_app()
app.include_router(probe)


@pytest.fixture
def browser() -> Callable[[], AsyncClient]:
    """A new browser for the application with the probe route."""
    return lambda: AsyncClient(transport=ASGITransport(app=app), base_url="http://test", headers={"Origin": WEB_ORIGIN})


@pytest.fixture
async def bima(browser, sign_up) -> AsyncIterator[AsyncClient]:
    """Bima, signed in, who creates the organization."""
    async with browser() as client:
        await sign_up(client, "bima@example.com", persona="mitra", name="Bima")
        yield client


@pytest.fixture
async def rani(browser, sign_up) -> AsyncIterator[AsyncClient]:
    """Rani, signed in, who is invited."""
    async with browser() as client:
        await sign_up(client, "rani@example.com", name="Rani")
        yield client


async def _create_organization(client: AsyncClient, name: str = ORGANIZATION) -> dict[str, Any]:
    response = await client.post(
        "/api/v1/organizations", json={"name": name, "kind": "company"}, headers={"Idempotency-Key": name}
    )
    assert response.status_code == 201, response.text
    return response.json()


async def _act_as(client: AsyncClient, party_id: str) -> dict[str, Any]:
    response = await client.put("/api/v1/me/context", json={"party_id": party_id})
    assert response.status_code == 200, response.text
    return response.json()


async def _invite(client: AsyncClient, organization: dict, email: str, capabilities: list[str], key: str = "i1"):
    return await client.post(
        f"/api/v1/organizations/{organization['id']}/invitations",
        json={"acting_party_id": organization["party_id"], "email": email, "capabilities": capabilities},
        headers={"Idempotency-Key": key},
    )


async def _token(client: AsyncClient, email: str) -> str:
    messages = (await client.get("/api/v1/dev/mailbox", params={"email": email})).json()
    return next(message for message in messages if "undangan" in message["body"])["body"].rsplit("/", 1)[1]


async def _member(bima: AsyncClient, rani: AsyncClient, capabilities: list[str]) -> dict[str, Any]:
    organization = await _create_organization(bima)
    await _act_as(bima, organization["party_id"])
    assert (await _invite(bima, organization, "rani@example.com", capabilities)).status_code == 201
    accepted = await rani.post(f"/api/v1/invitations/{await _token(rani, 'rani@example.com')}/accept")
    assert accepted.status_code == 200, accepted.text
    return organization


async def test_creator_joins_with_every_capability(bima: AsyncClient) -> None:
    """
    Condition:
    - Bima creates an organization.

    Expected:
    - An organization party exists and Bima is a member with every capability; ``/me`` lists it.
    """
    organization = await _create_organization(bima)
    me = (await bima.get("/api/v1/me")).json()
    members = (await bima.get(f"/api/v1/organizations/{organization['id']}/members")).json()

    assert organization["name"] == ORGANIZATION and organization["party_id"] and organization["operation_id"]
    assert [entry["name"] for entry in me["organizations"]] == [ORGANIZATION]
    assert members[0]["display_name"] == "Bima"
    assert set(members[0]["capabilities"]) == {capability.value for capability in Capability}


async def test_member_acts_only_with_granted_capabilities(bima: AsyncClient, rani: AsyncClient) -> None:
    """
    Condition:
    - Rani accepts an invitation with ``edit_portfolio`` only and acts as the organization (AC04).

    Expected:
    - Editing is allowed; deciding a pitch and inviting members are ``FORBIDDEN``.
    """
    organization = await _member(bima, rani, ["edit_portfolio"])
    me = await _act_as(rani, organization["party_id"])

    edit = await rani.post(f"/test/organizations/{organization['party_id']}/edit_portfolio")
    decide = await rani.post(f"/test/organizations/{organization['party_id']}/decide_pitch")
    invite = await _invite(rani, organization, "eve@example.com", ["schedule"], key="rani-invite")

    assert me["capabilities"] == ["edit_portfolio"]
    assert edit.json() == {"allowed": "edit_portfolio"}
    assert (decide.status_code, decide.json()["error"]["code"]) == (403, "FORBIDDEN")
    assert (invite.status_code, invite.json()["error"]["code"]) == (403, "FORBIDDEN")


async def test_personal_context_cannot_touch_the_organizations_resources(bima: AsyncClient, rani: AsyncClient) -> None:
    """
    Condition:
    - Rani is a member but still acts as herself.

    Expected:
    - The organization's resources are ``NOT_FOUND`` until she switches context.
    """
    organization = await _member(bima, rani, ["edit_portfolio"])

    response = await rani.post(f"/test/organizations/{organization['party_id']}/edit_portfolio")

    assert response.status_code == 404


async def test_switching_to_an_organization_one_has_not_joined_reveals_nothing(
    bima: AsyncClient, rani: AsyncClient
) -> None:
    """
    Condition:
    - Rani tries to act as an organization she does not belong to (AC05).

    Expected:
    - ``NOT_FOUND`` with no name or metadata of that organization, and her context is unchanged.
    """
    organization = await _create_organization(bima)

    response = await rani.put("/api/v1/me/context", json={"party_id": organization["party_id"]})
    me = (await rani.get("/api/v1/me")).json()

    assert response.status_code == 404
    assert ORGANIZATION not in response.text and organization["id"] not in response.text
    assert me["active_party_id"] == me["personal_party_id"]


@pytest.mark.parametrize("ending", ["expired", "revoked"])
async def test_expired_or_revoked_invitation_cannot_be_accepted(
    bima: AsyncClient, rani: AsyncClient, ending: str
) -> None:
    """
    Condition:
    - An invitation is accepted after seven days, or after it was revoked.

    Expected:
    - 410 ``INVITATION_EXPIRED`` and no membership.
    """
    start = datetime(2026, 11, 5, 9, tzinfo=UTC)
    organization = await _create_organization(bima)
    await _act_as(bima, organization["party_id"])
    with clock.frozen(start):
        invitation = (await _invite(bima, organization, "rani@example.com", ["schedule"])).json()
    if ending == "revoked":
        revoked = await bima.post(
            f"/api/v1/invitations/{invitation['id']}/revoke", json={"acting_party_id": organization["party_id"]}
        )
        assert revoked.json()["status"] == "revoked"
    accepted_at = start + (timedelta(days=7) if ending == "expired" else timedelta(hours=1))
    with clock.frozen(accepted_at):
        response = await rani.post(f"/api/v1/invitations/{await _token(rani, 'rani@example.com')}/accept")

    assert response.status_code == 410
    error = response.json()["error"]
    assert error["code"] == "INVITATION_EXPIRED"
    assert error["message"] == "Undangan ini sudah tidak berlaku. Minta undangan baru kepada pengelola organisasi."
    assert (await rani.get("/api/v1/me")).json()["organizations"] == []


async def test_invitation_shows_what_it_grants_and_stores_only_a_hash(bima: AsyncClient, rani: AsyncClient) -> None:
    """
    Condition:
    - Rani opens her invitation link before accepting.

    Expected:
    - She sees the organization, capabilities, expiry and ``pending``; the database holds only the token's hash.
    """
    organization = await _create_organization(bima)
    await _act_as(bima, organization["party_id"])
    await _invite(bima, organization, "rani@example.com", ["schedule", "edit_portfolio"])
    token = await _token(rani, "rani@example.com")

    detail = (await rani.get(f"/api/v1/invitations/{token}")).json()

    assert detail | {"expires_at": None} == {
        "organization_name": ORGANIZATION,
        "capabilities": ["edit_portfolio", "schedule"],
        "expires_at": None,
        "status": "pending",
    }
    async with get_session_factory()() as session:
        stored = await session.scalar(select(InvitationRecord))
    assert stored is not None and token not in stored.token_sha256


async def test_invitation_for_another_email_is_not_found(bima: AsyncClient, rani: AsyncClient) -> None:
    """
    Condition:
    - Rani opens a link meant for someone else.

    Expected:
    - ``NOT_FOUND``; nothing about the invitation is shown.
    """
    organization = await _create_organization(bima)
    await _act_as(bima, organization["party_id"])
    await _invite(bima, organization, "eve@example.com", ["schedule"])

    response = await rani.get(f"/api/v1/invitations/{await _token(bima, 'eve@example.com')}")

    assert response.status_code == 404


async def test_removed_members_job_is_rechecked_and_denied(bima: AsyncClient, rani: AsyncClient) -> None:
    """
    Condition:
    - Rani starts a job as the organization, then Bima removes her before it runs (AC06).

    Expected:
    - The job rechecks access, is denied, and fails at once without running its effect.
    """
    organization = await _member(bima, rani, ["edit_portfolio"])
    rani_me = await _act_as(rani, organization["party_id"])
    party_id = UUID(organization["party_id"])
    async with get_session_factory()() as session:
        await enqueue_job(
            session, "portfolio.export", {"account_id": rani_me["account"]["id"]}, actor_party_id=party_id
        )
        await session.commit()
    members = (await bima.get(f"/api/v1/organizations/{organization['id']}/members")).json()
    rani_membership = next(member for member in members if member["display_name"] == "Rani")
    removed = await bima.request(
        "DELETE",
        f"/api/v1/organizations/{organization['id']}/members/{rani_membership['account_id']}",
        json={"acting_party_id": organization["party_id"], "expected_version": rani_membership["version"]},
    )
    effects: list[str] = []
    registry = Registry()

    @registry.job("portfolio.export")
    async def export(session: AsyncSession, job_input: dict[str, Any]) -> None:
        await assert_can_act(session, UUID(job_input["account_id"]), party_id, Capability.EDIT_PORTFOLIO)
        effects.append("exported")

    await run_jobs(get_session_factory(), registry)

    assert removed.status_code == 204
    assert effects == []
    async with get_session_factory()() as session:
        job = await session.scalar(select(JobRecord))
    assert job is not None
    assert (job.status, job.attempts, job.last_error_code) == ("FAILED", 1, "APP-NOT-FOUND")
    me = (await rani.get("/api/v1/me")).json()
    assert me["active_party_id"] == me["personal_party_id"]
    assert me["organizations"] == []


async def test_old_tab_cannot_act_in_a_changed_context(bima: AsyncClient) -> None:
    """
    Condition:
    - One tab acts as the organization; another tab switches the session back to Bima personally; the first tab
      sends an invitation with the old ``acting_party_id``.

    Expected:
    - 409 ``STALE_CONTEXT`` and no invitation exists.
    """
    organization = await _create_organization(bima)
    await _act_as(bima, organization["party_id"])
    me = (await bima.get("/api/v1/me")).json()
    await _act_as(bima, me["personal_party_id"])

    response = await _invite(bima, organization, "rani@example.com", ["schedule"])

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "STALE_CONTEXT"
    async with get_session_factory()() as session:
        assert await session.scalar(select(func.count()).select_from(InvitationRecord)) == 0


async def test_last_member_manager_cannot_be_removed(bima: AsyncClient) -> None:
    """
    Condition:
    - Bima, the only member manager, tries to remove himself.

    Expected:
    - ``CONFLICT`` explaining that another manager is needed first.
    """
    organization = await _create_organization(bima)
    me = await _act_as(bima, organization["party_id"])
    members = (await bima.get(f"/api/v1/organizations/{organization['id']}/members")).json()

    response = await bima.request(
        "DELETE",
        f"/api/v1/organizations/{organization['id']}/members/{me['account']['id']}",
        json={"acting_party_id": organization["party_id"], "expected_version": members[0]["version"]},
    )

    assert response.status_code == 409
    assert response.json()["error"]["message"].startswith("Organisasi memerlukan setidaknya satu pengelola anggota.")


async def test_stale_membership_version_is_refused(bima: AsyncClient, rani: AsyncClient) -> None:
    """
    Condition:
    - Bima removes Rani with an old membership version.

    Expected:
    - ``STALE_VERSION`` with the current version, and Rani stays a member.
    """
    organization = await _member(bima, rani, ["schedule"])
    members = (await bima.get(f"/api/v1/organizations/{organization['id']}/members")).json()
    rani_membership = next(member for member in members if member["display_name"] == "Rani")

    response = await bima.request(
        "DELETE",
        f"/api/v1/organizations/{organization['id']}/members/{rani_membership['account_id']}",
        json={"acting_party_id": organization["party_id"], "expected_version": rani_membership["version"] + 5},
    )

    assert response.status_code == 409
    assert response.json()["error"]["current_version"] == rani_membership["version"]
    assert len((await rani.get("/api/v1/me")).json()["organizations"]) == 1
