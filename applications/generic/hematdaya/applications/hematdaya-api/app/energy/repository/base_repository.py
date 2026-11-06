"""Energy read interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

Span = tuple[datetime, datetime]


@dataclass(frozen=True)
class WholeAggregate:
    """Readings that fall wholly inside one part and one bucket, aggregated in SQL."""

    part: int
    bucket: int
    energy_mwh: int
    latest_end: datetime
    covered: list[Span]


@dataclass(frozen=True)
class Straddler:
    """A reading crossing a part or bucket boundary; its fragment is allocated in the service."""

    part: int
    bucket: int
    interval: Span
    fragment: Span
    energy_mwh: int
    quality: str


class EnergyRepository(ABC):
    """Aggregates current readings for source parts and time buckets."""

    @abstractmethod
    async def aggregate(
        self, parts: list[tuple[UUID, Span]], buckets: list[Span], now: datetime
    ) -> tuple[list[WholeAggregate], list[Straddler]]:
        """Aggregate completed readings of each (source, span) part into each bucket."""
