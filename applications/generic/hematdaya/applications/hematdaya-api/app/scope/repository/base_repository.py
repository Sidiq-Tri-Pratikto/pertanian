"""Storage interface for confirmed selections."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.scope.model.models import AggregationSelectionModel


class AggregationSelectionRepository(ABC):
    """Store one optional selection per site."""

    @abstractmethod
    async def get(self, site_id: UUID) -> AggregationSelectionModel | None:
        """Return the site's saved selection if any."""

    @abstractmethod
    async def replace(self, selection: AggregationSelectionModel) -> None:
        """Persist the selection and its new revision under the caller's site lock."""

    @abstractmethod
    async def clear(self, site_id: UUID) -> None:
        """Clear the selection under the caller's site lock."""
