"""Matching requests and responses."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from app.intake.model.schema import TargetAvailabilityResponse

SourceType = Literal["SUPPORT_REQUEST", "FUNDING_REQUEST"]
Result = Literal["PASS", "FAIL", "UNKNOWN"]


class MatchRequest(BaseModel):
    """Evaluate one owned source against every active opportunity."""

    acting_party_id: UUID
    source_type: SourceType
    source_id: UUID


class RequirementRow(BaseModel):
    """One requirement's result. ``action`` names what the applicant can do, such as ``complete-budget``."""

    requirement_id: UUID
    label: str
    field: str
    mandatory: bool
    applies_at: str
    verification_mode: str
    result: Result
    reason: str
    action: str | None


class FitResponse(BaseModel):
    """Conservative fit on 0–100 and the share of information it rests on; not a chance of funding."""

    lower: str
    upper: str
    coverage: str


class EvidenceResponse(BaseModel):
    """How much of the checklist rests on provided or reviewed evidence."""

    provided: int
    reviewed: int
    applicable: int
    note: str | None


class MatchResultResponse(BaseModel):
    """One opportunity version's result. Eligibility, readiness and fit are separate on purpose."""

    opportunity_id: UUID
    opportunity_version_id: UUID
    opportunity_version: int
    partner_party_id: UUID
    partner: str
    title: str
    availability: TargetAvailabilityResponse
    eligibility: Literal["ELIGIBLE", "NEEDS_VERIFICATION", "INCOMPATIBLE"]
    readiness: Literal["READY_TO_SUBMIT", "NEEDS_INFORMATION", "BLOCKED_FOR_THIS_TARGET"]
    relevant: bool
    label: str
    fit: FitResponse
    reasons: list[str]
    gap: RequirementRow | None
    later: list[RequirementRow]
    rows: list[RequirementRow]
    evidence: EvidenceResponse


class MatchSource(BaseModel):
    """The source version a run evaluated."""

    type: SourceType
    id: UUID
    version: int
    title: str


class MatchRunResponse(BaseModel):
    """A stored run: recommended results first, then those not to be shown as a positive match."""

    run_id: UUID
    created_at: datetime
    engine: str
    policy_versions: dict[str, int]
    source: MatchSource
    results: list[MatchResultResponse]
    excluded: list[MatchResultResponse]
    operation_id: UUID | None = None
