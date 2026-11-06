"""The pitch room: messages, tasks, notifications, whose turn and the Beranda queue (spec 027)."""

from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.access.service.policy import check_context
from app.access.service.service import party_names
from app.core import clock
from app.core.errors.base import FieldsInvalidError, InvalidTransitionError, NotFoundError
from app.discussion.model.schema import (
    CompleteTaskRequest,
    CreateTaskRequest,
    MessageResponse,
    NotificationResponse,
    QueueItem,
    SendMessageRequest,
    TaskResponse,
)
from app.discussion.repository.sqlalchemy.models import MessageRecord, NotificationRecord, TaskRecord
from app.discussion.repository.sqlalchemy.repository import SqlAlchemyDiscussionRepository
from app.discussion.service.next_action import NO_SCHEDULE, NextAction, next_action, schedule_states
from app.identity.model.models import Principal
from app.pitches.repository.sqlalchemy.models import PitchRecord
from app.pitches.service.decisions import require_side, side_of, visible_pitch
from app.pitches.service.submission import pitches_of_party
from app.platform.service.audit import record_audit
from app.platform.service.versions import check_expected

_ENDED = ("REJECTED", "WITHDRAWN", "CLOSED")
QUEUE_LIMIT = 50


async def turn_for(
    session: AsyncSession, record: PitchRecord, party_id: UUID, names: dict[UUID, str] | None = None
) -> NextAction:
    """Return the next action on one pitch for one of its parties.

    Args:
        session (AsyncSession): The request's session.
        record (PitchRecord): The pitch.
        party_id (UUID): The reader's party.
        names (dict[UUID, str] | None, optional): Known party names. Defaults to None.

    Returns:
        NextAction: The next action.
    """
    states = await schedule_states(session, [record.id])
    other = record.recipient_party_id if party_id == record.requester_party_id else record.requester_party_id
    names = names or await party_names(session, [other])
    side = "requester" if party_id == record.requester_party_id else "recipient"
    return next_action(record.status, side, party_id, names.get(other, ""), states.get(record.id, NO_SCHEDULE))


