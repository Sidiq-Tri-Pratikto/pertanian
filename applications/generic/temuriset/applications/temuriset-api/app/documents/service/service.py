"""Private documents: upload intents, versions, grants and the authorization behind every download."""

from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from datetime import timedelta
from typing import Any
from uuid import UUID, uuid4

import anyio
from sqlalchemy.ext.asyncio import AsyncSession

from app.access.model.models import Capability
from app.access.service.policy import check_context, require, require_case_file
from app.access.service.service import party_names
from app.core import clock
from app.core.database import get_session_factory
from app.core.errors import codes
from app.core.errors.base import AppError, ForbiddenError, NotFoundError, RequestInvalidError
from app.core.errors.recorder import emergency_log
from app.core.settings import Settings
from app.documents.model.schema import (
    DocumentResponse,
    DocumentVersionResponse,
    GrantRequest,
    GrantResponse,
    PersonalDocumentMetadata,
    RevokedResponse,
    UploadedResponse,
    UploadIntentRequest,
    UploadIntentResponse,
)
from app.documents.repository.sqlalchemy.models import (
    DocumentGrantRecord,
    DocumentRecord,
    DocumentVersionRecord,
    DownloadEventRecord,
    UploadIntentRecord,
)
from app.documents.repository.sqlalchemy.repository import SqlAlchemyDocumentRepository
from app.documents.service.sniff import LIMIT_TEXT, LIMITS, sniff
from app.documents.service.storage_service import StorageAdapter, TooLargeError, storage_for
from app.identity.model.models import Principal
from app.identity.service.service import IdentityService
from app.platform.service.audit import record_audit
from app.platform.service.outbox import enqueue_job

INTENT_LIFETIME = timedelta(hours=1)
REVOKED_MESSAGE = "Unduhan baru diblokir. Salinan yang sudah diunduh tidak dapat ditarik kembali."
_INTENT_EXPIRED = "Batas waktu unggah sudah lewat. Mulai unggah lagi dari awal."
_INTENT_USED = "Berkas untuk unggahan ini sudah diterima. Mulai unggahan baru untuk versi berikutnya."


class FileTooLargeError(AppError):
    """The declared or sent size passes the limit for its type."""

    code = codes.APP_FILE_TOO_LARGE

    def __init__(self, limit_text: str) -> None:
        """Name the limit.

        Args:
            limit_text (str): The limit in words, such as "20 MB untuk PDF dan DOCX".
        """
        super().__init__(f"Berkas melebihi batas {limit_text}. Kecilkan berkas lalu unggah lagi.")


class FileTypeUnsupportedError(AppError):
    """The type is not accepted."""

    code = codes.APP_FILE_TYPE_UNSUPPORTED


class FileNotAvailableError(AppError):
    """The version is quarantined or rejected."""

    code = codes.APP_FILE_NOT_AVAILABLE


class GrantRevokedError(AppError):
    """The grant was revoked; copies already delivered cannot be recalled."""

    code = codes.APP_GRANT_REVOKED


@dataclass(frozen=True)
class Download:
    """An authorized download: what to stream and how to label it."""

    storage_key: str
    media_type: str
    size_bytes: int
    filename: str
    version_id: UUID
    grant_id: UUID | None = None


def evidence_status(version: DocumentVersionRecord | None, mode: str) -> str:
    """Evaluate a document requirement against a version, for matching and preflight (019, 022).

    Args:
        version (DocumentVersionRecord | None): The linked version.
        mode (str): ``DOCUMENT_PRESENT`` or ``REVIEWER_CONFIRMED``.

    Returns:
        str: ``PASS`` or ``UNKNOWN``; a quarantined file or an unreviewed one never passes what it has not earned.
    """
    if version is None or version.file_state != "AVAILABLE":
        return "UNKNOWN"
    if mode == "REVIEWER_CONFIRMED":
        return "PASS" if version.review_state == "REVIEWED_SUPPORTED" else "UNKNOWN"
    return "PASS"


