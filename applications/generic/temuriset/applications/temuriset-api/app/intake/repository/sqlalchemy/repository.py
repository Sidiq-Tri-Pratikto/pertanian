"""Partner intake data access. Writes join the caller's transaction."""

from typing import Any
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.intake.repository.sqlalchemy.models import (
    OpportunityRecord,
    OpportunityVersionRecord,
    PartnerProfileRecord,
    RequirementRecord,
)


class SqlAlchemyIntakeRepository:
    """Partner profiles and opportunities over one session."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind to a session.

        Args:
            session (AsyncSession): The request's session.
        """
        self.session = session

    async def add(self, record: Any) -> Any:
        """Insert a row.

        Args:
            record (Any): An ORM row.

        Returns:
            Any: The row with generated values.
        """
        self.session.add(record)
        await self.session.flush()
        return record

    async def profile(self, party_id: UUID, *, lock: bool = False) -> PartnerProfileRecord | None:
        """Find a party's profile.

        Args:
            party_id (UUID): The party.
            lock (bool, optional): Lock it for this transaction. Defaults to False.

        Returns:
            PartnerProfileRecord | None: The profile.
        """
        query = select(PartnerProfileRecord).where(PartnerProfileRecord.party_id == party_id)
        return await self.session.scalar(query.with_for_update() if lock else query)

    async def insert_first_profile(self, values: dict[str, Any]) -> bool:
        """Insert a party's first profile unless another request just did.

        Args:
            values (dict[str, Any]): Profile columns, with ``party_id``.

        Returns:
            bool: True when this call created it; False when it lost the race to another first save.
        """
        statement = (
            insert(PartnerProfileRecord)
            .values(**values)
            .on_conflict_do_nothing(index_elements=[PartnerProfileRecord.party_id])
            .returning(PartnerProfileRecord.id)
        )
        return await self.session.scalar(statement) is not None

    async def find(self, opportunity_id: UUID, *, lock: bool = False) -> OpportunityRecord | None:
        """Find an opportunity.

        Args:
            opportunity_id (UUID): The opportunity.
            lock (bool, optional): Lock it for this transaction. Defaults to False.

        Returns:
            OpportunityRecord | None: The opportunity.
        """
        query = select(OpportunityRecord).where(OpportunityRecord.id == opportunity_id)
        return await self.session.scalar(query.with_for_update() if lock else query)

    async def of_partner(self, party_id: UUID, *, include_drafts: bool, limit: int | None) -> list[OpportunityRecord]:
        """List a partner's opportunities.

        Args:
            party_id (UUID): The partner.
            include_drafts (bool): Whether drafts are included; only the owner may see them.
            limit (int): The most to return.

        Returns:
            list[OpportunityRecord]: Newest change first.
        """
        query = select(OpportunityRecord).where(OpportunityRecord.partner_party_id == party_id)
        if not include_drafts:
            query = query.where(OpportunityRecord.status != "DRAFT")
        return list(await self.session.scalars(query.order_by(OpportunityRecord.updated_at.desc()).limit(limit)))

    async def live(self, limit: int) -> list[OpportunityRecord]:
        """List opportunities stored as active, of every partner, oldest first so the order is stable.

        Args:
            limit (int): The most to return.

        Returns:
            list[OpportunityRecord]: Opportunities; the caller still checks ``closes_at``.
        """
        query = select(OpportunityRecord).where(OpportunityRecord.status == "ACTIVE")
        return list(
            await self.session.scalars(query.order_by(OpportunityRecord.created_at, OpportunityRecord.id).limit(limit))
        )

    async def open_general_intake(self, party_id: UUID) -> OpportunityRecord | None:
        """Find a partner's general intake that is not closed or expired.

        Args:
            party_id (UUID): The partner.

        Returns:
            OpportunityRecord | None: The opportunity.
        """
        return await self.session.scalar(
            select(OpportunityRecord).where(
                OpportunityRecord.partner_party_id == party_id,
                OpportunityRecord.kind == "GENERAL_INTAKE",
                OpportunityRecord.status.not_in(("CLOSED", "EXPIRED")),
            )
        )

    async def version(self, version_id: UUID) -> OpportunityVersionRecord | None:
        """Read one version by id.

        Args:
            version_id (UUID): The version.

        Returns:
            OpportunityVersionRecord | None: The version.
        """
        return await self.session.get(OpportunityVersionRecord, version_id)

    async def version_by_number(self, opportunity_id: UUID, number: int) -> OpportunityVersionRecord | None:
        """Read one version by its number.

        Args:
            opportunity_id (UUID): The opportunity.
            number (int): The version number.

        Returns:
            OpportunityVersionRecord | None: The version.
        """
        return await self.session.scalar(
            select(OpportunityVersionRecord).where(
                OpportunityVersionRecord.opportunity_id == opportunity_id, OpportunityVersionRecord.number == number
            )
        )

    async def versions(self, version_ids: list[UUID]) -> dict[UUID, OpportunityVersionRecord]:
        """Read several versions at once.

        Args:
            version_ids (list[UUID]): The versions.

        Returns:
            dict[UUID, OpportunityVersionRecord]: Each version by id.
        """
        rows = await self.session.scalars(
            select(OpportunityVersionRecord).where(OpportunityVersionRecord.id.in_(version_ids))
        )
        return {row.id: row for row in rows}

    async def requirements(self, version_ids: list[UUID]) -> dict[UUID, list[RequirementRecord]]:
        """Read the requirements of several versions at once.

        Args:
            version_ids (list[UUID]): The versions.

        Returns:
            dict[UUID, list[RequirementRecord]]: Requirements per version, in their stored order.
        """
        found: dict[UUID, list[RequirementRecord]] = {version_id: [] for version_id in version_ids}
        rows = await self.session.scalars(
            select(RequirementRecord)
            .where(RequirementRecord.opportunity_version_id.in_(version_ids))
            .order_by(RequirementRecord.position)
        )
        for row in rows:
            found[row.opportunity_version_id].append(row)
        return found

    async def replace_requirements(self, version_id: UUID, rows: list[dict[str, Any]]) -> None:
        """Replace the requirements of a version that has not gone live.

        Args:
            version_id (UUID): The version.
            rows (list[dict[str, Any]]): Requirement columns, in order.
        """
        await self.session.execute(
            delete(RequirementRecord).where(RequirementRecord.opportunity_version_id == version_id)
        )
        for position, row in enumerate(rows):
            self.session.add(RequirementRecord(opportunity_version_id=version_id, position=position, **row))
        await self.session.flush()

    async def delete_profile(self, profile: PartnerProfileRecord) -> None:
        """Withdraw a current partner profile."""
        await self.session.delete(profile)
