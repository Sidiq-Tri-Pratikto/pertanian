"""Itemized revision rounds: request, draft answers, resubmit, review each answer (spec 025)."""

from typing import Any
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.access.model.models import Capability
from app.access.service.policy import check_context
from app.briefs.service.service import BriefService
from app.core.errors import codes
from app.core.errors.base import (
    AppError,
    FieldsInvalidError,
    ForbiddenError,
    InvalidTransitionError,
    NotFoundError,
)
from app.core.settings import get_settings
from app.documents.model.schema import GrantRequest
from app.documents.service.service import DocumentService, owned_file
from app.identity.model.models import Principal
from app.intake.model.models import AvailabilityReason
from app.pitches.model.schema import (
    AnswerRequest,
    ChosenFile,
    ItemReviewRequest,
    PitchActionResponse,
    ResubmitRequest,
    RevisionRequest,
)
from app.pitches.repository.sqlalchemy.models import (
    PitchRecord,
    PitchSubmissionFileRecord,
    PitchSubmissionRecord,
    RevisionAnswerRecord,
    RevisionItemRecord,
    RevisionRoundRecord,
)
from app.pitches.repository.sqlalchemy.repository import SqlAlchemyPitchRepository
from app.pitches.service.decisions import locked_pitch, move, side_of
from app.pitches.service.submission import CLOSED_REASON, PitchService, TargetClosedError
from app.platform.service.versions import StaleVersionError, check_expected


class RequiredAnswersMissingError(AppError):
    """A required item of the open round has no answer."""

    code = codes.APP_REQUIRED_ANSWERS_MISSING


