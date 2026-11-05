"""Pitch requests and responses."""

from datetime import datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.matching.model.schema import SourceType


class ChosenFile(BaseModel):
    """One file version to share with the recipient."""

    model_config = ConfigDict(extra="forbid")

    document_id: UUID
    version: Annotated[int, Field(ge=1)]


class SubmitPitchRequest(BaseModel):
    """Send on purpose: the fresh preflight, the brief as edited, and the files chosen."""

    model_config = ConfigDict(extra="forbid")

    acting_party_id: UUID
    preflight_token: Annotated[str, StringConstraints(min_length=1, max_length=200)]
    brief: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=10000)]
    files: Annotated[list[ChosenFile], Field(max_length=20)] = []


class SubmitPitchResponse(BaseModel):
    """The submitted pitch."""

    pitch_id: UUID
    status: str
    submission: int
    operation_id: UUID | None = None


class PitchSummary(BaseModel):
    """One row of a pitch list."""

    id: UUID
    status: str
    subject_type: SourceType
    subject_id: UUID
    subject_title: str
    opportunity_id: UUID
    opportunity_title: str
    requester_party_id: UUID
    requester_name: str
    recipient_party_id: UUID
    recipient_name: str
    purpose: str
    submitted_at: datetime


class SubmittedFile(BaseModel):
    """A file version a submission shared."""

    document_id: UUID
    version: int
    title: str


class SubmissionResponse(BaseModel):
    """One frozen submission."""

    number: int
    brief: str
    snapshot: dict[str, Any]
    files: list[SubmittedFile]
    submitted_at: datetime


class PitchResponse(PitchSummary):
    """A pitch with its frozen submissions, for its requester or recipient."""

    version: int
    submissions: list[SubmissionResponse]


Box = Literal["outgoing", "incoming"]
