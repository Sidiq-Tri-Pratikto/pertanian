"""The local operator grants have a bounded scope and an audit trail."""

from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.database import get_session_factory
from app.moderation.__main__ import change_grant, parser
from app.platform.repository.sqlalchemy.models import AuditEventRecord
from tests.integration.conftest import SignUp

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("clean_tables")]


async def test_command_grants_and_withdraws_operator_scope(client: AsyncClient, sign_up: SignUp) -> None:
    """
    Condition:
    - A local administrator grants and withdraws one account's moderation scope.

    Expected:
    - Operator access follows the live grant and both changes leave audit records.
    """
    me = await sign_up(client, "grant-recipient@example.test")
    account_id = me["account"]["id"]
    async with get_session_factory()() as session, session.begin():
        grant = await change_grant(session, parser().parse_args(["grant-operator", account_id]))
    assert (await client.get("/api/v1/operator/reports")).status_code == 200
    async with get_session_factory()() as session, session.begin():
        await change_grant(session, parser().parse_args(["revoke-operator", str(grant)]))
    assert (await client.get("/api/v1/operator/reports")).status_code == 404
    async with get_session_factory()() as session:
        rows = await session.scalars(select(AuditEventRecord).where(AuditEventRecord.subject_id == str(grant)))
        assert {row.action for row in rows} == {"operator.granted", "operator.revoked"}
        assert all(row.subject_id == str(UUID(str(grant))) for row in rows)
