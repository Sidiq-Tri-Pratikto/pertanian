"""Audit trail."""

from datetime import datetime
from typing import Any
from uuid import UUID

from app.audit.model.models import AuditEventModel
from app.audit.repository.base_repository import AuditRepository


class AuditService:
    """Records each committed change once. Callers record only when something actually changed."""

    def __init__(self, repository: AuditRepository) -> None:
        """Bind to storage.

        Args:
            repository (AuditRepository): Audit storage.
        """
        self.repository = repository

    async def record(
        self,
        *,
        site_id: UUID,
        actor_principal_id: UUID,
        action: str,
        subject_type: str,
        subject_id: UUID,
        affected_from: datetime | None = None,
        affected_to: datetime | None = None,
        detail: dict[str, Any] | None = None,
    ) -> None:
        """Append one event in the caller's transaction. Detail must never hold secrets.

        Args:
            site_id (UUID): The site changed.
            actor_principal_id (UUID): Who changed it.
            action (str): Dotted action name.
            subject_type (str): Entity type.
            subject_id (UUID): Entity.
            affected_from (datetime | None, optional): Affected interval start. Defaults to None.
            affected_to (datetime | None, optional): Affected interval end. Defaults to None.
            detail (dict[str, Any] | None, optional): Changed non-secret fields. Defaults to None.
        """
        await self.repository.add(
            AuditEventModel(
                site_id=site_id,
                actor_principal_id=actor_principal_id,
                action=action,
                subject_type=subject_type,
                subject_id=subject_id,
                affected_from=affected_from,
                affected_to=affected_to,
                detail=detail or {},
            )
        )
