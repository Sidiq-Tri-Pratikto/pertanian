"""Idempotency, operations, audit and outbox through the real application and Postgres (spec 005, US1)."""

import asyncio
import json
import logging
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi import APIRouter
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel
from sqlalchemy import func, select, text

from app.core import clock
from app.core.database import SessionDep, get_session_factory
from app.core.errors.base import ConflictError
from app.main import create_app
from app.platform.actor import ActorDep
from app.platform.model.schema import OperationResult
from app.platform.repository.sqlalchemy.models import AuditEventRecord, IdempotencyRecord, OutboxEventRecord
from app.platform.service.audit import record_audit
from app.platform.service.idempotency import Idempotency, idempotent
from app.platform.service.outbox import publish

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("clean_tables")]

ACTOR = UUID("00000000-0000-4000-8000-000000000001")
OTHER_ACTOR = UUID("00000000-0000-4000-8000-000000000002")
fail_before_commit: list[bool] = []


class NoteRequest(BaseModel):
    """Body of the test-only consequential route."""

    text: str


router = APIRouter()


@router.post("/test/notes", status_code=201)
async def create_note(
    body: NoteRequest, session: SessionDep, actor_party_id: ActorDep, operation: Idempotency = idempotent("tests.notes")
) -> object:
    """Test-only mutation: an audit event and an outbox event, then optionally a failure before commit."""
    note_id = str(uuid4())
    await record_audit(
        session, action="note.created", subject_type="note", subject_id=note_id, actor_party_id=actor_party_id
    )
    await publish(session, "note.created", {"note_id": note_id})
    if fail_before_commit and fail_before_commit.pop():
        raise ConflictError()
    return await operation.respond(
        {"operation_id": str(operation.operation_id), "id": note_id, "text": body.text},
        status_code=201,
        result=OperationResult(type="note", id=note_id),
    )


app = create_app()
app.include_router(router)


