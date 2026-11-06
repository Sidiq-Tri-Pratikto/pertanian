"""Outbox events and jobs: side effects queued in the transaction that decided them."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core import clock
from app.platform.repository.sqlalchemy.repository import SqlAlchemyPlatformRepository


async def publish(session: AsyncSession, topic: str, payload: dict[str, Any]) -> UUID:
    """Queue an event for the worker, in the caller's transaction.

    Args:
        session (AsyncSession): The request's session.
        topic (str): Event topic, such as ``pitch.submitted``.
        payload (dict[str, Any]): JSON payload; ids, not private content.

    Returns:
        UUID: The event id.
    """
    return await SqlAlchemyPlatformRepository(session).add_outbox_event(topic=topic, payload=payload)


async def enqueue_job(
    session: AsyncSession,
    kind: str,
    job_input: dict[str, Any] | None = None,
    *,
    actor_party_id: UUID | None = None,
    run_after: datetime | None = None,
    input_expires_at: datetime | None = None,
    dedupe_key: str | None = None,
) -> UUID:
    """Queue a job for the worker, in the caller's transaction.

    Args:
        session (AsyncSession): The request's session.
        kind (str): Job kind with a registered handler.
        job_input (dict[str, Any] | None, optional): JSON input. Defaults to None.
        actor_party_id (UUID | None, optional): Party the job acts for. Defaults to None.
        run_after (datetime | None, optional): Earliest start. Defaults to now.
        input_expires_at (datetime | None, optional): Deadline for scrubbing transient input. Defaults to None.
        dedupe_key (str | None, optional): Stable key for one logical job. Defaults to None.

    Returns:
        UUID: The job id.
    """
    due_at = run_after or clock.now()
    return await SqlAlchemyPlatformRepository(session).add_job(
        kind=kind,
        input=job_input or {},
        actor_party_id=actor_party_id,
        run_after=min(due_at, input_expires_at) if input_expires_at is not None else due_at,
        input_expires_at=input_expires_at,
        dedupe_key=dedupe_key,
    )
