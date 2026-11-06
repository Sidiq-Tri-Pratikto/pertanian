"""Demo scenario and session endpoints."""

from typing import Annotated

from fastapi import APIRouter, Header, Response, status

from app.demo.dependencies import DemoServiceDep
from app.demo.model.schema import (
    CreateDemoSessionRequest,
    DemoSessionResponse,
    DemoWorkspaceResponse,
    ScenarioResponse,
)
from app.identity.dependencies import PrincipalDep

router = APIRouter(prefix="/demo", tags=["demo"])


@router.get("/scenarios", summary="List demo scenarios")
async def list_scenarios(service: DemoServiceDep) -> list[ScenarioResponse]:
    """Return every scenario a client can start. Public.

    Args:
        service (DemoService): Demo rules.

    Returns:
        list[ScenarioResponse]: The catalog.
    """
    return [ScenarioResponse(**scenario.__dict__) for scenario in service.scenarios()]


@router.post("/sessions", status_code=status.HTTP_201_CREATED, summary="Start a demo session")
async def create_session(
    request: CreateDemoSessionRequest,
    service: DemoServiceDep,
    response: Response,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", max_length=128)],
    replay_proof: Annotated[str, Header(alias="X-Demo-Replay-Proof", max_length=256)],
) -> DemoSessionResponse:
    """Seed an isolated demo workspace, or recover the same one after a lost response.

    The key needs at least 128 random bits and the proof a separate 256. Send the same pair to recover within
    the replay window; use a new pair for a new session.

    Args:
        request (CreateDemoSessionRequest): The scenario.
        service (DemoService): Demo rules.
        response (Response): Lets a replay answer 200.
        idempotency_key (str): Operation ID.
        replay_proof (str): Secret replay proof.

    Returns:
        DemoSessionResponse: Token and workspace.
    """
    result = await service.create(request.scenario_id, idempotency_key, replay_proof)
    if result.replayed:
        response.status_code = status.HTTP_200_OK
    return DemoSessionResponse(**result.response, token=result.token)


@router.post("/sessions/current/reset", summary="Reset the demo workspace")
async def reset_session(principal: PrincipalDep, service: DemoServiceDep) -> DemoWorkspaceResponse:
    """Return the caller's workspace to its scenario start; the token stays valid.

    Args:
        principal (PrincipalModel): The acting principal.
        service (DemoService): Demo rules.

    Returns:
        DemoWorkspaceResponse: The workspace.
    """
    return DemoWorkspaceResponse(**await service.reset(principal))


@router.delete("/sessions/current", status_code=status.HTTP_204_NO_CONTENT, summary="End the demo session")
async def end_session(principal: PrincipalDep, service: DemoServiceDep) -> None:
    """End the session and delete its workspace.

    Args:
        principal (PrincipalModel): The acting principal.
        service (DemoService): Demo rules.
    """
    await service.end(principal)
