"""An operator's case-file access is checked on each request."""

from collections.abc import Callable
from datetime import timedelta
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core import clock
from app.core.database import get_session_factory
from app.moderation.repository.sqlalchemy.models import OperatorFileGrantRecord, OperatorGrantRecord
from app.platform.repository.sqlalchemy.models import AuditEventRecord
from tests.integration.conftest import SignUp
from tests.integration.documents.test_documents import _run_worker, _upload, _version, text_pdf

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("clean_tables")]


async def test_case_file_checks_exact_grant_and_audits_denials(
    client: AsyncClient, sign_up: SignUp, new_client: Callable[[], AsyncClient]
) -> None:
    """
    Condition:
    - A scoped operator handles a report about a document owner.
    - A case-specific grant is issued and then expires.

    Expected:
    - Denials survive request rollback in the audit trail.
    - A fresh range request succeeds only while the exact grant is live.
    """
    owner = await sign_up(client, "document-owner@example.test")
    client.headers["X-Acting-Party"] = owner["active_party_id"]
    doc = await _upload(client, text_pdf())
    await _run_worker()
    version = await _version(doc["document_id"])
    async with new_client() as operator:
        actor = await sign_up(operator, "case-worker@example.test")
        account_id = UUID(actor["account"]["id"])
        async with get_session_factory()() as session:
            session.add(OperatorGrantRecord(account_id=account_id, scope="moderation"))
            await session.commit()
        report = await client.post(
            "/api/v1/reports",
            json={"acting_party_id": owner["active_party_id"], "expected_version": None, "reason": "Review requested"},
            headers={"Idempotency-Key": "file-report"},
        )
        case_id = report.json()["id"]
        path = f"/api/v1/operator/reports/{case_id}/documents/{doc['document_id']}/versions/1/content"
        assert (await client.get(path)).status_code == 404
        denied = await operator.get(path)
        assert denied.status_code == 403, denied.text
        async with get_session_factory()() as session:
            grant = OperatorFileGrantRecord(
                report_id=UUID(case_id),
                document_version_id=version.id,
                operator_account_id=account_id,
                purpose="Review the evidence",
                granted_by="local-admin",
                expires_at=clock.now() + timedelta(hours=1),
            )
            session.add(grant)
            await session.commit()
        served = await operator.get(path, headers={"Range": "bytes=0-4"})
        assert served.status_code == 206 and served.content == b"%PDF-"
        async with get_session_factory()() as session:
            current = await session.get(OperatorFileGrantRecord, grant.id)
            current.expires_at = clock.now() - timedelta(seconds=1)
            await session.commit()
        assert (await operator.get(path, headers={"Range": "bytes=0-4"})).status_code == 403

    async with get_session_factory()() as session:
        events = await session.scalars(select(AuditEventRecord).where(AuditEventRecord.subject_id == case_id))
        actions = [event.action for event in events]
        assert actions.count("report.file_denied") == 2
        assert actions.count("report.file_downloaded") == 1
