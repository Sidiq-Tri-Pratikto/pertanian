"""Pitches: submit on purpose, list, read."""

from uuid import UUID

from fastapi import APIRouter, status

from app.core.database import SessionDep
from app.core.security import PrincipalDep
from app.core.types import Limit
from app.pitches.model.schema import Box, PitchResponse, PitchSummary, SubmitPitchRequest, SubmitPitchResponse
from app.pitches.service.submission import PitchService
from app.platform.model.schema import OperationResult
from app.platform.service.idempotency import Idempotency, idempotent

router = APIRouter(prefix="/pitches", tags=["pitches"])


@router.post("", status_code=status.HTTP_201_CREATED, summary="Send a pitch")
async def submit_pitch(
    body: SubmitPitchRequest,
    principal: PrincipalDep,
    session: SessionDep,
    operation: Idempotency = idempotent("pitches.submit"),
) -> SubmitPitchResponse:
    """Recheck a fresh preflight, freeze what is sent, share the chosen file versions and notify the recipient.

    Args:
        body (SubmitPitchRequest): Token, brief and files.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.
        operation (Idempotency): Replays a retried request; the same key with another body is a conflict.

    Returns:
        SubmitPitchResponse: The pitch.
    """
    submitted = await PitchService(session).submit(principal, body, operation.operation_id)
    return await operation.respond(  # type: ignore[return-value]
        submitted, status_code=201, result=OperationResult(type="pitch", id=str(submitted.pitch_id))
    )


@router.get("", summary="List my pitches")
async def list_pitches(
    principal: PrincipalDep, session: SessionDep, box: Box = "outgoing", limit: Limit = 50
) -> list[PitchSummary]:
    """List the acting party's sent or received pitches.

    Args:
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.
        box (Box, optional): ``outgoing`` or ``incoming``. Defaults to "outgoing".
        limit (int, optional): The most to return. Defaults to 50.

    Returns:
        list[PitchSummary]: Newest first.
    """
    return await PitchService(session).list_box(principal, box, limit)


@router.get("/{pitch_id}", summary="Read a pitch")
async def read_pitch(pitch_id: UUID, principal: PrincipalDep, session: SessionDep) -> PitchResponse:
    """Read a pitch as its requester or recipient.

    Args:
        pitch_id (UUID): The pitch.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.

    Returns:
        PitchResponse: The pitch and its frozen submissions.
    """
    return await PitchService(session).read(principal, pitch_id)
