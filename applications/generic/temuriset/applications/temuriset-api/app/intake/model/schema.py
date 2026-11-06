"""Partner profile, opportunity and handoff requests and responses. Inputs refuse any field they do not name."""

from datetime import date
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import AnyHttpUrl, AwareDatetime, BaseModel, ConfigDict, Field, StringConstraints, UrlConstraints

from app.intake.model.models import (
    AppliesAt,
    AvailabilityReason,
    ContactRoute,
    FinancialBasis,
    FinancialSubject,
    IntakeStatus,
    Operator,
    OpportunityKind,
    OpportunityStatus,
    ProfileSource,
    RelationshipForm,
    VerificationMode,
    Visibility,
)
from app.needs.model.schema import AmountText, UnknownReason
from app.portfolio.model.schema import Stage

MAX_REQUIREMENTS = 50

CurrencyText = Annotated[str, StringConstraints(pattern=r"^[A-Z]{3}$")]
ExternalUrl = Annotated[AnyHttpUrl, UrlConstraints(max_length=2000)]
Tag = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]


def _text(max_length: int) -> type[str]:
    return Annotated[str, StringConstraints(strip_whitespace=True, max_length=max_length)]  # type: ignore[return-value]


class _Input(BaseModel):
    """Refuses unnamed fields, so nobody can state assets under management, capacity or credentials here."""

    model_config = ConfigDict(extra="forbid")


class RangeInput(_Input):
    """An amount range and what it means. Leave min and max empty with a reason when it is not known."""

    subject: FinancialSubject = "partner"
    basis: FinancialBasis | None = None
    min: AmountText | None = None
    max: AmountText | None = None
    currency: CurrencyText | None = None
    period: _text(80) = ""
    months: Annotated[int, Field(ge=1, le=120)] | None = None
    unknown_reason: UnknownReason | None = None


class FinancialInput(RangeInput):
    """What an opportunity offers: a comparable range, non-cash support, license terms, or an explained unknown."""

    scope: _text(2000) = ""
    noncash: _text(500) = ""
    terms: _text(500) = ""


class PartnerProfileContent(_Input):
    """What a partner states about itself. Thesis is general; ``intake_status`` is about now."""

    subtype: _text(120) = ""
    thesis: _text(2000) = ""
    sectors: Annotated[list[Tag], Field(max_length=30)] = []
    stages: Annotated[list[Stage], Field(max_length=5)] = []
    regions: Annotated[list[Tag], Field(max_length=30)] = []
    support_forms: Annotated[list[Tag], Field(max_length=30)] = []
    relationship_forms: Annotated[list[RelationshipForm], Field(max_length=3)] = []
    review_expectations: _text(2000) = ""
    check_range: RangeInput | None = None
    intake_from: date | None = None
    intake_until: date | None = None
    contact_route: ContactRoute = "IN_APP"
    external_url: ExternalUrl | None = None


class SavePartnerProfileRequest(PartnerProfileContent):
    """Save one's own profile. ``expected_version`` is null only for the first save."""

    acting_party_id: UUID
    expected_version: int | None = None
    intake_status: Literal["OPEN", "CLOSED"] = "OPEN"


class RangeResponse(BaseModel):
    """A stored range. Unknown money is ``null`` with ``unknown_reason``, never zero."""

    subject: FinancialSubject
    basis: FinancialBasis | None
    min: str | None
    max: str | None
    currency: str | None
    period: str
    months: int | None
    unknown_reason: UnknownReason | None


class AvailabilityResponse(BaseModel):
    """Current availability, kept apart from the general thesis and labelled with where it comes from."""

    source: ProfileSource
    source_label: str
    intake_status: IntakeStatus
    current_intake_status: IntakeStatus
    label: str
    intake_from: date | None
    intake_until: date | None


class PartnerProfileResponse(BaseModel):
    """A partner profile as anyone signed in may read it."""

    party_id: UUID
    party_name: str
    version: int
    subtype: str
    thesis: str
    sectors: list[str]
    stages: list[Stage]
    regions: list[str]
    support_forms: list[str]
    relationship_forms: list[RelationshipForm]
    review_expectations: str
    check_range: RangeResponse | None
    availability: AvailabilityResponse
    contact_route: ContactRoute
    external_url: str | None
    operation_id: UUID | None = None


