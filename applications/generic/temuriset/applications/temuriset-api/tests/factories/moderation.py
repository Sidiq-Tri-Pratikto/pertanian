"""Moderation decisions made through the same report and operator routes as the product."""

from uuid import UUID

from httpx import AsyncClient

from app.core.database import get_session_factory
from app.moderation.repository.sqlalchemy.models import OperatorGrantRecord
from tests.integration.conftest import SignUp


async def grant_operator(client: AsyncClient, sign_up: SignUp) -> str:
    """Sign up a scoped operator and return their acting party."""
    actor = await sign_up(client, "integration-operator@example.test")
    async with get_session_factory()() as session, session.begin():
        session.add(OperatorGrantRecord(account_id=UUID(actor["account"]["id"]), scope="moderation"))
    return actor["active_party_id"]


async def suspend_listing(client: AsyncClient, party: str, kind: str, subject_id: str) -> dict:
    """File a report and suspend the listing in that case."""
    filed = await client.post(
        "/api/v1/reports",
        json={
            "acting_party_id": party,
            "expected_version": None,
            "subject_type": kind,
            "subject_id": subject_id,
            "reason": "Perlu ditinjau",
        },
        headers={"Idempotency-Key": f"report-{subject_id}"},
    )
    assert filed.status_code == 201, filed.text
    queue = await client.get("/api/v1/operator/reports")
    assert queue.status_code == 200, queue.text
    report = next(item for item in queue.json() if item["id"] == filed.json()["id"])
    return await change_suspension(client, party, report, "SUSPEND_LISTING")


async def change_suspension(client: AsyncClient, party: str, report: dict, action: str) -> dict:
    """Apply a suspension decision to the current case version."""
    changed = await client.post(
        f"/api/v1/operator/reports/{report['id']}/actions",
        json={"acting_party_id": party, "expected_version": report["version"], "action": action, "note": "Ditinjau"},
        headers={"Idempotency-Key": f"{action}-{report['id']}"},
    )
    assert changed.status_code == 200, changed.text
    return changed.json()
