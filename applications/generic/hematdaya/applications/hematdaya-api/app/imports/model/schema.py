"""Import request and response schemas."""

from datetime import date, datetime
from enum import StrEnum
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.imports.model.models import PowerMeaning, ValueKind

MAX_MAPPING_ENTRIES = 150_000
"""A file holds at most this many rows, so no answer map needs more entries."""

_MappingKey = Annotated[str, StringConstraints(min_length=1, max_length=120, pattern=r"^[^\x00]+$")]
"""An asset name or stream key: 60 characters, which ``lower()`` can at most double. JSONB refuses NUL."""
_DeclaredMinutes = Annotated[int, Field(ge=-(2**31), le=2**31 - 1)]
"""Only keeps the number sane. The range 1–1440 stays the parser's question, so a user gets its exact words."""


class ImportScope(StrEnum):
    """What the user says about the loads in a file."""

    DISJOINT = "disjoint"
    UNKNOWN_OVERLAP = "unknown_overlap"


class ImportMappingRequest(BaseModel):
    """The user's answers. Every field is optional, because a first preview may have none."""

    model_config = ConfigDict(extra="forbid")

    value_kind: ValueKind | None = Field(default=None, description="The chosen value column, when a file has several")
    power_meaning: PowerMeaning | None = Field(default=None, description="What a power column means")
    timezone_confirmed: bool = Field(default=False, description="Naive times may be read in the site's timezone")
    interval_minutes: dict[_MappingKey, _DeclaredMinutes] = Field(
        default_factory=dict, max_length=MAX_MAPPING_ENTRIES, description="Declared interval in minutes, by stream key"
    )
    asset_map: dict[_MappingKey, UUID | Literal["new"]] = Field(
        default_factory=dict, max_length=MAX_MAPPING_ENTRIES, description="Asset name to asset ID, or `new`"
    )
    scope: ImportScope | None = Field(default=None, description="Whether the file's loads are measured separately")


class ImportStatusResponse(StrEnum):
    """An import's stored status, or ``expired`` once an uncommitted preview has passed its expiry."""

    PREVIEWED = "previewed"
    COMMITTED = "committed"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ImportQuestionKind(StrEnum):
    """What a preview asks before it can be committed."""

    VALUE_KIND = "value_kind"
    POWER_MEANING = "power_meaning"
    TIMEZONE = "timezone"
    INTERVAL_DURATION = "interval_duration"
    SCOPE = "scope"
    ASSET_CHOICE = "asset_choice"
    OTHER_SOURCE = "other_source"
    STREAM_ASSETS = "stream_assets"
    ASSET_STREAMS = "asset_streams"


class AssetCandidateResponse(BaseModel):
    """An asset the user may pick for a name shared by several."""

    id: UUID
    name: str
    location: str | None
    category: str | None
    scope_kind: str


class ImportQuestionResponse(BaseModel):
    """One open question."""

    kind: ImportQuestionKind
    message: str
    streams: list[str] = []
    asset_name: str | None = None
    candidates: list[AssetCandidateResponse] = []


class ImportRowErrorResponse(BaseModel):
    """One invalid or conflicting row."""

    data_row: int
    file_line: int
    field: str
    reason: str
    message: str


class ImportErrorPageResponse(BaseModel):
    """One page of row errors, ordered by data row."""

    items: list[ImportRowErrorResponse]
    next_cursor: str | None


class ImportPeriodResponse(BaseModel):
    """The local dates accepted rows cover."""

    start_date: date
    end_date: date
    timezone: str


class ImportCommitRequest(BaseModel):
    """What a commit needs beyond its key."""

    model_config = ConfigDict(extra="forbid")

    acknowledge_skipped: bool = Field(default=False, description="The user accepts that invalid rows will be skipped")


class ImportCommitAssetResponse(BaseModel):
    """An asset a commit created or mapped to."""

    id: UUID
    name: str


class ImportCommitResultResponse(BaseModel):
    """What a commit did, stored once and returned unchanged by every later read."""

    import_id: UUID
    status: ImportStatusResponse
    rows_added: int = Field(description="Rows stored")
    rows_skipped: int = Field(description="Invalid rows acknowledged")
    rows_duplicate: int = Field(description="Exact repeats")
    assets_created: list[ImportCommitAssetResponse] = Field(default=[], description="In stream order")
    assets_mapped: list[ImportCommitAssetResponse] = Field(default=[], description="In stream order")
    period: ImportPeriodResponse | None = Field(default=None, description="Local dates changed; null when none were")
    affected_from: datetime | None = Field(default=None, description="Start of the changed data, in UTC")
    affected_to: datetime | None = Field(default=None, description="End of the changed data, in UTC")
    rows_after_site_clock: int = Field(default=0, description="Accepted rows ending after the site's clock at commit")
    acknowledge_skipped: bool = Field(description="What the first request sent")
    committed_at: datetime = Field(description="Wall-clock time of the commit")


class ImportCommitResponse(ImportCommitResultResponse):
    """A commit's answer: the first result, and whether this request only repeated it."""

    replayed: bool = Field(description="False for the first result, true for a repeat")


class ImportPreviewResponse(BaseModel):
    """A stored preview. Counts always cover the whole file; ``errors`` holds the first 50."""

    id: UUID
    status: ImportStatusResponse
    file_name: str
    expires_at: datetime
    total_rows: int
    accepted_rows: int
    invalid_rows: int
    duplicate_rows: int
    conflict_rows: int
    pending_rows: int
    blocked: bool
    block_reasons: list[str]
    needs_acknowledgment: bool
    questions: list[ImportQuestionResponse]
    mapping: dict[str, Any]
    assumptions: list[str]
    period: ImportPeriodResponse | None
    errors: list[ImportRowErrorResponse]
    next_error_cursor: str | None
    result: ImportCommitResultResponse | None = Field(default=None, description="The first result, once committed")
