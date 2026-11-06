"""Preflight and brief requests and responses."""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.core.openapi import ErrorBody
from app.intake.model.schema import TargetAvailabilityResponse
from app.matching.model.schema import FitResponse, RequirementRow, SourceType


class PreflightRequest(BaseModel):
    """Check one owned source against one opportunity before anything is sent."""

    model_config = ConfigDict(extra="forbid")

    acting_party_id: UUID
    source_type: SourceType
    source_id: UUID
    opportunity_id: UUID


class PartyName(BaseModel):
    """A party as a name."""

    party_id: UUID
    name: str


class PinnedOpportunity(BaseModel):
    """The opportunity version a preflight pinned."""

    id: UUID
    version_id: UUID
    version: int
    title: str


class PinnedSource(BaseModel):
    """The source version a preflight pinned."""

    type: SourceType
    id: UUID
    version: int
    title: str


class PinnedInvention(BaseModel):
    """One invention version the source reads."""

    invention_id: UUID
    version_id: UUID
    version: int
    title: str


class ShareableFile(BaseModel):
    """A file version the applicant may choose to share; nothing is shared until submission."""

    document_id: UUID
    version_id: UUID
    version: int
    title: str
    file_state: str
    review_state: str
    fact_keys: list[str]


class BriefSentence(BaseModel):
    """One sentence and the supplied facts it rests on."""

    text: str
    refs: list[dict[str, Any]]


class SummaryProvenance(BaseModel):
    """Trusted versions of the model and prompt that produced a selection."""

    model_config = ConfigDict(frozen=True)

    model_id: str
    model_version: str
    prompt_version: str


SummaryStatus = Literal["off", "used", "refused", "unavailable"]


class BriefResponse(BaseModel):
    """The editable template or an authorized extractive suggestion."""

    id: UUID
    preflight_id: UUID
    text: str
    sentences: list[BriefSentence]
    summarizer: str
    summarizer_status: SummaryStatus = "off"
    summarizer_provenance: SummaryProvenance | None = None
    summarizer_error: ErrorBody | None = None


class PreflightResponse(BaseModel):
    """Exactly what would be sent, under a token that pins every version and the permission generation."""

    preflight_id: UUID
    token: str
    expires_at: datetime
    readiness: Literal["READY_TO_SUBMIT", "NEEDS_INFORMATION", "BLOCKED_FOR_THIS_TARGET"]
    eligibility: Literal["ELIGIBLE", "NEEDS_VERIFICATION", "INCOMPATIBLE"]
    label: str
    fit: FitResponse
    sender: PartyName
    recipient: PartyName
    opportunity: PinnedOpportunity
    source: PinnedSource
    inventions: list[PinnedInvention]
    purpose: str | None
    availability: TargetAvailabilityResponse
    rows: list[RequirementRow]
    gap: RequirementRow | None
    later: list[RequirementRow]
    shareable_files: list[ShareableFile]
    brief: BriefResponse
    duplicate_pitch_id: UUID | None
