"""Partner intake: profiles, opportunities with versions and states, and external handoffs."""

from uuid import UUID

from fastapi import APIRouter, status

from app.core.database import SessionDep
from app.core.security import PrincipalDep
from app.core.types import MAX_LIMIT, Limit
from app.intake.model.schema import (
    CreateOpportunityRequest,
    HandoffResponse,
    OpportunityResponse,
    OpportunityTransitionRequest,
    OpportunityVersionResponse,
    PartnerProfileResponse,
    RecordHandoffRequest,
    SaveOpportunityRequest,
    SavePartnerProfileRequest,
)
from app.intake.service.service import IntakeService
from app.platform.model.schema import OperationResult
from app.platform.service.idempotency import Idempotency, idempotent

router = APIRouter(tags=["partner intake"])


@router.get("/partners/{party_id}", summary="Read a partner profile")
async def read_partner(party_id: UUID, principal: PrincipalDep, session: SessionDep) -> PartnerProfileResponse:
    """Read what a partner states about itself, as anyone signed in may see it.

    Args:
        party_id (UUID): The party.
        principal (PrincipalDep): Any signed-in account.
        session (SessionDep): Database session.

    Returns:
        PartnerProfileResponse: The profile.
    """
    return await IntakeService(session).read_profile(party_id, owner=principal.active_party_id == party_id)


@router.put("/partners/{party_id}", summary="Save one's own partner profile")
async def save_partner(
    party_id: UUID,
    body: SavePartnerProfileRequest,
    principal: PrincipalDep,
    session: SessionDep,
    operation: Idempotency = idempotent("partners.save"),
) -> PartnerProfileResponse:
    """Create or replace the profile. ``expected_version`` is null only for the first save.

    Args:
        party_id (UUID): The party.
        body (SavePartnerProfileRequest): Content and ``expected_version``.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.
        operation (Idempotency): Replays a retried save.

    Returns:
        PartnerProfileResponse: The saved profile.
    """
    saved = await IntakeService(session).save_profile(principal, party_id, body, operation.operation_id)
    return await operation.respond(saved, result=OperationResult(type="partner_profile", id=str(party_id)))  # type: ignore[return-value]


@router.post("/partners/{party_id}/handoffs", status_code=status.HTTP_201_CREATED, summary="Follow an external route")
async def record_handoff(
    party_id: UUID,
    body: RecordHandoffRequest,
    principal: PrincipalDep,
    session: SessionDep,
    operation: Idempotency = idempotent("partners.handoff"),
) -> HandoffResponse:
    """Record that the acting party followed a partner's external route. This is never a submitted pitch.

    Args:
        party_id (UUID): The partner.
        body (RecordHandoffRequest): The acting party.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.
        operation (Idempotency): Replays a retried click.

    Returns:
        HandoffResponse: The handoff, with the address to open.
    """
    handoff = await IntakeService(session).record_handoff(principal, party_id, body, operation.operation_id)
    return await operation.respond(  # type: ignore[return-value]
        handoff, status_code=201, result=OperationResult(type="external_handoff", id=str(handoff.id))
    )


@router.post("/opportunities", status_code=status.HTTP_201_CREATED, summary="Start an opportunity")
async def create_opportunity(
    body: CreateOpportunityRequest,
    principal: PrincipalDep,
    session: SessionDep,
    operation: Idempotency = idempotent("opportunities.create"),
) -> OpportunityResponse:
    """Start a draft for the acting party.

    Args:
        body (CreateOpportunityRequest): Kind and content.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.
        operation (Idempotency): Replays a retried request.

    Returns:
        OpportunityResponse: The draft.
    """
    created = await IntakeService(session).create(principal, body, operation.operation_id)
    return await operation.respond(  # type: ignore[return-value]
        created, status_code=201, result=OperationResult(type="opportunity", id=str(created.id))
    )


@router.get("/opportunities", summary="List opportunities")
async def list_opportunities(
    principal: PrincipalDep, session: SessionDep, partner_party_id: UUID | None = None, limit: Limit = MAX_LIMIT
) -> list[OpportunityResponse]:
    """List the acting party's opportunities, or what another partner has made visible.

    Args:
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.
        partner_party_id (UUID | None, optional): Another partner. Defaults to None.
        limit (Limit, optional): The most to return. Defaults to 100.

    Returns:
        list[OpportunityResponse]: Opportunities.
    """
    return await IntakeService(session).list_for(principal, partner_party_id, limit)


