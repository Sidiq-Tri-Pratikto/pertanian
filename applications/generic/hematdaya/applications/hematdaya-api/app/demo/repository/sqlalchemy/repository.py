"""Demo repository over SQLAlchemy."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.demo.model.models import CreateOperationModel, DemoSessionModel
from app.demo.repository.base_repository import DemoRepository
from app.demo.repository.sqlalchemy.models import CreateOperationRecord, DemoSessionRecord

ADMISSION_LOCK_KEY = 0x48444D4F  # "HDMO": one shared advisory lock for demo admission


def _session(record: DemoSessionRecord) -> DemoSessionModel:
    return DemoSessionModel(
        id=record.id,
        principal_id=record.principal_id,
        site_id=record.site_id,
        scenario_id=record.scenario_id,
        key_version=record.key_version,
        expires_at=record.expires_at,
    )


class SqlAlchemyDemoRepository(DemoRepository):
    """Demo sessions in Postgres."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind to the request session.

        Args:
            session (AsyncSession): The request's session.
        """
        self.session = session

    async def lock_admission(self) -> None:
        """Take the transaction-scoped advisory lock that serializes admission."""
        await self.session.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": ADMISSION_LOCK_KEY})

    async def get_operation(self, operation_id: str) -> CreateOperationModel | None:
        """Return a creation operation.

        Args:
            operation_id (str): Its ID.

        Returns:
            CreateOperationModel | None: The operation, or None.
        """
        record = await self.session.get(CreateOperationRecord, operation_id, populate_existing=True)
        if record is None:
            return None
        return CreateOperationModel(
            operation_id=record.operation_id,
            session_id=record.session_id,
            scenario_id=record.scenario_id,
            replay_proof_hash=record.replay_proof_hash,
            key_version=record.key_version,
            response=record.response,
            replay_expires_at=record.replay_expires_at,
            retain_until=record.retain_until,
        )

    async def add_operation(self, operation: CreateOperationModel) -> None:
        """Store a creation operation.

        Args:
            operation (CreateOperationModel): The operation.
        """
        self.session.add(CreateOperationRecord(**operation.model_dump()))
        await self.session.flush()

    async def get_session(self, session_id: UUID) -> DemoSessionModel | None:
        """Return a session.

        Args:
            session_id (UUID): Its ID.

        Returns:
            DemoSessionModel | None: The session, or None once purged or ended.
        """
        record = await self.session.get(DemoSessionRecord, session_id, populate_existing=True)
        return _session(record) if record is not None else None

    async def session_for_principal(self, principal_id: UUID) -> DemoSessionModel | None:
        """Return a demo principal's session.

        Args:
            principal_id (UUID): The principal.

        Returns:
            DemoSessionModel | None: The session, or None.
        """
        record = await self.session.scalar(
            select(DemoSessionRecord).where(DemoSessionRecord.principal_id == principal_id)
        )
        return _session(record) if record is not None else None

    async def session_for_token(self, token_hash: bytes) -> DemoSessionModel | None:
        """Return the session for a token digest.

        Args:
            token_hash (bytes): SHA-256 of the bearer token.

        Returns:
            DemoSessionModel | None: The session, or None.
        """
        record = await self.session.scalar(select(DemoSessionRecord).where(DemoSessionRecord.token_hash == token_hash))
        return _session(record) if record is not None else None

    async def add_session(self, session: DemoSessionModel, token_hash: bytes) -> None:
        """Store a session.

        Args:
            session (DemoSessionModel): The session.
            token_hash (bytes): Its token digest; the token itself is never stored.
        """
        self.session.add(DemoSessionRecord(**session.model_dump(), token_hash=token_hash))
        await self.session.flush()

    async def expired_sessions(self, now: datetime) -> list[DemoSessionModel]:
        """Return expired sessions.

        Args:
            now (datetime): Wall-clock now.

        Returns:
            list[DemoSessionModel]: Sessions to purge, by site ID.
        """
        query = select(DemoSessionRecord).where(DemoSessionRecord.expires_at <= now).order_by(DemoSessionRecord.site_id)
        return [_session(record) for record in await self.session.scalars(query)]

    async def delete_operations_retained_until(self, now: datetime) -> None:
        """Delete operation records whose retention has passed.

        Args:
            now (datetime): Wall-clock now.
        """
        await self.session.execute(delete(CreateOperationRecord).where(CreateOperationRecord.retain_until <= now))

    async def count_active(self, now: datetime) -> int:
        """Count live sessions.

        Args:
            now (datetime): Wall-clock now.

        Returns:
            int: Sessions that have not expired.
        """
        query = select(func.count()).select_from(DemoSessionRecord).where(DemoSessionRecord.expires_at > now)
        return await self.session.scalar(query) or 0

    async def count_created_since(self, since: datetime) -> int:
        """Count admitted creations.

        Args:
            since (datetime): Window start.

        Returns:
            int: Operations created after ``since``.
        """
        query = select(func.count()).select_from(CreateOperationRecord).where(CreateOperationRecord.created_at > since)
        return await self.session.scalar(query) or 0
