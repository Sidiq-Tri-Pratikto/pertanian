"""Insight storage interface."""

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from app.insights.model.models import InsightModel, InsightRevisionModel


class InsightRepository(ABC):
    """Stores insights and revisions. Callers hold the site write lock when publishing."""

    @abstractmethod
    async def in_period(self, site_id: UUID, kind: str, start: datetime, end: datetime) -> list[InsightModel]:
        """Return a site's insights for one kind and period."""

    @abstractmethod
    async def get(self, insight_id: UUID) -> InsightModel | None:
        """Return an insight."""

    @abstractmethod
    async def revision(self, insight_id: UUID, revision: int) -> InsightRevisionModel | None:
        """Return one revision."""

    @abstractmethod
    async def create(self, insight: InsightModel) -> None:
        """Store a new insight."""

    @abstractmethod
    async def add_revision(self, revision: InsightRevisionModel) -> None:
        """Append a revision."""

    @abstractmethod
    async def supersede(self, insight_id: UUID, revision: int, at: datetime) -> None:
        """Mark a revision superseded."""

    @abstractmethod
    async def set_state(self, insight_id: UUID, *, current_revision: int, active: bool) -> None:
        """Point an insight at its current revision and activity."""

    @abstractmethod
    async def latest_reading_end(self, source_ids: list[UUID], now: datetime) -> dict[UUID, datetime]:
        """Return each source's latest completed reading end."""
