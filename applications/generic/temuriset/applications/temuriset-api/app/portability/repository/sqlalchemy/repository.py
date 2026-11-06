"""Query and lock private portability records."""

import json
from typing import Any
from uuid import UUID

from sqlalchemy import delete, func, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.platform.repository.sqlalchemy.models import JobRecord
from app.portability.repository.sqlalchemy.models import (
    ExportJobRecord,
    ExternalReferenceRecord,
    ImportRowRecord,
    ImportRunRecord,
)


class PortabilityRepository:
    """Persistence in the request or worker transaction."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, record: ImportRunRecord | ExportJobRecord | ExternalReferenceRecord) -> None:
        """Insert a new record and assign its ID."""
        self.session.add(record)
        await self.session.flush()

    async def import_run(self, run_id: UUID, *, lock: bool = False) -> ImportRunRecord | None:
        """Load a run, optionally serializing stage advancement with cancellation."""
        query = select(ImportRunRecord).where(ImportRunRecord.id == run_id)
        return await self.session.scalar(query.with_for_update() if lock else query)

    async def export_job(self, export_id: UUID, *, lock: bool = False) -> ExportJobRecord | None:
        """Load an export, optionally locking expiry against generation."""
        query = select(ExportJobRecord).where(ExportJobRecord.id == export_id)
        return await self.session.scalar(query.with_for_update() if lock else query)

    async def add_import_rows(self, run_id: UUID, payloads: list[dict[str, Any]]) -> None:
        """Write the complete normalized file as bounded indexed rows."""
        await self.session.execute(
            insert(ImportRowRecord),
            [{"run_id": run_id, "position": position, "payload": payload} for position, payload in enumerate(payloads)],
        )

    async def import_rows(self, run_id: UUID, offset: int, limit: int) -> list[ImportRowRecord]:
        """Read one ordered window of a run."""
        rows = await self.session.scalars(
            select(ImportRowRecord)
            .where(ImportRowRecord.run_id == run_id, ImportRowRecord.position >= offset)
            .order_by(ImportRowRecord.position)
            .limit(limit)
        )
        return list(rows)

    async def purge_rows(self, run_id: UUID) -> None:
        """Remove the private staging payloads."""
        await self.session.execute(delete(ImportRowRecord).where(ImportRowRecord.run_id == run_id))

    async def reference(
        self, party_id: UUID, system: str, external_id: str, *, lock: bool = False
    ) -> ExternalReferenceRecord | None:
        """Find a source reference, locking even a not-yet-created key for upserts."""
        if lock:
            key = json.dumps([str(party_id), system, external_id], separators=(",", ":"))
            await self.session.execute(select(func.pg_advisory_xact_lock(func.hashtextextended(key, 0))))
        return await self.session.scalar(
            select(ExternalReferenceRecord).where(
                ExternalReferenceRecord.party_id == party_id,
                ExternalReferenceRecord.external_system == system,
                ExternalReferenceRecord.external_id == external_id,
            )
        )

    async def job_failures(self, job_ids: list[UUID]) -> dict[UUID, str | None]:
        """Read terminal platform failures without exposing job inputs or result metadata."""
        result = await self.session.execute(
            select(JobRecord.id, JobRecord.last_error_code).where(
                JobRecord.id.in_(job_ids), JobRecord.status.in_(["FAILED", "NEEDS_MANUAL_INPUT"])
            )
        )
        return {row.id: row.last_error_code for row in result}
