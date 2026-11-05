"""Access domain: capabilities, organizations, memberships, invitations."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel


class Capability(StrEnum):
    """What a member may do as an organization (FR02). A personal party holds every capability."""

    EDIT_PORTFOLIO = "edit_portfolio"
    SUBMIT_PITCH = "submit_pitch"
    REVIEW_PUBLICATION = "review_publication"
    DECIDE_PITCH = "decide_pitch"
    CONFIRM_RELATIONSHIP = "confirm_relationship"
    SCHEDULE = "schedule"
    MANAGE_MEMBERS = "manage_members"


ALL_CAPABILITIES = frozenset(Capability)


class OrganizationModel(BaseModel):
    """One organization and its party."""

    id: UUID
    party_id: UUID
    name: str
    kind: str
    version: int


class MembershipModel(BaseModel):
    """One active membership."""

    id: UUID
    organization_id: UUID
    account_id: UUID
    capabilities: list[str]
    version: int


class InvitationModel(BaseModel):
    """One invitation, without its token."""

    id: UUID
    organization_id: UUID
    email: str
    capabilities: list[str]
    expires_at: datetime
    revoked_at: datetime | None
    accepted_at: datetime | None
