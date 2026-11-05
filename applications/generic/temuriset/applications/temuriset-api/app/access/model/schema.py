"""Organization, membership, invitation and context requests and responses."""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, Field, StringConstraints

from app.access.model.models import Capability
from app.identity.model.schema import Email

OrganizationKind = Literal["company", "nonprofit", "community", "research_group", "other"]


class CreateOrganizationRequest(BaseModel):
    """Create an organization; the creator becomes a member with every capability."""

    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    kind: OrganizationKind


class OrganizationResponse(BaseModel):
    """One organization."""

    id: UUID
    party_id: UUID
    name: str
    kind: str
    version: int
    operation_id: UUID | None = None


class MemberResponse(BaseModel):
    """One member and what they may do."""

    account_id: UUID
    display_name: str
    capabilities: list[str]
    version: int


class RemoveMemberRequest(BaseModel):
    """Remove a member, acting as the organization."""

    acting_party_id: UUID
    expected_version: int


class InviteRequest(BaseModel):
    """Invite an email with explicit capabilities, acting as the organization."""

    acting_party_id: UUID
    email: Email
    capabilities: Annotated[list[Capability], Field(min_length=1)]


class InvitationResponse(BaseModel):
    """One invitation, as its organization sees it."""

    id: UUID
    email: str
    capabilities: list[str]
    expires_at: datetime
    status: Literal["pending", "accepted", "revoked", "expired"]
    operation_id: UUID | None = None


class InvitationDetailResponse(BaseModel):
    """What the invited account sees before accepting."""

    organization_name: str
    capabilities: list[str]
    expires_at: datetime
    status: Literal["pending", "accepted", "revoked", "expired"]


class ActingPartyRequest(BaseModel):
    """A consequential action names the party it acts as, so two tabs cannot cross contexts."""

    acting_party_id: UUID


class ContextRequest(BaseModel):
    """Act as another party: the personal party or an organization the account belongs to."""

    party_id: UUID
