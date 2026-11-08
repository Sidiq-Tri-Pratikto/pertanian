"""Shared operations on confirmed scope membership."""

from uuid import UUID

from app.scope.model.models import AggregationSelectionModel
from app.scope.repository.base_repository import AggregationSelectionRepository


class SelectionService:
    """Expose membership independently of scope evaluation and its energy dependency."""

    def __init__(self, repository: AggregationSelectionRepository) -> None:
        """Bind the site's selection storage."""
        self.repository = repository

    async def get(self, site_id: UUID) -> AggregationSelectionModel | None:
        """Read an owned site's saved selection in the caller's transaction."""
        return await self.repository.get(site_id)

    async def replace(self, selection: AggregationSelectionModel) -> None:
        """Save a validated selection under its site's write lock."""
        await self.repository.replace(selection)

    async def clear(self, site_id: UUID) -> None:
        """Remove confirmed membership as part of a locked site reset."""
        await self.repository.clear(site_id)
