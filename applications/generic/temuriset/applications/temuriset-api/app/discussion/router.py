"""The pitch room: messages, tasks, whose turn, notifications and the Beranda queue."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, status

from app.core.database import SessionDep
from app.core.security import PrincipalDep
from app.core.types import Limit
from app.discussion.model.schema import (
    CompleteTaskRequest,
    CreateTaskRequest,
    MessageResponse,
    NotificationResponse,
    QueueItem,
    SendMessageRequest,
    TaskResponse,
)
from app.discussion.service.next_action import NextAction
from app.discussion.service.service import DiscussionService
from app.platform.model.schema import OperationResult
from app.platform.service.idempotency import Idempotency, idempotent

router = APIRouter(tags=["discussion"])


@router.get("/pitches/{pitch_id}/messages", summary="Read a room's messages")
async def list_messages(
    pitch_id: UUID, principal: PrincipalDep, session: SessionDep, since: datetime | None = None, limit: Limit = 100
) -> list[MessageResponse]:
    """Read messages oldest first; poll with ``since`` for newer ones.

    Args:
        pitch_id (UUID): The pitch.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.
        since (datetime | None, optional): Only messages after this instant. Defaults to None.
        limit (int, optional): The most to return. Defaults to 100.

    Returns:
        list[MessageResponse]: Messages.
    """
    return await DiscussionService(session).messages(principal, pitch_id, since, limit)


@router.post("/pitches/{pitch_id}/messages", status_code=status.HTTP_201_CREATED, summary="Send a message")
async def send_message(
    pitch_id: UUID,
    body: SendMessageRequest,
    principal: PrincipalDep,
    session: SessionDep,
    operation: Idempotency = idempotent("messages.send"),
) -> MessageResponse:
    """Add a message to the room; a retry with the same key returns the same message.

    Args:
        pitch_id (UUID): The pitch.
        body (SendMessageRequest): The text.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.
        operation (Idempotency): Replays a retried request.

    Returns:
        MessageResponse: The message.
    """
    sent = await DiscussionService(session).send_message(principal, pitch_id, body, operation.operation_id)
    result = OperationResult(type="message", id=str(sent.id))
    return await operation.respond(sent, status_code=201, result=result)  # type: ignore[return-value]


@router.get("/pitches/{pitch_id}/tasks", summary="Read a room's tasks")
async def list_tasks(pitch_id: UUID, principal: PrincipalDep, session: SessionDep) -> list[TaskResponse]:
    """Read tasks oldest first.

    Args:
        pitch_id (UUID): The pitch.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.

    Returns:
        list[TaskResponse]: Tasks.
    """
    return await DiscussionService(session).tasks(principal, pitch_id)


@router.post("/pitches/{pitch_id}/tasks", status_code=status.HTTP_201_CREATED, summary="Add a task")
async def add_task(
    pitch_id: UUID,
    body: CreateTaskRequest,
    principal: PrincipalDep,
    session: SessionDep,
    operation: Idempotency = idempotent("tasks.create"),
) -> TaskResponse:
    """Add a task owned by one of the two parties.

    Args:
        pitch_id (UUID): The pitch.
        body (CreateTaskRequest): Title, owner, due date and reference.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.
        operation (Idempotency): Replays a retried request.

    Returns:
        TaskResponse: The task.
    """
    task = await DiscussionService(session).add_task(principal, pitch_id, body, operation.operation_id)
    result = OperationResult(type="task", id=str(task.id))
    return await operation.respond(task, status_code=201, result=result)  # type: ignore[return-value]


@router.post("/tasks/{task_id}/complete", summary="Complete a task")
async def complete_task(
    task_id: UUID,
    body: CompleteTaskRequest,
    principal: PrincipalDep,
    session: SessionDep,
    operation: Idempotency = idempotent("tasks.complete"),
) -> TaskResponse:
    """Mark a task done against its version.

    Args:
        task_id (UUID): The task.
        body (CompleteTaskRequest): ``expected_version``.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.
        operation (Idempotency): Replays a retried request.

    Returns:
        TaskResponse: The task.
    """
    task = await DiscussionService(session).complete_task(principal, task_id, body, operation.operation_id)
    return await operation.respond(task, result=OperationResult(type="task", id=str(task.id)))  # type: ignore[return-value]


@router.get("/pitches/{pitch_id}/next-action", summary="Whose turn it is")
async def read_next_action(pitch_id: UUID, principal: PrincipalDep, session: SessionDep) -> NextAction:
    """Return who acts next on a pitch, for the active party, computed on the server.

    Args:
        pitch_id (UUID): The pitch.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.

    Returns:
        NextAction: ``who`` is ``you``, ``other`` or null, with a title, text, tab and action.
    """
    return await DiscussionService(session).next_action(principal, pitch_id)


@router.get("/me/queue", summary="What waits, for Beranda")
async def read_queue(principal: PrincipalDep, session: SessionDep) -> list[QueueItem]:
    """List pitches waiting on someone, those waiting on the active party first.

    Args:
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.

    Returns:
        list[QueueItem]: Items.
    """
    return await DiscussionService(session).queue(principal)


@router.get("/notifications", summary="Read my notifications")
async def list_notifications(
    principal: PrincipalDep,
    session: SessionDep,
    since: datetime | None = None,
    unread: bool = False,
    limit: Limit = 50,
) -> list[NotificationResponse]:
    """Read the active party's in-app notifications, newest first.

    Args:
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.
        since (datetime | None, optional): Only newer ones. Defaults to None.
        unread (bool, optional): Only unread ones. Defaults to False.
        limit (int, optional): The most to return. Defaults to 50.

    Returns:
        list[NotificationResponse]: Notifications.
    """
    return await DiscussionService(session).notifications(principal, since, unread, limit)


@router.put("/notifications/{notification_id}/read", summary="Mark a notification read")
async def mark_read(notification_id: UUID, principal: PrincipalDep, session: SessionDep) -> NotificationResponse:
    """Mark one notification read; repeating it changes nothing.

    Args:
        notification_id (UUID): The notification.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.

    Returns:
        NotificationResponse: The notification.
    """
    return await DiscussionService(session).mark_read(principal, notification_id)
