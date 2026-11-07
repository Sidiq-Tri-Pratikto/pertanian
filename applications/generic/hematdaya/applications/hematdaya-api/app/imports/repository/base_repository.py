"""Import storage interface."""

from abc import ABC, abstractmethod
from collections.abc import Iterable
from datetime import datetime
from typing import Any
from uuid import UUID

from app.imports.model.models import ImportModel, ImportRowModel


class ImportRepository(ABC):
    """Stores previews and their row results. It flushes and never commits."""

    @abstractmethod
    async def add_import(self, model: ImportModel) -> None:
        """Insert an import."""

    @abstractmethod
    async def add_rows(self, import_id: UUID, rows: Iterable[ImportRowModel]) -> None:
        """Insert an import's row results in bulk, consuming ``rows`` one batch at a time."""

    @abstractmethod
    async def get_import(self, import_id: UUID) -> ImportModel | None:
        """Return an import, or None."""

    @abstractmethod
    async def get_import_locked(self, import_id: UUID) -> ImportModel | None:
        """Lock an import's row and return its state as of the lock, or None."""

    @abstractmethod
    async def find_by_key(self, site_id: UUID, key: str) -> UUID | None:
        """Return the import of a site that stored this key, or None."""

    @abstractmethod
    async def accepted_page(self, import_id: UUID, after_row: int, limit: int) -> list[ImportRowModel]:
        """Return accepted rows with their parsed data after a data row, in data row order."""

    @abstractmethod
    async def mark_committed(self, import_id: UUID, key: str, result: dict[str, Any]) -> bool:
        """Store a preview's key and result and set it committed; False when it was no longer a preview."""

    @abstractmethod
    async def error_page(self, import_id: UUID, after_row: int, limit: int) -> list[ImportRowModel]:
        """Return invalid and conflict rows after a data row, in data row order."""

    @abstractmethod
    async def delete_expired(self, now: datetime, limit: int) -> int:
        """Delete up to ``limit`` expired previews of any site, oldest first, and return how many."""

    @abstractmethod
    async def keep_newest_uncommitted(self, site_id: UUID, keep: int, *, excluding: UUID | None = None) -> int:
        """Delete a site's previews beyond its newest ``keep``, never ``excluding``, and return how many."""
