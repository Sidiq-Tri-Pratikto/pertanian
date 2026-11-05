"""Identity domain models."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class AccountModel(BaseModel):
    """One account."""

    id: UUID
    email: str
    email_verified_at: datetime | None
    display_name: str
    locale: str
    time_zone: str
    persona: str
    kind: str
    version: int


class EmailCodeModel(BaseModel):
    """One stored code, without the code itself."""

    id: UUID
    email: str
    purpose: str
    code_sha256: str
    salt: str
    profile: dict[str, Any] | None
    expires_at: datetime
    attempts: int


class SessionModel(BaseModel):
    """One live session."""

    id: UUID
    account_id: UUID
    active_party_id: UUID
    expires_at: datetime
    last_seen_at: datetime
