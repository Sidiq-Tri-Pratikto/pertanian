"""Inventions: create, list, read, save draft, publish, archive, public view."""

from uuid import UUID

from fastapi import APIRouter, status

from app.core.database import SessionDep
from app.core.security import PrincipalDep
from app.platform.model.schema import OperationResult
from app.platform.service.idempotency import Idempotency, idempotent
from app.portfolio.model.schema import (
    CreateInventionRequest,
    DraftRequest,
    InventionResponse,
    InventionSummaryResponse,
    PublicInventionResponse,
    PublishResponse,
    VersionedActionRequest,
)
from app.portfolio.service.service import PortfolioService

router = APIRouter(prefix="/inventions", tags=["inventions"])


@router.post("", status_code=status.HTTP_201_CREATED, summary="Start an invention")
async def create_invention(
    body: CreateInventionRequest,
    principal: PrincipalDep,
    session: SessionDep,
    operation: Idempotency = idempotent("inventions.create"),
) -> InventionResponse:
    """Start an invention with an empty draft for the acting party.

    Args:
        body (CreateInventionRequest): Acting party.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.
        operation (Idempotency): Replays a retried request.

    Returns:
        InventionResponse: The invention.
    """
    invention = await PortfolioService(session).create(principal, body)
    invention.operation_id = operation.operation_id
    return await operation.respond(  # type: ignore[return-value]
        invention, status_code=201, result=OperationResult(type="invention", id=str(invention.id))
    )


@router.get("", summary="List my inventions")
async def list_inventions(principal: PrincipalDep, session: SessionDep) -> list[InventionSummaryResponse]:
    """List the acting party's inventions, drafts and archived ones included.

    Args:
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.

    Returns:
        list[InventionSummaryResponse]: Inventions.
    """
    return await PortfolioService(session).list_mine(principal)


@router.get("/{invention_id}", summary="Read an invention as its owner")
async def read_invention(invention_id: UUID, principal: PrincipalDep, session: SessionDep) -> InventionResponse:
    """Read draft, published version and history.

    Args:
        invention_id (UUID): The invention.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.

    Returns:
        InventionResponse: The invention.
    """
    return await PortfolioService(session).owner_view(principal, invention_id)


@router.put("/{invention_id}/draft", summary="Save the draft")
async def save_draft(
    invention_id: UUID,
    body: DraftRequest,
    principal: PrincipalDep,
    session: SessionDep,
    operation: Idempotency = idempotent("inventions.save_draft"),
) -> InventionResponse:
    """Save the whole draft against ``expected_version``; publication rules do not apply here.

    Args:
        invention_id (UUID): The invention.
        body (DraftRequest): Content.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.
        operation (Idempotency): Replays a retried save.

    Returns:
        InventionResponse: The invention with its saved draft.
    """
    invention = await PortfolioService(session).save_draft(principal, invention_id, body, operation.operation_id)
    return await operation.respond(  # type: ignore[return-value]
        invention, result=OperationResult(type="invention", id=str(invention.id))
    )


@router.post("/{invention_id}/publish", summary="Publish the draft")
async def publish_invention(
    invention_id: UUID,
    body: VersionedActionRequest,
    principal: PrincipalDep,
    session: SessionDep,
    operation: Idempotency = idempotent("inventions.publish"),
) -> PublishResponse:
    """Publish the draft as an immutable version.

    Args:
        invention_id (UUID): The invention.
        body (VersionedActionRequest): Acting party and ``expected_version``.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.
        operation (Idempotency): Replays a retried request.

    Returns:
        PublishResponse: The version number and status.
    """
    result = await PortfolioService(session).publish(principal, invention_id, body)
    result.operation_id = operation.operation_id
    return await operation.respond(  # type: ignore[return-value]
        result, result=OperationResult(type="invention", id=str(invention_id))
    )


@router.post("/{invention_id}/archive", summary="Archive an invention")
async def archive_invention(
    invention_id: UUID, body: VersionedActionRequest, principal: PrincipalDep, session: SessionDep
) -> InventionResponse:
    """Archive: hidden from discovery and new submissions; history stays readable.

    Args:
        invention_id (UUID): The invention.
        body (VersionedActionRequest): Acting party and ``expected_version``.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.

    Returns:
        InventionResponse: The archived invention.
    """
    return await PortfolioService(session).archive(principal, invention_id, body)


@router.get("/{invention_id}/public", summary="Read the published version")
async def read_public(invention_id: UUID, _: PrincipalDep, session: SessionDep) -> PublicInventionResponse:
    """Read what anyone signed in may see: the published version, nothing private.

    Args:
        invention_id (UUID): The invention.
        _ (PrincipalDep): Any signed-in account.
        session (SessionDep): Database session.

    Returns:
        PublicInventionResponse: The projection.
    """
    return await PortfolioService(session).public_view(invention_id)
