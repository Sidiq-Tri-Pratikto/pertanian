"""Support request and budget requests and responses. Money crosses the wire as decimal strings only."""

from datetime import date
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, Field, StringConstraints

SupportForm = Literal[
    "project_funding", "testing_support", "mentoring", "facilities", "distribution", "technical_partner", "other"
]
RelationshipForm = Literal["PROJECT", "LICENSE"]
Basis = Literal["total_period", "monthly", "yearly"]
UnknownReason = Literal["not_determined", "not_disclosed"]


def _text(max_length: int) -> type[str]:
    return Annotated[str, StringConstraints(strip_whitespace=True, max_length=max_length)]  # type: ignore[return-value]


# Amounts are strings here and parsed exactly in the service, so a negative or malformed value gets a field message.
AmountText = Annotated[str, StringConstraints(strict=True, strip_whitespace=True, max_length=24)]


class BudgetLineInput(BaseModel):
    """One cost line."""

    label: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    quantity: AmountText
    unit_cost: AmountText
    explanation: _text(500) = ""


class BudgetInput(BaseModel):
    """The cost range of the request. Leave min and max empty with a reason when it is not known yet."""

    min: AmountText | None = None
    max: AmountText | None = None
    currency: Annotated[str, StringConstraints(pattern=r"^[A-Z]{3}$")] | None = None
    basis: Basis = "total_period"
    period: _text(80) = ""
    scope: _text(2000) = ""
    estimated_on: date | None = None
    assumptions: _text(2000) = ""
    unknown_reason: UnknownReason | None = None
    financial: bool = True
    lines: Annotated[list[BudgetLineInput], Field(max_length=50)] = []
    lines_explanation: _text(1000) = ""


class SupportRequestInput(BaseModel):
    """A support request's content. A draft may be incomplete; activation needs an outcome and support forms."""

    acting_party_id: UUID
    outcome: _text(200) = ""
    support_forms: Annotated[list[SupportForm], Field(max_length=7)] = []
    relationship_form: RelationshipForm = "PROJECT"
    scope: _text(2000) = ""
    months: Annotated[int, Field(ge=1, le=120)] | None = None
    region: _text(120) = ""
    accepts_partial: bool = False
    accepts_noncash: bool = False
    noncash_description: _text(1000) = ""
    budget: BudgetInput | None = None


class CreateSupportRequest(SupportRequestInput):
    """Start a request for a published invention."""

    invention_id: UUID


class UpdateSupportRequest(SupportRequestInput):
    """Replace the content against the version the client saw."""

    expected_version: int


class TransitionRequest(BaseModel):
    """Activate, pause or close against the version the client saw."""

    acting_party_id: UUID
    expected_version: int


class BudgetLineResponse(BaseModel):
    """A stored line and its exact total."""

    label: str
    quantity: str
    unit_cost: str
    total: str
    explanation: str


class BudgetResponse(BaseModel):
    """A stored budget. Unknown money is ``null`` with ``unknown_reason``, never zero."""

    min: str | None
    max: str | None
    currency: str | None
    basis: Basis
    period: str
    scope: str
    estimated_on: date | None
    assumptions: str
    unknown_reason: UnknownReason | None
    financial: bool
    lines: list[BudgetLineResponse]
    lines_total: str | None
    lines_explanation: str


class SupportRequestResponse(BaseModel):
    """One support request as its owner sees it."""

    id: UUID
    version: int
    invention_id: UUID
    invention_version: int
    invention_title: str
    outcome: str
    support_forms: list[str]
    relationship_form: RelationshipForm
    scope: str
    months: int | None
    region: str
    accepts_partial: bool
    accepts_noncash: bool
    noncash_description: str
    status: str
    budget: BudgetResponse | None
    operation_id: UUID | None = None
