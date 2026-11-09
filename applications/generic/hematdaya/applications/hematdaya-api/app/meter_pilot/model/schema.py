"""Public lab catalog and owner-scoped enrollment contracts."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.assets.model.schema import AssetName

METER_MODEL_ID = "shelly-plug-pm-gen3"
METER_MODEL_NAME = "Shelly Plug PM Gen3"
CADENCE_SECONDS = 60


class DeviceResponse(BaseModel):
    """One catalog model and the measurement this pilot can accept."""

    id: Literal["shelly-plug-pm-gen3"] = METER_MODEL_ID
    name: str = METER_MODEL_NAME
    status: Literal["planned", "available"]
    measurement_kind: Literal["counter"] = "counter"
    cadence_seconds: int = CADENCE_SECONDS
    scope_kind: Literal["device"] = "device"


class DeviceCatalogResponse(BaseModel):
    """Catalog metadata with the environment's capability state."""

    devices: list[DeviceResponse]


class StartEnrollmentRequest(BaseModel):
    """Select the sole verified adapter candidate."""

    model_config = ConfigDict(extra="forbid")
    model_id: Literal["shelly-plug-pm-gen3"]


class ConfirmEnrollmentRequest(BaseModel):
    """Name the single new appliance measured by the meter."""

    model_config = ConfigDict(extra="forbid")
    asset_name: AssetName


class EnrollmentResponse(BaseModel):
    """Setup progress for an owner, without any device credential."""

    id: UUID
    status: Literal["waiting", "ready", "connected", "expired"]
    expires_at: datetime
    first_measured_at: datetime | None
    asset_id: UUID | None


class PilotSessionResponse(BaseModel):
    """The site associated with a valid operator-issued access code."""

    site_id: UUID
    expires_at: datetime
