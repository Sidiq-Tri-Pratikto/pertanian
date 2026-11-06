"""Relationship requests and responses."""

from datetime import date, datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.needs.model.schema import AmountText

Kind = Literal["PROJECT", "LICENSE", "EQUITY"]
PublicField = Literal["name", "type", "scope", "date", "amount", "percent"]
Percent = Annotated[str, StringConstraints(pattern=r"^(100(\.0{1,2})?|\d{1,2}(\.\d{1,2})?)$")]


class PartnershipValues(BaseModel):
    """The summary both parties confirm. ``evidence`` is private and never public."""

    model_config = ConfigDict(extra="forbid")

    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
    scope: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]
    start_date: date
    amount: AmountText | None = None
    currency: Annotated[str, StringConstraints(pattern=r"^[A-Z]{3}$")] | None = None
    percent: Percent | None = Field(default=None, description="Equity only, with ``percent_date``.")
    percent_date: date | None = None
    evidence: Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)] = ""


class ProposePartnershipRequest(BaseModel):
    """Version 1, its public ceiling, and the proposer's own consent subset."""

    model_config = ConfigDict(extra="forbid")

    acting_party_id: UUID
    type: Kind
    values: PartnershipValues
    ceiling: Annotated[list[PublicField], Field(min_length=1, max_length=6)]
    subset: Annotated[list[PublicField], Field(max_length=6)] = []


class CorrectionRequest(BaseModel):
    """Correct or expand the current version; the new version starts with no confirmations."""

    model_config = ConfigDict(extra="forbid")

    acting_party_id: UUID
    version: int
    values: PartnershipValues
    ceiling: Annotated[list[PublicField], Field(min_length=1, max_length=6)] | None = None
    note: Annotated[str, StringConstraints(strip_whitespace=True, max_length=1000)] = ""


class ConfirmRequest(BaseModel):
    """Confirm the exact version and checksum the client showed, with this party's public subset."""

    model_config = ConfigDict(extra="forbid")

    acting_party_id: UUID
    version: int
    checksum: Annotated[str, StringConstraints(min_length=64, max_length=64)]
    subset: Annotated[list[PublicField], Field(max_length=6)] = []


class VersionedPartnershipRequest(BaseModel):
    """Decline the current version, against its number."""

    model_config = ConfigDict(extra="forbid")

    acting_party_id: UUID
    version: int


class RestrictRequest(BaseModel):
    """Hide one public field from now on."""

    model_config = ConfigDict(extra="forbid")

    acting_party_id: UUID
    field: PublicField


class ReviewRequest(BaseModel):
    """Contest the public claim; it is hidden while under review."""

    model_config = ConfigDict(extra="forbid")

    acting_party_id: UUID
    reason: Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)] = ""


class PartyName(BaseModel):
    """A party of the relationship."""

    party_id: UUID
    name: str


class ConfirmationResponse(BaseModel):
    """One party's confirmation of a version."""

    party_id: UUID
    subset: list[str]
    confirmed_at: datetime


class PartnershipVersionResponse(BaseModel):
    """One version with its confirmations."""

    number: int
    status: Literal["PENDING_COUNTERPARTY", "CONFIRMED", "CHANGES_REQUESTED", "DECLINED"]
    values: dict[str, Any]
    ceiling: list[str]
    checksum: str
    proposed_by_party_id: UUID
    note: str
    created_at: datetime
    confirmations: list[ConfirmationResponse]


class RestrictionResponse(BaseModel):
    """One restriction."""

    field: str
    party_id: UUID
    created_at: datetime


class EffectiveResponse(BaseModel):
    """What may be public now: the newest version both confirmed, cut by subsets and restrictions."""

    version: int | None
    fields: list[str]
    values: dict[str, Any]


class PartnershipResponse(BaseModel):
    """A relationship as its two parties see it."""

    id: UUID
    pitch_id: UUID
    type: Kind
    parties: list[PartyName]
    invention_ids: list[UUID]
    contested: bool
    current: PartnershipVersionResponse
    versions: list[PartnershipVersionResponse]
    restrictions: list[RestrictionResponse]
    effective: EffectiveResponse
    allowed_actions: list[str]
    operation_id: UUID | None = None


class SaveProfileRequest(BaseModel):
    """Publish or change the acting party's public profile."""

    model_config = ConfigDict(extra="forbid")

    acting_party_id: UUID
    expected_version: int
    bio: Annotated[str, StringConstraints(strip_whitespace=True, max_length=2000)] = ""
    published: bool


class ProfileResponse(BaseModel):
    """The acting party's own profile settings."""

    party_id: UUID
    bio: str
    published: bool
    version: int


class PublicInvention(BaseModel):
    """A published invention the party manages."""

    id: UUID
    title: str
    role: str


class PublicRelationship(BaseModel):
    """One confirmed relationship, only its fields both parties allowed (AC55)."""

    id: UUID
    role: str
    counterpart_party_id: UUID
    counterpart_name: str
    fields: dict[str, Any]
    inventions: list[PublicInvention]


class PublicProfileResponse(BaseModel):
    """What anyone may see of a party, computed now from publication and consent (FR-001)."""

    party_id: UUID
    name: str
    bio: str | None
    inventions: list[PublicInvention]
    relationships: list[PublicRelationship]
    nothing_published: bool