class RequirementInput(_Input):
    """One requirement. With no operator it is a narrative review question and can never block a pitch."""

    label: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    field: _text(80) | None = None
    operator: Operator | None = None
    value: Any = None
    mandatory: bool = True
    applies_at: AppliesAt = "SUBMISSION"
    verification_mode: VerificationMode = "DECLARATION"
    visibility: Visibility = "PUBLIC"
    reason: _text(1000) = ""


class OpportunityContent(_Input):
    """One opportunity's content. A draft may be incomplete; going live needs the fields a partner must state."""

    title: _text(200) = ""
    outcome: _text(2000) = ""
    included: _text(2000) = ""
    excluded: _text(2000) = ""
    support: _text(2000) = ""
    accepted_stages: Annotated[list[Stage], Field(max_length=5)] = []
    relationship_forms: Annotated[list[RelationshipForm], Field(max_length=3)] = []
    sectors: Annotated[list[Tag], Field(max_length=30)] = []
    keywords: Annotated[list[Tag], Field(max_length=50)] = []
    timing: _text(500) = ""
    financial: FinancialInput | None = None
    requirements: Annotated[list[RequirementInput], Field(max_length=MAX_REQUIREMENTS)] = []
    closes_at: AwareDatetime | None = None


class CreateOpportunityRequest(OpportunityContent):
    """Start a draft for the acting party."""

    acting_party_id: UUID
    kind: OpportunityKind = "SPECIFIC"


class SaveOpportunityRequest(OpportunityContent):
    """Replace the content against the version the client saw."""

    acting_party_id: UUID
    expected_version: int


class OpportunityTransitionRequest(_Input):
    """Activate, pause or close against the version the client saw."""

    acting_party_id: UUID
    expected_version: int


class RequirementResponse(BaseModel):
    """A stored requirement. ``version`` is the number of the opportunity version it belongs to."""

    id: UUID
    label: str
    field: str
    operator: Operator
    value: Any
    mandatory: bool
    applies_at: AppliesAt
    verification_mode: VerificationMode
    visibility: Visibility
    reason: str
    version: int


class FinancialResponse(BaseModel):
    """A stored financial basis, with amounts as decimal strings."""

    subject: FinancialSubject
    basis: FinancialBasis | None = None
    min: str | None = None
    max: str | None = None
    currency: str | None = None
    period: str = ""
    months: int | None = None
    scope: str = ""
    noncash: str = ""
    terms: str = ""
    unknown_reason: UnknownReason | None = None


class TargetAvailabilityResponse(BaseModel):
    """Whether a pitch may target this now, and why not when it may not."""

    available: bool
    reason: AvailabilityReason | None


class OpportunityVersionContent(BaseModel):
    """The content of one opportunity version."""

    number: int
    title: str
    outcome: str
    included: str
    excluded: str
    support: str
    accepted_stages: list[Stage]
    relationship_forms: list[RelationshipForm]
    sectors: list[str]
    keywords: list[str]
    timing: str
    financial: FinancialResponse | None
    requirements: list[RequirementResponse]


class OpportunityResponse(OpportunityVersionContent):
    """An opportunity and its current version. ``version`` is for ``expected_version``; ``number`` names the content."""

    id: UUID
    partner_party_id: UUID
    version: int
    current_version_id: UUID
    kind: OpportunityKind
    status: OpportunityStatus
    closes_at: AwareDatetime | None
    target_availability: TargetAvailabilityResponse
    general_intake_label: str | None
    operation_id: UUID | None = None


class OpportunityVersionResponse(OpportunityVersionContent):
    """One version as it stood. A pitch keeps pointing at the version it targeted."""

    id: UUID
    opportunity_id: UUID
    status: OpportunityStatus


class RecordHandoffRequest(_Input):
    """Record that the acting party followed a partner's external route."""

    acting_party_id: UUID


class HandoffResponse(BaseModel):
    """An external handoff. It is never a submitted or accepted pitch."""

    id: UUID
    partner_party_id: UUID
    external_url: str
    submitted: Literal[False] = False
    operation_id: UUID | None = None
