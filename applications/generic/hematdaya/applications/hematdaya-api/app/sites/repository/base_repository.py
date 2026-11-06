"""Site storage interface."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any
from uuid import UUID

from app.sites.model.models import SiteContext, SiteKind, SiteModel


class SiteRepository(ABC):
    """Stores sites. Every read is scoped to an owner unless it is an internal lock."""

    @abstractmethod
    async def get_owned(self, site_id: UUID, owner_id: UUID, *, lock: bool = False) -> SiteModel | None:
        """Return the owner's site, optionally taking the shared site write lock."""

    @abstractmethod
    async def lock(self, site_id: UUID) -> SiteModel | None:
        """Take the shared site write lock for a caller that already resolved the site."""

    @abstractmethod
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
        """Create a site."""

    @abstractmethod
    async def update(self, site_id: UUID, values: dict[str, Any]) -> SiteModel:
        """Change site fields."""

    @abstractmethod
    async def advance_revision(self, site_id: UUID, column: str) -> None:
        """Advance a revision counter on a locked site."""
