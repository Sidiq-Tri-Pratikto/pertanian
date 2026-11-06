"""Preflight, the template brief, extractive summary suggestions and export."""

import hashlib
import secrets
from collections.abc import Awaitable, Callable
from datetime import timedelta
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.access.service.policy import check_context
from app.access.service.service import party_names
from app.briefs.model.schema import (
    BriefResponse,
    BriefSentence,
    PartyName,
    PinnedInvention,
    PinnedOpportunity,
    PinnedSource,
    PreflightRequest,
    PreflightResponse,
    ShareableFile,
    SummaryStatus,
)
from app.briefs.repository.sqlalchemy.models import BriefRecord, PreflightRecord
from app.briefs.repository.sqlalchemy.repository import SqlAlchemyBriefRepository
from app.briefs.service.summarizer_service import (
    OffSummarizer,
    SummarizerPort,
    SummaryCandidate,
    SummaryRefusedError,
    SummaryUnavailableError,
    request_selection,
    select_sentences,
)
from app.briefs.service.template import brief_text, template_brief
from app.capabilities.service.guard import CapabilityUnavailableError
from app.core import clock
from app.core.errors.base import NotFoundError
from app.core.errors.public import error_response, public_error_for_code
from app.core.errors.recorder import record_failure
from app.core.openapi import ErrorBody
from app.core.settings import get_settings
from app.documents.service.service import evidence_results, owned_version_details
from app.funding.service.service import FundingService
from app.identity.model.models import Principal
from app.intake.service.service import IntakeService
from app.matching.engine.evaluate import ENGINE, POLICY_VERSIONS, evaluate
from app.matching.service.service import MatchingService, target_of
from app.moderation.service.suspension import ListingSuspendedError
from app.needs.service.service import NeedsService
from app.portfolio.service.service import invention_reference, version_view

PREFLIGHT_LIFETIME = timedelta(minutes=30)
REDACTED = "[Bagian ini disembunyikan karena berkas pendukungnya tidak lagi dapat diakses.]"
_REDACTED_SOURCE = "[Bagian ini disembunyikan karena sumber brief telah berubah.]"


def hash_token(token: str) -> str:
    """Digest a preflight token; only the digest is stored.

    Args:
        token (str): The token.

    Returns:
        str: Hex SHA-256.
    """
    return hashlib.sha256(token.encode()).hexdigest()


def permission_generation(principal: Principal) -> str:
    """Fingerprint what the acting member may do now; any change makes a preflight stale.

    Args:
        principal (Principal): Who is signed in.

    Returns:
        str: Hex SHA-256 of the acting party and its capabilities.
    """
    raw = f"{principal.active_party_id}:{','.join(sorted(principal.capabilities))}"
    return hashlib.sha256(raw.encode()).hexdigest()


def configuration_ref() -> str:
    """Name the configuration a preflight was computed under.

    Returns:
        str: Composition, engine and policy versions.
    """
    settings = get_settings()
    policies = ",".join(f"{key}@{value}" for key, value in sorted(POLICY_VERSIONS.items()))
    return f"{settings.composition}:{ENGINE}:{policies}"


def _brief_response(record: BriefRecord) -> BriefResponse:
    return BriefResponse(
        id=record.id,
        preflight_id=record.preflight_id,
        text=record.text,
        sentences=[BriefSentence.model_validate(sentence) for sentence in record.sentences],
        summarizer=record.summarizer,
    )


def _summary_fallback(template: BriefResponse, error: SummaryRefusedError | SummaryUnavailableError) -> BriefResponse:
    public = public_error_for_code(error.code)
    record_failure(error, operation="/api/v1/briefs/{brief_id}/summary", http_status=public.http_status)
    status: SummaryStatus = "refused" if isinstance(error, SummaryRefusedError) else "unavailable"
    template.summarizer_status = status
    template.summarizer_error = ErrorBody.model_validate(error_response(public, error.reference_id)["error"])
    return template


