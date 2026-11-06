"""Demo session domain models."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class DemoSessionModel(BaseModel):
    """An anonymous, expiring workspace: one principal, one demo site."""

    id: UUID
    principal_id: UUID
    site_id: UUID
    scenario_id: str
    key_version: str
    expires_at: datetime


class CreateOperationModel(BaseModel):
    """A demo creation, kept so a lost response can be recovered with its replay proof."""

    operation_id: str
    session_id: UUID | None
    scenario_id: str
    replay_proof_hash: bytes
    key_version: str
    response: dict[str, Any]
    replay_expires_at: datetime
    retain_until: datetime
