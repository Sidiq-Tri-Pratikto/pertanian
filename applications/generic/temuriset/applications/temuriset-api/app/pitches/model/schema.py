"""Pitch requests and responses."""

from datetime import date, datetime
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
    updated_at: datetime
    waiting_on_party_id: UUID | None = Field(
        description="Whose move it is: the requester or the recipient, or none during discussion and after the end."
    )


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


class DecisionResponse(BaseModel):
    """A recipient decision. Its reason is seen by the two parties only."""

    decision: Literal["APPROVE", "REJECT"]
    reason: str | None
    submission_number: int
    decided_at: datetime


class AnswerResponse(BaseModel):
    """The requester's answer to one item."""

    response: Literal["CAN", "DISCUSS", "CANNOT"]
    text: str
    files: list[SubmittedFile]
    version: int
    saved_at: datetime


class RevisionItemResponse(BaseModel):
    """One requested item, its answer once visible, and the recipient's review."""

    id: UUID
    position: int
    category: str
    question: str
    reason: str
    required: bool
    due_date: date | None
    expected_evidence: str
    review: Literal["ACCEPTED", "NEEDS_DETAIL"] | None
    review_note: str | None
    version: int
    answer: AnswerResponse | None


class RevisionRoundResponse(BaseModel):
    """One numbered round."""

    number: int
    submission_number: int
    requested_at: datetime
    open: bool = Field(description="Still waiting for the requester to resubmit; its answers are drafts.")
    items: list[RevisionItemResponse]


class PitchResponse(PitchSummary):
    """A pitch with its frozen submissions, decisions and rounds, for its requester or recipient."""

    version: int
    submissions: list[SubmissionResponse]
    decisions: list[DecisionResponse]
    rounds: list[RevisionRoundResponse]
    allowed_actions: list[str] = Field(
        description="What the reader may do now: table actions plus ``answer`` and ``review_items``."
    )


class PitchActionRequest(BaseModel):
    """A status change against the pitch version the client saw."""

    model_config = ConfigDict(extra="forbid")

    acting_party_id: UUID
    expected_version: int


class CloseRequest(PitchActionRequest):
    """Close a discussion, with the reason both parties will read."""

    reason: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]


class DecisionRequest(PitchActionRequest):
    """Approve for discussion or reject, on the submission the recipient read."""

    submission: Annotated[int, Field(ge=1)]
    decision: Literal["APPROVE", "REJECT"]
    reason: Annotated[str | None, StringConstraints(strip_whitespace=True, max_length=500)] = None


class RevisionItemInput(BaseModel):
    """One itemized question."""

    model_config = ConfigDict(extra="forbid")

    category: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)]
    question: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]
    reason: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]
    required: bool
    due_date: date | None = None
    expected_evidence: Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)] = ""


class RevisionRequest(PitchActionRequest):
    """Open a numbered round on the submission the recipient read."""

    submission: Annotated[int, Field(ge=1)]
    items: Annotated[list[RevisionItemInput], Field(min_length=1, max_length=20)]


class AnswerRequest(BaseModel):
    """Save a draft answer; the first save sends no version."""

    model_config = ConfigDict(extra="forbid")

    acting_party_id: UUID
    expected_version: int | None = None
    response: Literal["CAN", "DISCUSS", "CANNOT"]
    text: Annotated[str, StringConstraints(strip_whitespace=True, max_length=5000)] = ""
    files: Annotated[list[ChosenFile], Field(max_length=10)] = []


class ItemReviewRequest(BaseModel):
    """Accept an answer or ask for more detail."""

    model_config = ConfigDict(extra="forbid")

    acting_party_id: UUID
    expected_version: int
    result: Literal["ACCEPTED", "NEEDS_DETAIL"]
    note: Annotated[str | None, StringConstraints(strip_whitespace=True, max_length=1000)] = None


class ResubmitRequest(PitchActionRequest):
    """Send again after answering: the brief as edited and the file versions chosen on purpose."""

    brief: Annotated[str | None, StringConstraints(strip_whitespace=True, min_length=1, max_length=10000)] = None
    files: Annotated[list[ChosenFile], Field(max_length=20)] = []


class ItemReviewResponse(BaseModel):
    """An item's review after it was marked."""

    id: UUID
    review: Literal["ACCEPTED", "NEEDS_DETAIL"]
    review_note: str | None
    version: int


class PitchActionResponse(BaseModel):
    """The pitch after a status change."""

    pitch_id: UUID
    status: str
    version: int
    submission: int | None = None
    round: int | None = None
    operation_id: UUID | None = None


Box = Literal["outgoing", "incoming"]
