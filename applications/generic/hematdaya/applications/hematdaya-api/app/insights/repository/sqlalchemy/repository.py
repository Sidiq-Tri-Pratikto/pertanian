"""Insight repository over SQLAlchemy."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.insights.model.models import InsightModel, InsightRevisionModel
from app.insights.repository.base_repository import InsightRepository
from app.insights.repository.sqlalchemy.models import InsightRecord, InsightRevisionRecord


def _insight(record: InsightRecord) -> InsightModel:
    return InsightModel.model_validate(record, from_attributes=True)


class SqlAlchemyInsightRepository(InsightRepository):
    """Insights in Postgres."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind to the request session.

        Args:
            session (AsyncSession): The request's session.
        """
        self.session = session

    async def in_period(self, site_id: UUID, kind: str, start: datetime, end: datetime) -> list[InsightModel]:
        """Return a site's insights for one kind and period.

        Args:
            site_id (UUID): The site.
            kind (str): Insight kind.
            start (datetime): Period start.
            end (datetime): Period end.

        Returns:
            list[InsightModel]: Active and retired insights.
        """
        query = (
            select(InsightRecord)
            .where(
                InsightRecord.site_id == site_id,
                InsightRecord.kind == kind,
                InsightRecord.period_start == start,
                InsightRecord.period_end == end,
            )
            .execution_options(populate_existing=True)
        )
        return [_insight(record) for record in await self.session.scalars(query)]

    async def get(self, insight_id: UUID) -> InsightModel | None:
        """Return an insight.

        Args:
            insight_id (UUID): The insight.

        Returns:
            InsightModel | None: The insight, or None.
        """
        record = await self.session.get(InsightRecord, insight_id, populate_existing=True)
        return _insight(record) if record is not None else None

    async def revision(self, insight_id: UUID, revision: int) -> InsightRevisionModel | None:
        """Return one revision.

        Args:
            insight_id (UUID): The insight.
            revision (int): Revision number.

        Returns:
            InsightRevisionModel | None: The revision, or None.
        """
        record = await self.session.scalar(
            select(InsightRevisionRecord)
            .where(InsightRevisionRecord.insight_id == insight_id, InsightRevisionRecord.revision == revision)
            .execution_options(populate_existing=True)
        )
        return InsightRevisionModel.model_validate(record, from_attributes=True) if record is not None else None

    async def create(self, insight: InsightModel) -> None:
        """Store a new insight.

        Args:
            insight (InsightModel): The insight.
        """
        self.session.add(InsightRecord(**insight.model_dump()))
        await self.session.flush()

    async def add_revision(self, revision: InsightRevisionModel) -> None:
        """Append a revision.

        Args:
            revision (InsightRevisionModel): The revision.
        """
        self.session.add(InsightRevisionRecord(id=uuid4(), **revision.model_dump()))
        await self.session.flush()

    async def supersede(self, insight_id: UUID, revision: int, at: datetime) -> None:
        """Mark a revision superseded once.

        Args:
            insight_id (UUID): The insight.
            revision (int): Revision number.
            at (datetime): When.
        """
        await self.session.execute(
            update(InsightRevisionRecord)
            .where(
                InsightRevisionRecord.insight_id == insight_id,
                InsightRevisionRecord.revision == revision,
                InsightRevisionRecord.superseded_at.is_(None),
            )
            .values(superseded_at=at)
        )

    async def set_state(self, insight_id: UUID, *, current_revision: int, active: bool) -> None:
        """Point an insight at its current revision and activity.

        Args:
            insight_id (UUID): The insight.
            current_revision (int): Current revision.
            active (bool): Whether it is an active observation.
        """
        await self.session.execute(
            update(InsightRecord)
            .where(InsightRecord.id == insight_id)
            .values(current_revision=current_revision, active=active)
        )
