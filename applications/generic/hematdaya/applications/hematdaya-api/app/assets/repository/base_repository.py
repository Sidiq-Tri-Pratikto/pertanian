"""Asset storage interface."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any
from uuid import UUID

from app.assets.model.models import AssetModel, BindingModel, RelationKind, RelationModel, SourceModel


class AssetRepository(ABC):
    """Stores assets, sources, bindings and relations. Callers resolve the owned site first."""

    @abstractmethod
    async def list_assets(
        self, site_id: UUID, *, include_archived: bool, limit: int, after: tuple[str, UUID] | None
    ) -> list[AssetModel]:
        """Return assets ordered by name, then ID, after a cursor position."""

    @abstractmethod
    async def get_asset(self, asset_id: UUID) -> AssetModel | None:
        """Return an asset by ID, whatever its site."""

    @abstractmethod
    async def get_asset_in_site(self, site_id: UUID, asset_id: UUID) -> AssetModel | None:
        """Return an asset only when it belongs to the site."""

    @abstractmethod
    async def add_asset(self, site_id: UUID, fields: dict[str, Any]) -> AssetModel:
        """Create an asset."""

    @abstractmethod
    async def update_asset(self, asset_id: UUID, values: dict[str, Any]) -> AssetModel:
        """Change asset fields."""

    @abstractmethod
    async def add_source(self, site_id: UUID, fields: dict[str, Any]) -> SourceModel:
        """Create a source."""

    @abstractmethod
    async def get_source_in_site(self, site_id: UUID, source_id: UUID) -> SourceModel | None:
        """Return a source only when it belongs to the site."""

    @abstractmethod
    async def list_sources(self, source_ids: list[UUID]) -> list[SourceModel]:
        """Return sources by ID."""

    @abstractmethod
    async def list_bindings(self, asset_id: UUID) -> list[BindingModel]:
        """Return an asset's bindings, oldest first."""

    @abstractmethod
    async def get_binding(self, asset_id: UUID, binding_id: UUID) -> BindingModel | None:
        """Return a binding only when it belongs to the asset."""

    @abstractmethod
    async def add_binding(
        self, *, site_id: UUID, source_id: UUID, asset_id: UUID, effective_from: datetime, authoritative: bool
    ) -> BindingModel:
        """Create a binding; raise ``BindingOverlapError`` when authoritative ranges overlap."""

    @abstractmethod
    async def close_binding(self, binding_id: UUID, at: datetime) -> BindingModel | None:
        """End an open binding that started before ``at``; None when it was not open."""

    @abstractmethod
    async def containment(self, site_id: UUID) -> list[tuple[UUID, UUID]]:
        """Return (container, contained) pairs from parent links and ``contains`` relations."""

    @abstractmethod
    async def add_relation(self, site_id: UUID, from_asset_id: UUID, to_asset_id: UUID, kind: RelationKind) -> None:
        """Create a relation."""

    @abstractmethod
    async def list_relations(self, site_id: UUID) -> list[RelationModel]:
        """Return a site's relations."""

    @abstractmethod
    async def clear(self, site_id: UUID) -> None:
        """Delete a site's assets and sources; bindings, relations and readings cascade."""
