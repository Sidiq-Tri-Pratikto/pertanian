"""Platform domain models: plain values the repository returns instead of ORM rows."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class IdempotencyModel(BaseModel):
    """One consequential request and, once committed, its stored response."""

    actor_party_id: UUID
    operation: str
    key: str | None
    request_sha256: str
    status: str
    response_status: int | None
    response_body: dict[str, Any] | None
    operation_id: UUID
    result: dict[str, Any] | None
    expires_at: datetime


class OutboxEventModel(BaseModel):
    """One claimed outbox event."""

    id: UUID
    topic: str
    payload: dict[str, Any]
    attempts: int


class JobModel(BaseModel):
    """One claimed job."""

    id: UUID
    kind: str
    actor_party_id: UUID | None
    input: dict[str, Any]
    attempts: int
