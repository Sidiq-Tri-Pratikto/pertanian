"""Scheduling: propose, accept, replace, cancel, record outcomes, download a calendar file."""

from uuid import UUID

from fastapi import APIRouter, status
from fastapi.responses import Response

from app.core.database import SessionDep
from app.core.security import PrincipalDep
from app.platform.model.schema import OperationResult
from app.platform.service.idempotency import Idempotency, idempotent
from app.scheduling.model.schema import (
    AcceptRequest,
    MeetingResponse,
    OutcomeRequest,
    ProposalResponse,
    ProposeRequest,
    ScheduleResponse,
    VersionedRequest,
)
from app.scheduling.service.service import SchedulingService

router = APIRouter(tags=["scheduling"])


@router.get("/pitches/{pitch_id}/schedule", summary="Read a pitch's schedule")
async def read_schedule(pitch_id: UUID, principal: PrincipalDep, session: SessionDep) -> ScheduleResponse:
    """Read proposals and meetings, with expiry evaluated now.

    Args:
        pitch_id (UUID): The pitch.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.

    Returns:
        ScheduleResponse: Proposals and meetings.
    """
    return await SchedulingService(session).read(principal, pitch_id)


@router.post(
    "/pitches/{pitch_id}/schedule-proposals", status_code=status.HTTP_201_CREATED, summary="Propose meeting times"
)
async def propose(
    pitch_id: UUID,
    body: ProposeRequest,
    principal: PrincipalDep,
    session: SessionDep,
    operation: Idempotency = idempotent("schedule.propose"),
) -> ProposalResponse:
    """Offer 2–5 times; an open proposal is superseded. With ``replaces_meeting_id`` it proposes a replacement.

    Args:
        pitch_id (UUID): The pitch.
        body (ProposeRequest): Slots, length, zone, agenda, link and replaced meeting.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.
        operation (Idempotency): Replays a retried request.

    Returns:
        ProposalResponse: The proposal.
    """
    made = await SchedulingService(session).propose(principal, pitch_id, body, operation.operation_id)
    result = OperationResult(type="schedule_proposal", id=str(made.id))
    return await operation.respond(made, status_code=201, result=result)  # type: ignore[return-value]


@router.post("/schedule-proposals/{proposal_id}/accept", summary="Confirm a slot")
async def accept(
    proposal_id: UUID,
    body: AcceptRequest,
    principal: PrincipalDep,
    session: SessionDep,
    operation: Idempotency = idempotent("schedule.accept"),
) -> MeetingResponse:
    """Confirm one slot; a conflict changes nothing and is ``BOOKING_CONFLICT``.

    Args:
        proposal_id (UUID): The proposal.
        body (AcceptRequest): The slot and ``expected_version``.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.
        operation (Idempotency): Replays a retried request.

    Returns:
        MeetingResponse: The confirmed meeting.
    """
    meeting = await SchedulingService(session).accept(principal, proposal_id, body, operation.operation_id)
    result = OperationResult(type="meeting", id=str(meeting.id))
    return await operation.respond(meeting, result=result)  # type: ignore[return-value]


@router.post("/schedule-proposals/{proposal_id}/cancel", summary="Cancel a proposal")
async def cancel_proposal(
    proposal_id: UUID,
    body: VersionedRequest,
    principal: PrincipalDep,
    session: SessionDep,
    operation: Idempotency = idempotent("schedule.cancel"),
) -> ProposalResponse:
    """Cancel an open proposal; any meeting stays.

    Args:
        proposal_id (UUID): The proposal.
        body (VersionedRequest): ``expected_version``.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.
        operation (Idempotency): Replays a retried request.

    Returns:
        ProposalResponse: The proposal.
    """
    cancelled = await SchedulingService(session).cancel_proposal(principal, proposal_id, body, operation.operation_id)
    result = OperationResult(type="schedule_proposal", id=str(cancelled.id))
    return await operation.respond(cancelled, result=result)  # type: ignore[return-value]


@router.post("/meetings/{meeting_id}/cancel", summary="Cancel a meeting")
async def cancel_meeting(
    meeting_id: UUID,
    body: VersionedRequest,
    principal: PrincipalDep,
    session: SessionDep,
    operation: Idempotency = idempotent("meetings.cancel"),
) -> MeetingResponse:
    """Cancel a confirmed meeting and free both bookings.

    Args:
        meeting_id (UUID): The meeting.
        body (VersionedRequest): ``expected_version``.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.
        operation (Idempotency): Replays a retried request.

    Returns:
        MeetingResponse: The meeting.
    """
    meeting = await SchedulingService(session).cancel_meeting(principal, meeting_id, body, operation.operation_id)
    return await operation.respond(meeting, result=OperationResult(type="meeting", id=str(meeting.id)))  # type: ignore[return-value]


@router.post("/meetings/{meeting_id}/outcome", summary="Record a meeting outcome")
async def record_outcome(
    meeting_id: UUID,
    body: OutcomeRequest,
    principal: PrincipalDep,
    session: SessionDep,
    operation: Idempotency = idempotent("meetings.outcome"),
) -> MeetingResponse:
    """Record what the acting party says happened; only both agreeing settles it.

    Args:
        meeting_id (UUID): The meeting.
        body (OutcomeRequest): Result and note.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.
        operation (Idempotency): Replays a retried request.

    Returns:
        MeetingResponse: The meeting.
    """
    meeting = await SchedulingService(session).record_outcome(principal, meeting_id, body, operation.operation_id)
    return await operation.respond(meeting, result=OperationResult(type="meeting", id=str(meeting.id)))  # type: ignore[return-value]


@router.get(
    "/meetings/{meeting_id}/calendar.ics",
    summary="Download a calendar file",
    response_class=Response,
    responses={200: {"content": {"text/calendar": {}}}},
)
async def calendar_file(meeting_id: UUID, principal: PrincipalDep, session: SessionDep) -> Response:
    """Return the meeting as an iCalendar file built from its UTC instants.

    Args:
        meeting_id (UUID): The meeting.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.

    Returns:
        Response: ``text/calendar`` with an attachment name.
    """
    text = await SchedulingService(session).ics(principal, meeting_id)
    return Response(
        text,
        media_type="text/calendar; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="pertemuan-temuriset.ics"'},
    )
