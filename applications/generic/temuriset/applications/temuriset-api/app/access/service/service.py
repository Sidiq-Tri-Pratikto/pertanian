"""Parties, organizations, memberships, invitations and who may act as which party."""

from datetime import timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.access.model.models import ALL_CAPABILITIES, Capability, InvitationModel, OrganizationModel
from app.access.model.schema import (
    CreateOrganizationRequest,
    InvitationDetailResponse,
    InvitationResponse,
    InviteRequest,
    MemberResponse,
    RemoveMemberRequest,
)
from app.access.repository.sqlalchemy.repository import SqlAlchemyAccessRepository
from app.access.service.policy import check_context, require
from app.core import clock
from app.core.errors import codes
from app.core.errors.base import AppError, ConflictError, ForbiddenError, NotFoundError
from app.core.settings import Settings
from app.identity.model.models import Principal
from app.identity.model.schema import MembershipResponse
from app.identity.service.accounts import account_email, display_names
from app.identity.service.codes import hash_token, new_token
from app.identity.service.mailbox_service import DisabledMailbox, MailUnavailableError, mailbox_for
from app.platform.service.audit import record_audit
from app.platform.service.versions import StaleVersionError

INVITATION_LIFETIME = timedelta(days=7)
_LAST_MANAGER = "Organisasi memerlukan setidaknya satu pengelola anggota. Tambahkan pengelola lain terlebih dahulu."


class InvitationExpiredError(AppError):
    """The invitation expired, was revoked, or was already used."""

    code = codes.APP_INVITATION_EXPIRED


async def create_personal_party(session: AsyncSession, *, account_id: UUID, display_name: str) -> UUID:
    """Create the one personal party of an account, in the caller's transaction.

    Args:
        session (AsyncSession): The request's session.
        account_id (UUID): The account.
        display_name (str): Shown wherever the party acts.

    Returns:
        UUID: The party id.
    """
    return await SqlAlchemyAccessRepository(session).add_personal_party(
        account_id=account_id, display_name=display_name
    )


async def personal_party_id(session: AsyncSession, account_id: UUID) -> UUID:
    """Return the personal party of an account.

    Args:
        session (AsyncSession): The request's session.
        account_id (UUID): The account.

    Returns:
        UUID: The party id.
    """
    party_id = await SqlAlchemyAccessRepository(session).personal_party_id(account_id)
    assert party_id is not None, "every verified account has a personal party"  # noqa: S101
    return party_id


async def capabilities_for(session: AsyncSession, account_id: UUID, party_id: UUID) -> frozenset[str] | None:
    """What an account may do as a party, checked again on every request.

    Args:
        session (AsyncSession): The request's session.
        account_id (UUID): The account.
        party_id (UUID): The party it wants to act as.

    Returns:
        frozenset[str] | None: Every capability for its personal party, the membership's capabilities for an
            organization it belongs to, or None when it may not act as that party.
    """
    repository = SqlAlchemyAccessRepository(session)
    if party_id == await repository.personal_party_id(account_id):
        return ALL_CAPABILITIES
    organization_id = await repository.organization_of_party(party_id)
    if organization_id is None:
        return None
    membership = await repository.active_membership(organization_id, account_id)
    return frozenset(membership.capabilities) if membership is not None else None


async def memberships_for(session: AsyncSession, account_id: UUID) -> list[MembershipResponse]:
    """List the organizations an account belongs to.

    Args:
        session (AsyncSession): The request's session.
        account_id (UUID): The account.

    Returns:
        list[MembershipResponse]: Organization, its party, name and the member's capabilities.
    """
    repository = SqlAlchemyAccessRepository(session)
    result = []
    for membership in await repository.active_memberships(account_id=account_id):
        organization = await repository.find_organization(membership.organization_id)
        assert organization is not None  # noqa: S101 - memberships cascade with their organization
        result.append(
            MembershipResponse(
                organization_id=organization.id,
                party_id=organization.party_id,
                name=organization.name,
                capabilities=sorted(membership.capabilities),
            )
        )
    return result