class DiscussionService:
    """Messages and tasks in a pitch room, notifications, and what waits on whom."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind to the request.

        Args:
            session (AsyncSession): The request's session.
        """
        self.session = session
        self.repository = SqlAlchemyDiscussionRepository(session)

    async def _writable(self, principal: Principal, pitch_id: UUID, acting_party_id: UUID) -> PitchRecord:
        check_context(principal, acting_party_id)
        record, side = await visible_pitch(self.session, principal, pitch_id)
        require_side(principal, side)
        if record.status in _ENDED:
            raise InvalidTransitionError()
        return record

    async def send_message(
        self, principal: Principal, pitch_id: UUID, request: SendMessageRequest, operation_id: UUID | None = None
    ) -> MessageResponse:
        """Add a message to the room. Its text is stored, never logged or audited.

        Args:
            principal (Principal): Who is signed in.
            pitch_id (UUID): The pitch.
            request (SendMessageRequest): The text.
            operation_id (UUID | None, optional): For the response. Defaults to None.

        Returns:
            MessageResponse: The message.

        Raises:
            InvalidTransitionError: After the pitch ended.
        """
        record = await self._writable(principal, pitch_id, request.acting_party_id)
        message = await self.repository.add(
            MessageRecord(
                pitch_id=record.id,
                author_party_id=principal.active_party_id,
                author_account_id=principal.account_id,
                text=request.text,
            )
        )
        await record_audit(
            self.session,
            action="message.sent",
            subject_type="pitch",
            subject_id=str(record.id),
            actor_account_id=principal.account_id,
            actor_party_id=principal.active_party_id,
        )
        names = await party_names(self.session, [principal.active_party_id])
        return self._message(message, principal, names, operation_id)

    @staticmethod
    def _message(
        message: MessageRecord, principal: Principal, names: dict[UUID, str], operation_id: UUID | None = None
    ) -> MessageResponse:
        return MessageResponse(
            id=message.id,
            author_party_id=message.author_party_id,
            author_name=names.get(message.author_party_id, ""),
            mine=message.author_party_id == principal.active_party_id,
            text=message.text,
            created_at=message.created_at,
            operation_id=operation_id,
        )

    async def messages(
        self, principal: Principal, pitch_id: UUID, since: datetime | None, limit: int
    ) -> list[MessageResponse]:
        """Read the room's messages, oldest first; ``since`` returns only newer ones, for polling.

        Args:
            principal (Principal): Who is signed in.
            pitch_id (UUID): The pitch.
            since (datetime | None): Only messages after this instant.
            limit (int): The most to return.

        Returns:
            list[MessageResponse]: Messages.
        """
        record, _ = await visible_pitch(self.session, principal, pitch_id)
        names = await party_names(self.session, [record.requester_party_id, record.recipient_party_id])
        found = await self.repository.messages(record.id, since, limit)
        return [self._message(message, principal, names) for message in found]

    def _task(self, task: TaskRecord, names: dict[UUID, str], operation_id: UUID | None = None) -> TaskResponse:
        return TaskResponse(
            id=task.id,
            title=task.title,
            owner_party_id=task.owner_party_id,
            owner_name=names.get(task.owner_party_id, ""),
            due_date=task.due_date,
            reference=task.reference,
            status=task.status,  # type: ignore[arg-type]
            version=task.version,
            created_at=task.created_at,
            operation_id=operation_id,
        )

    async def add_task(
        self, principal: Principal, pitch_id: UUID, request: CreateTaskRequest, operation_id: UUID | None = None
    ) -> TaskResponse:
        """Add a task owned by one of the two parties. Approval history is untouched.

        Args:
            principal (Principal): Who is signed in.
            pitch_id (UUID): The pitch.
            request (CreateTaskRequest): Title, owner, due date and reference.
            operation_id (UUID | None, optional): For the response. Defaults to None.

        Returns:
            TaskResponse: The task.

        Raises:
            FieldsInvalidError: When the owner is not one of the two parties.
        """
        record = await self._writable(principal, pitch_id, request.acting_party_id)
        parties = (record.requester_party_id, record.recipient_party_id)
        if request.owner_party_id not in parties:
            raise FieldsInvalidError(
                [{"loc": ["body", "owner_party_id"], "msg": "Pilih salah satu pihak pitching ini.", "type": "owner"}]
            )
        task = await self.repository.add(
            TaskRecord(
                pitch_id=record.id,
                title=request.title,
                owner_party_id=request.owner_party_id,
                due_date=request.due_date,
                reference=request.reference,
                created_by_party_id=principal.active_party_id,
            )
        )
        return self._task(task, await party_names(self.session, list(parties)), operation_id)

    async def tasks(self, principal: Principal, pitch_id: UUID) -> list[TaskResponse]:
        """Read the room's tasks.

        Args:
            principal (Principal): Who is signed in.
            pitch_id (UUID): The pitch.

        Returns:
            list[TaskResponse]: Tasks, oldest first.
        """
        record, _ = await visible_pitch(self.session, principal, pitch_id)
        names = await party_names(self.session, [record.requester_party_id, record.recipient_party_id])
        return [self._task(task, names) for task in await self.repository.tasks(record.id)]

    async def complete_task(
        self, principal: Principal, task_id: UUID, request: CompleteTaskRequest, operation_id: UUID | None = None
    ) -> TaskResponse:
        """Mark a task done.

        Args:
            principal (Principal): Who is signed in.
            task_id (UUID): The task.
            request (CompleteTaskRequest): ``expected_version``.
            operation_id (UUID | None, optional): For the response. Defaults to None.

        Returns:
            TaskResponse: The task.

        Raises:
            NotFoundError: For a task outside the reader's rooms.
            InvalidTransitionError: When it is already done.
        """
        task = await self.repository.task(task_id)
        if task is None:
            raise NotFoundError()
        record = await self._writable(principal, task.pitch_id, request.acting_party_id)
        check_expected(task.version, request.expected_version)
        if task.status == "DONE":
            raise InvalidTransitionError()
        task.status, task.completed_at = "DONE", clock.now()
        task.version += 1
        await self.session.flush()
        names = await party_names(self.session, [record.requester_party_id, record.recipient_party_id])
        return self._task(task, names, operation_id)

    async def next_action(self, principal: Principal, pitch_id: UUID) -> NextAction:
        """Return the next action on one pitch for the active party.

        Args:
            principal (Principal): Who is signed in.
            pitch_id (UUID): The pitch.

        Returns:
            NextAction: The next action.
        """
        record, _ = await visible_pitch(self.session, principal, pitch_id)
        return await turn_for(self.session, record, principal.active_party_id)

    async def queue(self, principal: Principal) -> list[QueueItem]:
        """Return the pitches waiting on someone, those waiting on the active party first, for Beranda.

        Args:
            principal (Principal): Who is signed in.

        Returns:
            list[QueueItem]: Items.
        """
        records = await pitches_of_party(self.session, principal.active_party_id, QUEUE_LIMIT)
        states = await schedule_states(self.session, [record.id for record in records])
        parties = {party for record in records for party in (record.requester_party_id, record.recipient_party_id)}
        names = await party_names(self.session, list(parties))
        items = []
        for record in records:
            side = side_of(principal, record)
            assert side is not None  # noqa: S101 - pitches_of_party returns only the party's own pitches
            other = record.recipient_party_id if side == "requester" else record.requester_party_id
            action = next_action(
                record.status, side, principal.active_party_id, names.get(other, ""), states.get(record.id, NO_SCHEDULE)
            )
            if action.who is not None:
                items.append(
                    QueueItem(
                        **action.model_dump(),
                        pitch_id=record.id,
                        subject_title=record.subject_title,
                        opportunity_title=record.opportunity_title,
                        updated_at=record.updated_at,
                    )
                )
        items.sort(key=lambda item: item.updated_at, reverse=True)
        return sorted(items, key=lambda item: item.who != "you")

    @staticmethod
    def _notification(record: NotificationRecord) -> NotificationResponse:
        return NotificationResponse(
            id=record.id,
            pitch_id=record.pitch_id,
            text=record.text,
            tab=record.tab,
            created_at=record.created_at,
            read=record.read_at is not None,
        )

    async def notifications(
        self, principal: Principal, since: datetime | None, unread: bool, limit: int
    ) -> list[NotificationResponse]:
        """Read the active party's notifications, newest first.

        Args:
            principal (Principal): Who is signed in.
            since (datetime | None): Only newer ones, for polling.
            unread (bool): Only unread ones.
            limit (int): The most to return.

        Returns:
            list[NotificationResponse]: Notifications.
        """
        found = await self.repository.notifications(principal.active_party_id, since=since, unread=unread, limit=limit)
        return [self._notification(record) for record in found]

    async def mark_read(self, principal: Principal, notification_id: UUID) -> NotificationResponse:
        """Mark one of the active party's notifications read; repeating it changes nothing.

        Args:
            principal (Principal): Who is signed in.
            notification_id (UUID): The notification.

        Returns:
            NotificationResponse: The notification.

        Raises:
            NotFoundError: For another party's notification.
        """
        record = await self.repository.notification(notification_id)
        if record is None or record.party_id != principal.active_party_id:
            raise NotFoundError()
        if record.read_at is None:
            record.read_at = clock.now()
            await self.session.flush()
        return self._notification(record)
