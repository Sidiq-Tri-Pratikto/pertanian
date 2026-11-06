"""The vocabulary of partner intake: profile states, opportunity states and typed requirements."""

from typing import Literal

from app.needs.model.schema import Basis

IntakeStatus = Literal["OPEN", "CLOSED", "UNCONFIRMED"]
ProfileSource = Literal["OWNER_CONFIRMED", "SOURCE_REPORTED"]
ContactRoute = Literal["IN_APP", "EXTERNAL", "NONE"]
OpportunityKind = Literal["SPECIFIC", "GENERAL_INTAKE"]
OpportunityStatus = Literal["DRAFT", "ACTIVE", "PAUSED", "CLOSED", "EXPIRED"]
RelationshipForm = Literal["PROJECT", "LICENSE", "EQUITY"]
Operator = Literal["equals", "in_set", "intersects", "minimum", "maximum", "range_overlap", "exists", "manual_review"]
AppliesAt = Literal["SUBMISSION", "DISCUSSION", "PILOT", "COMMERCIALIZATION"]
VerificationMode = Literal["DECLARATION", "DOCUMENT_PRESENT", "REVIEWER_CONFIRMED"]
Visibility = Literal["PUBLIC", "PARTNER_ONLY"]
AvailabilityReason = Literal[
    "SUSPENDED",
    "TARGET_NOT_ACTIVE",
    "EXTERNAL_ROUTE",
    "NO_NEW_APPROACHES",
    "DIRECT_INTAKE_CLOSED",
    "INTAKE_UNCONFIRMED",
]
FinancialSubject = Literal["partner", "investorCheck", "license"]
# One investor's check has no period of its own, so it needs a basis the project budget does not.
FinancialBasis = Basis | Literal["per_investment"]
