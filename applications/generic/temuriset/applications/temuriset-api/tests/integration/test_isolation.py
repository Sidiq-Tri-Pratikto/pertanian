"""Two-party isolation harness (spec 007, FR-006): every data route, called as an unrelated party, reveals nothing.

Each data PR adds its routes to ``ROUTES``. ``test_every_route_is_covered`` fails when a route is neither here nor in
``NOT_DATA_ROUTES``, so a new route cannot ship without its isolation case.
"""

from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass
from typing import Any

import pytest
from httpx import AsyncClient

from app.main import app

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("clean_tables")]

# Routes with no other party's data: health, the manifest, signing in, one's own account, development helpers, and
# creating one's own organization.
NOT_DATA_ROUTES = {
    ("GET", "/health/live"),
    ("GET", "/health/ready"),
    ("GET", "/api/v1/capabilities"),
    ("POST", "/api/v1/auth/code"),
    ("POST", "/api/v1/auth/verify"),
    ("POST", "/api/v1/auth/sign-out"),
    ("GET", "/api/v1/me"),
    ("PATCH", "/api/v1/me"),
    ("GET", "/api/v1/dev/mailbox"),
    ("POST", "/api/v1/organizations"),
    ("POST", "/api/v1/inventions"),
}


@dataclass
class Owner:
    """What party A owns, for party B to reach for."""

    organization_id: str
    party_id: str
    account_id: str
    operation_id: str
    invitation_id: str
    invitation_token: str
    invention_id: str
    document_id: str
    intent_id: str
    grant_id: str
    support_request_id: str = ""
    published_invention_id: str = ""


@dataclass
class Case:
    """How to call one route against A's data."""

    method: str
    path: Callable[[Owner], str]
    body: Callable[[Owner, str], dict[str, Any] | None] = lambda _owner, _actor: None
    headers: dict[str, str] | None = None


