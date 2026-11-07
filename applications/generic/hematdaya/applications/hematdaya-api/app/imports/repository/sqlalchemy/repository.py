"""Import repository over SQLAlchemy."""

from collections.abc import Iterable
from datetime import datetime
from itertools import batched
from typing import Any
from uuid import UUID

from sqlalchemy import Select, delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.imports.model.models import ImportModel, ImportRowModel, ImportRowStatus, ImportStatus
from app.imports.repository.base_repository import ImportRepository
from app.imports.repository.sqlalchemy.models import ImportRecord, ImportRowRecord

_ROW_BATCH = 5000
_ERROR_STATUSES = (ImportRowStatus.INVALID.value, ImportRowStatus.CONFLICT.value)


def _import_model(record: ImportRecord) -> ImportModel:
    return ImportModel(
        id=record.id,
        site_id=record.site_id,
        status=ImportStatus(record.status),
        file_name=record.file_name,
        content_sha256=record.content_sha256,
        mapping=record.mapping,
        total_rows=record.total_rows,
        accepted_rows=record.accepted_rows,
        invalid_rows=record.invalid_rows,
        duplicate_rows=record.duplicate_rows,
        conflict_rows=record.conflict_rows,
        pending_rows=record.pending_rows,
        blocked=record.blocked,
        block_reasons=record.block_reasons,
        needs_acknowledgment=record.needs_acknowledgment,
        questions=record.questions,
        assumptions=record.assumptions,
        period_start=record.period_start,
        period_end=record.period_end,
        measurement_revision=record.measurement_revision,
        binding_revision=record.binding_revision,
        idempotency_key=record.idempotency_key,
        expires_at=record.expires_at,
        created_at=record.created_at,
        commit_result=record.commit_result,
    )


def _row_values(import_id: UUID, row: ImportRowModel) -> dict:
    return {
        "import_id": import_id,
        "data_row": row.data_row,
        "file_line": row.file_line,
        "status": row.status.value,
        "reason": row.reason,
        "field": row.field,
        "message": row.message,
        "parsed": row.parsed,
    }


