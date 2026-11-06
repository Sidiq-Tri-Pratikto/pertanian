"""Relationship records: propose, correct, confirm, decline, restrict, contest, read."""

from uuid import UUID

from fastapi import APIRouter

from app.core.database import SessionDep
from app.core.security import PrincipalDep
from app.platform.model.schema import OperationResult
from app.platform.service.idempotency import Idempotency, idempotent
from app.relationships.model.schema import (
    ConfirmRequest,
    CorrectionRequest,
    PartnershipResponse,
    ProfileResponse,
    ProposePartnershipRequest,
    PublicProfileResponse,
    RestrictRequest,
    ReviewRequest,
    SaveProfileRequest,
    VersionedPartnershipRequest,
)
from app.relationships.service.public_profile import PublicProfileService
from app.relationships.service.service import RelationshipService

router = APIRouter(tags=["relationships"])


@router.post("/pitches/{pitch_id}/partnerships", status_code=201, summary="Propose a relationship summary")
async def propose(
    pitch_id: UUID,
    body: ProposePartnershipRequest,
    principal: PrincipalDep,
    session: SessionDep,
    operation: Idempotency = idempotent("partnerships.propose"),
) -> PartnershipResponse:
    """Propose a relationship summary.

    Args:
        pitch_id (UUID): The pitch.
        body (ProposePartnershipRequest): The request.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.
        operation (Idempotency): Replays a retried request.

    Returns:
        PartnershipResponse: The relationship as its parties see it.
    """
    done = await RelationshipService(session).propose(principal, pitch_id, body, operation.operation_id)
    result = OperationResult(type="partnership", id=str(done.id))
    return await operation.respond(done, status_code=201, result=result)  # type: ignore[return-value]


@router.post("/partnerships/{partnership_id}/corrections", status_code=201, summary="Correct a relationship summary")
async def correct(
    partnership_id: UUID,
    body: CorrectionRequest,
    principal: PrincipalDep,
    session: SessionDep,
    operation: Idempotency = idempotent("partnerships.correct"),
) -> PartnershipResponse:
    """Correct a relationship summary.

    Args:
        partnership_id (UUID): The relationship.
        body (CorrectionRequest): The request.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.
        operation (Idempotency): Replays a retried request.

    Returns:
        PartnershipResponse: The relationship as its parties see it.
    """
    done = await RelationshipService(session).correct(principal, partnership_id, body, operation.operation_id)
    result = OperationResult(type="partnership", id=str(done.id))
    return await operation.respond(done, status_code=201, result=result)  # type: ignore[return-value]


@router.post("/partnerships/{partnership_id}/confirmations", status_code=200, summary="Confirm a relationship summary")
async def confirm(
    partnership_id: UUID,
    body: ConfirmRequest,
    principal: PrincipalDep,
    session: SessionDep,
    operation: Idempotency = idempotent("partnerships.confirm"),
) -> PartnershipResponse:
    """Confirm a relationship summary.

    Args:
        partnership_id (UUID): The relationship.
        body (ConfirmRequest): The request.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.
        operation (Idempotency): Replays a retried request.

    Returns:
        PartnershipResponse: The relationship as its parties see it.
    """
    done = await RelationshipService(session).confirm(principal, partnership_id, body, operation.operation_id)
    result = OperationResult(type="partnership", id=str(done.id))
    return await operation.respond(done, status_code=200, result=result)  # type: ignore[return-value]


@router.post("/partnerships/{partnership_id}/decline", status_code=200, summary="Decline a relationship summary")
async def decline(
    partnership_id: UUID,
    body: VersionedPartnershipRequest,
    principal: PrincipalDep,
    session: SessionDep,
    operation: Idempotency = idempotent("partnerships.decline"),
) -> PartnershipResponse:
    """Decline a relationship summary.

    Args:
        partnership_id (UUID): The relationship.
        body (VersionedPartnershipRequest): The request.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.
        operation (Idempotency): Replays a retried request.

    Returns:
        PartnershipResponse: The relationship as its parties see it.
    """
    done = await RelationshipService(session).decline(principal, partnership_id, body, operation.operation_id)
    result = OperationResult(type="partnership", id=str(done.id))
    return await operation.respond(done, status_code=200, result=result)  # type: ignore[return-value]