async def assert_can_act(session: AsyncSession, account_id: UUID, party_id: UUID, action: Capability) -> None:
    """Recheck access for work that runs later, such as a job a member started before being removed (AC06).

    Args:
        session (AsyncSession): The worker's or request's session.
        account_id (UUID): The account that started the work.
        party_id (UUID): The party it acted as.
        action (Capability): What the work does.

    Raises:
        NotFoundError: When the account may no longer act as the party.
        ForbiddenError: When it may, but no longer has the capability.
    """
    capabilities = await capabilities_for(session, account_id, party_id)
    if capabilities is None:
        raise NotFoundError()
    if action not in capabilities:
        raise ForbiddenError()


def _status(invitation: InvitationModel) -> str:
    if invitation.accepted_at is not None:
        return "accepted"
    if invitation.revoked_at is not None:
        return "revoked"
    return "expired" if invitation.expires_at <= clock.now() else "pending"


class AccessService:
    """Organizations, memberships and invitations for the signed-in account."""

    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        """Bind to the request.

        Args:
            session (AsyncSession): The request's session.
            settings (Settings): Settings.
        """
        self.session = session
        self.settings = settings
        self.repository = SqlAlchemyAccessRepository(session)

    async def create_organization(self, principal: Principal, request: CreateOrganizationRequest) -> OrganizationModel:
        """Create an organization; its creator joins with every capability.

        Args:
            principal (Principal): Who is signed in.
            request (CreateOrganizationRequest): Name and kind.

        Returns:
            OrganizationModel: The organization and its party.
        """
        organization = await self.repository.add_organization(name=request.name, kind=request.kind)
        await self.repository.add_membership(
            organization_id=organization.id, account_id=principal.account_id, capabilities=sorted(ALL_CAPABILITIES)
        )
        await record_audit(
            self.session,
            action="organization.created",
            subject_type="organization",
            subject_id=str(organization.id),
            actor_account_id=principal.account_id,
            actor_party_id=principal.active_party_id,
        )
        return organization

    async def _visible_organization(self, principal: Principal, organization_id: UUID) -> OrganizationModel:
        organization = await self.repository.find_organization(organization_id)
        if (
            organization is None
            or await self.repository.active_membership(organization_id, principal.account_id) is None
        ):
            raise NotFoundError()
        return organization

    async def list_members(self, principal: Principal, organization_id: UUID) -> list[MemberResponse]:
        """List members to anyone who belongs to the organization.

        Args:
            principal (Principal): Who is signed in.
            organization_id (UUID): The organization.

        Returns:
            list[MemberResponse]: Members and their capabilities.

        Raises:
            NotFoundError: When the account is not a member.
        """
        await self._visible_organization(principal, organization_id)
        memberships = await self.repository.active_memberships(organization_id=organization_id)
        names = await display_names(self.session, [membership.account_id for membership in memberships])
        return [
            MemberResponse(
                account_id=membership.account_id,
                display_name=names.get(membership.account_id, ""),
                capabilities=sorted(membership.capabilities),
                version=membership.version,
            )
            for membership in memberships
        ]

    async def remove_member(
        self, principal: Principal, organization_id: UUID, account_id: UUID, request: RemoveMemberRequest
    ) -> None:
        """Remove a member. Their past authorship stays; the last member manager cannot be removed.

        Args:
            principal (Principal): Who is signed in, acting as the organization.
            organization_id (UUID): The organization.
            account_id (UUID): The member to remove.
            request (RemoveMemberRequest): Acting party and ``expected_version``.

        Raises:
            StaleContextError: When the tab acts as another party.
            NotFoundError: When the organization or member is not visible.
            ForbiddenError: Without ``manage_members``.
            StaleVersionError: When the membership changed.
            ConflictError: When this is the last member manager.
        """
        check_context(principal, request.acting_party_id)
        organization = await self._visible_organization(principal, organization_id)
        require(principal, Capability.MANAGE_MEMBERS, organization.party_id)
        membership = await self.repository.active_membership(organization_id, account_id)
        if membership is None:
            raise NotFoundError()
        managers = [
            other
            for other in await self.repository.active_memberships(organization_id=organization_id)
            if Capability.MANAGE_MEMBERS in other.capabilities
        ]
        if Capability.MANAGE_MEMBERS in membership.capabilities and len(managers) == 1:
            raise ConflictError(_LAST_MANAGER)
        if not await self.repository.remove_membership(membership.id, request.expected_version, clock.now()):
            raise StaleVersionError(membership.version)
        await record_audit(
            self.session,
            action="membership.removed",
            subject_type="membership",
            subject_id=str(membership.id),
            actor_account_id=principal.account_id,
            actor_party_id=principal.active_party_id,
        )

    async def invite(self, principal: Principal, organization_id: UUID, request: InviteRequest) -> InvitationModel:
        """Invite an email with explicit capabilities; the link is emailed and only its hash is stored.

        Args:
            principal (Principal): Who is signed in, acting as the organization.
            organization_id (UUID): The organization.
            request (InviteRequest): Acting party, email and capabilities.

        Returns:
            InvitationModel: The invitation.

        Raises:
            StaleContextError: When the tab acts as another party.
            NotFoundError: When the organization is not visible.
            ForbiddenError: Without ``manage_members``.
        """
        check_context(principal, request.acting_party_id)
        organization = await self._visible_organization(principal, organization_id)
        require(principal, Capability.MANAGE_MEMBERS, organization.party_id)
        mailbox = mailbox_for(self.settings)
        if isinstance(mailbox, DisabledMailbox):
            raise MailUnavailableError()
        token = new_token()
        invitation = await self.repository.add_invitation(
            organization_id=organization_id,
            email=request.email,
            capabilities=sorted({str(capability) for capability in request.capabilities}),
            token_sha256=hash_token(token),
            invited_by_account_id=principal.account_id,
            expires_at=clock.now() + INVITATION_LIFETIME,
        )
        await mailbox.send(
            self.session,
            to_email=request.email,
            subject=f"Undangan bergabung dengan {organization.name} di TemuRiset",
            body=(
                f"Anda diundang bergabung dengan {organization.name}. Buka tautan ini dalam 7 hari:\n\n"
                f"{self.settings.web_origin}/undangan/{token}"
            ),
        )
        return invitation

    async def list_invitations(self, principal: Principal, organization_id: UUID) -> list[InvitationResponse]:
        """List an organization's invitations to its member managers.

        Args:
            principal (Principal): Who is signed in, acting as the organization.
            organization_id (UUID): The organization.

        Returns:
            list[InvitationResponse]: Invitations with their status.

        Raises:
            NotFoundError: When the organization is not visible.
            ForbiddenError: Without ``manage_members``.
        """
        organization = await self._visible_organization(principal, organization_id)
        require(principal, Capability.MANAGE_MEMBERS, organization.party_id)
        return [invitation_response(item) for item in await self.repository.invitations_of(organization_id)]

    async def _addressed_invitation(self, principal: Principal, token: str) -> InvitationModel:
        invitation = await self.repository.find_invitation(token_sha256=hash_token(token))
        if invitation is None or invitation.email != await account_email(self.session, principal.account_id):
            raise NotFoundError()
        return invitation

    async def invitation_detail(self, principal: Principal, token: str) -> InvitationDetailResponse:
        """Show the invited account what it would join.

        Args:
            principal (Principal): Who is signed in; must hold the invited email.
            token (str): The emailed token.

        Returns:
            InvitationDetailResponse: Organization, capabilities, expiry and status.

        Raises:
            NotFoundError: For an unknown token or another email.
        """
        invitation = await self._addressed_invitation(principal, token)
        organization = await self.repository.find_organization(invitation.organization_id)
        assert organization is not None  # noqa: S101 - invitations cascade with their organization
        return InvitationDetailResponse(
            organization_name=organization.name,
            capabilities=invitation.capabilities,
            expires_at=invitation.expires_at,
            status=_status(invitation),
        )

    async def accept(self, principal: Principal, token: str) -> OrganizationModel:
        """Join an organization with the invited capabilities.

        Args:
            principal (Principal): Who is signed in; must hold the invited email.
            token (str): The emailed token.

        Returns:
            OrganizationModel: The organization joined.

        Raises:
            NotFoundError: For an unknown token or another email.
            InvitationExpiredError: When expired, revoked or already used.
        """
        invitation = await self._addressed_invitation(principal, token)
        if _status(invitation) != "pending":
            raise InvitationExpiredError()
        await self.repository.update_invitation(invitation.id, accepted_at=clock.now())
        if await self.repository.active_membership(invitation.organization_id, principal.account_id) is None:
            await self.repository.add_membership(
                organization_id=invitation.organization_id,
                account_id=principal.account_id,
                capabilities=invitation.capabilities,
            )
        await record_audit(
            self.session,
            action="invitation.accepted",
            subject_type="invitation",
            subject_id=str(invitation.id),
            actor_account_id=principal.account_id,
            actor_party_id=principal.active_party_id,
        )
        organization = await self.repository.find_organization(invitation.organization_id)
        assert organization is not None  # noqa: S101 - invitations cascade with their organization
        return organization

    async def revoke(self, principal: Principal, invitation_id: UUID, acting_party_id: UUID) -> InvitationModel:
        """Revoke a pending invitation.

        Args:
            principal (Principal): Who is signed in, acting as the organization.
            invitation_id (UUID): The invitation.
            acting_party_id (UUID): The party the client acts as.

        Returns:
            InvitationModel: The revoked invitation.

        Raises:
            StaleContextError: When the tab acts as another party.
            NotFoundError: When the invitation is not visible.
            ForbiddenError: Without ``manage_members``.
        """
        check_context(principal, acting_party_id)
        invitation = await self.repository.find_invitation(invitation_id=invitation_id)
        if invitation is None:
            raise NotFoundError()
        organization = await self._visible_organization(principal, invitation.organization_id)
        require(principal, Capability.MANAGE_MEMBERS, organization.party_id)
        if invitation.revoked_at is None and invitation.accepted_at is None:
            await self.repository.update_invitation(invitation.id, revoked_at=clock.now())
        return invitation.model_copy(update={"revoked_at": invitation.revoked_at or clock.now()})


def invitation_response(invitation: InvitationModel, operation_id: UUID | None = None) -> InvitationResponse:
    """Render an invitation for its organization.

    Args:
        invitation (InvitationModel): The invitation.
        operation_id (UUID | None, optional): The operation that created it. Defaults to None.

    Returns:
        InvitationResponse: The response.
    """
    return InvitationResponse(
        id=invitation.id,
        email=invitation.email,
        capabilities=invitation.capabilities,
        expires_at=invitation.expires_at,
        status=_status(invitation),  # type: ignore[arg-type]
        operation_id=operation_id,
    )


async def party_names(session: AsyncSession, party_ids: list[UUID]) -> dict[UUID, str]:
    """Return how parties are shown to others.

    Args:
        session (AsyncSession): The request's session.
        party_ids (list[UUID]): The parties.

    Returns:
        dict[UUID, str]: Display name per party that exists.
    """
    return await SqlAlchemyAccessRepository(session).party_names(party_ids)


async def anonymize_personal_party(session: AsyncSession, account_id: UUID) -> None:
    """Remove the personal display name and end active memberships while retaining history."""
    await SqlAlchemyAccessRepository(session).anonymize_personal_party(account_id, clock.now())
