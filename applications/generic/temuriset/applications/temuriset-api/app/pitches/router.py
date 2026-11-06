"""Pitches: submit on purpose, list, read, decide, revise and resubmit."""

from uuid import UUID

from fastapi import APIRouter, status

from app.core.database import SessionDep
from app.core.security import PrincipalDep
from app.core.types import Limit
from app.pitches.model.schema import (
    AnswerRequest,
    AnswerResponse,
    Box,
    CloseRequest,
    DecisionRequest,
    ItemReviewRequest,
    ItemReviewResponse,
    PitchActionRequest,
    PitchActionResponse,
    PitchResponse,
    PitchSummary,
    ResubmitRequest,
    RevisionRequest,
    SubmitPitchRequest,
    SubmitPitchResponse,
)
from app.pitches.service.decisions import DecisionService
from app.pitches.service.revisions import RevisionService
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


def _result(response: PitchActionResponse) -> OperationResult:
    return OperationResult(type="pitch", id=str(response.pitch_id))


@router.post("/{pitch_id}/begin-review", summary="Begin reviewing a pitch")
async def begin_review(
    pitch_id: UUID,
    body: PitchActionRequest,
    principal: PrincipalDep,
    session: SessionDep,
    operation: Idempotency = idempotent("pitches.begin_review"),
) -> PitchActionResponse:
    """Mark a submitted pitch as under review. This decides nothing.

    Args:
        pitch_id (UUID): The pitch.
        body (PitchActionRequest): Acting party and ``expected_version``.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.
        operation (Idempotency): Replays a retried request.

    Returns:
        PitchActionResponse: The pitch.
    """
    moved = await DecisionService(session).begin_review(principal, pitch_id, body, operation.operation_id)
    return await operation.respond(moved, result=_result(moved))  # type: ignore[return-value]


@router.post("/{pitch_id}/decisions", summary="Approve for discussion or reject")
async def decide(
    pitch_id: UUID,
    body: DecisionRequest,
    principal: PrincipalDep,
    session: SessionDep,
    operation: Idempotency = idempotent("pitches.decide"),
) -> PitchActionResponse:
    """Decide on the exact submission and version. Approval opens discussion only; rejection needs a reason.

    Args:
        pitch_id (UUID): The pitch.
        body (DecisionRequest): Submission, ``expected_version``, decision and reason.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.
        operation (Idempotency): Replays a retried request.

    Returns:
        PitchActionResponse: The pitch.
    """
    moved = await DecisionService(session).decide(principal, pitch_id, body, operation.operation_id)
    return await operation.respond(moved, result=_result(moved))  # type: ignore[return-value]


@router.post("/{pitch_id}/revision-rounds", status_code=status.HTTP_201_CREATED, summary="Request a revision")
async def request_revision(
    pitch_id: UUID,
    body: RevisionRequest,
    principal: PrincipalDep,
    session: SessionDep,
    operation: Idempotency = idempotent("pitches.request_revision"),
) -> PitchActionResponse:
    """Open the next numbered round of itemized questions.

    Args:
        pitch_id (UUID): The pitch.
        body (RevisionRequest): Submission, ``expected_version`` and items.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.
        operation (Idempotency): Replays a retried request.

    Returns:
        PitchActionResponse: The pitch and round number.
    """
    moved = await RevisionService(session).request_revision(principal, pitch_id, body, operation.operation_id)
    return await operation.respond(moved, status_code=201, result=_result(moved))  # type: ignore[return-value]


@router.put("/{pitch_id}/revision-items/{item_id}/answer", summary="Save a draft answer")
async def save_answer(
    pitch_id: UUID, item_id: UUID, body: AnswerRequest, principal: PrincipalDep, session: SessionDep
) -> AnswerResponse:
    """Save the requester's draft answer to one item of the open round, against its version.

    Args:
        pitch_id (UUID): The pitch.
        item_id (UUID): The item.
        body (AnswerRequest): Response, text, files and ``expected_version``.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.

    Returns:
        AnswerResponse: The saved answer.
    """
    return AnswerResponse(**await RevisionService(session).save_answer(principal, pitch_id, item_id, body))


@router.put("/{pitch_id}/revision-items/{item_id}/review", summary="Review an answer")
async def review_item(
    pitch_id: UUID, item_id: UUID, body: ItemReviewRequest, principal: PrincipalDep, session: SessionDep
) -> ItemReviewResponse:
    """Accept an answer or ask for more detail, against the item's version.

    Args:
        pitch_id (UUID): The pitch.
        item_id (UUID): The item.
        body (ItemReviewRequest): Result, note and ``expected_version``.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.

    Returns:
        ItemReviewResponse: The item's review.
    """
    return ItemReviewResponse(**await RevisionService(session).review_item(principal, pitch_id, item_id, body))


@router.post("/{pitch_id}/resubmit", summary="Resubmit after answering")
async def resubmit(
    pitch_id: UUID,
    body: ResubmitRequest,
    principal: PrincipalDep,
    session: SessionDep,
    operation: Idempotency = idempotent("pitches.resubmit"),
) -> PitchActionResponse:
    """Send the next submission once every required item has an answer.

    Args:
        pitch_id (UUID): The pitch.
        body (ResubmitRequest): ``expected_version``, brief and files.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.
        operation (Idempotency): Replays a retried request.

    Returns:
        PitchActionResponse: The pitch and submission number.
    """
    moved = await RevisionService(session).resubmit(principal, pitch_id, body, operation.operation_id)
    return await operation.respond(moved, result=_result(moved))  # type: ignore[return-value]


@router.post("/{pitch_id}/withdraw", summary="Withdraw a pitch")
async def withdraw(
    pitch_id: UUID,
    body: PitchActionRequest,
    principal: PrincipalDep,
    session: SessionDep,
    operation: Idempotency = idempotent("pitches.withdraw"),
) -> PitchActionResponse:
    """Withdraw before a final decision; later decisions are refused.

    Args:
        pitch_id (UUID): The pitch.
        body (PitchActionRequest): Acting party and ``expected_version``.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.
        operation (Idempotency): Replays a retried request.

    Returns:
        PitchActionResponse: The pitch.
    """
    moved = await DecisionService(session).withdraw(principal, pitch_id, body, operation.operation_id)
    return await operation.respond(moved, result=_result(moved))  # type: ignore[return-value]


@router.post("/{pitch_id}/close", summary="Close a discussion")
async def close(
    pitch_id: UUID,
    body: CloseRequest,
    principal: PrincipalDep,
    session: SessionDep,
    operation: Idempotency = idempotent("pitches.close"),
) -> PitchActionResponse:
    """Close an approved discussion with a reason.

    Args:
        pitch_id (UUID): The pitch.
        body (CloseRequest): Acting party, ``expected_version`` and reason.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.
        operation (Idempotency): Replays a retried request.

    Returns:
        PitchActionResponse: The pitch.
    """
    moved = await DecisionService(session).close(principal, pitch_id, body, operation.operation_id)
    return await operation.respond(moved, result=_result(moved))  # type: ignore[return-value]
