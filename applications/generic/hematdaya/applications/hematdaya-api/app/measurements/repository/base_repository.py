"""Measurement storage interface."""

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from app.measurements.model.models import MeasurementRow


class MeasurementRepository(ABC):
    """Stores normalized readings. The caller holds the site write lock."""

    @abstractmethod
    async def current_rows(self, source_id: UUID, identity_keys: list[str]) -> dict[str, MeasurementRow]:
        """Return the current revision for each known identity."""

    @abstractmethod
    async def stored_intervals(self, source_id: UUID, start: datetime, end: datetime) -> list[MeasurementRow]:
        """Return current rows with energy whose interval overlaps ``[start, end)``, by interval start."""

    @abstractmethod
    async def insert(self, source_id: UUID, rows: list[MeasurementRow], received_at: datetime) -> None:
        """Insert rows in bulk."""

    @abstractmethod
    async def counter_points(self, source_id: UUID) -> list[MeasurementRow]:
        """Return a source's current counter readings."""

    @abstractmethod
    async def counter_deltas(self, source_id: UUID) -> list[MeasurementRow]:
        """Return a source's derived counter deltas."""

    @abstractmethod
    async def replace_counter_deltas(
        self, source_id: UUID, deltas: list[MeasurementRow], received_at: datetime
    ) -> None:
        """Replace a source's derived deltas, so displaced ones leave every read."""
