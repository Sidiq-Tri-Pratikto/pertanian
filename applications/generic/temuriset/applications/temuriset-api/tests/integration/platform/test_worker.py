"""Outbox dispatch and jobs through Postgres (spec 005, US2)."""

import asyncio
from collections import Counter
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import clock
from app.core.database import get_session_factory
from app.platform.repository.sqlalchemy.models import JobRecord, OutboxDeliveryRecord, OutboxEventRecord
from app.platform.service.outbox import enqueue_job, publish
from app.worker.loop import MAX_ATTEMPTS, dispatch_events, run_forever, run_jobs
from app.worker.registry import Registry

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("clean_tables")]

START = datetime(2026, 11, 5, 9, tzinfo=UTC)
FAKE_SECRET = "sk-fakeworkersecret123"


async def _publish(count: int = 1, topic: str = "note.created") -> list[UUID]:
    async with get_session_factory()() as session:
        ids = [await publish(session, topic, {"n": index}) for index in range(count)]
        await session.commit()
        return ids


async def _event(event_id: UUID) -> OutboxEventRecord:
    async with get_session_factory()() as session:
        event = await session.get(OutboxEventRecord, event_id)
        assert event is not None
        return event


async def _deliveries() -> int:
    async with get_session_factory()() as session:
        return await session.scalar(select(func.count()).select_from(OutboxDeliveryRecord)) or 0


async def test_events_are_delivered_to_every_consumer_once() -> None:
    """
    Condition:
    - Two consumers listen to a topic and the worker runs twice.

    Expected:
    - Each consumer handles the event once and the event is marked dispatched.
    """
    calls: Counter[str] = Counter()
    registry = Registry()
    registry.consumer("note.created", "index")(lambda _session, _payload: _count(calls, "index"))
    registry.consumer("note.created", "notify")(lambda _session, _payload: _count(calls, "notify"))
    with clock.frozen(START):
        [event_id] = await _publish()
        await dispatch_events(get_session_factory(), registry)
        await dispatch_events(get_session_factory(), registry)

    assert calls == {"index": 1, "notify": 1}
    assert (await _event(event_id)).dispatched_at == START
    assert await _deliveries() == 2


async def _count(calls: Counter[str], name: str) -> None:
    calls[name] += 1


