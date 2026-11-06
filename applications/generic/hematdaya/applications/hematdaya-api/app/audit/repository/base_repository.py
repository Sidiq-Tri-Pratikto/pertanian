"""Audit storage interface."""

from abc import ABC, abstractmethod

from app.audit.model.models import AuditEventModel


class AuditRepository(ABC):
    """Appends audit events."""

    @abstractmethod
    async def add(self, event: AuditEventModel) -> None:
        """Append an event in the current transaction."""
