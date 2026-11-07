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


@dataclass(frozen=True)
class CaptureQuery:
    """A source and an effective authority span for capture lookup."""

    source_id: UUID
    span: Span
    historical: bool


class EnergyRepository(ABC):
    """Aggregates current readings for source parts and time buckets."""

    @abstractmethod
    async def aggregate(
        self, parts: list[tuple[UUID, Span]], buckets: list[Span], now: datetime
    ) -> tuple[list[WholeAggregate], list[Straddler]]:
        """Aggregate completed readings of each (source, span) part into each bucket."""

    @abstractmethod
    async def capture_ranges(
        self, queries: list[CaptureQuery], now: datetime
    ) -> dict[int, tuple[datetime, datetime, datetime]]:
        """Return the attributed start, end and actual latest capture by query index."""


@dataclass(frozen=True)
class WholeReading:
    """A completed reading wholly inside one part and one window."""

    part: int
    window: int
    start: datetime
    end: datetime
    energy_mwh: int
    kind: str


class SlotRepository(ABC):
    """Lists whole readings for slot alignment."""

    @abstractmethod
    async def whole_readings(
        self, parts: list[tuple[UUID, Span]], windows: list[Span], now: datetime
    ) -> list[WholeReading]:
        """Return completed readings that fall wholly inside a part and a window."""
