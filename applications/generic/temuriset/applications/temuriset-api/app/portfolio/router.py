"""Inventions: create, list, read, save draft, publish, archive, public view, public updates."""

from uuid import UUID

from fastapi import APIRouter, status

from app.core.database import SessionDep
from app.core.security import PrincipalDep
from app.platform.model.schema import OperationResult
from app.platform.service.idempotency import Idempotency, idempotent
from app.portfolio.model.schema import (
    CreateInventionRequest,
    DraftRequest,
    EditUpdateRequest,
    InventionResponse,
    InventionSummaryResponse,
    InventionUpdateResponse,
    InvestorDigestRequest,
    PublicInventionResponse,
    PublicPageRequest,
    PublishResponse,
    UpdateRequest,
    VersionedActionRequest,
)
from app.portfolio.service.service import PortfolioService
from app.portfolio.service.updates import UpdateService

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
    invention_id: UUID,
    body: VersionedActionRequest,
    principal: PrincipalDep,
    session: SessionDep,
    operation: Idempotency = idempotent("inventions.archive"),
) -> InventionResponse:
    """Archive: hidden from discovery and new submissions; history stays readable.

    Args:
        invention_id (UUID): The invention.
        body (VersionedActionRequest): Acting party and ``expected_version``.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.
        operation (Idempotency): Replays a retried request.

    Returns:
        InventionResponse: The archived invention.
    """
    archived = await PortfolioService(session).archive(principal, invention_id, body, operation.operation_id)
    return await operation.respond(  # type: ignore[return-value]
        archived, result=OperationResult(type="invention", id=str(invention_id))
    )


@router.put("/{invention_id}/investor-digest", summary="Include in investor alerts and digests")
async def set_investor_digest(
    invention_id: UUID, body: InvestorDigestRequest, principal: PrincipalDep, session: SessionDep
) -> InventionResponse:
    """Switch whether investor alerts and digests may include this published invention; off by default.

    Args:
        invention_id (UUID): The invention.
        body (InvestorDigestRequest): Acting party, ``expected_version`` and the switch.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.

    Returns:
        InventionResponse: The invention.
    """
    return await PortfolioService(session).set_investor_digest(principal, invention_id, body)


@router.put("/{invention_id}/public-page", summary="Publish or withdraw the public invention page")
async def set_public_page(
    invention_id: UUID, body: PublicPageRequest, principal: PrincipalDep, session: SessionDep
) -> InventionResponse:
    """Switch the signed-out invention page and its photo and field-test summary; independent of investor alerts.

    Args:
        invention_id (UUID): The invention.
        body (PublicPageRequest): Acting party, ``expected_version``, the switch and the additions.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.

    Returns:
        InventionResponse: The invention.
    """
    return await PortfolioService(session).set_public_page(principal, invention_id, body)


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


@router.get("/{invention_id}/updates", summary="List the invention's public updates")
async def list_updates(
    invention_id: UUID, principal: PrincipalDep, session: SessionDep
) -> list[InventionUpdateResponse]:
    """List drafts, published and withdrawn updates, newest first, for the managing party.

    Args:
        invention_id (UUID): The invention.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.

    Returns:
        list[InventionUpdateResponse]: Up to 100 updates.
    """
    return await UpdateService(session).list_for_owner(principal, invention_id)


@router.post("/{invention_id}/updates", status_code=status.HTTP_201_CREATED, summary="Write a public update")
async def create_update(
    invention_id: UUID,
    body: UpdateRequest,
    principal: PrincipalDep,
    session: SessionDep,
    operation: Idempotency = idempotent("inventions.updates.create"),
) -> InventionUpdateResponse:
    """Save a new update as a draft; nothing is shown or sent yet.

    Args:
        invention_id (UUID): The invention.
        body (UpdateRequest): Acting party, title, body and language.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.
        operation (Idempotency): Replays a retried request.

    Returns:
        InventionUpdateResponse: The draft.
    """
    update = await UpdateService(session).create(principal, invention_id, body)
    update.operation_id = operation.operation_id
    return await operation.respond(  # type: ignore[return-value]
        update, status_code=201, result=OperationResult(type="invention_update", id=str(update.id))
    )


@router.put("/{invention_id}/updates/{update_id}", summary="Correct a public update")
async def edit_update(
    invention_id: UUID, update_id: UUID, body: EditUpdateRequest, principal: PrincipalDep, session: SessionDep
) -> InventionUpdateResponse:
    """Correct the text against ``expected_version``; a published update is never announced again.

    Args:
        invention_id (UUID): The invention.
        update_id (UUID): The update.
        body (EditUpdateRequest): The corrected text.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.

    Returns:
        InventionUpdateResponse: The update.
    """
    return await UpdateService(session).edit(principal, invention_id, update_id, body)


@router.post("/{invention_id}/updates/{update_id}/publish", summary="Publish a public update")
async def publish_update(
    invention_id: UUID,
    update_id: UUID,
    body: VersionedActionRequest,
    principal: PrincipalDep,
    session: SessionDep,
    operation: Idempotency = idempotent("inventions.updates.publish"),
) -> InventionUpdateResponse:
    """Show the update on the public page; needs the invention published and its public page on.

    Args:
        invention_id (UUID): The invention.
        update_id (UUID): The update.
        body (VersionedActionRequest): Acting party and ``expected_version``.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.
        operation (Idempotency): Replays a retried request.

    Returns:
        InventionUpdateResponse: The published update.
    """
    update = await UpdateService(session).publish(principal, invention_id, update_id, body)
    update.operation_id = operation.operation_id
    return await operation.respond(  # type: ignore[return-value]
        update, result=OperationResult(type="invention_update", id=str(update.id))
    )


@router.post("/{invention_id}/updates/{update_id}/withdraw", summary="Withdraw a public update")
async def withdraw_update(
    invention_id: UUID,
    update_id: UUID,
    body: VersionedActionRequest,
    principal: PrincipalDep,
    session: SessionDep,
    operation: Idempotency = idempotent("inventions.updates.withdraw"),
) -> InventionUpdateResponse:
    """Take a published update off the public page.

    Args:
        invention_id (UUID): The invention.
        update_id (UUID): The update.
        body (VersionedActionRequest): Acting party and ``expected_version``.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.
        operation (Idempotency): Replays a retried request.

    Returns:
        InventionUpdateResponse: The withdrawn update.
    """
    update = await UpdateService(session).withdraw(principal, invention_id, update_id, body)
    update.operation_id = operation.operation_id
    return await operation.respond(  # type: ignore[return-value]
        update, result=OperationResult(type="invention_update", id=str(update.id))
    )