async def test_failing_consumer_retries_with_backoff_without_repeating_the_others(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """
    Condition:
    - One of two consumers fails once (AC46).

    Expected:
    - The healthy consumer runs once; the event waits five seconds, then the failing consumer runs again and
      succeeds. The failure is recorded without the secret it carried.
    """
    calls: Counter[str] = Counter()
    failures = [True]
    registry = Registry()

    @registry.consumer("note.created", "healthy")
    async def healthy(_session: AsyncSession, _payload: dict[str, Any]) -> None:
        calls["healthy"] += 1

    @registry.consumer("note.created", "flaky")
    async def flaky(_session: AsyncSession, _payload: dict[str, Any]) -> None:
        calls["flaky"] += 1
        if failures and failures.pop():
            raise RuntimeError(f"provider refused token={FAKE_SECRET}")

    with clock.frozen(START):
        [event_id] = await _publish()
        await dispatch_events(get_session_factory(), registry)
    event = await _event(event_id)
    assert (event.attempts, event.available_at, event.dispatched_at) == (1, START + timedelta(seconds=5), None)
    assert event.last_error_code == "APP-UNKNOWN"

    with clock.frozen(START + timedelta(seconds=4)):
        assert await dispatch_events(get_session_factory(), registry) == 0
    with clock.frozen(START + timedelta(seconds=5)):
        await dispatch_events(get_session_factory(), registry)

    assert calls == {"healthy": 1, "flaky": 2}
    assert (await _event(event_id)).dispatched_at is not None
    assert "consumer:note.created:flaky" in caplog.text
    assert FAKE_SECRET not in caplog.text


async def test_consumer_writes_roll_back_with_its_failure() -> None:
    """
    Condition:
    - A consumer writes to the database and then fails midway (SC-002), then the worker restarts.

    Expected:
    - Its half-done write is gone, and after the retry exactly one delivery and one write exist.
    """
    attempts = [True]
    registry = Registry()

    @registry.consumer("note.created", "writer")
    async def writer(session: AsyncSession, _payload: dict[str, Any]) -> None:
        await enqueue_job(session, "derived")
        if attempts and attempts.pop():
            raise RuntimeError("killed midway")

    with clock.frozen(START):
        await _publish()
        await dispatch_events(get_session_factory(), registry)
    async with get_session_factory()() as session:
        assert await session.scalar(select(func.count()).select_from(JobRecord)) == 0

    with clock.frozen(START + timedelta(minutes=1)):
        await dispatch_events(get_session_factory(), Registry(consumers=registry.consumers))

    assert await _deliveries() == 1
    async with get_session_factory()() as session:
        assert await session.scalar(select(func.count()).select_from(JobRecord)) == 1


async def test_event_stops_at_the_attempt_limit() -> None:
    """
    Condition:
    - A consumer always fails.

    Expected:
    - After the attempt limit the event is no longer claimed and stays undispatched for an operator.
    """
    registry = Registry()

    @registry.consumer("note.created", "broken")
    async def broken(_session: AsyncSession, _payload: dict[str, Any]) -> None:
        raise RuntimeError("always")

    [event_id] = await _publish()
    for hour in range(MAX_ATTEMPTS + 2):
        with clock.frozen(START + timedelta(days=hour)):
            await dispatch_events(get_session_factory(), registry)

    event = await _event(event_id)
    assert (event.attempts, event.dispatched_at) == (MAX_ATTEMPTS, None)


async def test_two_workers_claim_each_event_once() -> None:
    """
    Condition:
    - Two workers poll at the same moment over 30 events.

    Expected:
    - Every event is handled exactly once.
    """
    seen: Counter[str] = Counter()
    registry = Registry()

    @registry.consumer("note.created", "slow")
    async def slow(_session: AsyncSession, payload: dict[str, Any]) -> None:
        seen[str(payload["n"])] += 1
        await asyncio.sleep(0.01)

    await _publish(30)
    for _ in range(3):
        await asyncio.gather(
            dispatch_events(get_session_factory(), registry), dispatch_events(get_session_factory(), registry)
        )

    assert len(seen) == 30
    assert set(seen.values()) == {1}
    assert await _deliveries() == 30


async def test_jobs_succeed_retry_fail_and_wait_for_unknown_kinds() -> None:
    """
    Condition:
    - A job that succeeds, one that fails until the limit, and one with no handler.

    Expected:
    - ``SUCCEEDED`` with its result, ``FAILED`` after the limit, ``NEEDS_MANUAL_INPUT`` for the unknown kind.
    """
    registry = Registry()

    @registry.job("export")
    async def export(_session: AsyncSession, job_input: dict[str, Any]) -> dict[str, Any]:
        return {"type": "export", "id": job_input["id"]}

    @registry.job("broken")
    async def broken(_session: AsyncSession, _input: dict[str, Any]) -> None:
        raise RuntimeError("always")

    with clock.frozen(START):
        async with get_session_factory()() as session:
            done = await enqueue_job(session, "export", {"id": "e1"})
            failing = await enqueue_job(session, "broken")
            unknown = await enqueue_job(session, "nobody-handles-this")
            await session.commit()
    for day in range(MAX_ATTEMPTS + 1):
        with clock.frozen(START + timedelta(days=day)):
            await run_jobs(get_session_factory(), registry)

    async with get_session_factory()() as session:
        jobs = {job.id: job for job in await session.scalars(select(JobRecord))}
    assert (jobs[done].status, jobs[done].result_ref) == ("SUCCEEDED", {"type": "export", "id": "e1"})
    assert (jobs[failing].status, jobs[failing].attempts) == ("FAILED", MAX_ATTEMPTS)
    assert (jobs[unknown].status, jobs[unknown].last_error_code) == ("NEEDS_MANUAL_INPUT", "UNKNOWN_JOB_KIND")


async def test_worker_loop_stops_when_asked() -> None:
    """
    Condition:
    - The worker loop runs with one queued event, then receives a stop signal.

    Expected:
    - It delivers the event and returns.
    """
    delivered = asyncio.Event()
    registry = Registry()

    @registry.consumer("note.created", "signal")
    async def signal(_session: AsyncSession, _payload: dict[str, Any]) -> None:
        delivered.set()

    await _publish()
    stop = asyncio.Event()
    worker = asyncio.create_task(run_forever(get_session_factory(), registry, poll_seconds=0.05, stop=stop))
    await asyncio.wait_for(delivered.wait(), timeout=5)
    stop.set()
    await asyncio.wait_for(worker, timeout=5)

    assert await _deliveries() == 1
