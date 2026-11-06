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
# creating one's own organization, invention, legal entity or opportunity.
NOT_DATA_ROUTES = {
    ("GET", "/health/live"),
    ("GET", "/health/ready"),
    ("GET", "/api/v1/capabilities"),
    ("POST", "/api/v1/auth/code"),
    ("POST", "/api/v1/auth/verify"),
    ("POST", "/api/v1/auth/sign-out"),
    ("GET", "/api/v1/me"),
    ("PATCH", "/api/v1/me"),
    # Settings are scoped to the session's active party; public profile redaction is tested in relationships.
    ("GET", "/api/v1/profiles/me"),
    ("PUT", "/api/v1/profiles/me"),
    ("GET", "/api/v1/profiles/{party_id}"),
    ("GET", "/api/v1/dev/mailbox"),
    # Development only: marks a party busy for browser tests, as another meeting would.
    ("POST", "/api/v1/dev/bookings"),
    ("POST", "/api/v1/organizations"),
    ("POST", "/api/v1/inventions"),
    ("POST", "/api/v1/legal-entities"),
    ("POST", "/api/v1/opportunities"),
    # Public by design: it reads only the projection, which never holds a draft or private text. The private-text
    # case is proven by ``test_discovery_reveals_no_private_text`` below.
    ("GET", "/api/v1/discovery"),
    # Demo mode only, and they hold labelled fictional accounts, never another party's data.
    ("GET", "/api/v1/demo/accounts"),
    ("POST", "/api/v1/demo/sign-in"),
    ("POST", "/api/v1/demo/reset"),
    ("POST", "/api/v1/reports"),
    ("POST", "/api/v1/privacy-requests"),
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
    funding_request_id: str = ""
    opportunity_id: str = ""
    match_run_id: str = ""
    brief_id: str = ""
    preflight_token: str = ""
    pitch_id: str = ""
    revision_item_id: str = ""
    report_id: str = ""
    privacy_request_id: str = ""
    task_id: str = ""
    notification_id: str = ""
    proposal_id: str = ""
    meeting_id: str = ""
    partnership_id: str = ""


@dataclass
class Case:
    """How to call one route against A's data."""

    method: str
    path: Callable[[Owner], str]
    body: Callable[[Owner, str], dict[str, Any] | None] = lambda _owner, _actor: None
    headers: dict[str, str] | None = None


RELATIONSHIP_VALUES = {"name": "Private summary", "scope": "Private scope", "start_date": "2026-12-01"}

ROUTES: dict[tuple[str, str], Case] = {
    ("GET", "/api/v1/reports"): Case("GET", lambda _o: "/api/v1/reports"),
    ("GET", "/api/v1/reports/{report_id}"): Case("GET", lambda o: f"/api/v1/reports/{o.report_id}"),
    ("GET", "/api/v1/operator/reports"): Case("GET", lambda _o: "/api/v1/operator/reports"),
    ("POST", "/api/v1/operator/reports/{report_id}/actions"): Case(
        "POST",
        lambda o: f"/api/v1/operator/reports/{o.report_id}/actions",
        lambda _o, actor: {"acting_party_id": actor, "expected_version": 1, "action": "START_REVIEW", "note": "Review"},
        {"Idempotency-Key": "isolation-review"},
    ),
    ("GET", "/api/v1/operator/reports/{report_id}/documents/{document_id}/versions/{number}/content"): Case(
        "GET",
        lambda o: f"/api/v1/operator/reports/{o.report_id}/documents/{o.document_id}/versions/1/content",
    ),
    ("GET", "/api/v1/privacy-requests"): Case("GET", lambda _o: "/api/v1/privacy-requests"),
    ("GET", "/api/v1/privacy-requests/{request_id}"): Case(
        "GET", lambda o: f"/api/v1/privacy-requests/{o.privacy_request_id}"
    ),
    ("GET", "/api/v1/privacy-requests/{request_id}/export"): Case(
        "GET", lambda o: f"/api/v1/privacy-requests/{o.privacy_request_id}/export"
    ),
    ("GET", "/api/v1/operator/privacy-requests"): Case("GET", lambda _o: "/api/v1/operator/privacy-requests"),
    ("POST", "/api/v1/operator/privacy-requests/{request_id}/fulfill"): Case(
        "POST",
        lambda o: f"/api/v1/operator/privacy-requests/{o.privacy_request_id}/fulfill",
        lambda _o, actor: {"acting_party_id": actor, "expected_version": 1},
        {"Idempotency-Key": "isolation-fulfill"},
    ),
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
        {"Idempotency-Key": "isolation-archive"},
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
    **{
        ("POST", f"/api/v1/support-requests/{{request_id}}/{action}"): Case(
            "POST",
            lambda o, action=action: f"/api/v1/support-requests/{o.support_request_id}/{action}",
            lambda _o, actor: {"acting_party_id": actor, "expected_version": 1},
            {"Idempotency-Key": f"isolation-support-{action}"},
        )
        for action in ("activate", "pause", "close")
    },
    ("GET", "/api/v1/legal-entities"): Case("GET", lambda _o: "/api/v1/legal-entities"),
    ("POST", "/api/v1/funding-requests"): Case(
        "POST",
        lambda _o: "/api/v1/funding-requests",
        lambda o, actor: {
            "acting_party_id": actor,
            "subject_type": "PROPOSED_ENTITY",
            "invention_ids": [o.published_invention_id],
        },
        {"Idempotency-Key": "isolation-funding"},
    ),
    ("GET", "/api/v1/funding-requests"): Case("GET", lambda _o: "/api/v1/funding-requests"),
    ("GET", "/api/v1/funding-requests/{request_id}"): Case(
        "GET", lambda o: f"/api/v1/funding-requests/{o.funding_request_id}"
    ),
    ("GET", "/api/v1/funding-requests/{request_id}/versions/{number}"): Case(
        "GET", lambda o: f"/api/v1/funding-requests/{o.funding_request_id}/versions/1"
    ),
    ("PUT", "/api/v1/funding-requests/{request_id}"): Case(
        "PUT",
        lambda o: f"/api/v1/funding-requests/{o.funding_request_id}",
        lambda _o, actor: {"acting_party_id": actor, "expected_version": 1, "subject_type": "PROPOSED_ENTITY"},
        {"Idempotency-Key": "isolation-funding-update"},
    ),
    **{
        ("POST", f"/api/v1/funding-requests/{{request_id}}/{action}"): Case(
            "POST",
            lambda o, action=action: f"/api/v1/funding-requests/{o.funding_request_id}/{action}",
            lambda _o, actor: {"acting_party_id": actor, "expected_version": 1},
            {"Idempotency-Key": f"isolation-funding-{action}"},
        )
        for action in ("activate", "pause", "close")
    },
    # The owner has no profile and only a draft opportunity, so these public reads must not reveal that either exists.
    ("GET", "/api/v1/partners/{party_id}"): Case("GET", lambda o: f"/api/v1/partners/{o.party_id}"),
    ("PUT", "/api/v1/partners/{party_id}"): Case(
        "PUT",
        lambda o: f"/api/v1/partners/{o.party_id}",
        lambda _o, actor: {"acting_party_id": actor, "expected_version": None, "thesis": "x"},
        {"Idempotency-Key": "isolation-partner"},
    ),
    ("POST", "/api/v1/partners/{party_id}/handoffs"): Case(
        "POST",
        lambda o: f"/api/v1/partners/{o.party_id}/handoffs",
        lambda _o, actor: {"acting_party_id": actor},
        {"Idempotency-Key": "isolation-handoff"},
    ),
    ("GET", "/api/v1/opportunities"): Case("GET", lambda _o: "/api/v1/opportunities"),
    ("GET", "/api/v1/opportunities/{opportunity_id}"): Case(
        "GET", lambda o: f"/api/v1/opportunities/{o.opportunity_id}"
    ),
    ("GET", "/api/v1/opportunities/{opportunity_id}/versions/{number}"): Case(
        "GET", lambda o: f"/api/v1/opportunities/{o.opportunity_id}/versions/1"
    ),
    ("PUT", "/api/v1/opportunities/{opportunity_id}"): Case(
        "PUT",
        lambda o: f"/api/v1/opportunities/{o.opportunity_id}",
        lambda _o, actor: {"acting_party_id": actor, "expected_version": 1, "title": "x"},
        {"Idempotency-Key": "isolation-opportunity-save"},
    ),
    **{
        ("POST", f"/api/v1/opportunities/{{opportunity_id}}/{action}"): Case(
            "POST",
            lambda o, action=action: f"/api/v1/opportunities/{o.opportunity_id}/{action}",
            lambda _o, actor: {"acting_party_id": actor, "expected_version": 1},
            {"Idempotency-Key": f"isolation-opportunity-{action}"},
        )
        for action in ("activate", "pause", "close")
    },
    ("GET", "/api/v1/saved-items"): Case("GET", lambda _o: "/api/v1/saved-items"),
    ("GET", "/api/v1/discovery-feedback"): Case("GET", lambda _o: "/api/v1/discovery-feedback"),
    **{
        (method, f"/api/v1/{path}/{{subject_type}}/{{subject_id}}"): Case(
            method,
            lambda o, path=path: f"/api/v1/{path}/INVENTION/{o.invention_id}",
            lambda _o, actor: {"acting_party_id": actor},
        )
        for method in ("PUT", "DELETE")
        for path in ("saved-items", "discovery-feedback")
    },
    ("POST", "/api/v1/matches"): Case(
        "POST",
        lambda _o: "/api/v1/matches",
        lambda o, actor: {
            "acting_party_id": actor,
            "source_type": "SUPPORT_REQUEST",
            "source_id": o.support_request_id,
        },
        {"Idempotency-Key": "isolation-match"},
    ),
    ("GET", "/api/v1/match-runs/{run_id}"): Case("GET", lambda o: f"/api/v1/match-runs/{o.match_run_id}"),
    ("POST", "/api/v1/pitches/preflight"): Case(
        "POST",
        lambda _o: "/api/v1/pitches/preflight",
        lambda o, actor: {
            "acting_party_id": actor,
            "source_type": "SUPPORT_REQUEST",
            "source_id": o.support_request_id,
            "opportunity_id": o.opportunity_id,
        },
    ),
    ("GET", "/api/v1/briefs/{brief_id}"): Case("GET", lambda o: f"/api/v1/briefs/{o.brief_id}"),
    ("POST", "/api/v1/briefs/{brief_id}/summary"): Case("POST", lambda o: f"/api/v1/briefs/{o.brief_id}/summary"),
    ("GET", "/api/v1/briefs/{brief_id}/export"): Case("GET", lambda o: f"/api/v1/briefs/{o.brief_id}/export"),
    ("POST", "/api/v1/pitches"): Case(
        "POST",
        lambda _o: "/api/v1/pitches",
        lambda o, actor: {"acting_party_id": actor, "preflight_token": o.preflight_token, "brief": "x", "files": []},
        {"Idempotency-Key": "isolation-pitch"},
    ),
    ("GET", "/api/v1/pitches"): Case("GET", lambda _o: "/api/v1/pitches?box=incoming"),
    ("GET", "/api/v1/pitches/{pitch_id}"): Case("GET", lambda o: f"/api/v1/pitches/{o.pitch_id}"),
    **{
        ("POST", f"/api/v1/pitches/{{pitch_id}}/{action}"): Case(
            "POST",
            lambda o, action=action: f"/api/v1/pitches/{o.pitch_id}/{action}",
            lambda _o, actor, body=body: {"acting_party_id": actor, "expected_version": 2, **body},
            {"Idempotency-Key": f"isolation-{action}"},
        )
        for action, body in {
            "begin-review": {},
            "decisions": {"submission": 1, "decision": "APPROVE"},
            "revision-rounds": {
                "submission": 1,
                "items": [{"category": "x", "question": "x", "reason": "x", "required": False}],
            },
            "resubmit": {},
            "withdraw": {},
            "close": {"reason": "x"},
        }.items()
    },
    ("GET", "/api/v1/pitches/{pitch_id}/messages"): Case("GET", lambda o: f"/api/v1/pitches/{o.pitch_id}/messages"),
    ("POST", "/api/v1/pitches/{pitch_id}/messages"): Case(
        "POST",
        lambda o: f"/api/v1/pitches/{o.pitch_id}/messages",
        lambda _o, actor: {"acting_party_id": actor, "text": "x"},
        {"Idempotency-Key": "isolation-message"},
    ),
    ("GET", "/api/v1/pitches/{pitch_id}/tasks"): Case("GET", lambda o: f"/api/v1/pitches/{o.pitch_id}/tasks"),
    ("POST", "/api/v1/pitches/{pitch_id}/tasks"): Case(
        "POST",
        lambda o: f"/api/v1/pitches/{o.pitch_id}/tasks",
        lambda o, actor: {"acting_party_id": actor, "title": "x", "owner_party_id": actor},
        {"Idempotency-Key": "isolation-task"},
    ),
    ("POST", "/api/v1/tasks/{task_id}/complete"): Case(
        "POST",
        lambda o: f"/api/v1/tasks/{o.task_id}/complete",
        lambda _o, actor: {"acting_party_id": actor, "expected_version": 1},
        {"Idempotency-Key": "isolation-complete"},
    ),
    ("GET", "/api/v1/pitches/{pitch_id}/next-action"): Case(
        "GET", lambda o: f"/api/v1/pitches/{o.pitch_id}/next-action"
    ),
    ("GET", "/api/v1/me/queue"): Case("GET", lambda _o: "/api/v1/me/queue"),
    ("GET", "/api/v1/pitches/{pitch_id}/schedule"): Case("GET", lambda o: f"/api/v1/pitches/{o.pitch_id}/schedule"),
    ("POST", "/api/v1/pitches/{pitch_id}/schedule-proposals"): Case(
        "POST",
        lambda o: f"/api/v1/pitches/{o.pitch_id}/schedule-proposals",
        lambda _o, actor: {
            "acting_party_id": actor,
            "slots": ["2030-01-01T09:00:00Z", "2030-01-01T11:00:00Z"],
            "minutes": 60,
            "time_zone": "Asia/Jakarta",
            "agenda": "x",
        },
        {"Idempotency-Key": "isolation-propose"},
    ),
    ("POST", "/api/v1/schedule-proposals/{proposal_id}/accept"): Case(
        "POST",
        lambda o: f"/api/v1/schedule-proposals/{o.proposal_id}/accept",
        lambda o, actor: {"acting_party_id": actor, "slot_id": o.proposal_id, "expected_version": 1},
        {"Idempotency-Key": "isolation-accept"},
    ),
    ("POST", "/api/v1/schedule-proposals/{proposal_id}/cancel"): Case(
        "POST",
        lambda o: f"/api/v1/schedule-proposals/{o.proposal_id}/cancel",
        lambda _o, actor: {"acting_party_id": actor, "expected_version": 1},
        {"Idempotency-Key": "isolation-cancel-proposal"},
    ),
    ("POST", "/api/v1/meetings/{meeting_id}/cancel"): Case(
        "POST",
        lambda o: f"/api/v1/meetings/{o.meeting_id}/cancel",
        lambda _o, actor: {"acting_party_id": actor, "expected_version": 1},
        {"Idempotency-Key": "isolation-cancel-meeting"},
    ),
    ("POST", "/api/v1/meetings/{meeting_id}/outcome"): Case(
        "POST",
        lambda o: f"/api/v1/meetings/{o.meeting_id}/outcome",
        lambda _o, actor: {"acting_party_id": actor, "result": "COMPLETED"},
        {"Idempotency-Key": "isolation-outcome"},
    ),
    ("GET", "/api/v1/meetings/{meeting_id}/calendar.ics"): Case(
        "GET", lambda o: f"/api/v1/meetings/{o.meeting_id}/calendar.ics"
    ),
    ("GET", "/api/v1/notifications"): Case("GET", lambda _o: "/api/v1/notifications"),
    ("PUT", "/api/v1/notifications/{notification_id}/read"): Case(
        "PUT", lambda o: f"/api/v1/notifications/{o.notification_id}/read"
    ),
    ("PUT", "/api/v1/pitches/{pitch_id}/revision-items/{item_id}/answer"): Case(
        "PUT",
        lambda o: f"/api/v1/pitches/{o.pitch_id}/revision-items/{o.revision_item_id}/answer",
        lambda _o, actor: {"acting_party_id": actor, "response": "CAN"},
    ),
    ("PUT", "/api/v1/pitches/{pitch_id}/revision-items/{item_id}/review"): Case(
        "PUT",
        lambda o: f"/api/v1/pitches/{o.pitch_id}/revision-items/{o.revision_item_id}/review",
        lambda _o, actor: {"acting_party_id": actor, "expected_version": 1, "result": "ACCEPTED"},
    ),
    ("GET", "/api/v1/pitches/{pitch_id}/partnership-options"): Case(
        "GET", lambda o: f"/api/v1/pitches/{o.pitch_id}/partnership-options"
    ),
    ("GET", "/api/v1/pitches/{pitch_id}/partnership"): Case(
        "GET", lambda o: f"/api/v1/pitches/{o.pitch_id}/partnership"
    ),
    ("POST", "/api/v1/pitches/{pitch_id}/partnerships"): Case(
        "POST",
        lambda o: f"/api/v1/pitches/{o.pitch_id}/partnerships",
        lambda _o, actor: {
            "acting_party_id": actor,
            "type": "PROJECT",
            "values": RELATIONSHIP_VALUES,
            "ceiling": ["name"],
        },
        {"Idempotency-Key": "isolation-partnership"},
    ),
    ("GET", "/api/v1/partnerships/{partnership_id}"): Case("GET", lambda o: f"/api/v1/partnerships/{o.partnership_id}"),
    ("POST", "/api/v1/partnerships/{partnership_id}/corrections"): Case(
        "POST",
        lambda o: f"/api/v1/partnerships/{o.partnership_id}/corrections",
        lambda _o, actor: {"acting_party_id": actor, "version": 1, "values": RELATIONSHIP_VALUES},
        {"Idempotency-Key": "isolation-correction"},
    ),
    ("POST", "/api/v1/partnerships/{partnership_id}/confirmations"): Case(
        "POST",
        lambda o: f"/api/v1/partnerships/{o.partnership_id}/confirmations",
        lambda _o, actor: {"acting_party_id": actor, "version": 1, "checksum": "0" * 64},
        {"Idempotency-Key": "isolation-confirmation"},
    ),
    ("POST", "/api/v1/partnerships/{partnership_id}/decline"): Case(
        "POST",
        lambda o: f"/api/v1/partnerships/{o.partnership_id}/decline",
        lambda _o, actor: {"acting_party_id": actor, "version": 1},
        {"Idempotency-Key": "isolation-decline"},
    ),
    ("POST", "/api/v1/partnerships/{partnership_id}/restrictions"): Case(
        "POST",
        lambda o: f"/api/v1/partnerships/{o.partnership_id}/restrictions",
        lambda _o, actor: {"acting_party_id": actor, "field": "name"},
        {"Idempotency-Key": "isolation-restriction"},
    ),
    ("POST", "/api/v1/partnerships/{partnership_id}/request-review"): Case(
        "POST",
        lambda o: f"/api/v1/partnerships/{o.partnership_id}/request-review",
        lambda _o, actor: {"acting_party_id": actor},
        {"Idempotency-Key": "isolation-review"},
    ),
    # Unpublished, so even the public view must not reveal that it exists.
    ("GET", "/api/v1/inventions/{invention_id}/public"): Case(
        "GET", lambda o: f"/api/v1/inventions/{o.invention_id}/public"
    ),
}


async def _approve_and_schedule(
    client: AsyncClient, partner: AsyncClient, party: str, partner_party: str, pitch_id: str
) -> dict[str, str]:
    """Advance the fixture through revision, approval, scheduling and a relationship proposal."""
    from datetime import timedelta  # noqa: PLC0415

    from app.core import clock  # noqa: PLC0415

    pitch = (await client.get(f"/api/v1/pitches/{pitch_id}")).json()
    item = pitch["rounds"][0]["items"][0]["id"]
    await client.put(
        f"/api/v1/pitches/{pitch_id}/revision-items/{item}/answer", json={"acting_party_id": party, "response": "CAN"}
    )
    resubmitted = await client.post(
        f"/api/v1/pitches/{pitch_id}/resubmit",
        json={"acting_party_id": party, "expected_version": pitch["version"]},
        headers={"Idempotency-Key": "resubmit"},
    )
    assert resubmitted.status_code == 200, resubmitted.text
    approved = await partner.post(
        f"/api/v1/pitches/{pitch_id}/decisions",
        json={
            "acting_party_id": partner_party,
            "expected_version": resubmitted.json()["version"],
            "submission": 2,
            "decision": "APPROVE",
        },
        headers={"Idempotency-Key": "approve"},
    )
    assert approved.status_code == 200, approved.text
    start = (clock.now() + timedelta(days=2)).replace(minute=0, second=0, microsecond=0)

    async def offer(slots: list, key: str, **body: str) -> dict:
        made = await partner.post(
            f"/api/v1/pitches/{pitch_id}/schedule-proposals",
            json={
                "acting_party_id": partner_party,
                "slots": [slot.isoformat() for slot in slots],
                "minutes": 60,
                "time_zone": "Asia/Jakarta",
                "agenda": "Agenda",
                **body,
            },
            headers={"Idempotency-Key": key},
        )
        assert made.status_code == 201, made.text
        return made.json()

    first = await offer([start, start + timedelta(hours=2)], "offer")
    meeting = await client.post(
        f"/api/v1/schedule-proposals/{first['id']}/accept",
        json={"acting_party_id": party, "slot_id": first["slots"][0]["id"], "expected_version": first["version"]},
        headers={"Idempotency-Key": "accept"},
    )
    assert meeting.status_code == 200, meeting.text
    later = start + timedelta(days=1)
    pending = await offer([later, later + timedelta(hours=2)], "replace", replaces_meeting_id=meeting.json()["id"])
    meeting_id = meeting.json()["id"]
    with clock.frozen(start + timedelta(hours=2)):
        for actor, actor_party in ((client, party), (partner, partner_party)):
            outcome = await actor.post(
                f"/api/v1/meetings/{meeting_id}/outcome",
                json={"acting_party_id": actor_party, "result": "COMPLETED"},
                headers={"Idempotency-Key": "owner-outcome"},
            )
            assert outcome.status_code == 200, outcome.text
    relationship = await client.post(
        f"/api/v1/pitches/{pitch_id}/partnerships",
        json={"acting_party_id": party, "type": "PROJECT", "values": RELATIONSHIP_VALUES, "ceiling": ["name"]},
        headers={"Idempotency-Key": "owner-partnership"},
    )
    assert relationship.status_code == 201, relationship.text
    return {"proposal_id": pending["id"], "meeting_id": meeting_id, "partnership_id": relationship.json()["id"]}


async def _pitch_to_a_partner(
    new_client: Callable[[], AsyncClient], sign_up, client: AsyncClient, party: str, support_id: str
) -> dict[str, str]:
    """Party A preflights its support request against another partner's mandate and sends a pitch."""
    from tests.factories.recipients import OPPORTUNITIES, PROFILES, create_opportunity, move_opportunity, save_profile  # noqa: PLC0415

    async with new_client() as partner:
        me = await sign_up(partner, "partner@example.com", persona="mitra", name="Partner")
        partner.headers["X-Acting-Party"] = me["active_party_id"]
        await save_profile(partner, me["active_party_id"], PROFILES["A"]["content"])
        created = (await create_opportunity(partner, me["active_party_id"], OPPORTUNITIES["A3"]["content"])).json()
        await move_opportunity(partner, me["active_party_id"], created["id"], "activate", 1)
        checked = (
            await client.post(
                "/api/v1/pitches/preflight",
                json={
                    "acting_party_id": party,
                    "source_type": "SUPPORT_REQUEST",
                    "source_id": support_id,
                    "opportunity_id": created["id"],
                },
            )
        ).json()
        pitch = await client.post(
            "/api/v1/pitches",
            json={"acting_party_id": party, "preflight_token": checked["token"], "brief": "Brief", "files": []},
            headers={"Idempotency-Key": "pitch"},
        )
        assert pitch.status_code == 201, pitch.text
        item = {"category": "Anggaran", "question": "Berapa?", "reason": "Perlu.", "required": True}
        opened = await partner.post(
            f"/api/v1/pitches/{pitch.json()['pitch_id']}/revision-rounds",
            json={"acting_party_id": me["active_party_id"], "expected_version": 1, "submission": 1, "items": [item]},
            headers={"Idempotency-Key": "round"},
        )
        assert opened.status_code == 201, opened.text
        task = await partner.post(
            f"/api/v1/pitches/{pitch.json()['pitch_id']}/tasks",
            json={"acting_party_id": me["active_party_id"], "title": "Rincian", "owner_party_id": party},
            headers={"Idempotency-Key": "task"},
        )
        assert task.status_code == 201, task.text
        scheduled = await _approve_and_schedule(client, partner, party, me["active_party_id"], pitch.json()["pitch_id"])
    read = (await client.get(f"/api/v1/pitches/{pitch.json()['pitch_id']}")).json()
    import app.discussion.service.notifications  # noqa: F401, PLC0415 - registers the notification consumers
    from app.core.database import get_session_factory  # noqa: PLC0415
    from app.worker.loop import dispatch_events  # noqa: PLC0415
    from app.worker.registry import registry  # noqa: PLC0415

    while await dispatch_events(get_session_factory(), registry):
        pass
    notices = (await client.get("/api/v1/notifications")).json()
    return {
        "brief_id": checked["brief"]["id"],
        "preflight_token": checked["token"],
        "pitch_id": pitch.json()["pitch_id"],
        "revision_item_id": read["rounds"][0]["items"][0]["id"],
        "task_id": task.json()["id"],
        "notification_id": notices[0]["id"],
        **scheduled,
    }


@pytest.fixture
async def owner(
    client: AsyncClient, new_client: Callable[[], AsyncClient], sign_up, published_invention
) -> AsyncIterator[Owner]:
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
    funding = (
        await client.post(
            "/api/v1/funding-requests",
            json={"acting_party_id": party, "subject_type": "PROPOSED_ENTITY", "invention_ids": [published["id"]]},
            headers={"Idempotency-Key": "funding"},
        )
    ).json()
    opportunity = (
        await client.post(
            "/api/v1/opportunities",
            json={"acting_party_id": party, "title": "Owner Co draft opportunity"},
            headers={"Idempotency-Key": "opportunity"},
        )
    ).json()
    match_run = (
        await client.post(
            "/api/v1/matches",
            json={"acting_party_id": party, "source_type": "SUPPORT_REQUEST", "source_id": support["id"]},
            headers={"Idempotency-Key": "match"},
        )
    ).json()
    pitch = await _pitch_to_a_partner(new_client, sign_up, client, party, support["id"])
    report = await client.post(
        "/api/v1/reports",
        json={"acting_party_id": party, "expected_version": None, "reason": "Owner Co private reason"},
        headers={"Idempotency-Key": "owner-report"},
    )
    assert report.status_code == 201, report.text
    export = await client.post(
        "/api/v1/privacy-requests",
        json={"acting_party_id": party, "expected_version": None, "kind": "EXPORT"},
        headers={"Idempotency-Key": "owner-export"},
    )
    assert export.status_code == 201, export.text
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
        funding_request_id=funding["id"],
        opportunity_id=opportunity["id"],
        match_run_id=match_run["run_id"],
        report_id=report.json()["id"],
        privacy_request_id=export.json()["id"],
        **pitch,
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
        owner.funding_request_id,
        owner.opportunity_id,
        owner.match_run_id,
        owner.brief_id,
        owner.pitch_id,
        owner.report_id,
        owner.privacy_request_id,
        owner.partnership_id,
    ):
        assert secret not in response.text


