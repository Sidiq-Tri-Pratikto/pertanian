"""Persisted assignment and setup state in the lab."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MeterAssignment(BaseModel):
    """Server-side mapping from the broker topic to the owner's site."""

    model_config = ConfigDict(from_attributes=True)
    meter_id: UUID
    site_id: UUID
    owner_id: UUID
    access_expires_at: datetime
    meter_revoked_at: datetime | None
    source_id: UUID | None


class Enrollment(BaseModel):
    """One attempt with its first reading, if one has been staged."""

    model_config = ConfigDict(from_attributes=True)
    id: UUID
    site_id: UUID
    expires_at: datetime
    started_at: datetime
    first_measured_at: datetime | None
    first_received_at: datetime | None
    first_energy_wh: Decimal | None
    asset_id: UUID | None
    confirm_key: str | None
    asset_name: str | None