class RevisionService:
    """Rounds, answers, resubmission and item review. An answer, even “Belum dapat dipenuhi”, never approves."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind to the request.

        Args:
            session (AsyncSession): The request's session.
        """
        self.session = session
        self.repository = SqlAlchemyPitchRepository(session)

    async def request_revision(
        self, principal: Principal, pitch_id: UUID, request: RevisionRequest, operation_id: UUID | None = None
    ) -> PitchActionResponse:
        """Open the next numbered round on the newest submission.

        Args:
            principal (Principal): Who is signed in.
            pitch_id (UUID): The pitch.
            request (RevisionRequest): Submission, ``expected_version`` and items.
            operation_id (UUID | None, optional): For the response. Defaults to None.

        Returns:
            PitchActionResponse: The pitch and the round number.

        Raises:
            StaleVersionError: When the submission is not the newest one.
            InvalidTransitionError: After a decision; clarification then uses discussion tasks.
        """
        check_context(principal, request.acting_party_id)
        record = await locked_pitch(self.repository, principal, pitch_id, "request_revision", request.expected_version)
        last = await self.repository.last_submission(record.id)
        if last is None or last.number != request.submission:
            raise StaleVersionError(record.version)
        number = len(await self.repository.rounds(record.id)) + 1
        round_ = await self.repository.add(
            RevisionRoundRecord(
                pitch_id=record.id,
                number=number,
                submission_number=last.number,
                requested_by_party_id=principal.active_party_id,
                requested_by_account_id=principal.account_id,
            )
        )
        for position, item in enumerate(request.items, start=1):
            await self.repository.add(RevisionItemRecord(round_id=round_.id, position=position, **item.model_dump()))
        await move(self.session, principal, record, "request_revision", {"round": number})
        return PitchActionResponse(
            pitch_id=record.id, status=record.status, version=record.version, round=number, operation_id=operation_id
        )

    async def _files(self, owner: UUID, files: list[ChosenFile], field: str) -> list[dict[str, Any]]:
        """Check each chosen file is an available version of the owner's own document."""
        found, errors = [], []
        for index, file in enumerate(files):
            detail = await owned_file(self.session, owner, file.document_id, file.version)
            if detail is None:
                errors.append(
                    {"loc": ["body", field, index], "msg": "Pilih versi berkas Anda yang tersedia.", "type": "file"}
                )
            else:
                found.append(detail)
        if errors:
            raise FieldsInvalidError(errors)
        return found

    async def _open_item(
        self, principal: Principal, pitch_id: UUID, item_id: UUID
    ) -> tuple[PitchRecord, RevisionItemRecord]:
        """Find an item of the pitch's open round, for its requester, holding the pitch against resubmission."""
        record = await self.repository.find(pitch_id, share=True)
        side = side_of(principal, record) if record else None
        found = await self.repository.item(item_id, lock=True)
        if record is None or side is None or found is None or found[1].pitch_id != record.id:
            raise NotFoundError()
        if side != "requester" or Capability.SUBMIT_PITCH not in principal.capabilities:
            raise ForbiddenError()
        rounds = await self.repository.rounds(record.id)
        if record.status != "REVISION_REQUESTED" or rounds[-1][0].id != found[1].id:
            raise InvalidTransitionError()
        return record, found[0]

    async def save_answer(
        self, principal: Principal, pitch_id: UUID, item_id: UUID, request: AnswerRequest
    ) -> dict[str, Any]:
        """Save a draft answer with its own version; it is shared only when the round is resubmitted.

        Args:
            principal (Principal): Who is signed in.
            pitch_id (UUID): The pitch.
            item_id (UUID): The item.
            request (AnswerRequest): Response, text, files and ``expected_version``.

        Returns:
            dict[str, Any]: The saved answer.

        Raises:
            InvalidTransitionError: When the item's round is no longer open.
            StaleVersionError: When the answer changed since the client read it, or a first save lost a race.
            FieldsInvalidError: When a file is not an available version of the requester's own document.
        """
        check_context(principal, request.acting_party_id)
        record, item = await self._open_item(principal, pitch_id, item_id)
        files = await self._files(record.requester_party_id, request.files, "files")
        answer = await self.repository.answer(item.id)
        if answer is None:
            if request.expected_version is not None:
                raise StaleVersionError(0)
            try:
                async with self.session.begin_nested():
                    answer = await self.repository.add(
                        RevisionAnswerRecord(
                            item_id=item.id,
                            response=request.response,
                            text=request.text,
                            files=files,
                            saved_by_account_id=principal.account_id,
                        )
                    )
            except IntegrityError as error:
                raise StaleVersionError(1) from error
        else:
            if request.expected_version is None:
                raise StaleVersionError(answer.version)
            check_expected(answer.version, request.expected_version)
            answer.response, answer.text, answer.files = request.response, request.text, files
            answer.saved_by_account_id = principal.account_id
            answer.version += 1
            await self.session.flush()
        return {
            "response": answer.response,
            "text": answer.text,
            "files": [{key: file[key] for key in ("document_id", "version", "title")} for file in answer.files],
            "version": answer.version,
            "saved_at": answer.updated_at,
        }

    async def resubmit(
        self, principal: Principal, pitch_id: UUID, request: ResubmitRequest, operation_id: UUID | None = None
    ) -> PitchActionResponse:
        """Send the next submission once every required item has an answer (AC43, AC45).

        The new submission freezes the source as it is now and the file versions chosen; earlier submissions and
        answers stay as they were.

        Args:
            principal (Principal): Who is signed in.
            pitch_id (UUID): The pitch.
            request (ResubmitRequest): ``expected_version``, brief and files.
            operation_id (UUID | None, optional): For the response. Defaults to None.

        Returns:
            PitchActionResponse: The pitch and the new submission number.

        Raises:
            RequiredAnswersMissingError: Listing the unanswered required items.
            TargetClosedError: When the target stopped accepting new submissions.
            FieldsInvalidError: When a file is not an available version of the requester's own document.
        """
        check_context(principal, request.acting_party_id)
        record = await locked_pitch(self.repository, principal, pitch_id, "resubmit", request.expected_version)
        _, items = (await self.repository.rounds(record.id))[-1]
        missing = [str(item.id) for item, answer in items if item.required and answer is None]
        if missing:
            raise RequiredAnswersMissingError(public_fields={"items": missing})
        checked = await BriefService(self.session).evaluate(
            principal, record.subject_type, record.subject_id, record.opportunity_id
        )
        availability = checked["opportunity"].target_availability
        if not availability.available:
            reason: AvailabilityReason = availability.reason  # type: ignore[assignment]
            raise TargetClosedError(public_fields={"reason": CLOSED_REASON[reason]})
        chosen = await self._files(record.requester_party_id, request.files, "files")
        answered = [file for _, answer in items if answer for file in answer.files]
        shared = list({(file["document_id"], file["version"]): file for file in chosen + answered}.values())
        last = await self.repository.last_submission(record.id)
        assert last is not None  # noqa: S101 - a pitch is created with its first submission
        submission = await self.repository.add(
            PitchSubmissionRecord(
                pitch_id=record.id,
                number=last.number + 1,
                preflight_id=None,
                brief=request.brief or last.brief,
                snapshot=await PitchService(self.session).snapshot(
                    principal, checked, record.subject_type, record.subject_id
                ),
                submitted_by_account_id=principal.account_id,
            )
        )
        documents = DocumentService(self.session, get_settings())
        for file in shared:
            grant = await documents.grant(
                principal,
                UUID(file["document_id"]),
                GrantRequest(
                    acting_party_id=principal.active_party_id,
                    version=file["version"],
                    grantee_party_id=record.recipient_party_id,
                    purpose="pitch",
                    pitch_id=record.id,
                ),
                capability=Capability.SUBMIT_PITCH,
            )
            await self.repository.add(
                PitchSubmissionFileRecord(
                    submission_id=submission.id,
                    document_id=UUID(file["document_id"]),
                    document_version_id=UUID(file["version_id"]),
                    version=file["version"],
                    title=file["title"],
                    grant_id=grant.id,
                )
            )
        # ponytail: the organization review gate (033) is not built, so a resubmission always goes straight back.
        await move(self.session, principal, record, "resubmit", {"submission": submission.number})
        return PitchActionResponse(
            pitch_id=record.id,
            status=record.status,
            version=record.version,
            submission=submission.number,
            operation_id=operation_id,
        )

    async def review_item(
        self, principal: Principal, pitch_id: UUID, item_id: UUID, request: ItemReviewRequest
    ) -> dict[str, Any]:
        """Accept an answered item or ask for more detail; the mark is stored per item and approves nothing.

        Args:
            principal (Principal): Who is signed in.
            pitch_id (UUID): The pitch.
            item_id (UUID): The item.
            request (ItemReviewRequest): Result, note and the item's ``expected_version``.

        Returns:
            dict[str, Any]: The item's review and version.

        Raises:
            InvalidTransitionError: While the round is open, for an unanswered item, or after the pitch ended.
            StaleVersionError: When the item changed since the client read it.
        """
        check_context(principal, request.acting_party_id)
        record = await self.repository.find(pitch_id)
        side = side_of(principal, record) if record else None
        found = await self.repository.item(item_id, lock=True)
        if record is None or side is None or found is None or found[1].pitch_id != record.id:
            raise NotFoundError()
        if side != "recipient" or Capability.DECIDE_PITCH not in principal.capabilities:
            raise ForbiddenError()
        item, round_ = found
        rounds = await self.repository.rounds(record.id)
        answered = any(row.id == item.id and answer for row, answer in rounds[round_.number - 1][1])
        # Answers become visible on resubmission, so only a resubmitted pitch still in review has items to mark.
        if record.status not in ("SUBMITTED", "UNDER_REVIEW") or not answered:
            raise InvalidTransitionError()
        check_expected(item.version, request.expected_version)
        item.review, item.review_note = request.result, request.note or None
        item.version += 1
        await self.session.flush()
        return {"id": item.id, "review": item.review, "review_note": item.review_note, "version": item.version}
