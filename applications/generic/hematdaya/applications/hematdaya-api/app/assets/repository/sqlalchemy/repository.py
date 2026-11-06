"""Asset repository over SQLAlchemy."""

from datetime import datetime
from typing import Any
from uuid import UUID

from asyncpg.exceptions import ExclusionViolationError
from sqlalchemy import and_, delete, select, tuple_, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.assets.model.models import (
    AssetModel,
    BindingModel,
    ExpectedUse,
    MeasurementKind,
    RelationKind,
    RelationModel,
    ScopeKind,
    SourceModel,
    SourceOrigin,
    TransportStatus,
)
from app.assets.repository.base_repository import AssetRepository
from app.assets.repository.sqlalchemy.models import AssetRecord, AssetRelationRecord, BindingRecord, SourceRecord
from app.assets.service.errors import BindingOverlapError


def _asset(record: AssetRecord) -> AssetModel:
    return AssetModel(
        id=record.id,
        site_id=record.site_id,
        name=record.name,
        category=record.category,
        location=record.location,
        scope_kind=ScopeKind(record.scope_kind),
        parent_asset_id=record.parent_asset_id,
        expected_use=ExpectedUse(record.expected_use),
        archived_at=record.archived_at,
    )


def _source(record: SourceRecord) -> SourceModel:
    return SourceModel(
        id=record.id,
        site_id=record.site_id,
        label=record.label,
        origin=SourceOrigin(record.origin),
        measurement_kind=MeasurementKind(record.measurement_kind),
        cadence_seconds=record.cadence_seconds,
        resolution_mwh=record.resolution_mwh,
        transport_status=TransportStatus(record.transport_status),
    )


def _binding(record: BindingRecord) -> BindingModel:
    return BindingModel(
        id=record.id,
        site_id=record.site_id,
        source_id=record.source_id,
        asset_id=record.asset_id,
        effective_from=record.effective_from,
        effective_to=record.effective_to,
        authoritative=record.authoritative,
    )