@router.post("/partnerships/{partnership_id}/restrictions", status_code=201, summary="Hide a public field")
async def restrict(
    partnership_id: UUID,
    body: RestrictRequest,
    principal: PrincipalDep,
    session: SessionDep,
    operation: Idempotency = idempotent("partnerships.restrict"),
) -> PartnershipResponse:
    """Hide a public field.

    Args:
        partnership_id (UUID): The relationship.
        body (RestrictRequest): The request.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.
        operation (Idempotency): Replays a retried request.

    Returns:
        PartnershipResponse: The relationship as its parties see it.
    """
    done = await RelationshipService(session).restrict(principal, partnership_id, body, operation.operation_id)
    result = OperationResult(type="partnership", id=str(done.id))
    return await operation.respond(done, status_code=201, result=result)  # type: ignore[return-value]


@router.post("/partnerships/{partnership_id}/request-review", status_code=200, summary="Contest the public claim")
async def request_review(
    partnership_id: UUID,
    body: ReviewRequest,
    principal: PrincipalDep,
    session: SessionDep,
    operation: Idempotency = idempotent("partnerships.review"),
) -> PartnershipResponse:
    """Contest the public claim.

    Args:
        partnership_id (UUID): The relationship.
        body (ReviewRequest): The request.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.
        operation (Idempotency): Replays a retried request.

    Returns:
        PartnershipResponse: The relationship as its parties see it.
    """
    done = await RelationshipService(session).request_review(principal, partnership_id, body, operation.operation_id)
    result = OperationResult(type="partnership", id=str(done.id))
    return await operation.respond(done, status_code=200, result=result)  # type: ignore[return-value]


@router.get("/partnerships/{partnership_id}", summary="Read a relationship")
async def read_partnership(partnership_id: UUID, principal: PrincipalDep, session: SessionDep) -> PartnershipResponse:
    """Read a relationship as one of its two parties.

    Args:
        partnership_id (UUID): The relationship.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.

    Returns:
        PartnershipResponse: Versions, confirmations, restrictions and what may be public.
    """
    return await RelationshipService(session).read(principal, partnership_id)


@router.get("/pitches/{pitch_id}/partnership", summary="Read a pitch's relationship")
async def read_pitch_partnership(
    pitch_id: UUID, principal: PrincipalDep, session: SessionDep
) -> PartnershipResponse | None:
    """Read the relationship that grew out of a pitch, or null before one is proposed.

    Args:
        pitch_id (UUID): The pitch.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.

    Returns:
        PartnershipResponse | None: The relationship.
    """
    return await RelationshipService(session).of_pitch(principal, pitch_id)


@router.get("/profiles/me", summary="Read my profile settings")
async def read_my_profile(principal: PrincipalDep, session: SessionDep) -> ProfileResponse:
    """Read the acting party's bio and whether it is published.

    Args:
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.

    Returns:
        ProfileResponse: The settings.
    """
    return await PublicProfileService(session).mine(principal)


@router.put("/profiles/me", summary="Publish my profile")
async def save_my_profile(body: SaveProfileRequest, principal: PrincipalDep, session: SessionDep) -> ProfileResponse:
    """Publish, change or withdraw the acting party's biography, against its version.

    Args:
        body (SaveProfileRequest): Bio, published flag and ``expected_version``.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.

    Returns:
        ProfileResponse: The settings.
    """
    return await PublicProfileService(session).save(principal, body)


@router.get("/profiles/{party_id}", summary="Read a public profile")
async def read_public_profile(party_id: UUID, session: SessionDep) -> PublicProfileResponse:
    """Read what anyone may see of a party, with no sign-in: published inventions and consented relationship fields.

    Args:
        party_id (UUID): The party.
        session (SessionDep): Database session.

    Returns:
        PublicProfileResponse: The public profile.
    """
    return await PublicProfileService(session).read(party_id)