async def evidence_results(
    session: AsyncSession, owner_party_id: UUID, version_ids: list[UUID]
) -> dict[UUID, dict[str, str]]:
    """Evaluate linked document versions for both verification modes, for matching (019).

    A version whose document another party owns counts as absent, so linking someone else's file proves nothing.

    Args:
        session (AsyncSession): The request's session.
        owner_party_id (UUID): The party whose evidence this is.
        version_ids (list[UUID]): Linked versions.

    Returns:
        dict[UUID, dict[str, str]]: ``PASS`` or ``UNKNOWN`` per mode, for each owned version.
    """
    versions = await SqlAlchemyDocumentRepository(session).owned_versions(owner_party_id, version_ids)
    return {
        version.id: {mode: evidence_status(version, mode) for mode in ("DOCUMENT_PRESENT", "REVIEWER_CONFIRMED")}
        for version in versions
    }


async def owned_version_details(
    session: AsyncSession, owner_party_id: UUID, version_ids: list[UUID]
) -> list[dict[str, Any]]:
    """Describe the party's own document versions among ``version_ids``, for preflight's file list (022).

    Args:
        session (AsyncSession): The request's session.
        owner_party_id (UUID): The owner.
        version_ids (list[UUID]): Candidate versions, such as those linked from invention facts.

    Returns:
        list[dict[str, Any]]: Document id, version id and number, title, file and review states; another party's
            versions are left out.
    """
    repository = SqlAlchemyDocumentRepository(session)
    details = []
    for version in await repository.owned_versions(owner_party_id, version_ids):
        document = await repository.document(version.document_id)
        assert document is not None  # noqa: S101 - versions cascade with their document
        details.append(
            {
                "document_id": str(document.id),
                "version_id": str(version.id),
                "version": version.number,
                "title": document.title,
                "file_state": version.file_state,
                "review_state": version.review_state,
            }
        )
    return sorted(details, key=lambda item: (item["title"], item["version"]))


async def owned_file(
    session: AsyncSession, owner_party_id: UUID, document_id: UUID, number: int
) -> dict[str, Any] | None:
    """Describe one available version of the party's own document, for revision answers and resubmission (025).

    Args:
        session (AsyncSession): The request's session.
        owner_party_id (UUID): The owner.
        document_id (UUID): The document.
        number (int): The version number.

    Returns:
        dict[str, Any] | None: Document id, version id and number, and title; None for another party's document,
            an unknown version, or one whose file is not available.
    """
    repository = SqlAlchemyDocumentRepository(session)
    document = await repository.document(document_id)
    if document is None or document.owner_party_id != owner_party_id:
        return None
    version = await repository.version(document_id=document_id, number=number)
    if version is None or version.file_state != "AVAILABLE":
        return None
    return {"document_id": str(document.id), "version_id": str(version.id), "version": number, "title": document.title}