ROUTES: dict[tuple[str, str], Case] = {
    ("GET", "/api/v1/operations/{operation_id}"): Case("GET", lambda o: f"/api/v1/operations/{o.operation_id}"),
    ("GET", "/api/v1/organizations/{organization_id}/members"): Case(
        "GET", lambda o: f"/api/v1/organizations/{o.organization_id}/members"
    ),
    ("DELETE", "/api/v1/organizations/{organization_id}/members/{account_id}"): Case(
        "DELETE",
        lambda o: f"/api/v1/organizations/{o.organization_id}/members/{o.account_id}",
        lambda _o, actor: {"acting_party_id": actor, "expected_version": 1},
    ),
    ("POST", "/api/v1/organizations/{organization_id}/invitations"): Case(
        "POST",
        lambda o: f"/api/v1/organizations/{o.organization_id}/invitations",
        lambda _o, actor: {"acting_party_id": actor, "email": "eve@example.com", "capabilities": ["schedule"]},
        {"Idempotency-Key": "isolation"},
    ),
    ("GET", "/api/v1/organizations/{organization_id}/invitations"): Case(
        "GET", lambda o: f"/api/v1/organizations/{o.organization_id}/invitations"
    ),
    ("GET", "/api/v1/invitations/{token}"): Case("GET", lambda o: f"/api/v1/invitations/{o.invitation_token}"),
    ("POST", "/api/v1/invitations/{token}/accept"): Case(
        "POST", lambda o: f"/api/v1/invitations/{o.invitation_token}/accept"
    ),
    ("POST", "/api/v1/invitations/{invitation_id}/revoke"): Case(
        "POST", lambda o: f"/api/v1/invitations/{o.invitation_id}/revoke", lambda _o, actor: {"acting_party_id": actor}
    ),
    ("PUT", "/api/v1/me/context"): Case("PUT", lambda _o: "/api/v1/me/context", lambda o, _a: {"party_id": o.party_id}),
    ("GET", "/api/v1/inventions"): Case("GET", lambda _o: "/api/v1/inventions"),
    ("GET", "/api/v1/inventions/{invention_id}"): Case("GET", lambda o: f"/api/v1/inventions/{o.invention_id}"),
    ("PUT", "/api/v1/inventions/{invention_id}/draft"): Case(
        "PUT",
        lambda o: f"/api/v1/inventions/{o.invention_id}/draft",
        lambda _o, actor: {"acting_party_id": actor, "expected_version": 1, "title": "x"},
        {"Idempotency-Key": "isolation-draft"},
    ),
    ("POST", "/api/v1/inventions/{invention_id}/publish"): Case(
        "POST",
        lambda o: f"/api/v1/inventions/{o.invention_id}/publish",
        lambda _o, actor: {"acting_party_id": actor, "expected_version": 1},
        {"Idempotency-Key": "isolation-publish"},
    ),
    ("POST", "/api/v1/inventions/{invention_id}/archive"): Case(
        "POST",
        lambda o: f"/api/v1/inventions/{o.invention_id}/archive",
        lambda _o, actor: {"acting_party_id": actor, "expected_version": 1},
    ),
    ("POST", "/api/v1/documents/upload-intents"): Case(
        "POST",
        lambda _o: "/api/v1/documents/upload-intents",
        lambda o, actor: {
            "acting_party_id": actor,
            "title": "x",
            "kind": "other",
            "media_type": "application/pdf",
            "size_bytes": 10,
            "document_id": o.document_id,
        },
    ),
    ("PUT", "/api/v1/documents/upload-intents/{intent_id}/content"): Case(
        "PUT", lambda o: f"/api/v1/documents/upload-intents/{o.intent_id}/content"
    ),
    ("GET", "/api/v1/documents"): Case("GET", lambda _o: "/api/v1/documents"),
    ("GET", "/api/v1/documents/{document_id}"): Case("GET", lambda o: f"/api/v1/documents/{o.document_id}"),
    ("POST", "/api/v1/documents/{document_id}/grants"): Case(
        "POST",
        lambda o: f"/api/v1/documents/{o.document_id}/grants",
        lambda _o, actor: {"acting_party_id": actor, "version": 1, "grantee_party_id": actor, "purpose": "pitch"},
        {"Idempotency-Key": "isolation-grant"},
    ),
    ("POST", "/api/v1/grants/{grant_id}/revoke"): Case(
        "POST",
        lambda o: f"/api/v1/grants/{o.grant_id}/revoke",
        lambda _o, actor: {"acting_party_id": actor},
        {"Idempotency-Key": "isolation-revoke"},
    ),
    ("GET", "/api/v1/documents/{document_id}/versions/{number}/content"): Case(
        "GET", lambda o: f"/api/v1/documents/{o.document_id}/versions/1/content"
    ),
    ("POST", "/api/v1/support-requests"): Case(
        "POST",
        lambda _o: "/api/v1/support-requests",
        lambda o, actor: {"acting_party_id": actor, "invention_id": o.published_invention_id, "outcome": "x"},
        {"Idempotency-Key": "isolation-support"},
    ),
    ("GET", "/api/v1/support-requests"): Case("GET", lambda _o: "/api/v1/support-requests"),
    ("GET", "/api/v1/support-requests/{request_id}"): Case(
        "GET", lambda o: f"/api/v1/support-requests/{o.support_request_id}"
    ),
    ("GET", "/api/v1/support-requests/{request_id}/versions/{number}"): Case(
        "GET", lambda o: f"/api/v1/support-requests/{o.support_request_id}/versions/1"
    ),
    ("PUT", "/api/v1/support-requests/{request_id}"): Case(
        "PUT",
        lambda o: f"/api/v1/support-requests/{o.support_request_id}",
        lambda _o, actor: {"acting_party_id": actor, "expected_version": 1, "outcome": "x"},
        {"Idempotency-Key": "isolation-support-update"},
    ),
    ("POST", "/api/v1/support-requests/{request_id}/{action}"): Case(
        "POST",
        lambda o: f"/api/v1/support-requests/{o.support_request_id}/close",
        lambda _o, actor: {"acting_party_id": actor, "expected_version": 1},
    ),
    # Unpublished, so even the public view must not reveal that it exists.
    ("GET", "/api/v1/inventions/{invention_id}/public"): Case(
        "GET", lambda o: f"/api/v1/inventions/{o.invention_id}/public"
    ),
}