@pytest.fixture
async def api() -> AsyncIterator[AsyncClient]:
    """Client for the application with the test-only route."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


def _headers(key: str | None, actor: UUID = ACTOR) -> dict[str, str]:
    headers = {"X-Party-Id": str(actor)}
    if key is not None:
        headers["Idempotency-Key"] = key
    return headers


async def _count(model: type) -> int:
    async with get_session_factory()() as session:
        return await session.scalar(select(func.count()).select_from(model)) or 0


async def test_repeated_request_replays_and_has_one_effect(api: AsyncClient) -> None:
    """
    Condition:
    - The same key and body are sent twice.

    Expected:
    - The second response is the stored one, marked replayed; one audit event and one outbox event exist.
    """
    first = await api.post("/test/notes", json={"text": "a"}, headers=_headers("k1"))
    second = await api.post("/test/notes", json={"text": "a"}, headers=_headers("k1"))

    assert first.status_code == second.status_code == 201
    assert second.json() == first.json()
    assert "Idempotent-Replayed" not in first.headers
    assert second.headers["Idempotent-Replayed"] == "true"
    assert await _count(AuditEventRecord) == 1
    assert await _count(OutboxEventRecord) == 1


async def test_key_order_in_the_body_does_not_change_the_request(api: AsyncClient) -> None:
    """
    Condition:
    - The same JSON object is sent with different whitespace.

    Expected:
    - It is the same request: replayed, not a conflict.
    """
    await api.post("/test/notes", json={"text": "a"}, headers=_headers("k-canonical"))
    again = await api.post(
        "/test/notes",
        content=b'{ "text" : "a" }',
        headers={**_headers("k-canonical"), "Content-Type": "application/json"},
    )

    assert again.status_code == 201
    assert again.headers["Idempotent-Replayed"] == "true"


async def test_same_key_with_another_body_is_a_conflict(api: AsyncClient, caplog: pytest.LogCaptureFixture) -> None:
    """
    Condition:
    - A key is reused with a different body.

    Expected:
    - ``IDEMPOTENCY_CONFLICT``, not retryable, recorded under its request ID, and nothing changes.
    """
    await api.post("/test/notes", json={"text": "a"}, headers=_headers("k2"))

    with caplog.at_level(logging.WARNING):
        response = await api.post("/test/notes", json={"text": "b"}, headers=_headers("k2"))

    assert response.status_code == 409
    error = response.json()["error"]
    assert error["code"] == "IDEMPOTENCY_CONFLICT"
    assert (
        error["message"]
        == "Kunci permintaan ini sudah dipakai untuk isi berbeda. Gunakan kunci baru untuk permintaan baru."
    )
    assert error["recovery"] == {"retryable": False}
    assert error["request_id"] in caplog.text
    assert await _count(AuditEventRecord) == 1


async def test_same_key_from_another_actor_is_another_request(api: AsyncClient) -> None:
    """
    Condition:
    - Two parties use the same key.

    Expected:
    - Each gets its own operation.
    """
    mine = await api.post("/test/notes", json={"text": "a"}, headers=_headers("shared"))
    theirs = await api.post("/test/notes", json={"text": "a"}, headers=_headers("shared", OTHER_ACTOR))

    assert mine.json()["operation_id"] != theirs.json()["operation_id"]
    assert await _count(AuditEventRecord) == 2


async def test_missing_key_is_refused_with_a_field_message(api: AsyncClient) -> None:
    """
    Condition:
    - A consequential POST has no ``Idempotency-Key``.

    Expected:
    - ``BAD_REQUEST`` naming the header with an Indonesian field message; nothing is written.
    """
    response = await api.post("/test/notes", json={"text": "a"}, headers=_headers(None))

    assert response.status_code == 400
    error = response.json()["error"]
    assert error["code"] == "BAD_REQUEST"
    assert error["details"] == [
        {"loc": ["header", "Idempotency-Key"], "msg": "Isian ini wajib diisi.", "type": "missing"}
    ]
    assert await _count(IdempotencyRecord) == 0


async def test_failure_before_commit_leaves_nothing_and_the_retry_completes(api: AsyncClient) -> None:
    """
    Condition:
    - The first attempt fails after writing, before commit; the client retries the identical request.

    Expected:
    - The failure leaves no audit event, outbox event or record; the retry completes the operation once.
    """
    fail_before_commit.append(True)
    failed = await api.post("/test/notes", json={"text": "a"}, headers=_headers("k3"))

    assert failed.status_code == 409
    assert (await _count(AuditEventRecord), await _count(OutboxEventRecord), await _count(IdempotencyRecord)) == (
        0,
        0,
        0,
    )

    retried = await api.post("/test/notes", json={"text": "a"}, headers=_headers("k3"))

    assert retried.status_code == 201
    assert "Idempotent-Replayed" not in retried.headers
    assert await _count(AuditEventRecord) == 1


async def test_lost_response_is_recovered_through_the_operation(api: AsyncClient) -> None:
    """
    Condition:
    - A request committed but the client lost the response; it asks for the operation.

    Expected:
    - ``COMMITTED`` with a result reference for the same actor; ``NOT_FOUND`` for another actor; ``UNKNOWN`` for an
      id the service never issued.
    """
    created = (await api.post("/test/notes", json={"text": "a"}, headers=_headers("k4"))).json()

    mine = await api.get(f"/api/v1/operations/{created['operation_id']}", headers=_headers(None))
    theirs = await api.get(f"/api/v1/operations/{created['operation_id']}", headers=_headers(None, OTHER_ACTOR))
    unknown = await api.get(f"/api/v1/operations/{uuid4()}", headers=_headers(None))

    assert mine.status_code == 200
    assert mine.json() == {
        "operation_id": created["operation_id"],
        "status": "COMMITTED",
        "result": {"type": "note", "id": created["id"]},
    }
    assert theirs.status_code == 404
    assert theirs.json()["error"]["code"] == "NOT_FOUND"
    assert unknown.json()["status"] == "UNKNOWN"


async def test_twenty_parallel_requests_with_one_key_have_one_effect(api: AsyncClient) -> None:
    """
    Condition:
    - The same key and body arrive 20 times at once (SC-001).

    Expected:
    - Every response carries the same operation; exactly one effect.
    """
    responses = await asyncio.gather(
        *(api.post("/test/notes", json={"text": "a"}, headers=_headers("k-race")) for _ in range(20))
    )

    assert {response.status_code for response in responses} == {201}
    assert len({response.json()["operation_id"] for response in responses}) == 1
    assert sum(response.headers.get("Idempotent-Replayed") == "true" for response in responses) == 19
    assert await _count(AuditEventRecord) == 1
    assert await _count(OutboxEventRecord) == 1


async def test_expired_key_starts_a_new_operation_and_the_old_one_stays_readable(api: AsyncClient) -> None:
    """
    Condition:
    - A key is reused after the seven-day retention.

    Expected:
    - A new operation runs; the old operation still reports ``COMMITTED``.
    """
    start = datetime(2026, 11, 1, tzinfo=UTC)
    with clock.frozen(start):
        old = (await api.post("/test/notes", json={"text": "a"}, headers=_headers("k5"))).json()
    with clock.frozen(start + timedelta(days=7, seconds=1)):
        new = await api.post("/test/notes", json={"text": "a"}, headers=_headers("k5"))
        status = await api.get(f"/api/v1/operations/{old['operation_id']}", headers=_headers(None))

    assert new.status_code == 201
    assert "Idempotent-Replayed" not in new.headers
    assert new.json()["operation_id"] != old["operation_id"]
    assert status.json()["status"] == "COMMITTED"
    assert await _count(AuditEventRecord) == 2


async def test_audit_events_cannot_be_changed() -> None:
    """
    Condition:
    - Someone tries to edit or delete an audit event in the database.

    Expected:
    - Postgres refuses it.
    """
    async with get_session_factory()() as session:
        await record_audit(session, action="note.created", subject_type="note", subject_id="1")
        await session.commit()

    for statement in ("UPDATE audit_events SET action = 'x'", "DELETE FROM audit_events"):
        async with get_session_factory()() as session:
            with pytest.raises(Exception, match="append-only"):  # noqa: B017 - the database's own refusal
                await session.execute(text(statement))
    assert await _count(AuditEventRecord) == 1


async def test_audit_detail_is_stored_as_given() -> None:
    """
    Condition:
    - An audit event with detail.

    Expected:
    - The detail is stored as JSON with the actor.
    """
    async with get_session_factory()() as session:
        await record_audit(
            session, action="note.created", subject_type="note", subject_id="1", actor_party_id=ACTOR, detail={"n": 1}
        )
        await session.commit()
        stored = await session.scalar(select(AuditEventRecord))

    assert stored is not None
    assert (stored.actor_party_id, json.dumps(stored.detail)) == (ACTOR, '{"n": 1}')
