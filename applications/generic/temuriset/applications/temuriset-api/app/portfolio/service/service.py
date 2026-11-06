"""Inventions: drafts that save anything, versions that never change once published."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.access.model.models import Capability
from app.access.service.policy import check_context, require
from app.access.service.service import party_names
from app.core import clock
from app.core.errors.base import ConflictError, NotFoundError
from app.identity.model.models import Principal
from app.platform.service.audit import record_audit
from app.platform.service.outbox import publish
from app.platform.service.versions import check_expected
from app.portfolio.model.schema import (
    CreateInventionRequest,
    DraftRequest,
    InventionResponse,
    InventionSummaryResponse,
    InventionVersionResponse,
    PublicClaimResponse,
    PublicFactResponse,
    PublicInventionResponse,
    PublishResponse,
    VersionedActionRequest,
)
from app.portfolio.repository.sqlalchemy.models import InventionRecord, InventionVersionRecord
from app.portfolio.repository.sqlalchemy.repository import SqlAlchemyPortfolioRepository
from app.portfolio.service.review_hook import PassThroughGate, PublicationGate
from app.portfolio.service.validation import PublicationInvalidError, publication_errors

_ARCHIVED = "Inovasi ini sudah diarsipkan. Riwayatnya tetap dapat dibaca, tetapi tidak dapat diubah atau dikirim."
_NO_DRAFT = "Tidak ada draf untuk diterbitkan. Ubah inovasi terlebih dahulu lalu terbitkan."


class PortfolioService:
    """Inventions of the acting party."""

    def __init__(self, session: AsyncSession, gate: PublicationGate | None = None) -> None:
        """Bind to the request.

        Args:
            session (AsyncSession): The request's session.
            gate (PublicationGate | None, optional): Organization review. Defaults to publishing at once.
        """
        self.session = session
        self.gate = gate or PassThroughGate()
        self.repository = SqlAlchemyPortfolioRepository(session)

    async def create(self, principal: Principal, request: CreateInventionRequest) -> InventionResponse:
        """Start an invention with an empty draft.

        Args:
            principal (Principal): Who is signed in.
            request (CreateInventionRequest): Acting party.

        Returns:
            InventionResponse: The new invention.
        """
        check_context(principal, request.acting_party_id)
        require(principal, Capability.EDIT_PORTFOLIO, principal.active_party_id)
        invention = await self.repository.add_invention(principal.active_party_id)
        return await self._view(invention)

    async def list_mine(self, principal: Principal) -> list[InventionSummaryResponse]:
        """List the active party's inventions, drafts and archived ones included.

        Args:
            principal (Principal): Who is signed in.

        Returns:
            list[InventionSummaryResponse]: Inventions.
        """
        result = []
        for invention in await self.repository.of_party(principal.active_party_id):
            draft = await self.repository.version(invention.draft_version_id)
            published = await self.repository.version(invention.published_version_id)
            shown = draft or published
            result.append(
                InventionSummaryResponse(
                    id=invention.id,
                    status=invention.status,
                    title=shown.title if shown else "",
                    version=invention.version,
                    has_draft=draft is not None,
                    published_number=published.number if published else None,
                )
            )
        return result

    async def _owned(self, principal: Principal, invention_id: UUID, *, lock: bool = False) -> InventionRecord:
        invention = await self.repository.find(invention_id, lock=lock)
        if invention is None or invention.managing_party_id != principal.active_party_id:
            raise NotFoundError()
        return invention

    async def _view(self, invention: InventionRecord, operation_id: UUID | None = None) -> InventionResponse:
        return InventionResponse(
            id=invention.id,
            managing_party_id=invention.managing_party_id,
            status=invention.status,
            version=invention.version,
            draft=await self.repository.version(invention.draft_version_id),
            published=await self.repository.version(invention.published_version_id),
            history=await self.repository.numbers(invention.id),
            operation_id=operation_id,
        )

    async def owner_view(self, principal: Principal, invention_id: UUID) -> InventionResponse:
        """Read an invention as its managing party.

        Args:
            principal (Principal): Who is signed in.
            invention_id (UUID): The invention.

        Returns:
            InventionResponse: Draft, published version and history.

        Raises:
            NotFoundError: When the active party does not manage it.
        """
        return await self._view(await self._owned(principal, invention_id))

    async def save_draft(
        self, principal: Principal, invention_id: UUID, request: DraftRequest, operation_id: UUID | None = None
    ) -> InventionResponse:
        """Save the whole draft. Nothing here enforces publication rules.

        Args:
            principal (Principal): Who is signed in.
            invention_id (UUID): The invention.
            request (DraftRequest): Content and ``expected_version``.
            operation_id (UUID | None, optional): For the response. Defaults to None.

        Returns:
            InventionResponse: The invention with its saved draft.

        Raises:
            StaleContextError: When the tab acts as another party.
            NotFoundError: When the active party does not manage it.
            ForbiddenError: Without ``edit_portfolio``.
            ConflictError: When it is archived.
            StaleVersionError: When it changed since the client read it.
        """
        check_context(principal, request.acting_party_id)
        invention = await self._owned(principal, invention_id, lock=True)
        require(principal, Capability.EDIT_PORTFOLIO, invention.managing_party_id)
        if invention.status == "ARCHIVED":
            raise ConflictError(_ARCHIVED)
        check_expected(invention.version, request.expected_version)
        content = request.model_dump(exclude={"acting_party_id", "expected_version", "facts", "claims"})
        await self.repository.write_draft(
            invention,
            content,
            [fact.model_dump() for fact in request.facts],
            [claim.model_dump() for claim in request.claims],
        )
        invention.version += 1
        await self.session.flush()
        return await self._view(invention, operation_id)

    async def publish(
        self, principal: Principal, invention_id: UUID, request: VersionedActionRequest
    ) -> PublishResponse:
        """Publish the draft as an immutable version, or send it to review when 033 says so.

        Args:
            principal (Principal): Who is signed in.
            invention_id (UUID): The invention.
            request (VersionedActionRequest): Acting party and ``expected_version``.

        Returns:
            PublishResponse: The published version number and status.

        Raises:
            PublicationInvalidError: When the draft breaks a publication rule; the draft is unchanged.
            ConflictError: When archived or when there is no draft.
        """
        check_context(principal, request.acting_party_id)
        invention = await self._owned(principal, invention_id, lock=True)
        require(principal, Capability.EDIT_PORTFOLIO, invention.managing_party_id)
        if invention.status == "ARCHIVED":
            raise ConflictError(_ARCHIVED)
        check_expected(invention.version, request.expected_version)
        draft = await self.repository.version(invention.draft_version_id)
        if draft is None or invention.draft_version_id is None:
            raise ConflictError(_NO_DRAFT)
        errors = publication_errors(draft)
        if errors:
            raise PublicationInvalidError(errors)
        status = await self.gate.decide(
            invention_id=invention.id, managing_party_id=invention.managing_party_id, number=draft.number
        )
        if status == "PUBLISHED":
            if invention.published_version_id is not None:
                await self.repository.set_version_state(invention.published_version_id, state="superseded")
            await self.repository.set_version_state(
                invention.draft_version_id, state="published", published_at=clock.now()
            )
            invention.published_version_id, invention.draft_version_id = invention.draft_version_id, None
            await publish(
                self.session,
                "invention.published",
                {"invention_id": str(invention.id), "version_id": str(invention.published_version_id)},
            )
        invention.status = status
        invention.version += 1
        await self.session.flush()
        await record_audit(
            self.session,
            action="invention.published" if status == "PUBLISHED" else "invention.review_requested",
            subject_type="invention",
            subject_id=str(invention.id),
            actor_account_id=principal.account_id,
            actor_party_id=principal.active_party_id,
            detail={"number": draft.number},
        )
        return PublishResponse(version=draft.number, status=status)

    async def archive(
        self,
        principal: Principal,
        invention_id: UUID,
        request: VersionedActionRequest,
        operation_id: UUID | None = None,
    ) -> InventionResponse:
        """Archive: gone from discovery and new submissions, history kept for authorized parties (AC09).

        Args:
            principal (Principal): Who is signed in.
            invention_id (UUID): The invention.
            request (VersionedActionRequest): Acting party and ``expected_version``.
            operation_id (UUID | None, optional): For the response. Defaults to None.

        Returns:
            InventionResponse: The archived invention.
        """
        check_context(principal, request.acting_party_id)
        invention = await self._owned(principal, invention_id, lock=True)
        require(principal, Capability.EDIT_PORTFOLIO, invention.managing_party_id)
        check_expected(invention.version, request.expected_version)
        if invention.status != "ARCHIVED":
            invention.status = "ARCHIVED"
            invention.version += 1
            await self.session.flush()
            await publish(self.session, "invention.archived", {"invention_id": str(invention.id)})
            await record_audit(
                self.session,
                action="invention.archived",
                subject_type="invention",
                subject_id=str(invention.id),
                actor_account_id=principal.account_id,
                actor_party_id=principal.active_party_id,
            )
        return await self._view(invention, operation_id)

    async def public_view(self, invention_id: UUID) -> PublicInventionResponse:
        """The published version as anyone may read it; private notes and document links stay out.

        Args:
            invention_id (UUID): The invention.

        Returns:
            PublicInventionResponse: The projection.

        Raises:
            NotFoundError: When unpublished or archived.
        """
        invention = await self.repository.find(invention_id)
        if invention is None or invention.status == "ARCHIVED" or invention.published_version_id is None:
            raise NotFoundError()
        version = await self.repository.version(invention.published_version_id)
        assert version is not None  # noqa: S101 - the pointer always names a stored version
        names = await party_names(self.session, [invention.managing_party_id])
        return PublicInventionResponse(
            id=invention.id,
            managing_party_id=invention.managing_party_id,
            managing_party_name=names.get(invention.managing_party_id, ""),
            number=version.number,
            title=version.title,
            summary=version.summary,
            problem=version.problem,
            solution=version.solution,
            intended_users=version.intended_users,
            sector=version.sector,
            stage=version.stage,
            keywords=version.keywords,
            facts=[PublicFactResponse.model_validate(fact.model_dump()) for fact in version.facts],
            claims=[PublicClaimResponse.model_validate(claim.model_dump()) for claim in version.claims],
            published_at=version.published_at,
        )


async def version_view(session: AsyncSession, version_id: UUID) -> InventionVersionResponse:
    """Read one invention version with its fact keys, document links and claims, for matching (019).

    Callers must have authorized the version first: it includes what only its owner may read.

    Args:
        session (AsyncSession): The request's session.
        version_id (UUID): The version.

    Returns:
        InventionVersionResponse: The version.
    """
    version = await SqlAlchemyPortfolioRepository(session).version(version_id)
    assert version is not None  # noqa: S101 - references are foreign keys
    return version


async def submittable_version(session: AsyncSession, invention_id: UUID) -> UUID:
    """Return the version a new need or submission may reference: the published one of an active invention.

    Args:
        session (AsyncSession): The request's session.
        invention_id (UUID): The invention.

    Returns:
        UUID: The published version.

    Raises:
        ConflictError: When archived or never published (AC09).
    """
    invention = await SqlAlchemyPortfolioRepository(session).find(invention_id)
    if invention is None:
        raise NotFoundError()
    if invention.status == "ARCHIVED" or invention.published_version_id is None:
        raise ConflictError(_ARCHIVED if invention.status == "ARCHIVED" else _NO_DRAFT)
    return invention.published_version_id


class InventionReference:
    """What a need or raise shows about the invention version it references."""

    def __init__(self, number: int, title: str, invention_id: UUID) -> None:
        """Hold the reference.

        Args:
            number (int): Version number.
            title (str): Version title.
            invention_id (UUID): The invention.
        """
        self.number = number
        self.title = title
        self.invention_id = invention_id


async def invention_reference(session: AsyncSession, version_id: UUID) -> InventionReference:
    """Read the number and title of an invention version.

    Args:
        session (AsyncSession): The request's session.
        version_id (UUID): The version.

    Returns:
        InventionReference: Number and title.
    """
    from app.portfolio.repository.sqlalchemy.models import InventionVersionRecord

    record = await session.get(InventionVersionRecord, version_id)
    assert record is not None  # noqa: S101 - references are foreign keys
    return InventionReference(record.number, record.title, record.invention_id)


async def owned_submittable_version(session: AsyncSession, invention_id: UUID, party_id: UUID) -> UUID:
    """Return the published version of an active invention the party manages.

    Args:
        session (AsyncSession): The request's session.
        invention_id (UUID): The invention.
        party_id (UUID): The acting party.

    Returns:
        UUID: The published version.

    Raises:
        NotFoundError: For another party's invention.
        ConflictError: When archived or never published.
    """
    invention = await SqlAlchemyPortfolioRepository(session).find(invention_id)
    if invention is None or invention.managing_party_id != party_id:
        raise NotFoundError()
    return await submittable_version(session, invention_id)


async def invention_ids_of(session: AsyncSession, version_ids: list[UUID]) -> list[UUID]:
    """Return the inventions that versions belong to, once each and in order, for relationships (030).

    Args:
        session (AsyncSession): The request's session.
        version_ids (list[UUID]): Versions.

    Returns:
        list[UUID]: Invention ids.
    """
    found: list[UUID] = []
    for version_id in version_ids:
        record = await session.get(InventionVersionRecord, version_id)
        if record is not None and record.invention_id not in found:
            found.append(record.invention_id)
    return found