class SqlAlchemyAssetRepository(AssetRepository):
    """Assets, sources, bindings and relations in Postgres."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind to the request session.

        Args:
            session (AsyncSession): The request's session.
        """
        self.session = session

    async def list_assets(
        self, site_id: UUID, *, include_archived: bool, limit: int, after: tuple[str, UUID] | None
    ) -> list[AssetModel]:
        """Return one page of a site's assets.

        Args:
            site_id (UUID): The owned site.
            include_archived (bool): Also return archived assets.
            limit (int): Page size.
            after (tuple[str, UUID] | None): The last (name, ID) already returned.

        Returns:
            list[AssetModel]: Up to ``limit`` assets.
        """
        query = select(AssetRecord).where(AssetRecord.site_id == site_id)
        if not include_archived:
            query = query.where(AssetRecord.archived_at.is_(None))
        if after is not None:
            query = query.where(tuple_(AssetRecord.name, AssetRecord.id) > tuple_(*after))
        query = query.order_by(AssetRecord.name, AssetRecord.id).limit(limit)
        return [_asset(record) for record in (await self.session.scalars(query))]

    async def get_asset(self, asset_id: UUID) -> AssetModel | None:
        """Return an asset by ID.

        Args:
            asset_id (UUID): The asset.

        Returns:
            AssetModel | None: The asset, or None.
        """
        record = await self.session.get(AssetRecord, asset_id, populate_existing=True)
        return _asset(record) if record is not None else None

    async def get_asset_in_site(self, site_id: UUID, asset_id: UUID) -> AssetModel | None:
        """Return an asset of a site.

        Args:
            site_id (UUID): The site.
            asset_id (UUID): The asset.

        Returns:
            AssetModel | None: The asset, or None when it is missing or elsewhere.
        """
        asset = await self.get_asset(asset_id)
        return asset if asset is not None and asset.site_id == site_id else None

    async def add_asset(self, site_id: UUID, fields: dict[str, Any]) -> AssetModel:
        """Create an asset.

        Args:
            site_id (UUID): The site.
            fields (dict[str, Any]): Column values.

        Returns:
            AssetModel: The stored asset.
        """
        record = AssetRecord(site_id=site_id, **fields)
        self.session.add(record)
        await self.session.flush()
        return _asset(record)

    async def update_asset(self, asset_id: UUID, values: dict[str, Any]) -> AssetModel:
        """Change asset fields.

        Args:
            asset_id (UUID): The asset.
            values (dict[str, Any]): Column values.

        Returns:
            AssetModel: The updated asset.
        """
        await self.session.execute(update(AssetRecord).where(AssetRecord.id == asset_id).values(**values))
        asset = await self.get_asset(asset_id)
        assert asset is not None  # The caller holds the site lock.
        return asset

    async def add_source(self, site_id: UUID, fields: dict[str, Any]) -> SourceModel:
        """Create a source.

        Args:
            site_id (UUID): The site.
            fields (dict[str, Any]): Column values.

        Returns:
            SourceModel: The stored source.
        """
        record = SourceRecord(site_id=site_id, **fields)
        self.session.add(record)
        await self.session.flush()
        return _source(record)

    async def get_source_in_site(self, site_id: UUID, source_id: UUID) -> SourceModel | None:
        """Return a source of a site.

        Args:
            site_id (UUID): The site.
            source_id (UUID): The source.

        Returns:
            SourceModel | None: The source, or None when it is missing or elsewhere.
        """
        record = await self.session.get(SourceRecord, source_id)
        return _source(record) if record is not None and record.site_id == site_id else None

    async def list_sources(self, source_ids: list[UUID]) -> list[SourceModel]:
        """Return sources by ID.

        Args:
            source_ids (list[UUID]): The sources.

        Returns:
            list[SourceModel]: The sources, ordered by label.
        """
        if not source_ids:
            return []
        query = select(SourceRecord).where(SourceRecord.id.in_(source_ids)).order_by(SourceRecord.label)
        return [_source(record) for record in await self.session.scalars(query)]

    async def list_bindings(self, asset_id: UUID) -> list[BindingModel]:
        """Return an asset's bindings.

        Args:
            asset_id (UUID): The asset.

        Returns:
            list[BindingModel]: Bindings, oldest first.
        """
        query = (
            select(BindingRecord)
            .where(BindingRecord.asset_id == asset_id)
            .order_by(BindingRecord.effective_from, BindingRecord.id)
            .execution_options(populate_existing=True)
        )
        return [_binding(record) for record in await self.session.scalars(query)]

    async def get_binding(self, asset_id: UUID, binding_id: UUID) -> BindingModel | None:
        """Return an asset's binding.

        Args:
            asset_id (UUID): The asset.
            binding_id (UUID): The binding.

        Returns:
            BindingModel | None: The binding, or None when it belongs to another asset.
        """
        record = await self.session.get(BindingRecord, binding_id, populate_existing=True)
        return _binding(record) if record is not None and record.asset_id == asset_id else None

    async def add_binding(
        self, *, site_id: UUID, source_id: UUID, asset_id: UUID, effective_from: datetime, authoritative: bool
    ) -> BindingModel:
        """Create a binding.

        Args:
            site_id (UUID): The site of both the source and the asset.
            source_id (UUID): The source.
            asset_id (UUID): The asset.
            effective_from (datetime): Start of the range.
            authoritative (bool): Whether it is the asset's reference source.

        Returns:
            BindingModel: The stored binding.

        Raises:
            BindingOverlapError: When another authoritative binding covers the same instant.
        """
        record = BindingRecord(
            site_id=site_id,
            source_id=source_id,
            asset_id=asset_id,
            effective_from=effective_from,
            authoritative=authoritative,
        )
        self.session.add(record)
        try:
            await self.session.flush()
        except IntegrityError as error:
            if isinstance(getattr(error.orig, "__cause__", None), ExclusionViolationError):
                raise BindingOverlapError(error=error) from error
            raise
        return _binding(record)

    async def close_binding(self, binding_id: UUID, at: datetime) -> BindingModel | None:
        """End an open binding; the condition keeps concurrent retries from moving the end.

        Args:
            binding_id (UUID): The binding.
            at (datetime): The end instant.

        Returns:
            BindingModel | None: The closed binding, or None when it was already closed or not yet started.
        """
        result = await self.session.execute(
            update(BindingRecord)
            .where(
                BindingRecord.id == binding_id,
                BindingRecord.effective_to.is_(None),
                BindingRecord.effective_from < at,
            )
            .values(effective_to=at)
            .returning(BindingRecord.id)
        )
        if result.scalar_one_or_none() is None:
            return None
        record = await self.session.get(BindingRecord, binding_id, populate_existing=True)
        return _binding(record) if record is not None else None

    async def containment(self, site_id: UUID) -> list[tuple[UUID, UUID]]:
        """Return a site's containment pairs.

        Args:
            site_id (UUID): The site.

        Returns:
            list[tuple[UUID, UUID]]: (container, contained) pairs.
        """
        parents = await self.session.execute(
            select(AssetRecord.parent_asset_id, AssetRecord.id).where(
                AssetRecord.site_id == site_id, AssetRecord.parent_asset_id.is_not(None)
            )
        )
        contains = await self.session.execute(
            select(AssetRelationRecord.from_asset_id, AssetRelationRecord.to_asset_id).where(
                and_(AssetRelationRecord.site_id == site_id, AssetRelationRecord.kind == RelationKind.CONTAINS.value)
            )
        )
        return [(row[0], row[1]) for row in [*parents, *contains]]

    async def add_relation(self, site_id: UUID, from_asset_id: UUID, to_asset_id: UUID, kind: RelationKind) -> None:
        """Create a relation.

        Args:
            site_id (UUID): The site of both assets.
            from_asset_id (UUID): First asset; the container for ``contains``.
            to_asset_id (UUID): Second asset.
            kind (RelationKind): The relation.
        """
        self.session.add(
            AssetRelationRecord(site_id=site_id, from_asset_id=from_asset_id, to_asset_id=to_asset_id, kind=kind.value)
        )
        await self.session.flush()

    async def list_relations(self, site_id: UUID) -> list[RelationModel]:
        """Return a site's relations.

        Args:
            site_id (UUID): The site.

        Returns:
            list[RelationModel]: The relations.
        """
        query = select(AssetRelationRecord).where(AssetRelationRecord.site_id == site_id)
        return [
            RelationModel(
                id=record.id,
                site_id=record.site_id,
                from_asset_id=record.from_asset_id,
                to_asset_id=record.to_asset_id,
                kind=RelationKind(record.kind),
            )
            for record in await self.session.scalars(query)
        ]

    async def clear(self, site_id: UUID) -> None:
        """Delete a site's assets and sources.

        Args:
            site_id (UUID): The locked site.
        """
        await self.session.execute(delete(AssetRecord).where(AssetRecord.site_id == site_id))
        await self.session.execute(delete(SourceRecord).where(SourceRecord.site_id == site_id))
