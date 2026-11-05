"""Platform data access. Writes join the caller's transaction; nothing here commits."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.platform.model.models import IdempotencyModel, JobModel, OutboxEventModel
from app.platform.repository.sqlalchemy.models import (
    AuditEventRecord,
    IdempotencyRecord,
    JobRecord,
    OutboxDeliveryRecord,
    OutboxEventRecord,
)


def _idempotency(record: IdempotencyRecord) -> IdempotencyModel:
    return IdempotencyModel(
        actor_party_id=record.actor_party_id,
        operation=record.operation,
        key=record.key,
        request_sha256=record.request_sha256,
        status=record.status,
        response_status=record.response_status,
        response_body=record.response_body,
        operation_id=record.operation_id,
        result=record.result,
        expires_at=record.expires_at,
    )


class SqlAlchemyPlatformRepository:
    """Platform tables over one session."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind to the request's or the worker's session.

        Args:
            session (AsyncSession): The session whose transaction every write joins.
        """
        self.session = session

    async def claim_idempotency_key(
        self, *, actor_party_id: UUID, operation: str, key: str, request_sha256: str, expires_at: datetime
    ) -> IdempotencyModel:
        """Insert a pending record, or wait for and lock the one holding the key.

        A concurrent request with the same key blocks on the unique index until the first transaction ends, so
        exactly one request runs the operation.

        Args:
            actor_party_id (UUID): The acting party.
            operation (str): The operation name.
            key (str): The client's key.
            request_sha256 (str): Digest of actor, operation, path and canonical body.
            expires_at (datetime): When the key may be reused.

        Returns:
            IdempotencyModel: The record holding the key, locked for this transaction.
        """
        await self.session.execute(
            insert(IdempotencyRecord)
            .values(
                actor_party_id=actor_party_id,
                operation=operation,
                key=key,
                request_sha256=request_sha256,
                status="pending",
                expires_at=expires_at,
            )
            .on_conflict_do_nothing(index_elements=["actor_party_id", "operation", "key"])
        )
        record = await self.session.scalar(
            select(IdempotencyRecord)
            .where(
                IdempotencyRecord.actor_party_id == actor_party_id,
                IdempotencyRecord.operation == operation,
                IdempotencyRecord.key == key,
            )
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        assert record is not None, "the insert or the conflicting row guarantees a record"  # noqa: S101
        return _idempotency(record)

    async def release_idempotency_key(self, operation_id: UUID) -> None:
        """Detach an expired key from its record, keeping the operation readable.

        Args:
            operation_id (UUID): The expired record's operation.
        """
        await self.session.execute(
            update(IdempotencyRecord).where(IdempotencyRecord.operation_id == operation_id).values(key=None)
        )

    async def complete_idempotency(
        self, operation_id: UUID, *, response_status: int, response_body: dict[str, Any], result: dict[str, Any] | None
    ) -> None:
        """Store the response a retry will replay.

        Args:
            operation_id (UUID): The operation.
            response_status (int): HTTP status.
            response_body (dict[str, Any]): JSON body.
            result (dict[str, Any] | None): Reference to what the operation produced.
        """
        await self.session.execute(
            update(IdempotencyRecord)
            .where(IdempotencyRecord.operation_id == operation_id)
            .values(
                status="committed",
                response_status=response_status,
                response_body=response_body,
                result=result,
                version=IdempotencyRecord.version + 1,
            )
        )

    async def find_operation(self, operation_id: UUID) -> IdempotencyModel | None:
        """Read one operation.

        Args:
            operation_id (UUID): The operation.

        Returns:
            IdempotencyModel | None: The record, or None.
        """
        record = await self.session.scalar(
            select(IdempotencyRecord).where(IdempotencyRecord.operation_id == operation_id)
        )
        return _idempotency(record) if record is not None else None

    async def add_audit_event(self, **values: Any) -> None:
        """Append one audit event.

        Args:
            **values (Any): Column values.
        """
        self.session.add(AuditEventRecord(**values))
        await self.session.flush()

    async def add_outbox_event(self, *, topic: str, payload: dict[str, Any]) -> UUID:
        """Queue one outbox event.

        Args:
            topic (str): Event topic.
            payload (dict[str, Any]): JSON payload.

        Returns:
            UUID: The event id.
        """
        record = OutboxEventRecord(topic=topic, payload=payload)
        self.session.add(record)
        await self.session.flush()
        return record.id

    async def add_job(self, **values: Any) -> UUID:
        """Queue one job.

        Args:
            **values (Any): Column values.

        Returns:
            UUID: The job id.
        """
        record = JobRecord(**values)
        self.session.add(record)
        await self.session.flush()
        return record.id

    async def claim_due_events(self, *, now: datetime, max_attempts: int, limit: int) -> list[OutboxEventModel]:
        """Lock due events no other worker holds.

        Args:
            now (datetime): Product time.
            max_attempts (int): Events that reached it are left for an operator.
            limit (int): Batch size.

        Returns:
            list[OutboxEventModel]: The claimed events, locked until the transaction ends.
        """
        records = await self.session.scalars(
            select(OutboxEventRecord)
            .where(
                OutboxEventRecord.dispatched_at.is_(None),
                OutboxEventRecord.available_at <= now,
                OutboxEventRecord.attempts < max_attempts,
            )
            .order_by(OutboxEventRecord.available_at, OutboxEventRecord.id)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        return [
            OutboxEventModel(id=record.id, topic=record.topic, payload=record.payload, attempts=record.attempts)
            for record in records
        ]

    async def delivered_consumers(self, event_id: UUID) -> set[str]:
        """List consumers that already handled an event.

        Args:
            event_id (UUID): The event.

        Returns:
            set[str]: Consumer names.
        """
        rows = await self.session.scalars(
            select(OutboxDeliveryRecord.consumer).where(OutboxDeliveryRecord.event_id == event_id)
        )
        return set(rows)

    async def add_delivery(self, *, event_id: UUID, consumer: str) -> None:
        """Record that a consumer handled an event.

        Args:
            event_id (UUID): The event.
            consumer (str): The consumer name.
        """
        self.session.add(OutboxDeliveryRecord(event_id=event_id, consumer=consumer))
        await self.session.flush()

    async def update_event(self, event_id: UUID, **values: Any) -> None:
        """Change an event's dispatch state.

        Args:
            event_id (UUID): The event.
            **values (Any): Column values.
        """
        await self.session.execute(update(OutboxEventRecord).where(OutboxEventRecord.id == event_id).values(**values))

    async def claim_due_jobs(self, *, now: datetime, limit: int) -> list[JobModel]:
        """Lock pending jobs no other worker holds.

        Args:
            now (datetime): Product time.
            limit (int): Batch size.

        Returns:
            list[JobModel]: The claimed jobs, locked until the transaction ends.
        """
        records = await self.session.scalars(
            select(JobRecord)
            .where(JobRecord.status == "PENDING", JobRecord.run_after <= now)
            .order_by(JobRecord.run_after, JobRecord.id)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        return [
            JobModel(
                id=record.id,
                kind=record.kind,
                actor_party_id=record.actor_party_id,
                input=record.input,
                attempts=record.attempts,
            )
            for record in records
        ]

    async def update_job(self, job_id: UUID, **values: Any) -> None:
        """Change a job's state.

        Args:
            job_id (UUID): The job.
            **values (Any): Column values.
        """
        await self.session.execute(
            update(JobRecord).where(JobRecord.id == job_id).values(version=JobRecord.version + 1, **values)
        )
