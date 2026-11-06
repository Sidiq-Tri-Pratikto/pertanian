"""Report, operator and privacy requests and responses. Inputs refuse any field they do not name."""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, StringConstraints

from app.documents.model.schema import PersonalDocumentMetadata
from app.identity.model.schema import AccountResponse, MembershipResponse

ReportCategory = Literal["IMPERSONATION", "UNSUPPORTED_CLAIM", "UNWANTED_CONTACT", "ABUSE", "OTHER"]
SubjectType = Literal[
    "INVENTION", "OPPORTUNITY", "PARTNER_PROFILE", "FUNDING_REQUEST", "SUPPORT_REQUEST", "PITCH", "MESSAGE", "OTHER"
]
ReportStatus = Literal["RECEIVED", "IN_REVIEW", "RESOLVED", "DISMISSED"]
OperatorAction = Literal["START_REVIEW", "SUSPEND_LISTING", "LIFT_SUSPENSION", "RESOLVE", "DISMISS"]
PrivacyKind = Literal["EXPORT", "DELETION"]
PrivacyStatus = Literal["RECEIVED", "PROCESSING", "FULFILLED"]

Required = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=4000)]
Label = Annotated[str, StringConstraints(strip_whitespace=True, max_length=200)]


class _Input(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CreateReportRequest(_Input):
    """Report something privately. The object is named, never checked, so a report cannot probe for what exists."""

    acting_party_id: UUID
    expected_version: None
    category: ReportCategory = "OTHER"
    subject_type: SubjectType = "OTHER"
    subject_id: UUID | None = None
    subject_label: Label = ""
    reason: Required


class ReportResponse(BaseModel):
    """What a reporter sees: the case and its status, and nothing an operator wrote."""

    id: UUID
    case_number: str
    status: ReportStatus
    operation_id: UUID | None = None


class OperatorActionRequest(_Input):
    """Act on a case against the version the operator saw, saying why."""

    acting_party_id: UUID
    expected_version: int
    action: OperatorAction
    note: Required


class OperatorActionResponse(BaseModel):
    """One thing an operator did."""

    action: OperatorAction
    note: str
    operator_account_id: UUID
    created_at: datetime


class OperatorReportResponse(BaseModel):
    """A case as an operator with the moderation scope sees it."""

    id: UUID
    case_number: str
    version: int
    category: ReportCategory
    subject_type: SubjectType
    subject_id: UUID | None
    subject_label: str
    reason: str
    status: ReportStatus
    reporter_party_id: UUID
    suspended: bool
    actions: list[OperatorActionResponse]
    created_at: datetime
    operation_id: UUID | None = None


class CreatePrivacyRequest(_Input):
    """Ask for one's data, or for its deletion."""

    acting_party_id: UUID
    expected_version: None
    kind: PrivacyKind


class CategoryToRemove(BaseModel):
    """A category a deletion removes."""

    key: str
    label: str


class CategoryRetained(CategoryToRemove):
    """A category a deletion keeps, with why and for how long."""

    reason: str
    period: str


class PrivacyAnswer(BaseModel):
    """The generated answer. ``removed`` lists only what has really been removed."""

    to_remove: list[CategoryToRemove]
    removed: list[CategoryToRemove]
    retained: list[CategoryRetained]
    notice: str


class PrivacyRequestResponse(BaseModel):
    """A privacy request and its answer."""

    id: UUID
    version: int
    kind: PrivacyKind
    status: PrivacyStatus
    answer: PrivacyAnswer
    policy_version: str | None
    created_at: datetime
    fulfilled_at: datetime | None
    operation_id: UUID | None = None


class FulfillPrivacyRequest(_Input):
    """Carry out a deletion against the version the operator saw."""

    acting_party_id: UUID
    expected_version: int


class PrivacyExportResponse(BaseModel):
    """Everything the requester may see now. Built on each read, so a lost permission is lost here too."""

    generated_at: datetime
    account: AccountResponse
    memberships: list[MembershipResponse]
    personal_party_id: UUID
    documents: list[PersonalDocumentMetadata]
    reports: list[ReportResponse]
    privacy_requests: list[PrivacyRequestResponse]
