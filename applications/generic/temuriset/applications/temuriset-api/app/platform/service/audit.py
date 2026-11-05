"""Audit events: who did what to which subject, committed with the change itself."""

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.platform.repository.sqlalchemy.repository import SqlAlchemyPlatformRepository


async def record_audit(
    session: AsyncSession,
    *,
    action: str,
    subject_type: str,
    subject_id: str,
    actor_party_id: UUID | None = None,
    actor_account_id: UUID | None = None,
    detail: dict[str, Any] | None = None,
) -> None:
    """Append an audit event to the caller's transaction, so it exists only if the change commits.

    Args:
        session (AsyncSession): The request's session.
        action (str): What happened, such as ``pitch.submitted``.
        subject_type (str): Kind of subject.
        subject_id (str): Subject id.
        actor_party_id (UUID | None, optional): Acting party. Defaults to None.
        actor_account_id (UUID | None, optional): Acting account. Defaults to None.
        detail (dict[str, Any] | None, optional): Non-secret facts about the change. Defaults to None.
    """
    await SqlAlchemyPlatformRepository(session).add_audit_event(
        action=action,
        subject_type=subject_type,
        subject_id=subject_id,
        actor_party_id=actor_party_id,
        actor_account_id=actor_account_id,
        detail=detail or {},
    )
