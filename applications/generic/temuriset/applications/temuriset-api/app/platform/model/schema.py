"""Operation status responses."""

from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel


class OperationStatus(StrEnum):
    """What a client may know about an operation it started."""

    PENDING = "PENDING"
    COMMITTED = "COMMITTED"
    UNKNOWN = "UNKNOWN"


class OperationResult(BaseModel):
    """What a committed operation produced."""

    type: str
    id: str


class OperationResponse(BaseModel):
    """Status of one operation, for a client that never received its response."""

    operation_id: UUID
    status: OperationStatus
    result: OperationResult | None = None
