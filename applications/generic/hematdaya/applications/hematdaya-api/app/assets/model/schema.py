"""Asset request and response schemas."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, StringConstraints

from app.assets.model.models import (
    ExpectedUse,
    MeasurementKind,
    ScopeKind,
    SourceOrigin,
    TransportStatus,
)

AssetName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)]
OptionalText = Annotated[str, StringConstraints(strip_whitespace=True, max_length=60)]


class CreateAssetRequest(BaseModel):
    """A new asset. Expected use stays unknown unless the user chooses it."""

    model_config = ConfigDict(extra="forbid")

    name: AssetName
    scope_kind: ScopeKind
    category: OptionalText | None = None
    location: OptionalText | None = None
    parent_asset_id: UUID | None = None
    expected_use: ExpectedUse = ExpectedUse.UNKNOWN


class UpdateAssetRequest(BaseModel):
    """Asset fields an owner may change. Archiving is reversible and keeps readings."""

    model_config = ConfigDict(extra="forbid")

    name: AssetName | None = None
    category: OptionalText | None = None
    location: OptionalText | None = None
    expected_use: ExpectedUse | None = None
    archived: bool | None = None


class CreateBindingRequest(BaseModel):
    """Attribute a source of the same site to an asset from a given instant."""

    model_config = ConfigDict(extra="forbid")

    source_id: UUID
    effective_from: AwareDatetime
    authoritative: bool = True


class AssetResponse(BaseModel):
    """An asset."""

    id: UUID
    name: str
    category: str | None
    location: str | None
    scope_kind: ScopeKind
    parent_asset_id: UUID | None
    expected_use: ExpectedUse
    archived: bool


class SourceResponse(BaseModel):
    """A source and how its readings arrive."""

    id: UUID
    label: str
    origin: SourceOrigin
    measurement_kind: MeasurementKind
    cadence_seconds: int | None
    resolution_mwh: int | None
    transport_status: TransportStatus


class BindingResponse(BaseModel):
    """A source's attribution to an asset over ``[effective_from, effective_to)``."""

    id: UUID
    source_id: UUID
    effective_from: datetime
    effective_to: datetime | None
    authoritative: bool


class AssetDetailResponse(AssetResponse):
    """An asset with its bindings, past and present, and their sources."""

    bindings: list[BindingResponse]
    sources: list[SourceResponse]


class AssetPageResponse(BaseModel):
    """One page of assets ordered by name, then ID."""

    items: list[AssetResponse]
    next_cursor: str | None
