"""Energy response schemas. Energy and ratios are decimal strings; unavailable values are null with a reason."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel

from app.assets.model.models import ScopeKind
from app.scope.service.validity import IssueType


class WindowResponse(BaseModel):
    """The resolved period in local dates and UTC instants."""

    start: datetime
    end: datetime
    effective_end: datetime
    start_date: date
    end_date: date
    timezone: str
    is_current: bool


class ScopeAssetResponse(BaseModel):
    """An asset considered for the total."""

    asset_id: UUID
    name: str


class ExcludedAssetResponse(ScopeAssetResponse):
    """An asset left out, with the reason."""

    reason: str


class ScopeIssueResponse(BaseModel):
    """Why a combined total is refused."""

    type: IssueType
    asset_ids: list[UUID]
    message: str


class ScopeResponse(BaseModel):
    """Which assets were considered and whether they may be added together."""

    valid: bool
    issues: list[ScopeIssueResponse]
    included: list[ScopeAssetResponse]
    excluded: list[ExcludedAssetResponse]


class CoverageResponse(BaseModel):
    """Completeness of the selection, never averaged away."""

    minimum: str | None
    concurrent: str | None
    allocated_estimate: bool


class GapResponse(BaseModel):
    """A stretch with no valid reading."""

    start: datetime
    end: datetime


class ConflictSourceResponse(BaseModel):
    """One unresolved candidate's value, shown beside the others and never summed."""

    source_id: UUID
    label: str
    energy_kwh: str


class AssetEnergyResponse(BaseModel):
    """One asset's recorded energy in the window."""

    asset_id: UUID
    name: str
    scope_kind: ScopeKind
    energy_kwh: str | None
    energy_unavailable_reason: str | None
    share_percent: str | None
    coverage: str | None
    gaps: list[GapResponse]
    conflict_sources: list[ConflictSourceResponse] | None


class SummaryResponse(BaseModel):
    """Recorded energy for a period and scope."""

    window: WindowResponse
    scope: ScopeResponse
    energy_kwh: str | None
    energy_unavailable_reason: str | None
    coverage: CoverageResponse
    assets: list[AssetEnergyResponse]
    latest_measurement_at: datetime | None
    origins: list[str]
    revision: int


class HistoryBucketResponse(BaseModel):
    """One bucket. A missing bucket is null with state ``missing``, never zero."""

    start: datetime
    end: datetime
    local_date: date
    local_time: str | None
    utc_offset: str
    energy_kwh: str | None
    unavailable_reason: str | None
    state: str
    coverage: str | None


class HighestBucketResponse(BaseModel):
    """The fully covered measured bucket with the greatest value; earliest start breaks a tie."""

    start: datetime


class HistoryResponse(BaseModel):
    """Bucketed history that reconciles with the summary."""

    window: WindowResponse
    bucket: str
    origins: list[str]
    resolution_mwh: int | None
    highest_bucket: HighestBucketResponse | None
    buckets: list[HistoryBucketResponse]
