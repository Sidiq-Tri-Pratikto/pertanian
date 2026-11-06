"""Support requests: create, list, read, update as new versions, and status changes."""

from uuid import UUID

from fastapi import APIRouter, status

from app.core.database import SessionDep
from app.core.security import PrincipalDep
from app.needs.model.schema import CreateSupportRequest, SupportRequestResponse, TransitionRequest, UpdateSupportRequest
from app.needs.service.service import NeedsService
from app.platform.model.schema import OperationResult
from app.platform.service.idempotency import Idempotency, idempotent

router = APIRouter(prefix="/support-requests", tags=["support requests"])


@router.post("", status_code=status.HTTP_201_CREATED, summary="Start a support request")
async def create_support_request(
    body: CreateSupportRequest,
    principal: PrincipalDep,
    session: SessionDep,
    operation: Idempotency = idempotent("support_requests.create"),
) -> SupportRequestResponse:
    """Start a draft request for a published invention, with an optional budget.

    Args:
        body (CreateSupportRequest): Invention and content.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.
        operation (Idempotency): Replays a retried request.

    Returns:
        SupportRequestResponse: The draft.
    """
    created = await NeedsService(session).create(principal, body)
    created.operation_id = operation.operation_id
    return await operation.respond(  # type: ignore[return-value]
        created, status_code=201, result=OperationResult(type="support_request", id=str(created.id))
    )


@router.get("", summary="List my support requests")
async def list_support_requests(
    principal: PrincipalDep, session: SessionDep, invention_id: UUID | None = None
) -> list[SupportRequestResponse]:
    """List the acting party's requests, optionally for one invention.

    Args:
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.
        invention_id (UUID | None, optional): Only this invention's. Defaults to None.

    Returns:
        list[SupportRequestResponse]: Requests.
    """
    return await NeedsService(session).list_mine(principal, invention_id)


@router.get("/{request_id}", summary="Read a support request")
async def read_support_request(
    request_id: UUID, principal: PrincipalDep, session: SessionDep
) -> SupportRequestResponse:
    """Read one request as its owner.

    Args:
        request_id (UUID): The request.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.

    Returns:
        SupportRequestResponse: The request.
    """
    return await NeedsService(session).read(principal, request_id)


@router.get("/{request_id}/versions/{number}", summary="Read an earlier version")
async def read_support_request_version(
    request_id: UUID, number: int, principal: PrincipalDep, session: SessionDep
) -> dict:
    """Read a request as it stood at one version.

    Args:
        request_id (UUID): The request.
        number (int): The version.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.

    Returns:
        dict: The snapshot.
    """
    return await NeedsService(session).version(principal, request_id, number)


@router.put("/{request_id}", summary="Change a support request")
async def update_support_request(
    request_id: UUID,
    body: UpdateSupportRequest,
    principal: PrincipalDep,
    session: SessionDep,
    operation: Idempotency = idempotent("support_requests.update"),
) -> SupportRequestResponse:
    """Replace the content as a new version against ``expected_version``.

    Args:
        request_id (UUID): The request.
        body (UpdateSupportRequest): Content.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.
        operation (Idempotency): Replays a retried save.

    Returns:
        SupportRequestResponse: The new version.
    """
    updated = await NeedsService(session).update(principal, request_id, body, operation.operation_id)
    return await operation.respond(updated, result=OperationResult(type="support_request", id=str(updated.id)))  # type: ignore[return-value]


# Each status change is its own operation, like publishing: a key spent on an activation says nothing about a close.
@router.post("/{request_id}/activate", summary="Activate a support request")
async def activate_support_request(
    request_id: UUID,
    body: TransitionRequest,
    principal: PrincipalDep,
    session: SessionDep,
    operation: Idempotency = idempotent("support_requests.activate"),
) -> SupportRequestResponse:
    """Move to ACTIVE from DRAFT or PAUSED; activation needs an outcome and at least one support form.

    Args:
        request_id (UUID): The request.
        body (TransitionRequest): Acting party and ``expected_version``.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.
        operation (Idempotency): Replays a retried request.

    Returns:
        SupportRequestResponse: The request in its new status.
    """
    moved = await NeedsService(session).transition(principal, request_id, "activate", body, operation.operation_id)
    return await operation.respond(moved, result=OperationResult(type="support_request", id=str(moved.id)))  # type: ignore[return-value]


@router.post("/{request_id}/pause", summary="Pause a support request")
async def pause_support_request(
    request_id: UUID,
    body: TransitionRequest,
    principal: PrincipalDep,
    session: SessionDep,
    operation: Idempotency = idempotent("support_requests.pause"),
) -> SupportRequestResponse:
    """Move from ACTIVE to PAUSED.

    Args:
        request_id (UUID): The request.
        body (TransitionRequest): Acting party and ``expected_version``.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.
        operation (Idempotency): Replays a retried request.

    Returns:
        SupportRequestResponse: The request in its new status.
    """
    moved = await NeedsService(session).transition(principal, request_id, "pause", body, operation.operation_id)
    return await operation.respond(moved, result=OperationResult(type="support_request", id=str(moved.id)))  # type: ignore[return-value]


@router.post("/{request_id}/close", summary="Close a support request")
async def close_support_request(
    request_id: UUID,
    body: TransitionRequest,
    principal: PrincipalDep,
    session: SessionDep,
    operation: Idempotency = idempotent("support_requests.close"),
) -> SupportRequestResponse:
    """Move to CLOSED from DRAFT, ACTIVE or PAUSED.

    Args:
        request_id (UUID): The request.
        body (TransitionRequest): Acting party and ``expected_version``.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.
        operation (Idempotency): Replays a retried request.

    Returns:
        SupportRequestResponse: The request in its new status.
    """
    moved = await NeedsService(session).transition(principal, request_id, "close", body, operation.operation_id)
    return await operation.respond(moved, result=OperationResult(type="support_request", id=str(moved.id)))  # type: ignore[return-value]
