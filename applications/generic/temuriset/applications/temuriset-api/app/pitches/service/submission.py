"""Deliberate submission: recheck the preflight, freeze what is sent, share chosen files, notify (spec 023)."""

from datetime import timedelta
from typing import Any
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.access.model.models import Capability
from app.access.service.policy import check_context, require
from app.access.service.service import party_names
from app.briefs.repository.sqlalchemy.repository import SqlAlchemyBriefRepository
from app.briefs.service.service import BriefService, hash_token, stale_preflight_reason
from app.core import clock
from app.core.errors import codes
from app.core.errors.base import AppError, FieldsInvalidError, NotFoundError
from app.core.settings import get_settings
from app.discussion.service.next_action import waiting_parties
from app.documents.model.schema import GrantRequest
from app.documents.service.service import DocumentService
from app.funding.service.service import FundingService
from app.identity.model.models import Principal
from app.intake.model.models import AvailabilityReason
from app.needs.service.service import NeedsService
from app.pitches.model.schema import (
    AnswerResponse,
    DecisionResponse,
    PitchResponse,
    PitchSummary,
    RevisionItemResponse,
    RevisionRoundResponse,
    SubmissionResponse,
    SubmitPitchRequest,
    SubmitPitchResponse,
    SubmittedFile,
)
from app.pitches.repository.sqlalchemy.models import PitchRecord, PitchSubmissionFileRecord, PitchSubmissionRecord
from app.pitches.repository.sqlalchemy.repository import SqlAlchemyPitchRepository
from app.pitches.service.transitions import Side, allowed
from app.platform.service.audit import record_audit
from app.platform.service.outbox import publish
from app.portfolio.service.service import version_view

# Policy ``pitch-rate-limit`` version 1.
PITCHES_PER_DAY = 5
RATE_WINDOW = timedelta(days=1)

CLOSED_REASON: dict[str, str] = {
    "TARGET_NOT_ACTIVE": "Mandat ini sudah ditutup, dijeda atau berakhir.",
    "EXTERNAL_ROUTE": "Mitra ini menerima lewat formulirnya sendiri, bukan pitching di TemuRiset.",
    "NO_NEW_APPROACHES": "Mitra ini sedang tidak menerima pendekatan baru.",
    "DIRECT_INTAKE_CLOSED": "Penerimaan umum mitra ini ditutup.",
    "INTAKE_UNCONFIRMED": "Ketersediaan mitra ini belum dikonfirmasi.",
}


class DuplicatePitchError(AppError):
    """An active pitch already exists for this source and target."""

    code = codes.APP_DUPLICATE_PITCH


class TargetClosedError(AppError):
    """The target no longer accepts new pitches."""

    code = codes.APP_TARGET_CLOSED


class PreflightStaleError(AppError):
    """The preflight is unknown, expired, or something it pinned changed."""

    code = codes.APP_PREFLIGHT_STALE


class NotReadyError(AppError):
    """A submission requirement is not met."""

    code = codes.APP_NOT_READY


class PitchRateLimitedError(AppError):
    """Too many new pitches in a day."""

    code = codes.APP_RATE_LIMITED

    def __init__(self, retry_after_seconds: int) -> None:
        """Say the limit and when it frees up.

        Args:
            retry_after_seconds (int): Seconds until another pitch may start.
        """
        super().__init__(
            f"Batas {PITCHES_PER_DAY} pitching baru per hari sudah tercapai. Coba lagi setelah batas itu berlalu."
        )
        self.recovery["retry_after_seconds"] = retry_after_seconds


async def active_pitch_id(
    session: AsyncSession, subject_type: str, subject_id: UUID, recipient_party_id: UUID, opportunity_id: UUID
) -> UUID | None:
    """Return the active pitch of a source to a target, for preflight's duplicate notice (AC39).

    Args:
        session (AsyncSession): The request's session.
        subject_type (str): Source type.
        subject_id (UUID): Source.
        recipient_party_id (UUID): Recipient.
        opportunity_id (UUID): Opportunity.

    Returns:
        UUID | None: The pitch.
    """
    found = await SqlAlchemyPitchRepository(session).active(
        subject_type, subject_id, recipient_party_id, opportunity_id
    )
    return found.id if found else None


def _actions(principal: Principal, record: PitchRecord, side: Side) -> list[str]:
    """What the reader may do now, so screens never re-derive the state table."""
    capability = Capability.SUBMIT_PITCH if side == "requester" else Capability.DECIDE_PITCH
    if capability not in principal.capabilities:
        return []
    actions = allowed(record.status, side)
    if side == "requester" and record.status == "REVISION_REQUESTED":
        actions.append("answer")
    if side == "recipient" and record.status in ("SUBMITTED", "UNDER_REVIEW"):
        actions.append("review_items")
    return actions


