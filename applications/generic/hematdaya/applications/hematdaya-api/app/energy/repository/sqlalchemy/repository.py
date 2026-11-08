"""Energy reads over SQL aggregation on ``current_measurements``."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.energy.repository.base_repository import (
    CaptureQuery,
    EnergyRepository,
    SlotRepository,
    Span,
    Straddler,
    WholeAggregate,
    WholeReading,
)

_HITS = """
WITH part AS (
    SELECT * FROM unnest(CAST(:p_idx AS int[]), CAST(:p_source AS uuid[]), CAST(:p_lo AS timestamptz[]),
        CAST(:p_hi AS timestamptz[])) AS t(idx, source_id, lo, hi)
), bucket AS (
    SELECT * FROM unnest(CAST(:b_idx AS int[]), CAST(:b_lo AS timestamptz[]), CAST(:b_hi AS timestamptz[]))
        AS t(idx, lo, hi)
), hit AS (
    SELECT p.idx AS part, b.idx AS bucket, c.interval_start AS s, c.interval_end AS e, c.energy_mwh AS energy,
        c.quality, c.kind, GREATEST(c.interval_start, p.lo, b.lo) AS fs, LEAST(c.interval_end, p.hi, b.hi) AS fe
    FROM part p
    JOIN current_measurements c ON c.source_id = p.source_id AND c.energy_mwh IS NOT NULL
        AND c.interval_start < p.hi AND c.interval_end > p.lo AND c.interval_end <= :now
    JOIN bucket b ON c.interval_start < b.hi AND c.interval_end > b.lo
    WHERE GREATEST(c.interval_start, p.lo, b.lo) < LEAST(c.interval_end, p.hi, b.hi)
)
"""
_WHOLE = (
    _HITS
    + """, whole AS (
    SELECT part, bucket, sum(energy)::bigint AS energy, max(e) AS latest, range_agg(tstzrange(s, e, '[)')) AS covered
    FROM hit WHERE fs = s AND fe = e GROUP BY part, bucket
)
SELECT part, bucket, energy, latest,
    ARRAY(SELECT lower(r) FROM unnest(covered) AS r ORDER BY 1) AS lows,
    ARRAY(SELECT upper(r) FROM unnest(covered) AS r ORDER BY 1) AS highs
FROM whole
"""
)
_STRADDLERS = _HITS + "SELECT part, bucket, s, e, fs, fe, energy, quality FROM hit WHERE NOT (fs = s AND fe = e)"


class SqlAlchemyEnergyRepository(EnergyRepository):
    """Energy reads in Postgres."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind to the request session.

        Args:
            session (AsyncSession): The request's session.
        """
        self.session = session

    async def aggregate(
        self, parts: list[tuple[UUID, Span]], buckets: list[Span], now: datetime
    ) -> tuple[list[WholeAggregate], list[Straddler]]:
        """Sum whole readings with their covered ranges, and list boundary-crossing readings.

        Only completed readings count: an interval ending after ``now`` is excluded, one ending exactly at
        ``now`` is included.

        Args:
            parts (list[tuple[UUID, Span]]): (source, span) pairs, indexed by position.
            buckets (list[Span]): Half-open buckets, indexed by position.
            now (datetime): Site time.

        Returns:
            tuple[list[WholeAggregate], list[Straddler]]: Whole aggregates and straddling readings.
        """
        if not parts or not buckets:
            return [], []
        params = {
            "p_idx": list(range(len(parts))),
            "p_source": [source for source, _ in parts],
            "p_lo": [span[0] for _, span in parts],
            "p_hi": [span[1] for _, span in parts],
            "b_idx": list(range(len(buckets))),
            "b_lo": [bucket[0] for bucket in buckets],
            "b_hi": [bucket[1] for bucket in buckets],
            "now": now,
        }
        whole = [
            WholeAggregate(row.part, row.bucket, row.energy, row.latest, list(zip(row.lows, row.highs, strict=True)))
            for row in await self.session.execute(text(_WHOLE), params)
        ]
        straddlers = [
            Straddler(row.part, row.bucket, (row.s, row.e), (row.fs, row.fe), row.energy, row.quality)
            for row in await self.session.execute(text(_STRADDLERS), params)
        ]
        return whole, straddlers

    async def capture_ranges(
        self, queries: list[CaptureQuery], now: datetime
    ) -> dict[int, tuple[datetime, datetime, datetime]]:
        """Read valid, current, completed interval captures for effective segments in one query."""
        result = await self.session.execute(
            text("""
                WITH part AS (
                    SELECT * FROM unnest(CAST(:indices AS int[]), CAST(:sources AS uuid[]),
                        CAST(:starts AS timestamptz[]), CAST(:ends AS timestamptz[]),
                        CAST(:historical AS boolean[])) AS t(idx, source_id, lo, hi, historical)
                )
                SELECT p.idx, min(GREATEST(c.interval_start, p.lo)) AS start,
                    max(LEAST(c.interval_end, p.hi)) AS "end", max(c.interval_end) AS latest
                FROM part p
                JOIN current_measurements c ON c.source_id = p.source_id
                    AND c.energy_mwh IS NOT NULL AND c.quality = 'valid'
                    AND c.interval_start < c.interval_end AND c.interval_end <= :now
                    AND ((p.historical AND c.interval_start < p.hi AND p.lo < c.interval_end)
                        OR (NOT p.historical AND p.lo <= c.interval_start AND c.interval_end <= p.hi))
                GROUP BY p.idx
                """),
            {
                "indices": list(range(len(queries))),
                "sources": [query.source_id for query in queries],
                "starts": [query.span[0] for query in queries],
                "ends": [query.span[1] for query in queries],
                "historical": [query.historical for query in queries],
                "now": now,
            },
        )
        return {row.idx: (row.start, row.end, row.latest) for row in result}


_WHOLE_READINGS = _HITS + "SELECT part, bucket, s, e, energy, kind FROM hit WHERE fs = s AND fe = e ORDER BY bucket, s"


class SqlAlchemySlotRepository(SlotRepository):
    """Whole readings for slot alignment, in one query across every window."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind to the request session.

        Args:
            session (AsyncSession): The request's session.
        """
        self.session = session

    async def whole_readings(
        self, parts: list[tuple[UUID, Span]], windows: list[Span], now: datetime
    ) -> list[WholeReading]:
        """List whole, completed readings; a reading crossing a part or window edge never becomes a slot.

        Args:
            parts (list[tuple[UUID, Span]]): (source, span) authority parts.
            windows (list[Span]): Current and prior windows.
            now (datetime): Site time.

        Returns:
            list[WholeReading]: Readings by window and start.
        """
        if not parts or not windows:
            return []
        params = {
            "p_idx": list(range(len(parts))),
            "p_source": [source for source, _ in parts],
            "p_lo": [span[0] for _, span in parts],
            "p_hi": [span[1] for _, span in parts],
            "b_idx": list(range(len(windows))),
            "b_lo": [window[0] for window in windows],
            "b_hi": [window[1] for window in windows],
            "now": now,
        }
        return [
            WholeReading(row.part, row.bucket, row.s, row.e, row.energy, row.kind)
            for row in await self.session.execute(text(_WHOLE_READINGS), params)
        ]
