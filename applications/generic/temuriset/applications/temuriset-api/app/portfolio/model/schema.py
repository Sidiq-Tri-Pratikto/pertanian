"""Invention requests and responses."""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

Stage = Literal["IDEA", "PROTOTYPE", "PILOT", "WORKING", "MARKET"]
Timing = Literal["CURRENT", "PLANNED", "REQUESTED"]
Provenance = Literal["SOURCE_REPORTED", "SELF_DECLARED", "PROVIDED", "REVIEWED", "UNKNOWN"]
ClaimKind = Literal["creator", "contributor", "manager", "rights_holder", "authority"]
ClaimStatus = Literal["asserted", "not_established", "reviewed"]


def _text(max_length: int, min_length: int = 0) -> type[str]:
    return Annotated[str, StringConstraints(strip_whitespace=True, min_length=min_length, max_length=max_length)]  # type: ignore[return-value]


class FactInput(BaseModel):
    """A fact as the owner states it."""

    label: _text(120, 1)
    value: _text(200, 1)
    unit: _text(40) = ""
    timing: Timing
    provenance: Provenance = "SELF_DECLARED"
    key: _text(64) | None = None
    document_version_id: UUID | None = None


class ClaimInput(BaseModel):
    """A people-and-rights claim as the owner states it."""

    kind: ClaimKind
    subject_name: _text(160, 1)
    party_id: UUID | None = None
    scope: _text(200) = ""
    status: ClaimStatus = "asserted"
    source: _text(200) = ""
    asserted_at: datetime | None = None


class CreateInventionRequest(BaseModel):
    """Start an invention for the acting party."""

    acting_party_id: UUID


class DraftRequest(BaseModel):
    """The whole draft. Optional fields never block a save; publication rules apply only on publish."""

    acting_party_id: UUID
    expected_version: int
    title: _text(200) = ""
    summary: _text(2000) = ""
    problem: _text(5000) = ""
    solution: _text(5000) = ""
    intended_users: _text(2000) = ""
    sector: _text(80) = ""
    stage: Stage | None = None
    keywords: Annotated[list[_text(40, 1)], Field(max_length=20)] = []
    facts: Annotated[list[FactInput], Field(max_length=50)] = []
    claims: Annotated[list[ClaimInput], Field(max_length=50)] = []
    private_notes: _text(5000) = ""


class VersionedActionRequest(BaseModel):
    """Publish or archive against the version the client saw."""

    acting_party_id: UUID
    expected_version: int


class FactResponse(FactInput):
    """A stored fact."""


class ClaimResponse(ClaimInput):
    """A stored claim."""


class InventionVersionResponse(BaseModel):
    """One version as its owner sees it."""

    number: int
    state: str
    title: str
    summary: str
    problem: str
    solution: str
    intended_users: str
    sector: str
    stage: Stage | None
    keywords: list[str]
    facts: list[FactResponse]
    claims: list[ClaimResponse]
    private_notes: str
    published_at: datetime | None


class PublicPhotoResponse(BaseModel):
    """The photo the managing party published, with its size so the page can reserve the space."""

    document_id: UUID
    version: int
    alt: str
    width: int
    height: int
    orientation: int = Field(default=1, description="EXIF orientation 1 to 8, read before metadata was removed.")


class PublicPageResponse(BaseModel):
    """The owner's choices for the public invention page (051)."""

    enabled: bool = False
    field_test: str | None = None
    photo: PublicPhotoResponse | None = None
    content_locale: Literal["id", "en"] = "id"


class InventionResponse(BaseModel):
    """The owner's view: draft, published version and history."""

    id: UUID
    managing_party_id: UUID
    status: str
    version: int
    draft: InventionVersionResponse | None
    published: InventionVersionResponse | None
    history: list[int]
    investor_digest: bool = Field(
        default=False, description="Whether the managing party allows investor alerts and digests to include it."
    )
    public_page: PublicPageResponse = Field(default_factory=PublicPageResponse)
    operation_id: UUID | None = None


class InvestorDigestRequest(BaseModel):
    """Include or exclude the published invention from investor alerts and digests."""

    model_config = ConfigDict(extra="forbid")

    acting_party_id: UUID
    expected_version: int
    enabled: bool


class PublicPhotoChoice(BaseModel):
    """One version of the managing party's own document, as the public photo."""

    model_config = ConfigDict(extra="forbid")

    document_id: UUID
    version: int = Field(ge=1)


class PublicPageRequest(BaseModel):
    """Publish or withdraw the public invention page, independent of investor alerts (051)."""

    model_config = ConfigDict(extra="forbid")

    acting_party_id: UUID
    expected_version: int
    enabled: bool
    field_test: str | None = Field(default=None, max_length=600, description="A short public field-test summary.")
    photo: PublicPhotoChoice | None = None
    photo_alt: str | None = Field(default=None, max_length=200, description="What the photo shows; required with one.")
    content_locale: Literal["id", "en"] = Field(default="id", description="The language the owner wrote in.")


class InventionSummaryResponse(BaseModel):
    """One row of Inovasi Saya."""

    id: UUID
    status: str
    title: str
    version: int
    has_draft: bool
    published_number: int | None


class PublishResponse(BaseModel):
    """The outcome of a publication."""

    version: int
    status: str
    operation_id: UUID | None = None


class PublicFactResponse(BaseModel):
    """A fact as anyone may read it."""

    label: str
    value: str
    unit: str
    timing: Timing
    provenance: Provenance


class PublicClaimResponse(BaseModel):
    """A claim as anyone may read it."""

    kind: ClaimKind
    subject_name: str
    scope: str
    status: ClaimStatus
    source: str
    asserted_at: datetime | None


class PublicInventionResponse(BaseModel):
    """The published version and nothing private."""

    id: UUID
    managing_party_id: UUID
    managing_party_name: str
    number: int
    title: str
    summary: str
    problem: str
    solution: str
    intended_users: str
    sector: str
    stage: Stage | None
    keywords: list[str]
    facts: list[PublicFactResponse]
    claims: list[PublicClaimResponse]
    published_at: datetime | None
