"""Idempotent consequential requests: a retried request never repeats its effect."""

import hashlib
import json
from dataclasses import dataclass
from datetime import timedelta
from typing import Any
from uuid import UUID

from fastapi import Depends, Request
from fastapi.encoders import jsonable_encoder
from fastapi.params import Depends as DependsParam
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core import clock
from app.core.database import SessionDep
from app.core.errors import codes
from app.core.errors.base import AppError, RequestInvalidError
from app.core.errors.public import field_message
from app.platform.actor import ActorDep
from app.platform.model.schema import OperationResult
from app.platform.repository.sqlalchemy.repository import SqlAlchemyPlatformRepository

# Policy `idempotency-retention` v1: a key may be reused seven days after its request.
RETENTION = timedelta(days=7)
KEY_HEADER = "Idempotency-Key"
REPLAYED_HEADER = "Idempotent-Replayed"
_MAX_KEY_LENGTH = 128


class IdempotencyConflictError(AppError):
    """The key was already used for a different request."""

    code = codes.APP_IDEMPOTENCY_CONFLICT


class IdempotencyKeyMissingError(RequestInvalidError):
    """A consequential request arrived without a usable key."""

    def __init__(self) -> None:
        """Explain which header is missing."""
        super().__init__(
            "Permintaan ini memerlukan kunci Idempotency-Key. Kirim ulang dengan kunci tersebut.",
            public_fields={
                "details": [{"loc": ["header", KEY_HEADER], "msg": field_message("missing"), "type": "missing"}]
            },
        )


class IdempotentReplay(Exception):  # noqa: N818 - a control-flow signal, not a failure
    """Carries the stored response of a committed request to its retry."""

    def __init__(self, status_code: int, body: dict[str, Any]) -> None:
        """Hold the stored response.

        Args:
            status_code (int): Stored HTTP status.
            body (dict[str, Any]): Stored JSON body.
        """
        super().__init__("replay")
        self.status_code = status_code
        self.body = body


async def replay_response(_: Request, replay: Exception) -> JSONResponse:
    """Answer a retry with the stored response.

    Args:
        _ (Request): The retried request.
        replay (Exception): The ``IdempotentReplay`` signal.

    Returns:
        JSONResponse: The stored response, marked as replayed.
    """
    assert isinstance(replay, IdempotentReplay)  # noqa: S101 - registered for this type only
    return JSONResponse(replay.body, status_code=replay.status_code, headers={REPLAYED_HEADER: "true"})


def request_digest(actor_party_id: UUID, operation: str, body: bytes) -> str:
    """Digest what makes two requests the same: actor, operation and canonical body.

    Args:
        actor_party_id (UUID): The acting party.
        operation (str): The operation name.
        body (bytes): The raw request body.

    Returns:
        str: Hex SHA-256.
    """
    try:
        canonical = json.dumps(json.loads(body), sort_keys=True, separators=(",", ":")).encode()
    except ValueError:
        canonical = body
    return hashlib.sha256(f"{actor_party_id}\n{operation}\n".encode() + canonical).hexdigest()


@dataclass
class Idempotency:
    """The running operation of one consequential request.

    Attributes:
        operation_id (UUID): Returned to the client; ``GET /api/v1/operations/{id}`` reports on it.
    """

    operation_id: UUID
    _repository: SqlAlchemyPlatformRepository

    async def respond(
        self, body: BaseModel | dict[str, Any], *, status_code: int = 200, result: OperationResult | None = None
    ) -> JSONResponse:
        """Store the response for retries, in the request's transaction, and return it.

        Args:
            body (BaseModel | dict[str, Any]): The response body; it should carry ``operation_id``.
            status_code (int, optional): HTTP status. Defaults to 200.
            result (OperationResult | None, optional): What the operation produced. Defaults to None.

        Returns:
            JSONResponse: The response.
        """
        content = jsonable_encoder(body)
        await self._repository.complete_idempotency(
            self.operation_id,
            response_status=status_code,
            response_body=content,
            result=result.model_dump() if result is not None else None,
        )
        return JSONResponse(content, status_code=status_code)


def idempotent(operation: str) -> DependsParam:
    """Make a consequential POST idempotent.

    The same key and body replays the stored response with ``Idempotent-Replayed: true``. The same key with a
    different body is refused with ``IDEMPOTENCY_CONFLICT``. Concurrent requests with one key wait on the database,
    so exactly one of them runs the operation. A request that fails rolls back with its record, so the next
    identical request completes it.

    Args:
        operation (str): Stable operation name, such as ``pitches.submit``.

    Returns:
        DependsParam: A dependency yielding an ``Idempotency``.
    """

    async def begin(request: Request, session: SessionDep, actor_party_id: ActorDep) -> Idempotency:
        key = request.headers.get(KEY_HEADER)
        if not key or len(key) > _MAX_KEY_LENGTH:
            raise IdempotencyKeyMissingError()
        digest = request_digest(actor_party_id, operation, await request.body())
        repository = SqlAlchemyPlatformRepository(session)
        claim = {"actor_party_id": actor_party_id, "operation": operation, "key": key, "request_sha256": digest}
        record = await repository.claim_idempotency_key(**claim, expires_at=clock.now() + RETENTION)
        if record.status == "committed" and record.expires_at <= clock.now():
            await repository.release_idempotency_key(record.operation_id)
            record = await repository.claim_idempotency_key(**claim, expires_at=clock.now() + RETENTION)
        if record.request_sha256 != digest:
            raise IdempotencyConflictError()
        if record.status == "committed" and record.response_status is not None:
            raise IdempotentReplay(record.response_status, record.response_body or {})
        return Idempotency(record.operation_id, repository)

    return Depends(begin)
