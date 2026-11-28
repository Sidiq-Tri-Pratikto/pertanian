"""Matching: run an owned source against active opportunities, and read a stored run."""

from uuid import UUID

from fastapi import APIRouter, Request, status

from app.core.database import SessionDep
from app.core.security import PrincipalDep
from app.matching.model.schema import MatchRequest, MatchResultResponse, MatchRunResponse
from app.matching.service.service import MatchingService
from app.platform.model.schema import OperationResult
from app.platform.service.idempotency import Idempotency, idempotent

router = APIRouter(tags=["matching"])


@router.post("/matches", status_code=status.HTTP_201_CREATED, summary="Match a need or raise")
async def run_match(
    body: MatchRequest,
    principal: PrincipalDep,
    session: SessionDep,
    request: Request,
    operation: Idempotency = idempotent("matches.run"),
) -> MatchRunResponse:
    """Evaluate an owned source against every other partner's active opportunity, with reasons and gaps.

    Args:
        body (MatchRequest): The source.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.
        request (Request): Carries the immutable startup retrieval snapshot.
        operation (Idempotency): Replays a retried request.

    Returns:
        MatchRunResponse: The stored run.
    """
    experiment = getattr(request.app.state, "match_retrieval", None)
    run = await MatchingService(session).run(principal, body, experiment)
    run.operation_id = operation.operation_id
    return await operation.respond(  # type: ignore[return-value]
        run, status_code=201, result=OperationResult(type="match_run", id=str(run.run_id))
    )


@router.get("/match-runs/{run_id}", summary="Read a match run")
async def read_match_run(run_id: UUID, principal: PrincipalDep, session: SessionDep) -> MatchRunResponse:
    """Read a stored run as it was computed.

    Args:
        run_id (UUID): The run.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.

    Returns:
        MatchRunResponse: The run.
    """
    return await MatchingService(session).read(principal, run_id)


@router.get("/inventions/{invention_id}/fit", summary="Preview how a published invention fits my active mandates")
async def preview_invention_fit(
    invention_id: UUID,
    principal: PrincipalDep,
    session: SessionDep,
    acting_party_id: UUID | None = None,
) -> list[MatchResultResponse]:
    """Evaluate a published invention's public projection against each of the acting party's own active mandates.

    Args:
        invention_id (UUID): The published invention.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.
        acting_party_id (UUID | None, optional): Optional acting party check. Defaults to None.

    Returns:
        list[MatchResultResponse]: One preview result per active mandate; nothing is stored.
    """
    return await MatchingService(session).invention_fit(principal, invention_id, acting_party_id)
