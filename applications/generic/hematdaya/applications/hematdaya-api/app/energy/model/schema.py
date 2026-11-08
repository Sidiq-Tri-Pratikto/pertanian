"""Energy response schemas. Energy and ratios are decimal strings; unavailable values are null with a reason."""

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.assets.model.models import ScopeKind, SourceOrigin
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


FreshnessState = Literal["unknown", "current", "stale", "historical"]


class CaptureRangeResponse(BaseModel):
    """The span of recorded data attributable to a historical source in the report."""

    start: datetime
    end: datetime


class SourceFreshnessResponse(BaseModel):
    """The capture and freshness for one effective asset/source pair."""

    source_id: UUID
    label: str
    asset_id: UUID
    origin: SourceOrigin
    state: FreshnessState
    last_capture_at: datetime | None
    cadence_seconds: int | None = Field(gt=0)
    policy_version: Literal[1]
    historical_range: CaptureRangeResponse | None


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
    selection_revision: int | None = None
    binding_revision: int | None = None
    source_freshness: list[SourceFreshnessResponse] = Field(default_factory=list)


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
    comparison_kwh: str | None = None
    reference_kwh: str | None = None


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
    comparison_state: str | None
    buckets: list[HistoryBucketResponse]
