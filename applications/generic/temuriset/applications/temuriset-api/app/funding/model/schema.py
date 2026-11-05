"""Funding requests and legal entities. Money crosses the wire as decimal strings only.

Inputs refuse unknown fields: no valuation, share count or percentage is accepted, so none can be stored or derived.
"""

from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.needs.model.schema import AmountText

SubjectType = Literal["EXISTING_ENTITY", "PROPOSED_ENTITY"]
FinancingStage = Literal["pre_seed", "seed", "series_a", "series_b_plus", "bridge"]
FinancingForm = Literal["equity", "convertible_note", "safe", "debt", "revenue_based"]
ReviewStatus = Literal["declared", "verified"]
PROPOSED_LABEL = "Perusahaan belum didirikan"


def _text(max_length: int, min_length: int = 0) -> type[str]:
    return Annotated[  # type: ignore[return-value]
        str, StringConstraints(strip_whitespace=True, min_length=min_length, max_length=max_length)
    ]


class LegalEntityInput(BaseModel):
    """A company the acting party declares."""

    model_config = ConfigDict(extra="forbid")

    acting_party_id: UUID
    name: _text(200, 2)
    jurisdiction: _text(120) = ""
    registration_reference: _text(120) = ""


class LegalEntityResponse(BaseModel):
    """A legal entity. ``declared`` means the owner said so; nobody has checked it yet."""

    id: UUID
    name: str
    jurisdiction: str
    registration_reference: str
    review_status: ReviewStatus


class FundingRequestInput(BaseModel):
    """A raise's content. A draft may be incomplete; activation needs a target, a currency and an invention."""

    model_config = ConfigDict(extra="forbid")

    acting_party_id: UUID
    subject_type: SubjectType
    legal_entity_id: UUID | None = None
    proposed_name: _text(200) = ""
    financing_stage: FinancingStage | None = None
    financing_form: FinancingForm | None = None
    currency: Annotated[str, StringConstraints(pattern=r"^[A-Z]{3}$")] | None = None
    target_amount: AmountText | None = None
    desired_min: AmountText | None = None
    desired_max: AmountText | None = None
    accepts_partial: bool = False
    accepts_syndicated: bool = False
    intended_use: _text(2000) = ""
    timing: _text(200) = ""
    invention_ids: Annotated[list[UUID], Field(max_length=20)] = []


class UpdateFundingRequest(FundingRequestInput):
    """Replace the content against the version the client saw."""

    expected_version: int


class LinkedInvention(BaseModel):
    """An invention version the raise develops."""

    invention_id: UUID
    version: int
    title: str


class FundingRequestResponse(BaseModel):
    """One funding request as its owner sees it."""

    id: UUID
    version: int
    subject_type: SubjectType
    subject_label: str
    legal_entity: LegalEntityResponse | None
    proposed_name: str
    financing_stage: FinancingStage | None
    financing_form: FinancingForm | None
    currency: str | None
    target_amount: str | None
    desired_min: str | None
    desired_max: str | None
    accepts_partial: bool
    accepts_syndicated: bool
    intended_use: str
    timing: str
    inventions: list[LinkedInvention]
    status: str
    operation_id: UUID | None = None
