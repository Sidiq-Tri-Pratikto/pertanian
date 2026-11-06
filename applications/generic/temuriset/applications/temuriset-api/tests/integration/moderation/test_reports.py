"""Private reporting and scoped operator actions through the HTTP API."""

from collections.abc import Callable
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.database import get_session_factory
from app.moderation.repository.sqlalchemy.models import OperatorGrantRecord
from app.platform.repository.sqlalchemy.models import AuditEventRecord
from tests.integration.conftest import SignUp

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("clean_tables")]


async def test_report_is_private_and_actions_are_audited(
    client: AsyncClient, sign_up: SignUp, new_client: Callable[[], AsyncClient]
) -> None:
    """
    Condition:
    - An impersonation report names an opaque subject and a private reason.
    - A separate account holds a moderation grant.

    Expected:
    - The reporter sees the case status, strangers cannot see the report, and operator actions are audited.
    - Replaying the same intent has one effect, and a stale action cannot overwrite the case.
    """
    me = await sign_up(client, "reporter@example.test")
    body = {
        "acting_party_id": me["active_party_id"],
        "expected_version": None,
        "category": "IMPERSONATION",
        "subject_type": "PITCH",
        "subject_id": str(uuid4()),
        "reason": "A private reason",
    }
    report = await client.post("/api/v1/reports", json=body, headers={"Idempotency-Key": "report"})
    assert report.status_code == 201, report.text
    case = report.json()
    case_id = case["id"]
    assert case["case_number"] and case["status"] == "RECEIVED"
    assert "reason" not in case and "actions" not in case
    assert (await client.get("/api/v1/operator/reports")).status_code == 404

    async with new_client() as operator:
        operator_me = await sign_up(operator, "operator@example.test")
        assert (await operator.get(f"/api/v1/reports/{case_id}")).status_code == 404
        async with get_session_factory()() as session:
            session.add(OperatorGrantRecord(account_id=UUID(operator_me["account"]["id"]), scope="moderation"))
            await session.commit()
        queue = await operator.get("/api/v1/operator/reports")
        assert queue.status_code == 200, queue.text
        version = queue.json()[0]["version"]
        action = {
            "acting_party_id": operator_me["active_party_id"],
            "expected_version": version,
            "action": "START_REVIEW",
            "note": "Evidence received",
        }
        url = f"/api/v1/operator/reports/{case_id}/actions"
        headers = {"Idempotency-Key": "review"}
        applied = await operator.post(url, json=action, headers=headers)
        assert applied.status_code == 200, applied.text
        replayed = await operator.post(url, json=action, headers=headers)
        assert replayed.json() == applied.json()
        assert replayed.headers["Idempotent-Replayed"] == "true"
        changed = {**action, "note": "A different intent"}
        conflict = await operator.post(url, json=changed, headers=headers)
        assert conflict.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"
        stale = await operator.post(url, json=action, headers={"Idempotency-Key": "stale"})
        assert stale.json()["error"]["code"] == "STALE_VERSION"

    current = (await client.get(f"/api/v1/reports/{case_id}")).json()
    assert current["status"] == "IN_REVIEW"
    assert "Evidence received" not in str(current)
    async with get_session_factory()() as session:
        events = list(await session.scalars(select(AuditEventRecord).where(AuditEventRecord.subject_id == case_id)))
        assert [event.action for event in events].count("report.start_review") == 1
        assert "Evidence received" not in str([event.detail for event in events])
