"""Store site selections in the caller's transaction."""

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.scope.model.models import AggregationSelectionModel
from app.scope.repository.base_repository import AggregationSelectionRepository
from app.scope.repository.sqlalchemy.models import AggregationSelectionAssetRecord, AggregationSelectionRecord


class SqlAlchemyAggregationSelectionRepository(AggregationSelectionRepository):
    """SQLAlchemy implementation of confirmed selections."""

    def __init__(self, session: AsyncSession) -> None:
        """Use the caller's request session."""
        self.session = session

    async def get(self, site_id: UUID) -> AggregationSelectionModel | None:
        """Load the revision and canonically ordered membership, retaining an empty persisted selection."""
        member = AggregationSelectionAssetRecord
        selection = AggregationSelectionRecord
        result = await self.session.execute(
            select(selection.revision, member.asset_id)
            .outerjoin(member, member.site_id == selection.site_id)
            .where(selection.site_id == site_id)
            .order_by(member.asset_id)
        )
        rows = result.all()
        if not rows:
            return None
        return AggregationSelectionModel(
            site_id=site_id, revision=rows[0].revision, asset_ids=[row.asset_id for row in rows if row.asset_id]
        )

    async def replace(self, selection: AggregationSelectionModel) -> None:
        """Replace membership and revision while the caller holds the site write lock."""
        member = AggregationSelectionAssetRecord
        record = AggregationSelectionRecord
        previous = await self.session.get(record, selection.site_id)
        if previous is None:
            self.session.add(record(site_id=selection.site_id, revision=selection.revision))
            await self.session.flush()
        else:
            previous.revision = selection.revision
            await self.session.execute(delete(member).where(member.site_id == selection.site_id))
        await self.session.execute(
            insert(member),
            [{"site_id": selection.site_id, "asset_id": asset_id} for asset_id in selection.asset_ids],
        )
        await self.session.flush()

    async def clear(self, site_id: UUID) -> None:
        """Delete the confirmed selection and its members."""
        await self.session.execute(
            delete(AggregationSelectionRecord).where(AggregationSelectionRecord.site_id == site_id)
        )