@router.get("/opportunities/{opportunity_id}", summary="Read an opportunity")
async def read_opportunity(opportunity_id: UUID, principal: PrincipalDep, session: SessionDep) -> OpportunityResponse:
    """Read an opportunity with its current version.

    Args:
        opportunity_id (UUID): The opportunity.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.

    Returns:
        OpportunityResponse: The opportunity.
    """
    return await IntakeService(session).read(principal, opportunity_id)


@router.get("/opportunities/{opportunity_id}/versions/{number}", summary="Read one version of an opportunity")
async def read_opportunity_version(
    opportunity_id: UUID, number: int, principal: PrincipalDep, session: SessionDep
) -> OpportunityVersionResponse:
    """Read one version as it stood.

    Args:
        opportunity_id (UUID): The opportunity.
        number (int): The version number.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.

    Returns:
        OpportunityVersionResponse: The version.
    """
    return await IntakeService(session).read_version(principal, opportunity_id, number)


@router.put("/opportunities/{opportunity_id}", summary="Change an opportunity")
async def save_opportunity(
    opportunity_id: UUID,
    body: SaveOpportunityRequest,
    principal: PrincipalDep,
    session: SessionDep,
    operation: Idempotency = idempotent("opportunities.save"),
) -> OpportunityResponse:
    """Save the content: a draft in place, a live opportunity as the next version, current at once.

    Args:
        opportunity_id (UUID): The opportunity.
        body (SaveOpportunityRequest): Content and ``expected_version``.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.
        operation (Idempotency): Replays a retried save.

    Returns:
        OpportunityResponse: The opportunity with its new content.
    """
    saved = await IntakeService(session).save(principal, opportunity_id, body, operation.operation_id)
    return await operation.respond(saved, result=OperationResult(type="opportunity", id=str(saved.id)))  # type: ignore[return-value]


# Each status change is its own operation, like publishing: a key spent on an activation says nothing about a close.
@router.post("/opportunities/{opportunity_id}/activate", summary="Activate an opportunity")
async def activate_opportunity(
    opportunity_id: UUID,
    body: OpportunityTransitionRequest,
    principal: PrincipalDep,
    session: SessionDep,
    operation: Idempotency = idempotent("opportunities.activate"),
) -> OpportunityResponse:
    """Move to ACTIVE from DRAFT or PAUSED; going live needs a profile and everything a partner must state.

    Args:
        opportunity_id (UUID): The opportunity.
        body (OpportunityTransitionRequest): Acting party and ``expected_version``.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.
        operation (Idempotency): Replays a retried request.

    Returns:
        OpportunityResponse: The opportunity in its new status.
    """
    moved = await IntakeService(session).transition(principal, opportunity_id, "activate", body, operation.operation_id)
    return await operation.respond(moved, result=OperationResult(type="opportunity", id=str(moved.id)))  # type: ignore[return-value]


@router.post("/opportunities/{opportunity_id}/pause", summary="Pause an opportunity")
async def pause_opportunity(
    opportunity_id: UUID,
    body: OpportunityTransitionRequest,
    principal: PrincipalDep,
    session: SessionDep,
    operation: Idempotency = idempotent("opportunities.pause"),
) -> OpportunityResponse:
    """Move from ACTIVE to PAUSED.

    Args:
        opportunity_id (UUID): The opportunity.
        body (OpportunityTransitionRequest): Acting party and ``expected_version``.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.
        operation (Idempotency): Replays a retried request.

    Returns:
        OpportunityResponse: The opportunity in its new status.
    """
    moved = await IntakeService(session).transition(principal, opportunity_id, "pause", body, operation.operation_id)
    return await operation.respond(moved, result=OperationResult(type="opportunity", id=str(moved.id)))  # type: ignore[return-value]


@router.post("/opportunities/{opportunity_id}/close", summary="Close an opportunity")
async def close_opportunity(
    opportunity_id: UUID,
    body: OpportunityTransitionRequest,
    principal: PrincipalDep,
    session: SessionDep,
    operation: Idempotency = idempotent("opportunities.close"),
) -> OpportunityResponse:
    """Move to CLOSED from DRAFT, ACTIVE or PAUSED. New pitches stop; nothing is invented for existing ones.

    Args:
        opportunity_id (UUID): The opportunity.
        body (OpportunityTransitionRequest): Acting party and ``expected_version``.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.
        operation (Idempotency): Replays a retried request.

    Returns:
        OpportunityResponse: The opportunity in its new status.
    """
    moved = await IntakeService(session).transition(principal, opportunity_id, "close", body, operation.operation_id)
    return await operation.respond(moved, result=OperationResult(type="opportunity", id=str(moved.id)))  # type: ignore[return-value]