async def test_discovery_reveals_no_private_text(owner: Owner, new_client: Callable[[], AsyncClient], sign_up) -> None:
    """
    Condition:
    - Party A holds a draft invention and a published one, and every consumer has run (SC-001). Private notes are
      proven unsearchable in ``tests/integration/discovery``.

    Expected:
    - A stranger's search finds the published title only, never the draft, its id or A's other records.
    """
    import app.discovery.service.projection  # noqa: F401, PLC0415 - registers the projection consumers
    from app.core.database import get_session_factory  # noqa: PLC0415
    from app.worker.loop import dispatch_events  # noqa: PLC0415
    from app.worker.registry import registry  # noqa: PLC0415

    while await dispatch_events(get_session_factory(), registry):
        pass
    async with new_client() as stranger:
        await sign_up(stranger, "stranger@example.com", name="Stranger")
        everything = await stranger.get("/api/v1/discovery")
        draft = await stranger.get("/api/v1/discovery", params={"q": "Owner Co invention"})

    found = [item["title"] for group in draft.json()["sections"] for item in group["items"]]
    assert found == ["Owner Co published invention"]
    assert "Owner Co published invention" in everything.text
    for secret in (owner.invention_id, owner.support_request_id, owner.document_id, "Owner Co document"):
        assert secret not in everything.text
