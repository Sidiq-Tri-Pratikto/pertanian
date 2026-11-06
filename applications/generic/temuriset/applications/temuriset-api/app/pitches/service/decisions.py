"""Recipient decisions and the status moves around them: begin review, approve, reject, withdraw, close (spec 025)."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.access.model.models import Capability
from app.access.service.policy import check_context
from app.core.errors.base import FieldsInvalidError, ForbiddenError, NotFoundError
from app.identity.model.models import Principal
from app.pitches.model.schema import CloseRequest, DecisionRequest, PitchActionRequest, PitchActionResponse
from app.pitches.repository.sqlalchemy.models import PitchDecisionRecord, PitchRecord
from app.pitches.repository.sqlalchemy.repository import SqlAlchemyPitchRepository
from app.pitches.service.transitions import TABLE, TERMINAL, Side, target
from app.platform.service.audit import record_audit
from app.platform.service.outbox import publish
from app.platform.service.versions import StaleVersionError, check_expected

CAPABILITY_OF: dict[Side, Capability] = {"requester": Capability.SUBMIT_PITCH, "recipient": Capability.DECIDE_PITCH}


def side_of(principal: Principal, record: PitchRecord) -> Side | None:
    """Return which side of the pitch the active party is on.

    Args:
        principal (Principal): Who is signed in.
        record (PitchRecord): The pitch.

    Returns:
        Side | None: The side, or None for anyone else.
    """
    if principal.active_party_id == record.requester_party_id:
        return "requester"
    if principal.active_party_id == record.recipient_party_id:
        return "recipient"
    return None


async def pitch_by_id(session: AsyncSession, pitch_id: UUID) -> PitchRecord | None:
    """Find a pitch with no access check, for worker consumers only (027).

    Args:
        session (AsyncSession): The worker's session.
        pitch_id (UUID): The pitch.

    Returns:
        PitchRecord | None: The pitch.
    """
    return await SqlAlchemyPitchRepository(session).find(pitch_id)


async def visible_pitch(
    session: AsyncSession, principal: Principal, pitch_id: UUID, *, lock: bool = False
) -> tuple[PitchRecord, Side]:
    """Find a pitch the active party is a side of, for other modules' rooms (027, 028).

    Args:
        session (AsyncSession): The request's session.
        principal (Principal): Who is signed in.
        pitch_id (UUID): The pitch.
        lock (bool): Serialize mutations against the pitch when requested.

    Returns:
        tuple[PitchRecord, Side]: The pitch and the reader's side.

    Raises:
        NotFoundError: For anyone but its two parties (AC48).
    """
    record = await SqlAlchemyPitchRepository(session).find(pitch_id, lock=lock)
    side = side_of(principal, record) if record else None
    if record is None or side is None:
        raise NotFoundError()
    return record, side


def require_side(principal: Principal, side: Side) -> None:
    """Refuse a member without its side's capability: ``submit_pitch`` or ``decide_pitch``.

    Args:
        principal (Principal): Who is signed in.
        side (Side): The reader's side.

    Raises:
        ForbiddenError: Without the capability.
    """
    if CAPABILITY_OF[side] not in principal.capabilities:
        raise ForbiddenError()


async def locked_pitch(
    repository: SqlAlchemyPitchRepository, principal: Principal, pitch_id: UUID, action: str, expected_version: int
) -> PitchRecord:
    """Lock a pitch for an action, after the checks every action shares.

    Args:
        repository (SqlAlchemyPitchRepository): Pitch storage.
        principal (Principal): Who is signed in.
        pitch_id (UUID): The pitch.
        action (str): A table action.
        expected_version (int): The version the client saw.

    Returns:
        PitchRecord: The locked pitch.

    Raises:
        NotFoundError: For anyone but its two parties.
        ForbiddenError: For the other side, or a member without the side's capability.
        StaleVersionError: When it changed since the client read it (AC41).
        InvalidTransitionError: When the table has no such move from its status (AC42).
    """
    record = await repository.find(pitch_id, lock=True)
    side = side_of(principal, record) if record else None
    if record is None or side is None:
        raise NotFoundError()
    if side not in TABLE[action][2] or CAPABILITY_OF[side] not in principal.capabilities:
        raise ForbiddenError()
    check_expected(record.version, expected_version)
    target(record.status, action)
    return record


async def move(
    session: AsyncSession, principal: Principal, record: PitchRecord, action: str, payload: dict | None = None
) -> None:
    """Apply a table action: new status, new version, the event and the audit, in the request's transaction.

    Args:
        session (AsyncSession): The request's session.
        principal (Principal): Who acts.
        record (PitchRecord): The locked pitch.
        action (str): A table action.
        payload (dict | None, optional): Extra event fields. Defaults to None.
    """
    record.status = target(record.status, action)
    record.active = record.status not in TERMINAL
    record.version += 1
    await session.flush()
    await publish(
        session,
        f"pitch.{action}",
        {
            "pitch_id": str(record.id),
            "requester_party_id": str(record.requester_party_id),
            "recipient_party_id": str(record.recipient_party_id),
            "status": record.status,
            "version": record.version,
            "actor_party_id": str(principal.active_party_id),
            **(payload or {}),
        },
    )
    await record_audit(
        session,
        action=f"pitch.{action}",
        subject_type="pitch",
        subject_id=str(record.id),
        actor_account_id=principal.account_id,
        actor_party_id=principal.active_party_id,
    )


def _response(record: PitchRecord, operation_id: UUID | None, **extra: int) -> PitchActionResponse:
    return PitchActionResponse(
        pitch_id=record.id, status=record.status, version=record.version, operation_id=operation_id, **extra
    )


class DecisionService:
    """Begins review, decides, withdraws and closes. Silence never decides anything."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind to the request.

        Args:
            session (AsyncSession): The request's session.
        """
        self.session = session
        self.repository = SqlAlchemyPitchRepository(session)

    async def _simple(
        self, principal: Principal, pitch_id: UUID, action: str, request: PitchActionRequest, operation_id: UUID | None
    ) -> PitchActionResponse:
        check_context(principal, request.acting_party_id)
        record = await locked_pitch(self.repository, principal, pitch_id, action, request.expected_version)
        await move(self.session, principal, record, action)
        return _response(record, operation_id)

    async def begin_review(
        self, principal: Principal, pitch_id: UUID, request: PitchActionRequest, operation_id: UUID | None = None
    ) -> PitchActionResponse:
        """Mark a submitted pitch as under review. This is not a decision.

        Args:
            principal (Principal): Who is signed in.
            pitch_id (UUID): The pitch.
            request (PitchActionRequest): Acting party and ``expected_version``.
            operation_id (UUID | None, optional): For the response. Defaults to None.

        Returns:
            PitchActionResponse: The pitch.
        """
        return await self._simple(principal, pitch_id, "begin_review", request, operation_id)

    async def withdraw(
        self, principal: Principal, pitch_id: UUID, request: PitchActionRequest, operation_id: UUID | None = None
    ) -> PitchActionResponse:
        """Withdraw before a final decision; later decisions on it are refused.

        Args:
            principal (Principal): Who is signed in.
            pitch_id (UUID): The pitch.
            request (PitchActionRequest): Acting party and ``expected_version``.
            operation_id (UUID | None, optional): For the response. Defaults to None.

        Returns:
            PitchActionResponse: The pitch.
        """
        return await self._simple(principal, pitch_id, "withdraw", request, operation_id)

    async def close(
        self, principal: Principal, pitch_id: UUID, request: CloseRequest, operation_id: UUID | None = None
    ) -> PitchActionResponse:
        """Close an approved discussion, with a reason.

        Args:
            principal (Principal): Who is signed in.
            pitch_id (UUID): The pitch.
            request (CloseRequest): Acting party, ``expected_version`` and reason.
            operation_id (UUID | None, optional): For the response. Defaults to None.

        Returns:
            PitchActionResponse: The pitch.
        """
        check_context(principal, request.acting_party_id)
        record = await locked_pitch(self.repository, principal, pitch_id, "close", request.expected_version)
        await move(self.session, principal, record, "close", {"reason": request.reason})
        return _response(record, operation_id)

    async def decide(
        self, principal: Principal, pitch_id: UUID, request: DecisionRequest, operation_id: UUID | None = None
    ) -> PitchActionResponse:
        """Approve for discussion or reject, on the exact submission and version (FR-001).

        Approval opens discussion only: no funding, partnership or commitment record is made (AC40).

        Args:
            principal (Principal): Who is signed in.
            pitch_id (UUID): The pitch.
            request (DecisionRequest): Submission, ``expected_version``, decision and reason.
            operation_id (UUID | None, optional): For the response. Defaults to None.

        Returns:
            PitchActionResponse: The pitch.

        Raises:
            StaleVersionError: When the submission is not the newest one.
            FieldsInvalidError: When a rejection has no reason.
        """
        check_context(principal, request.acting_party_id)
        action = "approve" if request.decision == "APPROVE" else "reject"
        record = await locked_pitch(self.repository, principal, pitch_id, action, request.expected_version)
        last = await self.repository.last_submission(record.id)
        if last is None or last.number != request.submission:
            raise StaleVersionError(record.version)
        if action == "reject" and not request.reason:
            raise FieldsInvalidError(
                [
                    {
                        "loc": ["body", "reason"],
                        "msg": "Tuliskan alasan singkat. Alasan hanya terlihat oleh pengirim pitching.",
                        "type": "required",
                    }
                ]
            )
        await self.repository.add(
            PitchDecisionRecord(
                pitch_id=record.id,
                submission_number=last.number,
                pitch_version=record.version,
                decision=request.decision,
                reason=request.reason or None,
                decided_by_party_id=principal.active_party_id,
                decided_by_account_id=principal.account_id,
            )
        )
        await move(self.session, principal, record, action, {"submission": last.number})
        return _response(record, operation_id)
