"""Import repository over SQLAlchemy."""

from collections.abc import Iterable
from datetime import datetime
from itertools import batched
from uuid import UUID

from sqlalchemy import Select, delete, insert, select
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

    async def keep_newest_uncommitted(self, site_id: UUID, keep: int) -> int:
        """Delete a site's previews beyond the newest ones. Committed imports are never touched.

        Args:
            site_id (UUID): The site.
            keep (int): How many previews stay.

        Returns:
            int: How many were deleted.
        """
        beyond = (
            select(ImportRecord.id)
            .where(ImportRecord.site_id == site_id, ImportRecord.status == ImportStatus.PREVIEWED.value)
            .order_by(ImportRecord.created_at.desc(), ImportRecord.id.desc())
            .offset(keep)
        )
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
