"""Privacy request ownership and generated retention answers."""

import asyncio
from collections.abc import Callable

import pytest
from httpx import AsyncClient

from tests.integration.conftest import SignUp

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("clean_tables")]


async def test_privacy_exports_and_deletion_answers_are_private(
    client: AsyncClient, sign_up: SignUp, new_client: Callable[[], AsyncClient]
) -> None:
    """
    Condition:
    - A requester creates both kinds of privacy request.

    Expected:
    - An initial deletion response distinguishes planned removals and retained categories.
    - The export includes current requester data and a stranger sees neither record.
    """
    me = await sign_up(client, "private-requester@example.test")
    common = {"acting_party_id": me["active_party_id"], "expected_version": None}
    deleted = await client.post(
        "/api/v1/privacy-requests",
        json={**common, "kind": "DELETION"},
        headers={"Idempotency-Key": "deletion"},
    )
    assert deleted.status_code == 201, deleted.text
    deletion = deleted.json()
    assert deletion["status"] == "RECEIVED" and deletion["policy_version"]
    assert deletion["answer"]["removed"] == []
    assert deletion["answer"]["to_remove"]
    assert all(item["reason"] and item["period"] for item in deletion["answer"]["retained"])
    assert "tidak dapat ditarik kembali" in deletion["answer"]["notice"]
    duplicate = await client.post(
        "/api/v1/privacy-requests",
        json={**common, "kind": "DELETION"},
        headers={"Idempotency-Key": "another-deletion"},
    )
    assert duplicate.status_code == 409

    exported = await client.post(
        "/api/v1/privacy-requests",
        json={**common, "kind": "EXPORT"},
        headers={"Idempotency-Key": "export"},
    )
    assert exported.status_code == 201, exported.text
    path = f"/api/v1/privacy-requests/{exported.json()['id']}/export"
    download = await client.get(path)
    assert download.status_code == 200, download.text
    assert download.headers["Cache-Control"] == "private, no-store"
    assert download.json()["account"]["email"] == "private-requester@example.test"
    assert "session" not in download.json()
    async with new_client() as stranger:
        await sign_up(stranger, "private-stranger@example.test")
        assert (await stranger.get(path)).status_code == 404
        assert (await stranger.get(f"/api/v1/privacy-requests/{deletion['id']}")).status_code == 404


