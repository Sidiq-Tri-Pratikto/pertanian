"""Measurement repository over SQLAlchemy."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, insert, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.measurements.model.models import MeasurementRow, Quality, StoredKind
from app.measurements.repository.base_repository import MeasurementRepository
from app.measurements.repository.sqlalchemy.models import MeasurementRecord

_COLUMNS = (
    "identity_key, source_record_id, kind, interval_start, interval_end, measured_at, energy_mwh, raw_value,"
    " raw_unit, counter_segment, quality, revision, provenance"
)
_KEY_CHUNK = 5000


def _row(mapping: dict) -> MeasurementRow:
    return MeasurementRow(**{**mapping, "kind": StoredKind(mapping["kind"]), "quality": Quality(mapping["quality"])})


class SqlAlchemyMeasurementRepository(MeasurementRepository):
    """Measurements in Postgres."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind to the request session.

        Args:
            session (AsyncSession): The request's session.
        """
        self.session = session

    async def current_rows(self, source_id: UUID, identity_keys: list[str]) -> dict[str, MeasurementRow]:
        """Return current revisions by identity.

        Args:
            source_id (UUID): The source.
            identity_keys (list[str]): Identities to look up.

        Returns:
            dict[str, MeasurementRow]: Current rows keyed by identity; unknown identities are absent.
        """
        found: dict[str, MeasurementRow] = {}
        for offset in range(0, len(identity_keys), _KEY_CHUNK):
            result = await self.session.execute(
                text(
                    f"SELECT {_COLUMNS} FROM current_measurements"
                    " WHERE source_id = :source AND identity_key = ANY(:keys)"
                ),
                {"source": source_id, "keys": identity_keys[offset : offset + _KEY_CHUNK]},
            )
            found.update({row["identity_key"]: _row(dict(row)) for row in result.mappings()})
        return found

    async def stored_intervals(self, source_id: UUID, start: datetime, end: datetime) -> list[MeasurementRow]:
        """Return current rows with energy whose interval overlaps a half-open window.

        Args:
            source_id (UUID): The source.
            start (datetime): Window start, inclusive.
            end (datetime): Window end, exclusive.

        Returns:
            list[MeasurementRow]: Rows by interval start. Adjacent intervals are not included.
        """
        result = await self.session.execute(
            text(
                f"SELECT {_COLUMNS} FROM current_measurements"
                " WHERE source_id = :source AND energy_mwh IS NOT NULL"
                " AND interval_start < :end AND interval_end > :start ORDER BY interval_start"
            ),
            {"source": source_id, "start": start, "end": end},
        )
        return [_row(dict(row)) for row in result.mappings()]

    async def insert(self, source_id: UUID, rows: list[MeasurementRow], received_at: datetime) -> None:
        """Insert rows in one set-based statement batch.

        Args:
            source_id (UUID): The source.
            rows (list[MeasurementRow]): Normalized rows with their revisions.
            received_at (datetime): Wall-clock arrival time.
        """
        if rows:
            await self.session.execute(
                insert(MeasurementRecord),
                [{**row.model_dump(), "source_id": source_id, "received_at": received_at} for row in rows],
            )

    async def counter_points(self, source_id: UUID) -> list[MeasurementRow]:
        """Return current counter readings.

        Args:
            source_id (UUID): The source.

        Returns:
            list[MeasurementRow]: Points in capture order.
        """
        return await self._current_of_kind(source_id, StoredKind.COUNTER_POINT, "measured_at")

    async def counter_deltas(self, source_id: UUID) -> list[MeasurementRow]:
        """Return derived counter deltas.

        Args:
            source_id (UUID): The source.

        Returns:
            list[MeasurementRow]: Deltas in time order.
        """
        return await self._current_of_kind(source_id, StoredKind.COUNTER_DELTA, "interval_start")

    async def replace_counter_deltas(
        self, source_id: UUID, deltas: list[MeasurementRow], received_at: datetime
    ) -> None:
        """Replace derived deltas; raw counter readings keep their full revision history.

        Args:
            source_id (UUID): The source.
            deltas (list[MeasurementRow]): The deltas now derived from current readings.
            received_at (datetime): Wall-clock time of the change.
        """
        await self.session.execute(
            delete(MeasurementRecord).where(
                MeasurementRecord.source_id == source_id, MeasurementRecord.kind == StoredKind.COUNTER_DELTA.value
            )
        )
        await self.insert(source_id, deltas, received_at)

    async def _current_of_kind(self, source_id: UUID, kind: StoredKind, order: str) -> list[MeasurementRow]:
        result = await self.session.execute(
            text(
                f"SELECT {_COLUMNS} FROM current_measurements"
                + f" WHERE source_id = :source AND kind = :kind ORDER BY {order}"
            ),
            {"source": source_id, "kind": kind.value},
        )
        return [_row(dict(row)) for row in result.mappings()]
