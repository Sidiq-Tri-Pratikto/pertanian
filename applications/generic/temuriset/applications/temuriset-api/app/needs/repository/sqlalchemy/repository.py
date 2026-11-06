"""Needs data access. Writes join the caller's transaction."""

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.needs.repository.sqlalchemy.models import (
    ProjectBudgetLineRecord,
    ProjectBudgetRecord,
    SupportRequestRecord,
    SupportRequestVersionRecord,
)


class SqlAlchemyNeedsRepository:
    """Support requests over one session."""

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

    async def find(self, request_id: UUID, *, lock: bool = False) -> SupportRequestRecord | None:
        """Find a request.

        Args:
            request_id (UUID): The request.
            lock (bool, optional): Lock it for this transaction. Defaults to False.

        Returns:
            SupportRequestRecord | None: The request.
        """
        query = select(SupportRequestRecord).where(SupportRequestRecord.id == request_id)
        return await self.session.scalar(query.with_for_update() if lock else query)

    async def of_party(self, party_id: UUID, invention_id: UUID | None) -> list[SupportRequestRecord]:
        """List a party's requests, optionally for one invention.

        Args:
            party_id (UUID): The owner.
            invention_id (UUID | None): Only this invention's.

        Returns:
            list[SupportRequestRecord]: Newest change first.
        """
        query = select(SupportRequestRecord).where(SupportRequestRecord.owner_party_id == party_id)
        if invention_id is not None:
            query = query.where(SupportRequestRecord.invention_id == invention_id)
        return list(await self.session.scalars(query.order_by(SupportRequestRecord.updated_at.desc())))

    async def budget(
        self, request_id: UUID, version: int
    ) -> tuple[ProjectBudgetRecord | None, list[ProjectBudgetLineRecord]]:
        """Read the budget of one request version with its lines.

        Args:
            request_id (UUID): The request.
            version (int): The request version.

        Returns:
            tuple[ProjectBudgetRecord | None, list[ProjectBudgetLineRecord]]: Budget and lines.
        """
        budget = await self.session.scalar(
            select(ProjectBudgetRecord).where(
                ProjectBudgetRecord.support_request_id == request_id, ProjectBudgetRecord.version == version
            )
        )
        if budget is None:
            return None, []
        lines = await self.session.scalars(
            select(ProjectBudgetLineRecord)
            .where(ProjectBudgetLineRecord.budget_id == budget.id)
            .order_by(ProjectBudgetLineRecord.position)
        )
        return budget, list(lines)

    async def write_budget(self, request_id: UUID, version: int, values: dict, lines: list[dict]) -> None:
        """Store the budget of a request version.

        Args:
            request_id (UUID): The request.
            version (int): The request version.
            values (dict): Budget columns.
            lines (list[dict]): Line columns.
        """
        budget = await self.add(ProjectBudgetRecord(support_request_id=request_id, version=version, **values))
        for line in lines:
            self.session.add(ProjectBudgetLineRecord(budget_id=budget.id, **line))
        await self.session.flush()

    async def snapshot(self, request_id: UUID, number: int, snapshot: dict) -> None:
        """Keep the request as it stood at one version.

        Args:
            request_id (UUID): The request.
            number (int): The version.
            snapshot (dict): The response body at that version.
        """
        await self.add(SupportRequestVersionRecord(support_request_id=request_id, number=number, snapshot=snapshot))

    async def version_snapshot(self, request_id: UUID, number: int) -> dict | None:
        """Read the request as it stood at one version.

        Args:
            request_id (UUID): The request.
            number (int): The version.

        Returns:
            dict | None: The snapshot.
        """
        return await self.session.scalar(
            select(SupportRequestVersionRecord.snapshot).where(
                SupportRequestVersionRecord.support_request_id == request_id,
                SupportRequestVersionRecord.number == number,
            )
        )
