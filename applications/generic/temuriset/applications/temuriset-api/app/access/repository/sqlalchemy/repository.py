"""Access data access. Writes join the caller's transaction."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.access.model.models import InvitationModel, MembershipModel, OrganizationModel
from app.access.repository.sqlalchemy.models import (
    InvitationRecord,
    MembershipRecord,
    OrganizationRecord,
    PartyRecord,
)


def _membership(record: MembershipRecord) -> MembershipModel:
    return MembershipModel.model_validate(record, from_attributes=True)


def _invitation(record: InvitationRecord) -> InvitationModel:
    return InvitationModel.model_validate(record, from_attributes=True)


class SqlAlchemyAccessRepository:
    """Parties, organizations, memberships and invitations over one session."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind to a session.

        Args:
            session (AsyncSession): The request's session.
        """
        self.session = session

    async def add_personal_party(self, *, account_id: UUID, display_name: str) -> UUID:
        """Insert a personal party.

        Args:
            account_id (UUID): The account.
            display_name (str): Shown wherever the party acts.

        Returns:
            UUID: The party id.
        """
        record = PartyRecord(kind="personal", display_name=display_name, account_id=account_id)
        self.session.add(record)
        await self.session.flush()
        return record.id

    async def personal_party_id(self, account_id: UUID) -> UUID | None:
        """Find the personal party of an account.

        Args:
            account_id (UUID): The account.

        Returns:
            UUID | None: The party id.
        """
        return await self.session.scalar(select(PartyRecord.id).where(PartyRecord.account_id == account_id))

    async def add_organization(self, *, name: str, kind: str) -> OrganizationModel:
        """Insert an organization with its party.

        Args:
            name (str): Organization name.
            kind (str): Organization kind.

        Returns:
            OrganizationModel: The organization.
        """
        organization = OrganizationRecord(name=name, kind=kind)
        self.session.add(organization)
        await self.session.flush()
        party = PartyRecord(kind="organization", display_name=name, organization_id=organization.id)
        self.session.add(party)
        await self.session.flush()
        return OrganizationModel(
            id=organization.id, party_id=party.id, name=name, kind=kind, version=organization.version
        )

    async def find_organization(self, organization_id: UUID) -> OrganizationModel | None:
        """Find an organization with its party.

        Args:
            organization_id (UUID): The organization.

        Returns:
            OrganizationModel | None: The organization.
        """
        row = (
            await self.session.execute(
                select(OrganizationRecord, PartyRecord.id)
                .join(PartyRecord, PartyRecord.organization_id == OrganizationRecord.id)
                .where(OrganizationRecord.id == organization_id)
            )
        ).first()
        if row is None:
            return None
        organization, party_id = row
        return OrganizationModel(
            id=organization.id,
            party_id=party_id,
            name=organization.name,
            kind=organization.kind,
            version=organization.version,
        )

    async def organization_of_party(self, party_id: UUID) -> UUID | None:
        """Find the organization behind an organization party.

        Args:
            party_id (UUID): The party.

        Returns:
            UUID | None: The organization id, or None for a personal or unknown party.
        """
        return await self.session.scalar(select(PartyRecord.organization_id).where(PartyRecord.id == party_id))

    async def add_membership(self, *, organization_id: UUID, account_id: UUID, capabilities: list[str]) -> None:
        """Insert an active membership.

        Args:
            organization_id (UUID): The organization.
            account_id (UUID): The member.
            capabilities (list[str]): What the member may do.
        """
        self.session.add(
            MembershipRecord(organization_id=organization_id, account_id=account_id, capabilities=capabilities)
        )
        await self.session.flush()

    async def active_membership(self, organization_id: UUID, account_id: UUID) -> MembershipModel | None:
        """Find an account's active membership in an organization.

        Args:
            organization_id (UUID): The organization.
            account_id (UUID): The account.

        Returns:
            MembershipModel | None: The membership.
        """
        record = await self.session.scalar(
            select(MembershipRecord).where(
                MembershipRecord.organization_id == organization_id,
                MembershipRecord.account_id == account_id,
                MembershipRecord.status == "active",
            )
        )
        return _membership(record) if record is not None else None

    async def active_memberships(
        self, *, organization_id: UUID | None = None, account_id: UUID | None = None
    ) -> list[MembershipModel]:
        """List active memberships of an organization or of an account.

        Args:
            organization_id (UUID | None, optional): The organization. Defaults to None.
            account_id (UUID | None, optional): The account. Defaults to None.

        Returns:
            list[MembershipModel]: Oldest first.
        """
        query = select(MembershipRecord).where(MembershipRecord.status == "active")
        if organization_id is not None:
            query = query.where(MembershipRecord.organization_id == organization_id)
        if account_id is not None:
            query = query.where(MembershipRecord.account_id == account_id)
        return [
            _membership(record) for record in await self.session.scalars(query.order_by(MembershipRecord.created_at))
        ]

    async def remove_membership(self, membership_id: UUID, expected_version: int, now: datetime) -> bool:
        """Mark a membership removed if still at ``expected_version``.

        Args:
            membership_id (UUID): The membership.
            expected_version (int): The version the client saw.
            now (datetime): Product time.

        Returns:
            bool: False when the version moved on.
        """
        result = await self.session.execute(
            update(MembershipRecord)
            .where(MembershipRecord.id == membership_id, MembershipRecord.version == expected_version)
            .values(status="removed", revoked_at=now, version=MembershipRecord.version + 1)
        )
        return result.rowcount == 1  # type: ignore[attr-defined]

    async def add_invitation(self, **values: Any) -> InvitationModel:
        """Insert an invitation.

        Args:
            **values (Any): Column values.

        Returns:
            InvitationModel: The invitation.
        """
        record = InvitationRecord(**values)
        self.session.add(record)
        await self.session.flush()
        return _invitation(record)

    async def find_invitation(
        self, *, invitation_id: UUID | None = None, token_sha256: str | None = None
    ) -> InvitationModel | None:
        """Find an invitation by id or by token hash, locked for this transaction.

        Args:
            invitation_id (UUID | None, optional): The invitation. Defaults to None.
            token_sha256 (str | None, optional): Hashed token. Defaults to None.

        Returns:
            InvitationModel | None: The invitation.
        """
        query = select(InvitationRecord).with_for_update()
        if invitation_id is not None:
            query = query.where(InvitationRecord.id == invitation_id)
        if token_sha256 is not None:
            query = query.where(InvitationRecord.token_sha256 == token_sha256)
        record = await self.session.scalar(query)
        return _invitation(record) if record is not None else None

    async def invitations_of(self, organization_id: UUID) -> list[InvitationModel]:
        """List an organization's invitations, newest first.

        Args:
            organization_id (UUID): The organization.

        Returns:
            list[InvitationModel]: Invitations.
        """
        rows = await self.session.scalars(
            select(InvitationRecord)
            .where(InvitationRecord.organization_id == organization_id)
            .order_by(InvitationRecord.created_at.desc())
        )
        return [_invitation(record) for record in rows]

    async def update_invitation(self, invitation_id: UUID, **values: Any) -> None:
        """Change an invitation.

        Args:
            invitation_id (UUID): The invitation.
            **values (Any): Column values.
        """
        await self.session.execute(
            update(InvitationRecord).where(InvitationRecord.id == invitation_id).values(**values)
        )

    async def party_names(self, party_ids: list[UUID]) -> dict[UUID, str]:
        """Read party display names.

        Args:
            party_ids (list[UUID]): The parties.

        Returns:
            dict[UUID, str]: Display name per party that exists.
        """
        rows = await self.session.execute(
            select(PartyRecord.id, PartyRecord.display_name).where(PartyRecord.id.in_(party_ids))
        )
        return {party_id: name for party_id, name in rows}

    async def anonymize_personal_party(self, account_id: UUID, now: datetime) -> None:
        """Clear personal presentation and end membership access without changing organizations."""
        await self.session.execute(
            update(PartyRecord)
            .where(PartyRecord.account_id == account_id)
            .values(display_name="Akun dihapus", version=PartyRecord.version + 1)
        )
        await self.session.execute(
            update(MembershipRecord)
            .where(MembershipRecord.account_id == account_id, MembershipRecord.status == "active")
            .values(status="removed", revoked_at=now, version=MembershipRecord.version + 1)
        )
