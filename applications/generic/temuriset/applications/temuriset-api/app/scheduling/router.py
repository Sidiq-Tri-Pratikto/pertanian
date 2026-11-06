"""Scheduling: propose, accept, replace, cancel, record outcomes, download a calendar file."""

import re
from json import dumps
from typing import Annotated, Literal
from urllib.parse import urlencode
from uuid import UUID

from fastapi import APIRouter, Query, Request, status
from fastapi.responses import RedirectResponse, Response
from starlette.datastructures import MutableHeaders, QueryParams
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.database import SessionDep
from app.core.errors.base import AppError
from app.core.logging import CALENDAR_CALLBACK_PATH
from app.core.security import PrincipalDep, current_principal
from app.core.settings import get_settings
from app.platform.model.schema import OperationResult
from app.platform.service.idempotency import Idempotency, claim_operation, idempotent
from app.scheduling.model.schema import (
    AcceptRequest,
    CalendarConnectRequest,
    CalendarConnectResponse,
    CalendarDisconnectResponse,
    CalendarStatusResponse,
    CalendarVersionRequest,
    MeetingResponse,
    OutcomeRequest,
    ProposalResponse,
    ProposeRequest,
    ScheduleResponse,
    VersionedRequest,
)
from app.scheduling.service.calendar_adapter import CalendarUnavailableError
from app.scheduling.service.calendar_connection import (
    CalendarCallbackInvalidError,
    CalendarConnectionService,
    record_calendar_failure,
)
from app.scheduling.service.service import SchedulingService

router = APIRouter(tags=["scheduling"])


_CALENDAR_RESPONSE_HEADERS = {"Cache-Control": "private, no-store", "Referrer-Policy": "no-referrer"}
_STATE = re.compile(r"[a-f0-9]{64}")
_CODE = re.compile(r"[A-Za-z0-9._~-]{1,256}")


class CalendarPrivacyMiddleware:
    """Keep callback queries out of routing metadata and calendar responses out of caches."""

    def __init__(self, app: ASGIApp) -> None:
        """Wrap the API's calendar HTTP entry points."""
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Keep credentials private on both successful and rejected requests."""
        if scope["type"] != "http" or not (
            scope["path"] == "/api/v1/me/calendar" or scope["path"].startswith("/api/v1/me/calendar/")
        ):
            await self.app(scope, receive, send)
            return
        if scope["path"].rstrip("/") == CALENDAR_CALLBACK_PATH:
            private_state = dict(scope.get("state", {}), calendar_callback_query=scope["query_string"])
            scope = dict(scope, state=private_state, query_string=b"", path=CALENDAR_CALLBACK_PATH)

        async def private_response(message: Message) -> None:
            if message["type"] == "http.response.start":
                MutableHeaders(scope=message).update(_CALENDAR_RESPONSE_HEADERS)
            await send(message)

        await self.app(scope, receive, private_response)


@router.get("/pitches/{pitch_id}/schedule", summary="Read a pitch's schedule")
async def read_schedule(
    pitch_id: UUID,
    request: Request,
    response: Response,
    principal: PrincipalDep,
    session: SessionDep,
) -> ScheduleResponse:
    """Read authorized scheduling data and optionally annotate the viewer's own calendar."""
    response.headers["Cache-Control"] = "private, no-store"
    scheduling = SchedulingService(session)
    schedule = await scheduling.read(principal, pitch_id)
    calendar = CalendarConnectionService(session, get_settings())
    query = scheduling.calendar_windows(schedule) if calendar.enabled else None
    if query is None:
        return schedule
    try:
        credential = await calendar.credential(principal)
    except CalendarUnavailableError as error:
        record_calendar_failure(error, "calendar.freebusy")
        return schedule
    if credential is None:
        return schedule

    # Reads may expire proposals and refresh sessions. End that transaction before waiting on the provider.
    await session.commit()
    try:
        busy = await calendar.adapter.freebusy(credential.token, list(query[1].values()))
    except CalendarUnavailableError as error:
        record_calendar_failure(error, "calendar.freebusy")
        busy = None
    session.expire_all()
    current = await current_principal(request, session)
    schedule = await scheduling.read(current, pitch_id)
    if busy is not None and current == principal and await calendar.current(current, credential.version):
        scheduling.annotate_calendar(schedule, query, busy)
    return schedule


@router.get("/me/calendar", summary="Read my calendar connection")
async def calendar_status(principal: PrincipalDep, session: SessionDep) -> CalendarStatusResponse:
    """Report only the signed-in account's connection state."""
    return await CalendarConnectionService(session, get_settings()).status(principal)