@pytest.fixture
async def owner(client: AsyncClient, sign_up, published_invention) -> AsyncIterator[Owner]:
    """Party A: an organization with a member manager, an operation and a pending invitation."""
    await sign_up(client, "owner@example.com", name="Owner")
    organization = (
        await client.post(
            "/api/v1/organizations", json={"name": "Owner Co", "kind": "company"}, headers={"Idempotency-Key": "o"}
        )
    ).json()
    me = (await client.put("/api/v1/me/context", json={"party_id": organization["party_id"]})).json()
    invitation = (
        await client.post(
            f"/api/v1/organizations/{organization['id']}/invitations",
            json={
                "acting_party_id": organization["party_id"],
                "email": "guest@example.com",
                "capabilities": ["schedule"],
            },
            headers={"Idempotency-Key": "i"},
        )
    ).json()
    mail = (await client.get("/api/v1/dev/mailbox", params={"email": "guest@example.com"})).json()
    invention = (
        await client.post(
            "/api/v1/inventions", json={"acting_party_id": organization["party_id"]}, headers={"Idempotency-Key": "inv"}
        )
    ).json()
    await client.put(
        f"/api/v1/inventions/{invention['id']}/draft",
        json={"acting_party_id": organization["party_id"], "expected_version": 1, "title": "Owner Co invention"},
        headers={"Idempotency-Key": "inv-draft"},
    )
    party = organization["party_id"]
    pdf = b"%PDF-1.4 owner co document"
    intent = (
        await client.post(
            "/api/v1/documents/upload-intents",
            json={
                "acting_party_id": party,
                "title": "Owner Co document",
                "kind": "evidence",
                "media_type": "application/pdf",
                "size_bytes": len(pdf),
            },
        )
    ).json()
    uploaded = (await client.put(intent["upload_url"], content=pdf)).json()
    spare = (
        await client.post(
            "/api/v1/documents/upload-intents",
            json={
                "acting_party_id": party,
                "title": "Owner Co spare",
                "kind": "other",
                "media_type": "application/pdf",
                "size_bytes": len(pdf),
            },
        )
    ).json()
    grant = (
        await client.post(
            f"/api/v1/documents/{uploaded['document_id']}/grants",
            json={
                "acting_party_id": party,
                "version": 1,
                "grantee_party_id": me["personal_party_id"],
                "purpose": "pitch",
            },
            headers={"Idempotency-Key": "grant"},
        )
    ).json()
    published = await published_invention(client, "Owner Co published invention")
    support = (
        await client.post(
            "/api/v1/support-requests",
            json={"acting_party_id": party, "invention_id": published["id"], "outcome": "Owner Co pilot"},
            headers={"Idempotency-Key": "support"},
        )
    ).json()
    yield Owner(
        organization_id=organization["id"],
        party_id=organization["party_id"],
        account_id=me["account"]["id"],
        operation_id=organization["operation_id"],
        invitation_id=invitation["id"],
        invitation_token=mail[0]["body"].rsplit("/", 1)[1],
        invention_id=invention["id"],
        document_id=uploaded["document_id"],
        intent_id=spare["intent_id"],
        grant_id=grant["id"],
        support_request_id=support["id"],
        published_invention_id=published["id"],
    )


def test_every_route_is_covered() -> None:
    """
    Condition:
    - The application's route table, as published in its OpenAPI contract.

    Expected:
    - Every route is either an isolation case or explicitly not a data route.
    """
    routes = {(method.upper(), path) for path, item in app.openapi()["paths"].items() for method in item}

    assert routes - NOT_DATA_ROUTES - set(ROUTES) == set()
    assert set(ROUTES) - routes == set()


@pytest.mark.parametrize("route", sorted(ROUTES), ids=lambda route: f"{route[0]} {route[1]}")
async def test_unrelated_party_sees_nothing(
    owner: Owner, new_client: Callable[[], AsyncClient], sign_up, route: tuple[str, str]
) -> None:
    """
    Condition:
    - An unrelated, signed-in party calls the route with party A's identifiers.

    Expected:
    - ``NOT_FOUND`` or an empty list, and none of A's names or identifiers in the answer.
    """
    case = ROUTES[route]
    async with new_client() as stranger:
        me = await sign_up(stranger, "stranger@example.com", name="Stranger")
        response = await stranger.request(
            case.method, case.path(owner), json=case.body(owner, me["active_party_id"]), headers=case.headers
        )

    assert response.status_code == 404 or (response.status_code == 200 and response.json() == []), response.text
    for secret in (
        "Owner Co",
        owner.organization_id,
        owner.party_id,
        owner.account_id,
        "guest@example.com",
        owner.invention_id,
        owner.document_id,
        "Owner Co document",
        owner.support_request_id,
        owner.published_invention_id,
    ):
        assert secret not in response.text
