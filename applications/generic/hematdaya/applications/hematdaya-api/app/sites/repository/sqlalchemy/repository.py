"""Site repository over SQLAlchemy."""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from sqlalchemy import delete, select, update
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
        binding_revision=record.binding_revision,
        measurement_revision=record.measurement_revision,
    )


class SqlAlchemySiteRepository(SiteRepository):
    """Sites in Postgres."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind to the request session.

        Args:
            session (AsyncSession): The request's session.
        """
        self.session = session

    async def get_owned(
        self, site_id: UUID, owner_id: UUID, *, lock: bool | Literal["share"] = False
    ) -> SiteModel | None:
        """Return the owner's site.

        Args:
            site_id (UUID): The site.
            owner_id (UUID): The acting principal.
            lock (bool | Literal['share'], optional): True for ``FOR UPDATE``, or 'share' for ``FOR SHARE``.

        Returns:
            SiteModel | None: The site, or None when it does not exist or belongs to someone else.
        """
        query = select(SiteRecord).where(SiteRecord.id == site_id, SiteRecord.owner_principal_id == owner_id)
        if lock:
            query = query.with_for_update(read=lock == "share").execution_options(populate_existing=True)
        record = (await self.session.execute(query)).scalar_one_or_none()
        return None if record is None else _to_model(record)

    async def lock(self, site_id: UUID) -> SiteModel | None:
        """Take the shared site write lock without an owner check, for callers that already resolved the site.

        Args:
            site_id (UUID): The site.

        Returns:
            SiteModel | None: The site as of the lock, or None when it is gone.
        """
        record = (
            await self.session.execute(select(SiteRecord).where(SiteRecord.id == site_id).with_for_update())
        ).scalar_one_or_none()
        if record is None:
            return None
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

    async def advance_revision(self, site_id: UUID, column: str) -> None:
        """Advance one monotonic revision counter.

        Args:
            site_id (UUID): The site, locked by the caller.
            column (str): ``binding_revision`` or ``measurement_revision``.
        """
        await self.session.execute(
            update(SiteRecord).where(SiteRecord.id == site_id).values({column: getattr(SiteRecord, column) + 1})
        )

    async def delete(self, site_ids: list[UUID]) -> None:
        """Delete sites; their assets, sources, readings, audit and sessions cascade.

        Args:
            site_ids (list[UUID]): Sites to delete.
        """
        if not site_ids:
            return
        await self.session.execute(
            select(SiteRecord.id).where(SiteRecord.id.in_(site_ids)).order_by(SiteRecord.id).with_for_update()
        )
        await self.session.execute(delete(SiteRecord).where(SiteRecord.id.in_(site_ids)))
