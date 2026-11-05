"""One worker pass: claim due events and jobs, run them, record the outcome, back off on failure."""

import asyncio
import logging
from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core import clock
from app.core.errors.base import AppError
from app.core.errors.recorder import record_failure
from app.platform.model.models import JobModel, OutboxEventModel
from app.platform.repository.sqlalchemy.repository import SqlAlchemyPlatformRepository
from app.worker.registry import Registry

MAX_ATTEMPTS = 8
BATCH_SIZE = 20
_BASE_DELAY = timedelta(seconds=5)
_MAX_DELAY = timedelta(hours=1)
_FAILURE_STATUS = 500

logger = logging.getLogger(__name__)


def backoff(attempts: int) -> timedelta:
    """Delay before the next attempt: doubling from five seconds, at most an hour.

    Args:
        attempts (int): Failed attempts so far, at least 1.

    Returns:
        timedelta: The delay.
    """
    return min(_BASE_DELAY * 2 ** (attempts - 1), _MAX_DELAY)


async def dispatch_events(session_factory: async_sessionmaker[AsyncSession], registry: Registry) -> int:
    """Run every consumer of each due event once.

    Claimed events stay locked until this transaction ends, so a second worker skips them. Each consumer runs in a
    savepoint: a failure undoes only its own writes, the delivery records of consumers that succeeded commit, and
    the event comes back after a backoff. A consumer with a delivery record never runs again for that event.

    Args:
        session_factory (async_sessionmaker[AsyncSession]): Session factory.
        registry (Registry): Consumers per topic.

    Returns:
        int: Events claimed.
    """
    async with session_factory() as session, session.begin():
        repository = SqlAlchemyPlatformRepository(session)
        events = await repository.claim_due_events(now=clock.now(), max_attempts=MAX_ATTEMPTS, limit=BATCH_SIZE)
        for event in events:
            await _dispatch_one(session, repository, registry, event)
        return len(events)


async def _dispatch_one(
    session: AsyncSession, repository: SqlAlchemyPlatformRepository, registry: Registry, event: OutboxEventModel
) -> None:
    delivered = await repository.delivered_consumers(event.id)
    failure: AppError | None = None
    for name, handler in registry.consumers.get(event.topic, {}).items():
        if name in delivered:
            continue
        try:
            async with session.begin_nested():
                await handler(session, event.payload)
                await repository.add_delivery(event_id=event.id, consumer=name)
        except Exception as error:  # noqa: BLE001 - worker boundary: one failing consumer must not stop the others
            failure = AppError(error=error)
            record_failure(failure, operation=f"consumer:{event.topic}:{name}", http_status=_FAILURE_STATUS)
    if failure is None:
        await repository.update_event(event.id, dispatched_at=clock.now())
        return
    attempts = event.attempts + 1
    await repository.update_event(
        event.id, attempts=attempts, available_at=clock.now() + backoff(attempts), last_error_code=failure.code
    )


async def run_jobs(session_factory: async_sessionmaker[AsyncSession], registry: Registry) -> int:
    """Run each due job, retrying failures with backoff until the attempt limit.

    Args:
        session_factory (async_sessionmaker[AsyncSession]): Session factory.
        registry (Registry): Handlers per job kind.

    Returns:
        int: Jobs claimed.
    """
    async with session_factory() as session, session.begin():
        repository = SqlAlchemyPlatformRepository(session)
        jobs = await repository.claim_due_jobs(now=clock.now(), limit=BATCH_SIZE)
        for job in jobs:
            await _run_one(session, repository, registry, job)
        return len(jobs)


async def _run_one(
    session: AsyncSession, repository: SqlAlchemyPlatformRepository, registry: Registry, job: JobModel
) -> None:
    handler = registry.jobs.get(job.kind)
    if handler is None:
        # Nothing can run it until a release registers the kind; an operator decides.
        await repository.update_job(job.id, status="NEEDS_MANUAL_INPUT", last_error_code="UNKNOWN_JOB_KIND")
        return
    try:
        async with session.begin_nested():
            result_ref = await handler(session, job.input)
    except Exception as error:  # noqa: BLE001 - worker boundary: a failing job is recorded and retried
        failure = AppError(error=error)
        record_failure(failure, operation=f"job:{job.kind}", http_status=_FAILURE_STATUS)
        attempts = job.attempts + 1
        retry = attempts < MAX_ATTEMPTS
        await repository.update_job(
            job.id,
            attempts=attempts,
            status="PENDING" if retry else "FAILED",
            run_after=clock.now() + backoff(attempts),
            last_error_code=failure.code,
        )
        return
    await repository.update_job(job.id, status="SUCCEEDED", result_ref=result_ref, attempts=job.attempts + 1)


async def run_forever(
    session_factory: async_sessionmaker[AsyncSession],
    registry: Registry,
    *,
    poll_seconds: float = 1.0,
    stop: asyncio.Event | None = None,
) -> None:
    """Poll until stopped, sleeping only when there was nothing to do.

    Args:
        session_factory (async_sessionmaker[AsyncSession]): Session factory.
        registry (Registry): Consumers and job handlers.
        poll_seconds (float, optional): Idle sleep. Defaults to 1.0.
        stop (asyncio.Event | None, optional): Set to finish after the current pass. Defaults to None.
    """
    stop = stop or asyncio.Event()
    while not stop.is_set():
        try:
            busy = await dispatch_events(session_factory, registry) + await run_jobs(session_factory, registry)
        except Exception as error:  # noqa: BLE001 - the loop outlives a database outage; it retries next poll
            record_failure(AppError(error=error), operation="worker:poll", http_status=_FAILURE_STATUS)
            busy = 0
        if not busy:
            try:
                await asyncio.wait_for(stop.wait(), timeout=poll_seconds)
            except TimeoutError:
                pass