class SqlAlchemyImportRepository(ImportRepository):
    """Imports in Postgres."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind to the request session.

        Args:
            session (AsyncSession): The request's session.
        """
        self.session = session

    async def add_import(self, model: ImportModel) -> None:
        """Insert an import.

        Args:
            model (ImportModel): The import. ``created_at`` comes from the database.
        """
        values = model.model_dump(exclude={"created_at"})
        await self.session.execute(insert(ImportRecord).values(**values | {"status": model.status.value}))

    async def add_rows(self, import_id: UUID, rows: Iterable[ImportRowModel]) -> None:
        """Insert row results in batches, consuming ``rows`` lazily so a large file is never held twice.

        Args:
            import_id (UUID): The import.
            rows (Iterable[ImportRowModel]): Its row results.
        """
        for batch in batched(rows, _ROW_BATCH):
            await self.session.execute(insert(ImportRowRecord), [_row_values(import_id, row) for row in batch])

    async def get_import(self, import_id: UUID) -> ImportModel | None:
        """Return an import.

        Args:
            import_id (UUID): The import.

        Returns:
            ImportModel | None: The import, or None when it does not exist.
        """
        record = await self.session.scalar(select(ImportRecord).where(ImportRecord.id == import_id))
        return None if record is None else _import_model(record)

    async def get_import_locked(self, import_id: UUID) -> ImportModel | None:
        """Lock an import's row. The caller already holds its site's lock.

        ``populate_existing`` matters here: the session's identity map would otherwise answer with the state from
        before the wait, so a second concurrent commit would write everything again.

        Args:
            import_id (UUID): The import.

        Returns:
            ImportModel | None: The import as of the lock, or None when it does not exist.
        """
        record = await self.session.scalar(
            select(ImportRecord)
            .where(ImportRecord.id == import_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        return None if record is None else _import_model(record)

    async def find_by_key(self, site_id: UUID, key: str) -> UUID | None:
        """Return the import of a site that stored this key.

        Args:
            site_id (UUID): The site.
            key (str): The idempotency key.

        Returns:
            UUID | None: The import, or None when no import of this site stored it.
        """
        return await self.session.scalar(
            select(ImportRecord.id).where(ImportRecord.site_id == site_id, ImportRecord.idempotency_key == key)
        )

    async def accepted_page(self, import_id: UUID, after_row: int, limit: int) -> list[ImportRowModel]:
        """Return accepted rows after a data row. Plain columns, so a large file never fills the identity map.

        Args:
            import_id (UUID): The import.
            after_row (int): The last data row already returned; 0 to start.
            limit (int): Maximum rows.

        Returns:
            list[ImportRowModel]: Rows with their parsed data, in data row order.
        """
        rows = await self.session.execute(
            select(ImportRowRecord.data_row, ImportRowRecord.file_line, ImportRowRecord.parsed)
            .where(
                ImportRowRecord.import_id == import_id,
                ImportRowRecord.data_row > after_row,
                ImportRowRecord.status == ImportRowStatus.ACCEPTED.value,
            )
            .order_by(ImportRowRecord.data_row)
            .limit(limit)
        )
        return [
            ImportRowModel(
                data_row=row.data_row, file_line=row.file_line, status=ImportRowStatus.ACCEPTED, parsed=row.parsed
            )
            for row in rows
        ]

    async def mark_committed(self, import_id: UUID, key: str, result: dict[str, Any]) -> bool:
        """Store a preview's key and result and set it committed, in one statement.

        Args:
            import_id (UUID): The import.
            key (str): The idempotency key that succeeded.
            result (dict[str, Any]): The first result, as JSON.

        Returns:
            bool: False when the row was no longer a preview, and nothing changed.
        """
        outcome = await self.session.execute(
            update(ImportRecord)
            .where(ImportRecord.id == import_id, ImportRecord.status == ImportStatus.PREVIEWED.value)
            .values(status=ImportStatus.COMMITTED.value, idempotency_key=key, commit_result=result)
        )
        return outcome.rowcount == 1

    async def error_page(self, import_id: UUID, after_row: int, limit: int) -> list[ImportRowModel]:
        """Return invalid and conflict rows after a data row.

        Args:
            import_id (UUID): The import.
            after_row (int): The last data row already returned; 0 to start.
            limit (int): Maximum rows.

        Returns:
            list[ImportRowModel]: Rows in data row order.
        """
        records = await self.session.scalars(
            select(ImportRowRecord)
            .where(
                ImportRowRecord.import_id == import_id,
                ImportRowRecord.data_row > after_row,
                ImportRowRecord.status.in_(_ERROR_STATUSES),
            )
            .order_by(ImportRowRecord.data_row)
            .limit(limit)
        )
        return [
            ImportRowModel(
                data_row=record.data_row,
                file_line=record.file_line,
                status=ImportRowStatus(record.status),
                reason=record.reason,
                field=record.field,
                message=record.message,
            )
            for record in records
        ]

    async def delete_expired(self, now: datetime, limit: int) -> int:
        """Delete expired previews of any site. Rows held by a concurrent purge are left to it.

        Args:
            now (datetime): Wall-clock now.
            limit (int): Maximum imports to delete.

        Returns:
            int: How many were deleted.
        """
        expired = (
            select(ImportRecord.id)
            .where(ImportRecord.status == ImportStatus.PREVIEWED.value, ImportRecord.expires_at < now)
            .order_by(ImportRecord.expires_at)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        return await self._delete_previews(expired)

    async def keep_newest_uncommitted(self, site_id: UUID, keep: int, *, excluding: UUID | None = None) -> int:
        """Delete a site's previews beyond the newest ones. Committed imports are never touched.

        Args:
            site_id (UUID): The site.
            keep (int): How many previews stay, not counting ``excluding``.
            excluding (UUID | None, optional): A preview that is neither counted nor removed, so one that was just
                stored cannot purge itself when ``created_at`` ties or inverts. Defaults to None.

        Returns:
            int: How many were deleted.
        """
        beyond = (
            select(ImportRecord.id)
            .where(ImportRecord.site_id == site_id, ImportRecord.status == ImportStatus.PREVIEWED.value)
            .order_by(ImportRecord.created_at.desc(), ImportRecord.id.desc())
            .offset(keep)
        )
        if excluding is not None:
            beyond = beyond.where(ImportRecord.id != excluding)
        return await self._delete_previews(beyond)

    async def _delete_previews(self, chosen: Select) -> int:
        # Chosen in a statement of its own: as a subquery of the DELETE, Postgres may run it more than once, and a
        # LIMIT there can then remove more rows than it names.
        ids = list(await self.session.scalars(chosen))
        if not ids:
            return 0
        # The status repeats here so a row that a concurrent commit just changed is rechecked and kept.
        statement = delete(ImportRecord).where(
            ImportRecord.id.in_(ids), ImportRecord.status == ImportStatus.PREVIEWED.value
        )
        return (await self.session.execute(statement)).rowcount