class BriefService:
    """Preflights and briefs for the acting party."""

    def __init__(self, session: AsyncSession, summarizer: SummarizerPort | None = None) -> None:
        """Bind to the request.

        Args:
            session (AsyncSession): The request's session.
            summarizer (SummarizerPort | None, optional): The summarizer. Defaults to off.
        """
        self.session = session
        self.repository = SqlAlchemyBriefRepository(session)
        self.summarizer = summarizer or OffSummarizer()

    async def evaluate(self, principal: Principal, source_type: str, source_id: UUID, opportunity_id: UUID) -> dict:
        """Evaluate one owned source against one opportunity as an applicant reads it, with everything a pin needs.

        Args:
            principal (Principal): Who is signed in.
            source_type (str): ``SUPPORT_REQUEST`` or ``FUNDING_REQUEST``.
            source_id (UUID): The source.
            opportunity_id (UUID): The target.

        Returns:
            dict: ``source``, ``title``, ``version_ids``, ``opportunity``, ``partner_name`` and ``result``.

        Raises:
            NotFoundError: For another party's source, a draft target, or one's own opportunity.
        """
        source, title, version_ids = await MatchingService(self.session).source_of(
            principal, source_type, source_id, lock_inventions=True
        )
        opportunity = await IntakeService(self.session).read(principal, opportunity_id, lock_for_pitch=True)
        if opportunity.partner_party_id == principal.active_party_id:
            raise NotFoundError()
        names = await party_names(self.session, [opportunity.partner_party_id, principal.active_party_id])
        result = evaluate(source, target_of(opportunity, names.get(opportunity.partner_party_id, "")))
        return {
            "source": source,
            "title": title,
            "version_ids": version_ids,
            "opportunity": opportunity,
            "partner_name": names.get(opportunity.partner_party_id, ""),
            "sender_name": names.get(principal.active_party_id, ""),
            "result": result,
        }

    async def preflight(self, principal: Principal, request: PreflightRequest) -> PreflightResponse:
        """Show exactly what would be sent, pin it under a 30-minute token, and build the template brief.

        Args:
            principal (Principal): Who is signed in.
            request (PreflightRequest): Source and target.

        Returns:
            PreflightResponse: The preflight; not-ready ones are returned too but cannot be submitted.
        """
        check_context(principal, request.acting_party_id)
        checked = await self.evaluate(principal, request.source_type, request.source_id, request.opportunity_id)
        source, opportunity, result = checked["source"], checked["opportunity"], checked["result"]
        versions = [await version_view(self.session, version_id) for version_id in checked["version_ids"]]
        support = raise_ = None
        if request.source_type == "SUPPORT_REQUEST":
            support, _ = await NeedsService(self.session).source(principal, request.source_id)
        else:
            raise_, _ = await FundingService(self.session).source(principal, request.source_id)
        keys: dict[str, list[str]] = {}
        for version in versions:
            for fact in version.facts:
                if fact.document_version_id and fact.key:
                    keys.setdefault(str(fact.document_version_id), []).append(fact.key)
        files = await owned_version_details(self.session, principal.active_party_id, [UUID(key) for key in keys])
        files = [
            {**item, "fact_keys": sorted(set(keys[item["version_id"]]))}
            for item in files
            if item["file_state"] == "AVAILABLE"
        ]
        token = secrets.token_urlsafe(32)
        version_ids = [str(version_id) for version_id in checked["version_ids"]]
        record = await self.repository.add(
            PreflightRecord(
                actor_party_id=principal.active_party_id,
                actor_account_id=principal.account_id,
                token_sha256=hash_token(token),
                source_type=request.source_type,
                source_id=request.source_id,
                source_version=source.version,
                invention_version_ids=version_ids,
                opportunity_id=opportunity.id,
                opportunity_version_id=opportunity.current_version_id,
                recipient_party_id=opportunity.partner_party_id,
                configuration_ref=configuration_ref(),
                permission_generation=permission_generation(principal),
                result=result,
                shareable_files=files,
                expires_at=clock.now() + PREFLIGHT_LIFETIME,
            )
        )
        sentences = template_brief(
            versions=versions,
            version_ids=version_ids,
            request=support,
            raise_=raise_,
            opportunity={
                "id": str(opportunity.id),
                "version_id": str(opportunity.current_version_id),
                "title": opportunity.title,
            },
            result=result,
        )
        brief = await self.repository.add(
            BriefRecord(
                preflight_id=record.id,
                owner_party_id=principal.active_party_id,
                text=brief_text(sentences),
                sentences=sentences,
            )
        )
        from app.pitches.service.submission import active_pitch_id  # noqa: PLC0415 - pitches imports this module

        inventions = []
        for version_id in checked["version_ids"]:
            reference = await invention_reference(self.session, version_id)
            inventions.append(
                PinnedInvention(
                    invention_id=reference.invention_id,
                    version_id=version_id,
                    version=reference.number,
                    title=reference.title,
                )
            )
        return PreflightResponse(
            preflight_id=record.id,
            token=token,
            expires_at=record.expires_at,
            readiness=result["readiness"],
            eligibility=result["eligibility"],
            label=result["label"],
            fit=result["fit"],
            sender=PartyName(party_id=principal.active_party_id, name=checked["sender_name"]),
            recipient=PartyName(party_id=opportunity.partner_party_id, name=checked["partner_name"]),
            opportunity=PinnedOpportunity(
                id=opportunity.id,
                version_id=opportunity.current_version_id,
                version=opportunity.number,
                title=opportunity.title,
            ),
            source=PinnedSource(
                type=request.source_type, id=request.source_id, version=source.version, title=checked["title"]
            ),
            inventions=inventions,
            purpose=source.relationship,
            availability=opportunity.target_availability,
            rows=result["rows"],
            gap=result["gap"],
            later=result["later"],
            shareable_files=[ShareableFile.model_validate(item) for item in files],
            brief=_brief_response(brief),
            duplicate_pitch_id=await active_pitch_id(
                self.session, request.source_type, request.source_id, opportunity.partner_party_id, opportunity.id
            ),
        )

    async def _own_brief(self, principal: Principal, brief_id: UUID) -> BriefRecord:
        record = await self.repository.brief(brief_id)
        if record is None or record.owner_party_id != principal.active_party_id:
            raise NotFoundError()
        return record

    async def read(self, principal: Principal, brief_id: UUID) -> BriefResponse:
        """Read one's own brief.

        Args:
            principal (Principal): Who is signed in.
            brief_id (UUID): The brief.

        Returns:
            BriefResponse: The brief.
        """
        return _brief_response(await self._own_brief(principal, brief_id))

    async def _visible_sentences(self, owner: UUID, sentences: list[BriefSentence]) -> list[BriefSentence]:
        files_by_sentence = [
            {UUID(ref["document_version_id"]) for ref in sentence.refs if ref.get("document_version_id")}
            for sentence in sentences
        ]
        linked = list({file for files in files_by_sentence for file in files})
        evidence = await evidence_results(self.session, owner, linked)
        available = {file for file, checks in evidence.items() if checks["DOCUMENT_PRESENT"] == "PASS"}
        return [
            sentence if files <= available else BriefSentence(text=REDACTED, refs=[])
            for sentence, files in zip(sentences, files_by_sentence, strict=True)
        ]

    async def _summary_template(
        self, brief_id: UUID, resolve_principal: Callable[[], Awaitable[Principal]]
    ) -> tuple[BriefResponse, bool]:
        principal = await resolve_principal()
        record = await self._own_brief(principal, brief_id)
        preflight = await self.repository.preflight(record.preflight_id)
        assert preflight is not None  # noqa: S101 - briefs cascade with their preflight
        template = _brief_response(record)
        pinned = False
        fresh = False
        try:
            source, _, versions = await MatchingService(self.session).source_of(
                principal, preflight.source_type, preflight.source_id
            )
            opportunity = await IntakeService(self.session).read(principal, preflight.opportunity_id)
        except (NotFoundError, CapabilityUnavailableError, ListingSuspendedError):
            pass  # The stored pins no longer have a live view; mask their template below.
        else:
            pinned = (
                preflight.actor_party_id == principal.active_party_id
                and opportunity.partner_party_id == preflight.recipient_party_id
                and opportunity.current_version_id == preflight.opportunity_version_id
                and source.version == preflight.source_version
                and [str(version) for version in versions] == preflight.invention_version_ids
            )
            fresh = (
                pinned
                and stale_preflight_reason(
                    preflight, principal, {"source": source, "version_ids": versions, "opportunity": opportunity}
                )
                is None
            )

        template.sentences = (
            await self._visible_sentences(record.owner_party_id, template.sentences)
            if pinned
            else [BriefSentence(text=_REDACTED_SOURCE, refs=[]) for _ in template.sentences]
        )
        template.text = "\n".join(sentence.text for sentence in template.sentences)
        # Release the transaction (including any auth refresh) before calling the provider.
        # Expunge the read snapshot so the next check cannot reuse older ORM objects.
        await self.session.commit()
        self.session.expunge_all()
        return template, fresh

    async def summarize(self, brief_id: UUID, resolve_principal: Callable[[], Awaitable[Principal]]) -> BriefResponse:
        """Return a verified extractive suggestion or the editable template under current access.

        Args:
            brief_id (UUID): The brief.
            resolve_principal (Callable[[], Awaitable[Principal]]): Reauthenticate each attempt and delivery.

        Returns:
            BriefResponse: Selected originals and provenance, or a template with live redaction.
        """
        retried = False
        provenance = self.summarizer.provenance
        while True:
            template, fresh = await self._summary_template(brief_id, resolve_principal)
            if self.summarizer.name == "off":
                return template
            originals = {uuid4().hex: sentence for sentence in template.sentences if sentence.refs}
            if not fresh or len(originals) < 2 or provenance is None:
                return _summary_fallback(template, SummaryRefusedError())

            candidates = tuple(
                SummaryCandidate(identifier, sentence.text) for identifier, sentence in originals.items()
            )
            selected: list[BriefSentence] = []
            error: SummaryUnavailableError | SummaryRefusedError | None = None
            try:
                output = await request_selection(self.summarizer, candidates)
                selected = select_sentences(output, originals)
            except (TimeoutError, ConnectionError) as cause:
                if not retried:
                    retried = True
                    continue
                error = SummaryUnavailableError()
                error.__cause__ = cause
            except (SummaryUnavailableError, SummaryRefusedError) as failure:
                error = failure

            latest, fresh = await self._summary_template(brief_id, resolve_principal)
            if error is not None:
                return _summary_fallback(latest, error)
            if not fresh or any(sentence not in latest.sentences for sentence in selected):
                return _summary_fallback(latest, SummaryRefusedError())
            latest.text = "\n".join(sentence.text for sentence in selected)
            latest.sentences = selected
            latest.summarizer = self.summarizer.name
            latest.summarizer_status = "used"
            latest.summarizer_provenance = provenance
            return latest

    async def export(self, principal: Principal, brief_id: UUID, text_format: str) -> str:
        """Export a brief under today's permissions: a sentence whose file is no longer accessible is redacted (AC36).

        Args:
            principal (Principal): Who is signed in.
            brief_id (UUID): The brief.
            text_format (str): ``md`` or ``txt``.

        Returns:
            str: The export, naming its source versions.
        """
        record = await self._own_brief(principal, brief_id)
        preflight = await self.repository.preflight(record.preflight_id)
        assert preflight is not None  # noqa: S101 - briefs cascade with their preflight
        sentences = await self._visible_sentences(record.owner_party_id, _brief_response(record).sentences)
        lines = [sentence.text for sentence in sentences]
        heading = (
            f"Sumber: {preflight.source_type} versi {preflight.source_version}; "
            f"mandat {preflight.result['title']} versi {preflight.result['opportunity_version']}"
        )
        if text_format == "md":
            return "# Brief pitching\n\n" + f"_{heading}_\n\n" + "\n".join(f"- {line}" for line in lines) + "\n"
        return "Brief pitching\n" + heading + "\n\n" + "\n".join(lines) + "\n"


def stale_preflight_reason(record: PreflightRecord, principal: Principal, current: dict[str, Any]) -> str | None:
    """Say why a preflight no longer holds, or None when every pin still matches (AC34).

    Args:
        record (PreflightRecord): The preflight.
        principal (Principal): Who is submitting now.
        current (dict[str, Any]): A fresh ``BriefService.evaluate`` result.

    Returns:
        str | None: What changed, in Indonesian.
    """
    if record.expires_at <= clock.now():
        return "Pemeriksaan sudah lebih dari 30 menit."
    if record.actor_party_id != principal.active_party_id or record.permission_generation != permission_generation(
        principal
    ):
        return "Wewenang atau konteks Anda berubah setelah pemeriksaan."
    if current["opportunity"].current_version_id != record.opportunity_version_id:
        return "Mandat berubah setelah pemeriksaan."
    if (
        current["source"].version != record.source_version
        or [str(version_id) for version_id in current["version_ids"]] != record.invention_version_ids
    ):
        return "Kebutuhan atau inovasi berubah setelah pemeriksaan."
    if record.configuration_ref != configuration_ref():
        return "Konfigurasi layanan berubah setelah pemeriksaan."
    return None
