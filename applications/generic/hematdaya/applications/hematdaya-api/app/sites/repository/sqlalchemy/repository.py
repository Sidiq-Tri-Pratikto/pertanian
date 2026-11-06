"""Site repository over SQLAlchemy."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.sites.model.models import SiteContext, SiteKind, SiteModel
from app.sites.repository.base_repository import SiteRepository
from app.sites.repository.sqlalchemy.models import SiteRecord


def _to_model(record: SiteRecord) -> SiteModel:
    return SiteModel(
        id=record.id,
        owner_principal_id=record.owner_principal_id,
        kind=SiteKind(record.kind),
        name=record.name,
        context=SiteContext(record.context),
        timezone=record.timezone,
        currency=record.currency,
        virtual_now=record.virtual_now,
    )


class SqlAlchemySiteRepository(SiteRepository):
    """Sites in Postgres."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind to the request session.

        Args:
            session (AsyncSession): The request's session.
        """
        self.session = session

    async def get_owned(self, site_id: UUID, owner_id: UUID, *, lock: bool = False) -> SiteModel | None:
        """Return the owner's site.

        Args:
            site_id (UUID): The site.
            owner_id (UUID): The acting principal.
            lock (bool, optional): Take ``FOR UPDATE``, the shared site write lock. Defaults to False.

        Returns:
            SiteModel | None: The site, or None when it does not exist or belongs to someone else.
        """
        query = select(SiteRecord).where(SiteRecord.id == site_id, SiteRecord.owner_principal_id == owner_id)
        if lock:
            query = query.with_for_update()
        record = (await self.session.execute(query)).scalar_one_or_none()
        if record is None:
            return None
        if lock:
            await self.session.refresh(record)
        return _to_model(record)

    async def add(
        self,
        *,
        owner_id: UUID,
        kind: SiteKind,
        name: str,
        context: SiteContext,
        timezone: str,
        currency: str,
        virtual_now: datetime | None,
    ) -> SiteModel:
        """Create a site.

        Args:
            owner_id (UUID): The owner principal.
            kind (SiteKind): Demo or standard.
            name (str): Display name.
            context (SiteContext): Usage context.
            timezone (str): IANA timezone.
            currency (str): Currency code.
            virtual_now (datetime | None): Demo clock, None for standard sites.

        Returns:
            SiteModel: The stored site.
        """
        record = SiteRecord(
            owner_principal_id=owner_id,
            kind=kind.value,
            name=name,
            context=context.value,
            timezone=timezone,
            currency=currency,
            virtual_now=virtual_now,
        )
        self.session.add(record)
        await self.session.flush()
        return _to_model(record)

    async def update(self, site_id: UUID, values: dict[str, Any]) -> SiteModel:
        """Change site fields.

        Args:
            site_id (UUID): The site, already resolved through its owner.
            values (dict[str, Any]): Column values.

        Returns:
            SiteModel: The updated site.
        """
        if values:
            await self.session.execute(update(SiteRecord).where(SiteRecord.id == site_id).values(**values))
        record = await self.session.get(SiteRecord, site_id, populate_existing=True)
        assert record is not None  # The caller holds the site lock.
        return _to_model(record)