class DocumentService:
    """Documents of the acting party, and downloads by grantees."""

    def __init__(self, session: AsyncSession, settings: Settings, storage: StorageAdapter | None = None) -> None:
        """Bind to the request.

        Args:
            session (AsyncSession): The request's session.
            settings (Settings): Settings.
            storage (StorageAdapter | None, optional): Byte storage. Defaults to the local folder.
        """
        self.session = session
        self.identity = IdentityService(session, settings)
        self.storage = storage or storage_for(settings)
        self.repository = SqlAlchemyDocumentRepository(session)

    async def _owned(self, principal: Principal, document_id: UUID) -> DocumentRecord:
        document = await self.repository.document(document_id)
        if document is None or document.owner_party_id != principal.active_party_id:
            raise NotFoundError()
        return document

    async def create_intent(self, principal: Principal, request: UploadIntentRequest) -> UploadIntentResponse:
        """Accept a declared file, or refuse its type or size before any byte is sent.

        Args:
            principal (Principal): Who is signed in.
            request (UploadIntentRequest): Title, kind, type and size.

        Returns:
            UploadIntentResponse: Where to send the bytes.

        Raises:
            FileTypeUnsupportedError: For any type but PDF, DOCX, PNG, JPEG or WEBP.
            FileTooLargeError: Over 20 MB for documents or 5 MB for images.
        """
        check_context(principal, request.acting_party_id)
        require(principal, Capability.EDIT_PORTFOLIO, principal.active_party_id)
        await self.identity.lock_active_account(principal.account_id)
        if request.media_type not in LIMITS:
            raise FileTypeUnsupportedError()
        if request.size_bytes > LIMITS[request.media_type]:
            raise FileTooLargeError(LIMIT_TEXT[request.media_type])
        if request.document_id is not None:
            await self._owned(principal, request.document_id)
        intent = await self.repository.add(
            UploadIntentRecord(
                owner_party_id=principal.active_party_id,
                document_id=request.document_id,
                title=request.title,
                kind=request.kind,
                media_type=request.media_type,
                size_bytes=request.size_bytes,
                created_by_account_id=principal.account_id,
                expires_at=clock.now() + INTENT_LIFETIME,
            )
        )
        return UploadIntentResponse(
            intent_id=intent.id,
            upload_url=f"/api/v1/documents/upload-intents/{intent.id}/content",
            max_bytes=request.size_bytes,
            expires_at=intent.expires_at,
        )

    async def receive(self, principal: Principal, intent_id: UUID, body: AsyncIterator[bytes]) -> UploadedResponse:
        """Store the bytes in quarantine and queue the scan. A signature that does not match is rejected at once.

        An interrupted transfer stores nothing and the intent can be retried until it expires.

        Args:
            principal (Principal): Who is signed in.
            intent_id (UUID): The intent.
            body (AsyncIterator[bytes]): The streamed request body.

        Returns:
            UploadedResponse: The new version and its file state.

        Raises:
            NotFoundError: For another party's intent.
            RequestInvalidError: When the intent expired or was used.
            FileTooLargeError: When more bytes arrive than were declared.
        """
        await self.identity.lock_active_account(principal.account_id)
        intent = await self.repository.intent(intent_id)
        if intent is None or intent.owner_party_id != principal.active_party_id:
            raise NotFoundError()
        if intent.completed_at is not None:
            raise RequestInvalidError(_INTENT_USED)
        if intent.expires_at <= clock.now():
            raise RequestInvalidError(_INTENT_EXPIRED)
        key = uuid4().hex
        try:
            stored = await self.storage.write(key, body, intent.size_bytes)
        except TooLargeError as error:
            raise FileTooLargeError(LIMIT_TEXT[intent.media_type]) from error
        async with self.storage.materialize(key, intent.size_bytes) as path:
            matches = await anyio.to_thread.run_sync(sniff, path) == intent.media_type
        document = (
            await self.repository.document(intent.document_id)
            if intent.document_id
            else await self.repository.add(
                DocumentRecord(owner_party_id=intent.owner_party_id, kind=intent.kind, title=intent.title)
            )
        )
        assert document is not None  # noqa: S101 - intents cascade with their document
        number = await self.repository.next_number(document.id)
        version = await self.repository.add(
            DocumentVersionRecord(
                document_id=document.id,
                number=number,
                storage_key=key,
                sha256=stored.sha256,
                media_type=intent.media_type,
                size_bytes=stored.size_bytes,
                file_state="QUARANTINED" if matches else "REJECTED",
            )
        )
        await self.repository.supersede_reviews(document.id, number)
        intent.completed_at = clock.now()
        if matches:
            await enqueue_job(
                self.session, "documents.scan", {"version_id": str(version.id)}, actor_party_id=document.owner_party_id
            )
        await record_audit(
            self.session,
            action="document.uploaded",
            subject_type="document",
            subject_id=str(document.id),
            actor_account_id=principal.account_id,
            actor_party_id=principal.active_party_id,
            detail={"number": number, "file_state": version.file_state},
        )
        return UploadedResponse(
            document_id=document.id, version_id=version.id, number=number, file_state=version.file_state
        )

    async def list_mine(self, principal: Principal) -> list[DocumentResponse]:
        """List the acting party's documents with every version and grant.

        Args:
            principal (Principal): Who is signed in.

        Returns:
            list[DocumentResponse]: Documents.
        """
        return [
            await self._view(document) for document in await self.repository.documents_of(principal.active_party_id)
        ]

    async def prepare_party_erasure(self, party_id: UUID) -> None:
        """Revoke retrieval and prevent queued scans from restoring availability."""
        await self.repository.prepare_party_erasure(party_id, clock.now())

    async def erase_party_bytes(self, party_id: UUID) -> None:
        """Erase the prepared files before the worker may mark their category removed."""
        for version in await self.repository.pending_erase_versions(party_id):
            await self.storage.delete(version.storage_key)
            version.file_state = "ERASED"
            version.extracted_characters = None

    async def export_personal_metadata(self, principal: Principal) -> list[PersonalDocumentMetadata]:
        """Return only metadata for documents owned by the requester's personal party."""
        documents = await self.repository.documents_of(principal.personal_party_id)
        return [PersonalDocumentMetadata.model_validate(item, from_attributes=True) for item in documents]

    async def owner_view(self, principal: Principal, document_id: UUID) -> DocumentResponse:
        """Read one document as its owner.

        Args:
            principal (Principal): Who is signed in.
            document_id (UUID): The document.

        Returns:
            DocumentResponse: Versions, states and grants.

        Raises:
            NotFoundError: For anyone else, with no title.
        """
        return await self._view(await self._owned(principal, document_id))

    async def _view(self, document: DocumentRecord) -> DocumentResponse:
        grants = await self.repository.grants_of(document.id)
        names = await party_names(self.session, [grant.grantee_party_id for grant, _, _ in grants])
        return DocumentResponse(
            id=document.id,
            title=document.title,
            kind=document.kind,
            versions=[
                DocumentVersionResponse.model_validate(version, from_attributes=True)
                for version in await self.repository.versions(document.id)
            ],
            grants=[
                GrantResponse(
                    id=grant.id,
                    version=number,
                    grantee_party_id=grant.grantee_party_id,
                    grantee_name=names.get(grant.grantee_party_id, ""),
                    purpose=grant.purpose,
                    revoked_at=grant.revoked_at,
                    downloads=downloads,
                )
                for grant, number, downloads in grants
            ],
        )

    async def grant(
        self,
        principal: Principal,
        document_id: UUID,
        request: GrantRequest,
        capability: Capability = Capability.EDIT_PORTFOLIO,
    ) -> GrantResponse:
        """Share one version with one party for one purpose; repeating it returns the same grant.

        Args:
            principal (Principal): Who is signed in.
            document_id (UUID): The document.
            request (GrantRequest): Version, grantee and purpose.
            capability (Capability, optional): What the member needs; a submission shares with ``submit_pitch``.
                Defaults to ``edit_portfolio``.

        Returns:
            GrantResponse: The grant.

        Raises:
            NotFoundError: When the document, version or grantee does not exist for this owner.
        """
        check_context(principal, request.acting_party_id)
        document = await self._owned(principal, document_id)
        require(principal, capability, document.owner_party_id)
        version = await self.repository.version(document_id=document.id, number=request.version)
        names = await party_names(self.session, [request.grantee_party_id])
        if version is None or request.grantee_party_id not in names:
            raise NotFoundError()
        active = [
            grant
            for grant in await self.repository.grants_for(version.id, request.grantee_party_id)
            if grant.revoked_at is None and grant.purpose == request.purpose
        ]
        grant = (
            active[0]
            if active
            else await self.repository.add(
                DocumentGrantRecord(
                    document_version_id=version.id,
                    grantee_party_id=request.grantee_party_id,
                    purpose=request.purpose,
                    pitch_id=request.pitch_id,
                    granted_by_account_id=principal.account_id,
                )
            )
        )
        await record_audit(
            self.session,
            action="document.granted",
            subject_type="document_grant",
            subject_id=str(grant.id),
            actor_account_id=principal.account_id,
            actor_party_id=principal.active_party_id,
            detail={"version": version.number},
        )
        return GrantResponse(
            id=grant.id,
            version=version.number,
            grantee_party_id=grant.grantee_party_id,
            grantee_name=names[request.grantee_party_id],
            purpose=grant.purpose,
            revoked_at=grant.revoked_at,
            downloads=await self.repository.downloads_of(grant.id),
        )

    async def revoke(self, principal: Principal, grant_id: UUID, acting_party_id: UUID) -> RevokedResponse:
        """Block every new download under a grant, and say plainly that delivered copies stay delivered (AC65).

        Args:
            principal (Principal): Who is signed in, as the owner.
            grant_id (UUID): The grant.
            acting_party_id (UUID): The party the client acts as.

        Returns:
            RevokedResponse: How many copies already left.

        Raises:
            NotFoundError: When the grant is not the acting party's.
        """
        check_context(principal, acting_party_id)
        grant = await self.repository.grant(grant_id)
        version = await self.repository.version(version_id=grant.document_version_id) if grant else None
        document = await self.repository.document(version.document_id) if version else None
        if grant is None or document is None or document.owner_party_id != principal.active_party_id:
            raise NotFoundError()
        require(principal, Capability.EDIT_PORTFOLIO, document.owner_party_id)
        if grant.revoked_at is None:
            grant.revoked_at = clock.now()
            await record_audit(
                self.session,
                action="document.grant_revoked",
                subject_type="document_grant",
                subject_id=str(grant.id),
                actor_account_id=principal.account_id,
                actor_party_id=principal.active_party_id,
            )
        return RevokedResponse(
            revoked=True, copies_already_delivered=await self.repository.downloads_of(grant.id), message=REVOKED_MESSAGE
        )

    async def authorize_download(
        self, principal: Principal, document_id: UUID, number: int, byte_range: str | None
    ) -> Download:
        """Authorize and record a direct version download, including range requests."""
        file = await self.resolve_download(principal, document_id, number)
        await self.record_delivery(principal, file, byte_range)
        return file

    async def resolve_download(
        self, principal: Principal, document_id: UUID, number: int, *, required_grant_id: UUID | None = None
    ) -> Download:
        """Check one exact version and applicable live grant without recording a delivered copy."""
        document = await self.repository.document(document_id)
        version = await self.repository.version(document_id=document_id, number=number) if document else None
        if document is None or version is None:
            raise NotFoundError()
        grant_id = None
        if document.owner_party_id != principal.active_party_id:
            grants = await self.repository.grants_for(version.id, principal.active_party_id)
            if required_grant_id is not None:
                grants = [grant for grant in grants if grant.id == required_grant_id]
            if not grants:
                raise NotFoundError()
            now = clock.now()
            valid = next(
                (
                    grant
                    for grant in grants
                    if grant.revoked_at is None and (grant.expires_at is None or grant.expires_at > now)
                ),
                None,
            )
            if valid is None:
                raise GrantRevokedError()
            grant_id = valid.id
        elif required_grant_id is not None:
            raise NotFoundError()
        if version.file_state != "AVAILABLE":
            raise FileNotAvailableError()
        return self._download(version, grant_id)

    async def require_version(self, version_id: UUID) -> None:
        """Validate a local administrator's exact document version reference."""
        if await self.repository.version(version_id=version_id) is None:
            raise NotFoundError()

    async def case_download(
        self,
        principal: Principal,
        case_id: UUID,
        document_id: UUID,
        number: int,
        grant_for_version: Callable[[UUID], Awaitable[UUID | None]],
    ) -> Download:
        """Check a case-specific authorization on each fetch before exposing protected bytes."""
        version = await self.repository.version(document_id=document_id, number=number)
        grant_id = await grant_for_version(version.id) if version is not None else None
        try:
            require_case_file(granted=grant_id is not None)
            if version is None or version.file_state != "AVAILABLE":
                raise FileNotAvailableError()
        except (ForbiddenError, FileNotAvailableError) as denial:
            # A refusal rolls back the request session. The audit evidence must survive it.
            try:
                async with get_session_factory()() as audit_session, audit_session.begin():
                    await record_audit(
                        audit_session,
                        action="report.file_denied",
                        subject_type="report",
                        subject_id=str(case_id),
                        actor_account_id=principal.account_id,
                    )
            except Exception:  # noqa: BLE001 - a secondary audit failure cannot mask the original denial
                emergency_log(denial.reference_id, denial.code)
            raise
        await record_audit(
            self.session,
            action="report.file_downloaded",
            subject_type="report",
            subject_id=str(case_id),
            actor_account_id=principal.account_id,
            detail={"grant_id": str(grant_id), "version_id": str(version.id)},
        )
        return self._download(version)

    @staticmethod
    def _download(version: DocumentVersionRecord, grant_id: UUID | None = None) -> Download:
        extension = {"application/pdf": "pdf", "image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}.get(
            version.media_type, "docx"
        )
        return Download(
            storage_key=version.storage_key,
            media_type=version.media_type,
            size_bytes=version.size_bytes,
            filename=f"dokumen-v{version.number}.{extension}",
            version_id=version.id,
            grant_id=grant_id,
        )

    async def record_delivery(self, principal: Principal, file: Download, byte_range: str | None = None) -> None:
        """Record one delivered copy for grant owners' revocation history."""
        if file.grant_id is not None:
            await self.repository.add(
                DownloadEventRecord(
                    grant_id=file.grant_id,
                    actor_party_id=principal.active_party_id,
                    range=(byte_range or None) and byte_range[:64],
                )
            )
