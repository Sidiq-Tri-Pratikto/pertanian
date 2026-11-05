"""Match run storage."""

from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.matching.repository.sqlalchemy.models import MatchResultRecord, MatchRunRecord


class SqlAlchemyMatchingRepository:
    """Writes and reads match runs."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind to the session.

        Args:
            session (AsyncSession): The request's session.
        """
        self.session = session

    async def save_run(self, run: MatchRunRecord, results: list[tuple[bool, dict[str, Any]]]) -> MatchRunRecord:
        """Store a run and its results in order.

        Args:
            run (MatchRunRecord): The run.
            results (list[tuple[bool, dict[str, Any]]]): Whether each result is shown, and the result.

        Returns:
            MatchRunRecord: The stored run.
        """
        self.session.add(run)
        await self.session.flush()
        for position, (shown, result) in enumerate(results):
            self.session.add(
                MatchResultRecord(
                    run_id=run.id,
                    position=position,
                    shown=shown,
                    opportunity_version_id=UUID(result["opportunity_version_id"]),
                    eligibility=result["eligibility"],
                    readiness=result["readiness"],
                    relevant=result["relevant"],
                    fit_lower=Decimal(result["fit"]["lower"]),
                    fit_upper=Decimal(result["fit"]["upper"]),
                    coverage=Decimal(result["fit"]["coverage"]),
                    result=result,
                )
            )
        await self.session.flush()
        return run

    async def run(self, run_id: UUID) -> tuple[MatchRunRecord, list[MatchResultRecord]] | None:
        """Read a run with its results in order.

        Args:
            run_id (UUID): The run.

        Returns:
            tuple[MatchRunRecord, list[MatchResultRecord]] | None: The run, or None.
        """
        run = await self.session.get(MatchRunRecord, run_id)
        if run is None:
            return None
        rows = await self.session.scalars(
            select(MatchResultRecord).where(MatchResultRecord.run_id == run_id).order_by(MatchResultRecord.position)
        )
        return run, list(rows)
