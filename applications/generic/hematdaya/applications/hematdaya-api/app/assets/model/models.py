"""Asset, source, binding and relation domain models."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel


class ScopeKind(StrEnum):
    """What an asset's readings cover."""

    DEVICE = "device"
    GROUP = "group"
    CIRCUIT = "circuit"
    SITE_TOTAL = "site_total"


class ExpectedUse(StrEnum):
    """How the user expects the asset to run. Never derived from its category."""

    UNKNOWN = "unknown"
    CONTINUOUS = "continuous"
    SCHEDULED = "scheduled"
    INTERMITTENT = "intermittent"


class SourceOrigin(StrEnum):
    """Where a source's readings come from."""

    LIVE = "live"
    IMPORT = "import"
    DATASET_REPLAY = "dataset_replay"
    SIMULATED = "simulated"


class MeasurementKind(StrEnum):
    """What a source's raw values mean."""

    INTERVAL_ENERGY = "interval_energy"
    AVERAGE_POWER = "average_power"
    INSTANTANEOUS_POWER = "instantaneous_power"
    COUNTER = "counter"


class TransportStatus(StrEnum):
    """How a source reaches the API. Nothing is ever a real live connection before 046."""

    NONE = "none"
    SIMULATED_LIVE = "simulated_live"
    HISTORICAL = "historical"


class RelationKind(StrEnum):
    """What is known about two assets' physical loads."""

    CONTAINS = "contains"
    UNKNOWN_OVERLAP = "unknown_overlap"
    DISJOINT = "disjoint"


class AssetModel(BaseModel):
    """Something measured. A name is not an identity; the ID is."""

    id: UUID
    site_id: UUID
    name: str
    category: str | None
    location: str | None
    scope_kind: ScopeKind
    parent_asset_id: UUID | None
    expected_use: ExpectedUse
    archived_at: datetime | None


class SourceModel(BaseModel):
    """A stream of readings, bound to assets over time."""

    id: UUID
    site_id: UUID
    label: str
    origin: SourceOrigin
    measurement_kind: MeasurementKind
    cadence_seconds: int | None
    resolution_mwh: int | None
    transport_status: TransportStatus


class BindingModel(BaseModel):
    """A source attributed to an asset over the half-open range ``[effective_from, effective_to)``."""

    id: UUID
    site_id: UUID
    source_id: UUID
    asset_id: UUID
    effective_from: datetime
    effective_to: datetime | None
    authoritative: bool


class RelationModel(BaseModel):
    """A known relation between two assets of one site."""

    id: UUID
    site_id: UUID
    from_asset_id: UUID
    to_asset_id: UUID
    kind: RelationKind
