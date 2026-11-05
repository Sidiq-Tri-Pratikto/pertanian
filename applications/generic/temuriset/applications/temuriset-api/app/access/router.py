"""Organizations, members, invitations and the acting context."""

from uuid import UUID

from fastapi import APIRouter, status

from app.access.model.schema import (
    ActingPartyRequest,
    ContextRequest,
    CreateOrganizationRequest,
    InvitationDetailResponse,
    InvitationResponse,
    InviteRequest,
    MemberResponse,
    OrganizationResponse,
    RemoveMemberRequest,
)
from app.access.service.service import AccessService, invitation_response
from app.core.database import SessionDep
from app.core.security import PrincipalDep
from app.core.settings import get_settings
from app.identity.model.schema import MeResponse
from app.identity.service.service import IdentityService
from app.platform.model.schema import OperationResult
from app.platform.service.idempotency import Idempotency, idempotent

router = APIRouter(tags=["organizations"])


@router.post("/organizations", status_code=status.HTTP_201_CREATED, summary="Create an organization")
async def create_organization(
    body: CreateOrganizationRequest,
    principal: PrincipalDep,
    session: SessionDep,
    operation: Idempotency = idempotent("organizations.create"),
) -> OrganizationResponse:
    """Create an organization; the creator becomes a member with every capability.

    Args:
        body (CreateOrganizationRequest): Name and kind.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.
        operation (Idempotency): Replays a retried request.

    Returns:
        OrganizationResponse: The organization and its party.
    """
    organization = await AccessService(session, get_settings()).create_organization(principal, body)
    response = OrganizationResponse(**organization.model_dump(), operation_id=operation.operation_id)
    return await operation.respond(  # type: ignore[return-value]
        response, status_code=201, result=OperationResult(type="organization", id=str(organization.id))
    )


@router.get("/organizations/{organization_id}/members", summary="List members")
async def list_members(organization_id: UUID, principal: PrincipalDep, session: SessionDep) -> list[MemberResponse]:
    """List an organization's members to its members.

    Args:
        organization_id (UUID): The organization.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.

    Returns:
        list[MemberResponse]: Members and capabilities.
    """
    return await AccessService(session, get_settings()).list_members(principal, organization_id)


@router.delete(
    "/organizations/{organization_id}/members/{account_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a member",
)
async def remove_member(
    organization_id: UUID, account_id: UUID, body: RemoveMemberRequest, principal: PrincipalDep, session: SessionDep
) -> None:
    """Remove a member, acting as the organization with ``manage_members``.

    Args:
        organization_id (UUID): The organization.
        account_id (UUID): The member.
        body (RemoveMemberRequest): Acting party and ``expected_version``.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.
    """
    await AccessService(session, get_settings()).remove_member(principal, organization_id, account_id, body)


@router.post(
    "/organizations/{organization_id}/invitations", status_code=status.HTTP_201_CREATED, summary="Invite a member"
)
async def invite(
    organization_id: UUID,
    body: InviteRequest,
    principal: PrincipalDep,
    session: SessionDep,
    operation: Idempotency = idempotent("invitations.create"),
) -> InvitationResponse:
    """Email an invitation with explicit capabilities, valid for seven days.

    Args:
        organization_id (UUID): The organization.
        body (InviteRequest): Acting party, email and capabilities.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.
        operation (Idempotency): Replays a retried request.

    Returns:
        InvitationResponse: The invitation, without its token.
    """
    invitation = await AccessService(session, get_settings()).invite(principal, organization_id, body)
    response = invitation_response(invitation, operation.operation_id)
    return await operation.respond(  # type: ignore[return-value]
        response, status_code=201, result=OperationResult(type="invitation", id=str(invitation.id))
    )


@router.get("/organizations/{organization_id}/invitations", summary="List invitations")
async def list_invitations(
    organization_id: UUID, principal: PrincipalDep, session: SessionDep
) -> list[InvitationResponse]:
    """List invitations to the organization's member managers.

    Args:
        organization_id (UUID): The organization.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.

    Returns:
        list[InvitationResponse]: Invitations with status and expiry.
    """
    return await AccessService(session, get_settings()).list_invitations(principal, organization_id)


@router.get("/invitations/{token}", summary="Read an invitation")
async def read_invitation(token: str, principal: PrincipalDep, session: SessionDep) -> InvitationDetailResponse:
    """Show the invited account what it would join.

    Args:
        token (str): The emailed token.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.

    Returns:
        InvitationDetailResponse: Organization, capabilities, expiry and status.
    """
    return await AccessService(session, get_settings()).invitation_detail(principal, token)


@router.post("/invitations/{token}/accept", summary="Accept an invitation")
async def accept_invitation(token: str, principal: PrincipalDep, session: SessionDep) -> OrganizationResponse:
    """Join the organization. Accepting twice is harmless; an expired or revoked invitation is refused.

    Args:
        token (str): The emailed token.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.

    Returns:
        OrganizationResponse: The organization joined.
    """
    organization = await AccessService(session, get_settings()).accept(principal, token)
    return OrganizationResponse(**organization.model_dump())


@router.post("/invitations/{invitation_id}/revoke", summary="Revoke an invitation")
async def revoke_invitation(
    invitation_id: UUID, body: ActingPartyRequest, principal: PrincipalDep, session: SessionDep
) -> InvitationResponse:
    """Revoke a pending invitation, acting as the organization with ``manage_members``.

    Args:
        invitation_id (UUID): The invitation.
        body (ActingPartyRequest): Acting party.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.

    Returns:
        InvitationResponse: The revoked invitation.
    """
    invitation = await AccessService(session, get_settings()).revoke(principal, invitation_id, body.acting_party_id)
    return invitation_response(invitation)


@router.put("/me/context", summary="Change who you act as")
async def set_context(body: ContextRequest, principal: PrincipalDep, session: SessionDep) -> MeResponse:
    """Act as the personal party or an organization the account belongs to.

    Args:
        body (ContextRequest): The party to act as.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.

    Returns:
        MeResponse: The account in its new context.
    """
    identity = IdentityService(session, get_settings())
    return await identity.me(await identity.set_active_party(principal, body.party_id))