@pytest.mark.parametrize("mail_mode", ["development", "disabled"])
async def test_deletion_waits_for_the_worker_and_preserves_audit(
    client: AsyncClient,
    sign_up: SignUp,
    new_client: Callable[[], AsyncClient],
    monkeypatch: pytest.MonkeyPatch,
    mail_mode: str,
) -> None:
    """
    Condition:
    - A scoped operator approves a deletion containing one document.

    Expected:
    - The API reports processing while bytes exist. The worker removes the bytes,
      records an accurate outcome, and leaves the audit trail intact.
    """
    from uuid import UUID

    from sqlalchemy import select, update

    from app.core import clock
    from app.core.database import get_session_factory
    from app.identity.repository.sqlalchemy.models import MailboxMessageRecord
    from app.moderation.repository.sqlalchemy.models import (
        OperatorGrantRecord,
        PrivacyRequestRecord,
        RetentionHoldRecord,
    )
    from app.platform.repository.sqlalchemy.models import AuditEventRecord, JobRecord
    from tests.integration.documents.test_documents import _run_worker, _upload, _version, text_pdf

    me = await sign_up(client, "to-erase@example.test")
    client.headers["X-Acting-Party"] = me["active_party_id"]
    uploaded = await _upload(client, text_pdf())
    await _run_worker()
    version = await _version(uploaded["document_id"])
    response = await client.post(
        "/api/v1/privacy-requests",
        json={"acting_party_id": me["active_party_id"], "expected_version": None, "kind": "DELETION"},
        headers={"Idempotency-Key": "delete-me"},
    )
    request_id = response.json()["id"]
    assert "public_listings" in {item["key"] for item in response.json()["answer"]["to_remove"]}
    async with get_session_factory()() as session, session.begin():
        session.add(
            RetentionHoldRecord(
                account_id=UUID(me["account"]["id"]),
                category_key="public_listings",
                reason="Catatan masih diperlukan untuk audit.",
                period="Sampai audit selesai",
            )
        )
    async with new_client() as operator:
        actor = await sign_up(operator, "delete-operator@example.test")
        async with get_session_factory()() as session, session.begin():
            session.add(OperatorGrantRecord(account_id=UUID(actor["account"]["id"]), scope="moderation"))
        path = f"/api/v1/operator/privacy-requests/{request_id}/fulfill"
        body = {"acting_party_id": actor["active_party_id"], "expected_version": 1}
        competing = await asyncio.gather(
            operator.post(path, json=body, headers={"Idempotency-Key": "fulfill-1"}),
            operator.post(path, json=body, headers={"Idempotency-Key": "fulfill-2"}),
        )
        assert sorted(item.status_code for item in competing) == [200, 409]
        result = next(item for item in competing if item.status_code == 200)
        assert next(item for item in competing if item.status_code == 409).json()["error"]["code"] == "STALE_VERSION"
        receipt = result.json()
        assert receipt["status"] == "PROCESSING"
        assert any(
            item["key"] == "public_listings" and item["reason"] == "Catatan masih diperlukan untuk audit."
            for item in receipt["answer"]["retained"]
        )
        assert "private_documents" not in {item["key"] for item in receipt["answer"]["removed"]}
        replay = await operator.post(
            path, json=body, headers={"Idempotency-Key": result.request.headers["Idempotency-Key"]}
        )
        assert replay.headers["Idempotent-Replayed"] == "true"
        conflict = await operator.post(
            path,
            json={**body, "expected_version": 2},
            headers={"Idempotency-Key": result.request.headers["Idempotency-Key"]},
        )
        assert conflict.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"
        assert (await client.get("/api/v1/me")).status_code == 401

    from app.core.settings import get_settings
    from app.documents.service.storage_service import LocalStorage

    path = LocalStorage(get_settings().storage_path).local_path(version.storage_key)
    assert path.exists()

    async def unavailable(_storage: LocalStorage, _key: str) -> None:
        raise OSError("storage is unavailable")

    with monkeypatch.context() as patch:
        patch.setattr(LocalStorage, "delete", unavailable)
        await _run_worker()

    assert path.exists()
    async with get_session_factory()() as session, session.begin():
        pending = await session.get(PrivacyRequestRecord, UUID(request_id))
        assert pending is not None and pending.status == "PROCESSING"
        assert pending.answer["removed"] == []
        await session.execute(
            update(JobRecord).where(JobRecord.kind == "documents.erase").values(run_after=clock.now())
        )

    monkeypatch.setattr(get_settings(), "mailbox_adapter", mail_mode)
    await _run_worker()
    assert not path.exists()
    async with get_session_factory()() as session:
        row = await session.get(PrivacyRequestRecord, UUID(request_id))
        assert row is not None and row.status == "FULFILLED"
        assert "private_documents" in {item["key"] for item in row.answer["removed"]}
        events = await session.scalars(select(AuditEventRecord).where(AuditEventRecord.subject_id == request_id))
        actions = [event.action for event in events]
        assert actions.count("privacy.fulfilled") == 1
        assert ("privacy.notification_unavailable" in actions) == (mail_mode == "disabled")
        outcomes = list(
            await session.scalars(
                select(MailboxMessageRecord).where(MailboxMessageRecord.to_email == "to-erase@example.test")
            )
        )
        if mail_mode == "disabled":
            assert outcomes == []
        else:
            assert len(outcomes) == 1
            assert outcomes[0].subject == "Hasil permintaan penghapusan"
            assert "Catatan masih diperlukan untuk audit." in outcomes[0].body
            assert "Isi berkas pribadi" in outcomes[0].body


async def test_export_rechecks_membership_and_never_includes_organization_documents(
    client: AsyncClient, sign_up: SignUp, new_client: Callable[[], AsyncClient]
) -> None:
    """
    Condition:
    - An organization has a private document and the requester is a current editor.
    - That editor's membership is subsequently revoked.

    Expected:
    - The export contains membership metadata only while authorized and never includes organization documents.
    """
    from uuid import UUID

    from sqlalchemy import update

    from app.access.repository.sqlalchemy.models import MembershipRecord
    from app.core.database import get_session_factory
    from tests.integration.documents.test_documents import _upload, text_pdf

    await sign_up(client, "org-owner-for-export@example.test")
    org = (
        await client.post(
            "/api/v1/organizations",
            json={"name": "Private Research Team", "kind": "company"},
            headers={"Idempotency-Key": "organization"},
        )
    ).json()
    assert (await client.put("/api/v1/me/context", json={"party_id": org["party_id"]})).status_code == 200
    client.headers["X-Acting-Party"] = org["party_id"]
    await _upload(client, text_pdf(), title="Organization evidence")
    async with new_client() as requester:
        me = await sign_up(requester, "org-editor-export@example.test")
        account_id = UUID(me["account"]["id"])
        async with get_session_factory()() as session, session.begin():
            session.add(
                MembershipRecord(
                    organization_id=UUID(org["id"]), account_id=account_id, capabilities=["edit_portfolio"]
                )
            )
        assert (await requester.put("/api/v1/me/context", json={"party_id": org["party_id"]})).status_code == 200
        response = await requester.post(
            "/api/v1/privacy-requests",
            json={"acting_party_id": org["party_id"], "expected_version": None, "kind": "EXPORT"},
            headers={"Idempotency-Key": "requester-export"},
        )
        assert response.status_code == 201, response.text
        path = f"/api/v1/privacy-requests/{response.json()['id']}/export"
        data = (await requester.get(path)).json()
        assert data["memberships"][0]["name"] == "Private Research Team"
        assert data["documents"] == []
        async with get_session_factory()() as session, session.begin():
            await session.execute(
                update(MembershipRecord).where(MembershipRecord.account_id == account_id).values(status="removed")
            )
        after = (await requester.get(path)).json()
        assert after["memberships"] == [] and after["documents"] == []