@router.post("/me/calendar/connect", summary="Consent to the local free/busy calendar")
async def connect_calendar(
    request: Request,
    body: CalendarConnectRequest,
    principal: PrincipalDep,
    session: SessionDep,
) -> CalendarConnectResponse:
    """Commit explicit consent and return a same-origin navigation path without credentials."""
    calendar = CalendarConnectionService(session, get_settings())
    calendar.require_enabled()
    operation = await claim_operation(
        request,
        session,
        principal.personal_party_id,
        "calendar.connect",
        dumps({"request": body.model_dump(), "session": str(principal.session_id)}).encode(),
        owner_account_id=principal.account_id,
    )
    state = await calendar.begin(principal, body.expected_version)
    result = CalendarConnectResponse(**state.model_dump(), operation_id=operation.operation_id)
    return await operation.respond(result)  # type: ignore[return-value]


@router.get("/me/calendar/connect", summary="Open the local calendar consent screen", response_class=RedirectResponse)
async def authorize_calendar(
    version: Annotated[int, Query(ge=1)],
    principal: PrincipalDep,
    session: SessionDep,
) -> RedirectResponse:
    """Redirect the initiating browser session to the fixed loopback provider."""
    url = await CalendarConnectionService(session, get_settings()).authorization(principal, version)
    return RedirectResponse(url, status_code=303, headers=_CALENDAR_RESPONSE_HEADERS)


@router.get("/me/calendar/callback", summary="Finish local calendar consent", response_class=RedirectResponse)
async def calendar_callback(request: Request, session: SessionDep) -> RedirectResponse:
    """Consume state before the exchange and always redirect without reflecting callback parameters."""
    settings = get_settings()
    calendar = CalendarConnectionService(session, settings)
    calendar.require_enabled()
    result = {"kalender": "terhubung"}
    try:
        await _finish_calendar_callback(request, session, calendar)
    except AppError as error:
        record_calendar_failure(error, CALENDAR_CALLBACK_PATH)
        result = {"kalender": "gagal", "ref": error.reference_id}
    return RedirectResponse(
        settings.web_origin + "/settings?" + urlencode(result) + "#kalender",
        status_code=303,
        headers=_CALENDAR_RESPONSE_HEADERS,
    )


async def _finish_calendar_callback(
    request: Request,
    session: SessionDep,
    calendar: CalendarConnectionService,
) -> None:
    calendar.require_enabled()
    principal = await current_principal(request, session)
    callback_query = request.state.calendar_callback_query
    if len(callback_query) > 4096:
        raise CalendarCallbackInvalidError()
    params = QueryParams(callback_query)
    states = params.getlist("state")
    if len(states) != 1 or _STATE.fullmatch(states[0]) is None:
        raise CalendarCallbackInvalidError()
    pending = await calendar.consume(principal, states[0])
    await session.commit()

    token = None
    try:
        codes = params.getlist("code")
        if "error" in params or len(codes) != 1 or _CODE.fullmatch(codes[0]) is None:
            raise CalendarCallbackInvalidError()
        token = await calendar.adapter.exchange(codes[0], pending.verifier)
        session.expire_all()
        current = await current_principal(request, session)
        if not await calendar.complete(current, pending.version, token):
            raise CalendarCallbackInvalidError()
    except AppError:
        await calendar.abandon(principal, pending.version)
        await session.commit()
        if token is not None:
            await _revoke_calendar_token(calendar, token.access_token)
        raise


async def _revoke_calendar_token(
    calendar: CalendarConnectionService,
    token: str,
) -> Literal["confirmed", "unconfirmed"]:
    try:
        await calendar.adapter.revoke(token)
    except CalendarUnavailableError as error:
        record_calendar_failure(error, "calendar.revoke")
        return "unconfirmed"
    return "confirmed"


@router.post("/me/calendar/disconnect", summary="Disconnect my external calendar")
async def disconnect_calendar(
    request: Request,
    body: CalendarVersionRequest,
    principal: PrincipalDep,
    session: SessionDep,
) -> CalendarDisconnectResponse:
    """Commit local invalidation before attempting bounded provider revocation."""
    calendar = CalendarConnectionService(session, get_settings())
    operation = await claim_operation(
        request,
        session,
        principal.personal_party_id,
        "calendar.disconnect",
        await request.body(),
        owner_account_id=principal.account_id,
    )
    state, token, had_token = await calendar.invalidate(principal, body.expected_version)
    result = CalendarDisconnectResponse(
        state=state.state,
        version=state.version,
        revocation="unconfirmed" if had_token else "not_required",
        operation_id=operation.operation_id,
    )
    response = await operation.respond(result)
    await session.commit()
    if token is not None and await _revoke_calendar_token(calendar, token) == "confirmed":
        await calendar.confirm_revocation(principal, state.version)
    return response  # type: ignore[return-value]


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
