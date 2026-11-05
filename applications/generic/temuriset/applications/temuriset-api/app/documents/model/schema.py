"""Document requests and responses."""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, Field, StringConstraints

DocumentKind = Literal["evidence", "presentation", "technical", "other"]
GrantPurpose = Literal["pitch", "discussion"]


class UploadIntentRequest(BaseModel):
    """Declare a file before sending it, so size and type are refused before any byte moves."""

    acting_party_id: UUID
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
    kind: DocumentKind
    media_type: Annotated[str, StringConstraints(max_length=120)]
    size_bytes: Annotated[int, Field(gt=0)]
    document_id: UUID | None = None


class UploadIntentResponse(BaseModel):
    """Where and until when to send the bytes."""

    intent_id: UUID
    upload_url: str
    max_bytes: int
    expires_at: datetime


class UploadedResponse(BaseModel):
    """The stored version; available only after the scan."""

    document_id: UUID
    number: int
    file_state: str


class DocumentVersionResponse(BaseModel):
    """One version's three independent states."""

    number: int
    media_type: str
    size_bytes: int
    sha256: str
    file_state: str
    extraction_state: str
    review_state: str
    created_at: datetime


class GrantResponse(BaseModel):
    """Who may download which version, and how many copies already left."""

    id: UUID
    version: int
    grantee_party_id: UUID
    grantee_name: str
    purpose: str
    revoked_at: datetime | None
    downloads: int


class DocumentResponse(BaseModel):
    """A document as its owner sees it."""

    id: UUID
    title: str
    kind: str
    versions: list[DocumentVersionResponse]
    grants: list[GrantResponse]


class GrantRequest(BaseModel):
    """Share one version with one party for one purpose."""

    acting_party_id: UUID
    version: int
    grantee_party_id: UUID
    purpose: GrantPurpose
    pitch_id: UUID | None = None


class RevokeRequest(BaseModel):
    """Stop new downloads, acting as the owner."""

    acting_party_id: UUID


class RevokedResponse(BaseModel):
    """Revocation is honest about copies that already left."""

    revoked: bool
    copies_already_delivered: int
    message: str
