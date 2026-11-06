"""Discussion storage."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.discussion.repository.sqlalchemy.models import MessageRecord, NotificationRecord, TaskRecord


class SqlAlchemyDiscussionRepository:
    """Writes and reads messages, tasks and notifications."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind to the session.

        Args:
            session (AsyncSession): The request's session.
        """
        self.session = session

    async def add[RecordT](self, record: RecordT) -> RecordT:
        """Insert a record.

        Args:
            record (RecordT): A message or task.

        Returns:
            RecordT: The stored record.
        """
        self.session.add(record)
        await self.session.flush()
        return record

    async def messages(self, pitch_id: UUID, since: datetime | None, limit: int) -> list[MessageRecord]:
        """Read a room's messages, oldest first, optionally only those after a time.

        Args:
            pitch_id (UUID): The pitch.
            since (datetime | None): Only newer messages.
            limit (int): The most to return.

        Returns:
            list[MessageRecord]: Messages.
        """
        query = select(MessageRecord).where(MessageRecord.pitch_id == pitch_id)
        if since is not None:
            query = query.where(MessageRecord.created_at > since)
        return list(await self.session.scalars(query.order_by(MessageRecord.created_at, MessageRecord.id).limit(limit)))

    async def tasks(self, pitch_id: UUID) -> list[TaskRecord]:
        """Read a room's tasks, oldest first.

        Args:
            pitch_id (UUID): The pitch.

        Returns:
            list[TaskRecord]: Tasks.
        """
        query = select(TaskRecord).where(TaskRecord.pitch_id == pitch_id).order_by(TaskRecord.created_at)
        return list(await self.session.scalars(query))

    async def task(self, task_id: UUID) -> TaskRecord | None:
        """Find a task, locked for a change.

        Args:
            task_id (UUID): The task.

        Returns:
            TaskRecord | None: The task.
        """
        query = select(TaskRecord).where(TaskRecord.id == task_id).with_for_update()
        return await self.session.scalar(query.execution_options(populate_existing=True))

    async def notify(self, values: dict[str, Any]) -> bool:
        """Insert a notification unless one exists for its event, party and channel.

        Args:
            values (dict[str, Any]): Column values.

        Returns:
            bool: Whether a row was added.
        """
        statement = (
            insert(NotificationRecord)
            .values(**values)
            .on_conflict_do_nothing(index_elements=["event_key", "party_id", "channel"])
        )
        result = await self.session.execute(statement)
        return bool(result.rowcount)  # type: ignore[attr-defined]

    async def notifications(
        self, party_id: UUID, *, since: datetime | None, unread: bool, limit: int
    ) -> list[NotificationRecord]:
        """Read a party's notifications, newest first.

        Args:
            party_id (UUID): The party.
            since (datetime | None): Only newer ones.
            unread (bool): Only unread ones.
            limit (int): The most to return.

        Returns:
            list[NotificationRecord]: Notifications.
        """
        query = select(NotificationRecord).where(NotificationRecord.party_id == party_id)
        if since is not None:
            query = query.where(NotificationRecord.created_at > since)
        if unread:
            query = query.where(NotificationRecord.read_at.is_(None))
        order = (NotificationRecord.created_at.desc(), NotificationRecord.id)
        return list(await self.session.scalars(query.order_by(*order).limit(limit)))

    async def notification(self, notification_id: UUID) -> NotificationRecord | None:
        """Find a notification.

        Args:
            notification_id (UUID): The notification.

        Returns:
            NotificationRecord | None: The notification.
        """
        return await self.session.get(NotificationRecord, notification_id)