async def pitches_of_party(session: AsyncSession, party_id: UUID, limit: int) -> list[PitchRecord]:
    """Return a party's sent and received pitches, most recently changed first, for Beranda (027).

    Args:
        session (AsyncSession): The request's session.
        party_id (UUID): The party.
        limit (int): The most to return.

    Returns:
        list[PitchRecord]: Pitches.
    """
    return await SqlAlchemyPitchRepository(session).involving(party_id, limit)


async def latest_snapshot(session: AsyncSession, pitch_id: UUID) -> dict[str, Any]:
    """Return the newest frozen submission's snapshot, for relationships (030).

    Args:
        session (AsyncSession): The request's session.
        pitch_id (UUID): The pitch.

    Returns:
        dict[str, Any]: The snapshot; empty when there is none.
    """
    last = await SqlAlchemyPitchRepository(session).last_submission(pitch_id)
    return last.snapshot if last else {}


class PitchService:
    """Submits pitches and reads them for their requester or recipient."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind to the request.

        Args:
            session (AsyncSession): The request's session.
        """
        self.session = session
        self.repository = SqlAlchemyPitchRepository(session)

    async def _rate_limit(self, party_id: UUID) -> None:
        since = clock.now() - RATE_WINDOW
        if await self.repository.created_since(party_id, since) >= PITCHES_PER_DAY:
            oldest = await self.repository.oldest_since(party_id, since)
            wait = int(((oldest or since) + RATE_WINDOW - clock.now()).total_seconds()) + 1
            raise PitchRateLimitedError(max(wait, 1))

    @staticmethod
    def _chosen_files(
        request: SubmitPitchRequest, shareable: list[dict[str, Any]], rows: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Match the chosen files to the preflight's list and check every required file is among them."""
        offered = {(item["document_id"], item["version"]): item for item in shareable}
        chosen = []
        errors = []
        for index, file in enumerate(request.files):
            item = offered.get((str(file.document_id), file.version))
            if item is None:
                errors.append(
                    {"loc": ["body", "files", index], "msg": "Pilih berkas dari daftar pemeriksaan.", "type": "file"}
                )
            else:
                chosen.append(item)
        if errors:
            raise FieldsInvalidError(errors)
        keys = {key for item in chosen for key in item["fact_keys"]}
        for row in rows:
            needs_file = row["verification_mode"] == "DOCUMENT_PRESENT" and row["field"].startswith("document:")
            if needs_file and row["mandatory"] and row["applies_at"] == "SUBMISSION":
                if row["field"].partition(":")[2] not in keys:
                    raise NotReadyError(
                        f"Pilih berkas untuk syarat “{row['label']}” sebelum mengirim.",
                        public_fields={"requirement": row["label"]},
                    )
        return chosen

    async def snapshot(
        self, principal: Principal, checked: dict[str, Any], source_type: str, source_id: UUID
    ) -> dict[str, Any]:
        """Freeze the source, the facts shown and the requirement rows; references, never bytes.

        Args:
            principal (Principal): The requester.
            checked (dict[str, Any]): What ``BriefService.evaluate`` returned.
            source_type (str): ``SUPPORT_REQUEST`` or ``FUNDING_REQUEST``.
            source_id (UUID): The source.

        Returns:
            dict[str, Any]: The snapshot.
        """
        if source_type == "SUPPORT_REQUEST":
            source, _ = await NeedsService(self.session).source(principal, source_id)
        else:
            source, _ = await FundingService(self.session).source(principal, source_id)
        inventions = []
        for version_id in checked["version_ids"]:
            version = await version_view(self.session, version_id)
            inventions.append(
                {
                    "version_id": str(version_id),
                    "number": version.number,
                    "title": version.title,
                    "stage": version.stage,
                    "facts": [
                        {"label": fact.label, "value": fact.value, "unit": fact.unit, "timing": fact.timing}
                        for fact in version.facts
                    ],
                }
            )
        opportunity = checked["opportunity"]
        return jsonable_encoder(
            {
                "source": source,
                "inventions": inventions,
                "opportunity": {
                    "id": opportunity.id,
                    "version_id": opportunity.current_version_id,
                    "version": opportunity.number,
                    "title": opportunity.title,
                },
                "requirements": checked["result"]["rows"],
            }
        )

    async def submit(
        self, principal: Principal, request: SubmitPitchRequest, operation_id: UUID | None = None
    ) -> SubmitPitchResponse:
        """Recheck the preflight, then freeze, share and notify in one transaction (FR-002, FR-003).

        Args:
            principal (Principal): Who is signed in.
            request (SubmitPitchRequest): Token, brief and files.
            operation_id (UUID | None, optional): For the response. Defaults to None.

        Returns:
            SubmitPitchResponse: The pitch.

        Raises:
            NotFoundError: When the token is not this party's.
            PreflightStaleError: When the token expired or anything it pinned changed (AC34).
            TargetClosedError: When the target no longer accepts pitches (AC26).
            DuplicatePitchError: When an active pitch exists (AC39).
            NotReadyError: When a submission requirement is not met.
            PitchRateLimitedError: Over five new pitches in a day.
        """
        check_context(principal, request.acting_party_id)
        require(principal, Capability.SUBMIT_PITCH, principal.active_party_id)
        record = await SqlAlchemyBriefRepository(self.session).preflight_by_token(hash_token(request.preflight_token))
        if record is None or record.actor_party_id != principal.active_party_id:
            # Another party's token, or none at all, reveals nothing; a known one that went stale says why.
            raise NotFoundError()
        checked = await BriefService(self.session).evaluate(
            principal, record.source_type, record.source_id, record.opportunity_id
        )
        availability = checked["opportunity"].target_availability
        if not availability.available:
            reason: AvailabilityReason = availability.reason  # type: ignore[assignment]
            raise TargetClosedError(public_fields={"reason": CLOSED_REASON[reason]})
        stale = stale_preflight_reason(record, principal, checked)
        if stale is not None:
            raise PreflightStaleError(public_fields={"reason": stale})
        existing = await active_pitch_id(
            self.session, record.source_type, record.source_id, record.recipient_party_id, record.opportunity_id
        )
        if existing is not None:
            raise DuplicatePitchError(public_fields={"pitch_id": str(existing)})
        result = checked["result"]
        if result["readiness"] != "READY_TO_SUBMIT":
            label = result["gap"]["label"] if result["gap"] else ""
            raise NotReadyError(public_fields={"requirement": label})
        chosen = self._chosen_files(request, record.shareable_files, result["rows"])
        await self._rate_limit(principal.active_party_id)
        try:
            async with self.session.begin_nested():
                pitch = await self.repository.add(
                    PitchRecord(
                        requester_party_id=principal.active_party_id,
                        recipient_party_id=record.recipient_party_id,
                        opportunity_id=record.opportunity_id,
                        opportunity_version_id=record.opportunity_version_id,
                        opportunity_title=checked["opportunity"].title,
                        subject_type=record.source_type,
                        subject_id=record.source_id,
                        subject_title=checked["title"],
                        purpose=checked["source"].relationship or "",
                        status="SUBMITTED",
                    )
                )
        except IntegrityError as error:
            # A parallel submission with another key won the active-pitch index (FR-001).
            existing = await active_pitch_id(
                self.session, record.source_type, record.source_id, record.recipient_party_id, record.opportunity_id
            )
            raise DuplicatePitchError(public_fields={"pitch_id": str(existing)}, error=error) from error
        submission = await self.repository.add(
            PitchSubmissionRecord(
                pitch_id=pitch.id,
                number=1,
                preflight_id=record.id,
                brief=request.brief,
                snapshot=await self.snapshot(principal, checked, record.source_type, record.source_id),
                submitted_by_account_id=principal.account_id,
            )
        )
        documents = DocumentService(self.session, get_settings())
        for item in chosen:
            grant = await documents.grant(
                principal,
                UUID(item["document_id"]),
                GrantRequest(
                    acting_party_id=principal.active_party_id,
                    version=item["version"],
                    grantee_party_id=record.recipient_party_id,
                    purpose="pitch",
                    pitch_id=pitch.id,
                ),
                capability=Capability.SUBMIT_PITCH,
            )
            await self.repository.add(
                PitchSubmissionFileRecord(
                    submission_id=submission.id,
                    document_id=UUID(item["document_id"]),
                    document_version_id=UUID(item["version_id"]),
                    version=item["version"],
                    title=item["title"],
                    grant_id=grant.id,
                )
            )
        await publish(
            self.session,
            "pitch.submitted",
            {
                "pitch_id": str(pitch.id),
                "requester_party_id": str(principal.active_party_id),
                "recipient_party_id": str(record.recipient_party_id),
                "version": 1,
            },
        )
        await record_audit(
            self.session,
            action="pitch.submitted",
            subject_type="pitch",
            subject_id=str(pitch.id),
            actor_account_id=principal.account_id,
            actor_party_id=principal.active_party_id,
        )
        return SubmitPitchResponse(pitch_id=pitch.id, status=pitch.status, submission=1, operation_id=operation_id)

    async def _summaries(self, records: list[PitchRecord]) -> list[PitchSummary]:
        parties = {party for record in records for party in (record.requester_party_id, record.recipient_party_id)}
        names = await party_names(self.session, list(parties))
        waiting = await waiting_parties(self.session, records)
        return [
            PitchSummary(
                id=record.id,
                status=record.status,
                subject_type=record.subject_type,  # type: ignore[arg-type]
                subject_id=record.subject_id,
                subject_title=record.subject_title,
                opportunity_id=record.opportunity_id,
                opportunity_title=record.opportunity_title,
                requester_party_id=record.requester_party_id,
                requester_name=names.get(record.requester_party_id, ""),
                recipient_party_id=record.recipient_party_id,
                recipient_name=names.get(record.recipient_party_id, ""),
                purpose=record.purpose,
                submitted_at=record.created_at,
                updated_at=record.updated_at,
                waiting_on_party_id=waiting[record.id],
            )
            for record in records
        ]

    async def list_box(self, principal: Principal, box: str, limit: int) -> list[PitchSummary]:
        """List the acting party's outgoing or incoming pitches.

        Args:
            principal (Principal): Who is signed in.
            box (str): ``outgoing`` or ``incoming``.
            limit (int): The most to return.

        Returns:
            list[PitchSummary]: Newest first.
        """
        records = await self.repository.of_party(principal.active_party_id, incoming=box == "incoming", limit=limit)
        return await self._summaries(records)

    async def read(self, principal: Principal, pitch_id: UUID) -> PitchResponse:
        """Read a pitch as its requester or recipient.

        Args:
            principal (Principal): Who is signed in.
            pitch_id (UUID): The pitch.

        Returns:
            PitchResponse: The pitch with its frozen submissions.

        Raises:
            NotFoundError: For anyone else.
        """
        record = await self.repository.find(pitch_id)
        if record is None or principal.active_party_id not in (record.requester_party_id, record.recipient_party_id):
            raise NotFoundError()
        summary = (await self._summaries([record]))[0]
        side: Side = "requester" if principal.active_party_id == record.requester_party_id else "recipient"
        submissions = [
            SubmissionResponse(
                number=submission.number,
                brief=submission.brief,
                snapshot=submission.snapshot,
                files=[SubmittedFile(document_id=f.document_id, version=f.version, title=f.title) for f in files],
                submitted_at=submission.created_at,
            )
            for submission, files in await self.repository.submissions(record.id)
        ]
        decisions = [
            DecisionResponse(
                decision=decision.decision,  # type: ignore[arg-type]
                reason=decision.reason,
                submission_number=decision.submission_number,
                decided_at=decision.created_at,
            )
            for decision in await self.repository.decisions(record.id)
        ]
        stored = await self.repository.rounds(record.id)
        rounds = []
        for index, (round_, items) in enumerate(stored):
            is_open = record.status == "REVISION_REQUESTED" and index == len(stored) - 1
            # Draft answers stay with the requester until the round is resubmitted.
            hidden = is_open and side == "recipient"
            rounds.append(
                RevisionRoundResponse(
                    number=round_.number,
                    submission_number=round_.submission_number,
                    requested_at=round_.created_at,
                    open=is_open,
                    items=[
                        RevisionItemResponse(
                            id=item.id,
                            position=item.position,
                            category=item.category,
                            question=item.question,
                            reason=item.reason,
                            required=item.required,
                            due_date=item.due_date,
                            expected_evidence=item.expected_evidence,
                            review=item.review,  # type: ignore[arg-type]
                            review_note=item.review_note,
                            version=item.version,
                            answer=None
                            if answer is None or hidden
                            else AnswerResponse(
                                response=answer.response,  # type: ignore[arg-type]
                                text=answer.text,
                                files=[
                                    SubmittedFile(**{k: f[k] for k in ("document_id", "version", "title")})
                                    for f in answer.files
                                ],
                                version=answer.version,
                                saved_at=answer.updated_at,
                            ),
                        )
                        for item, answer in items
                    ],
                )
            )
        return PitchResponse(
            **summary.model_dump(),
            version=record.version,
            submissions=submissions,
            decisions=decisions,
            rounds=rounds,
            allowed_actions=_actions(principal, record, side),
        )
