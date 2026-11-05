"""Company funding: legal entities and funding requests. Every mutation needs ``company_funding``; reads never do."""

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, status

from app.capabilities.service.guard import require_capability
from app.core.database import SessionDep
from app.core.security import PrincipalDep
from app.funding.model.schema import (
    FundingRequestInput,
    FundingRequestResponse,
    LegalEntityInput,
    LegalEntityResponse,
    UpdateFundingRequest,
)
from app.funding.service.service import FundingService
from app.needs.model.schema import TransitionRequest
from app.platform.model.schema import OperationResult
from app.platform.service.idempotency import Idempotency, idempotent

router = APIRouter(tags=["company funding"])
GUARD = [require_capability("company_funding")]


@router.post(
    "/legal-entities", status_code=status.HTTP_201_CREATED, dependencies=GUARD, summary="Declare a legal entity"
)
async def declare_legal_entity(
    body: LegalEntityInput, principal: PrincipalDep, session: SessionDep
) -> LegalEntityResponse:
    """Record a company as declared by the acting party.

    Args:
        body (LegalEntityInput): Name, jurisdiction and registration reference.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.

    Returns:
        LegalEntityResponse: The entity.
    """
    return await FundingService(session).declare_entity(principal, body)


@router.get("/legal-entities", summary="List my legal entities")
async def list_legal_entities(principal: PrincipalDep, session: SessionDep) -> list[LegalEntityResponse]:
    """List the acting party's legal entities.

    Args:
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.

    Returns:
        list[LegalEntityResponse]: Entities.
    """
    return await FundingService(session).entities(principal)


@router.post(
    "/funding-requests", status_code=status.HTTP_201_CREATED, dependencies=GUARD, summary="Start a funding request"
)
async def create_funding_request(
    body: FundingRequestInput,
    principal: PrincipalDep,
    session: SessionDep,
    operation: Idempotency = idempotent("funding_requests.create"),
) -> FundingRequestResponse:
    """Start a draft raise linked to published inventions.

    Args:
        body (FundingRequestInput): Content and links.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.
        operation (Idempotency): Replays a retried request.

    Returns:
        FundingRequestResponse: The draft.
    """
    created = await FundingService(session).create(principal, body)
    created.operation_id = operation.operation_id
    return await operation.respond(  # type: ignore[return-value]
        created, status_code=201, result=OperationResult(type="funding_request", id=str(created.id))
    )


@router.get("/funding-requests", summary="List my funding requests")
async def list_funding_requests(principal: PrincipalDep, session: SessionDep) -> list[FundingRequestResponse]:
    """List the acting party's funding requests, also when company funding is switched off (AC67).

    Args:
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.

    Returns:
        list[FundingRequestResponse]: Requests.
    """
    return await FundingService(session).list_mine(principal)


@router.get("/funding-requests/{request_id}", summary="Read a funding request")
async def read_funding_request(
    request_id: UUID, principal: PrincipalDep, session: SessionDep
) -> FundingRequestResponse:
    """Read one request as its owner.

    Args:
        request_id (UUID): The request.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.

    Returns:
        FundingRequestResponse: The request.
    """
    return await FundingService(session).read(principal, request_id)


@router.get("/funding-requests/{request_id}/versions/{number}", summary="Read an earlier funding request version")
async def read_funding_request_version(
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
    return await FundingService(session).version(principal, request_id, number)


@router.put("/funding-requests/{request_id}", dependencies=GUARD, summary="Change a funding request")
async def update_funding_request(
    request_id: UUID,
    body: UpdateFundingRequest,
    principal: PrincipalDep,
    session: SessionDep,
    operation: Idempotency = idempotent("funding_requests.update"),
) -> FundingRequestResponse:
    """Replace the content as a new version against ``expected_version``.

    Args:
        request_id (UUID): The request.
        body (UpdateFundingRequest): Content.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.
        operation (Idempotency): Replays a retried save.

    Returns:
        FundingRequestResponse: The new version.
    """
    updated = await FundingService(session).update(principal, request_id, body, operation.operation_id)
    return await operation.respond(updated, result=OperationResult(type="funding_request", id=str(updated.id)))  # type: ignore[return-value]


@router.post("/funding-requests/{request_id}/{action}", dependencies=GUARD, summary="Activate, pause or close a raise")
async def transition_funding_request(
    request_id: UUID,
    action: Literal["activate", "pause", "close"],
    body: TransitionRequest,
    principal: PrincipalDep,
    session: SessionDep,
) -> FundingRequestResponse:
    """Change the status.

    Args:
        request_id (UUID): The request.
        action (Literal["activate", "pause", "close"]): The change.
        body (TransitionRequest): Acting party and ``expected_version``.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.

    Returns:
        FundingRequestResponse: The request in its new status.
    """
    return await FundingService(session).transition(principal, request_id, action, body)
