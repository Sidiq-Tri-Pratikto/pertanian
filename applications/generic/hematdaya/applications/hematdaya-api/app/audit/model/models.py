"""Audit domain model."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class AuditEventModel(BaseModel):
    """One committed change: who, what, when and the affected interval.

    Attributes:
        site_id (UUID): The site changed.
        actor_principal_id (UUID): Who changed it.
        action (str): Dotted action name, for example ``binding.closed``.
        subject_type (str): The changed entity type.
        subject_id (UUID): The changed entity.
        affected_from (datetime | None): Start of the affected data interval.
        affected_to (datetime | None): End of the affected data interval, exclusive.
        detail (dict[str, Any]): Non-secret changed fields.
    """

    site_id: UUID
    actor_principal_id: UUID
    action: str
    subject_type: str
    subject_id: UUID
    affected_from: datetime | None = None
    affected_to: datetime | None = None
    detail: dict[str, Any] = {}
