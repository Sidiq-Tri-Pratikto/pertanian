"""Queued exports whose requester and exact resource dependencies stay live through delivery."""

import json
from base64 import b64encode
from collections.abc import AsyncIterator
from typing import Any
from uuid import UUID

from anyio import to_thread
from sqlalchemy.ext.asyncio import AsyncSession

from app.access.service.policy import check_context, require_account
from app.core import clock
from app.core.errors.base import AppError, ForbiddenError, NotFoundError
from app.core.errors.public import public_error_for_code
from app.core.settings import get_settings
from app.documents.service.service import (
    DocumentService,
    Download,
    FileNotAvailableError,
    FileTooLargeError,
    GrantRevokedError,
)
from app.documents.service.storage_service import StorageAdapter, storage_for
from app.identity.model.models import Principal
from app.platform.service.outbox import enqueue_job
from app.portability.model.schema import CreateExportRequest, ExportStatus, ExportStatusResponse, InventionSelection
from app.portability.repository.sqlalchemy.models import ExportJobRecord
from app.portability.repository.sqlalchemy.repository import PortabilityRepository
from app.portability.service.common import (
    actor_membership,
    announce,
    artifact_key,
    byte_chunks,
    live_actor,
    read_bounded,
)
from app.portability.service.file_format import MAX_BYTES, PORTABLE_FIELDS, STAGING_LIFETIME
from app.portfolio.model.schema import InventionVersionResponse
from app.portfolio.service.service import PortfolioService

_ACCESS_ERRORS = (NotFoundError, ForbiddenError, FileNotAvailableError, GrantRevokedError)
_EXPORT_PROVENANCE = {"source": "TemuRiset"}


class ExportService:
    """Authorize explicit selections and never hand the browser a private storage URL."""

    def __init__(self, session: AsyncSession, storage: StorageAdapter | None = None) -> None:
        self.session = session
        self.repository = PortabilityRepository(session)
        self.storage = storage or storage_for(get_settings())
        self.documents = DocumentService(session, get_settings(), self.storage)
        self.portfolio = PortfolioService(session)

    async def start(self, actor: Principal, body: CreateExportRequest) -> ExportStatusResponse:
        """Pin current resource versions and applicable document grants before enqueuing."""
        check_context(actor, body.acting_party_id)
        membership_id = await actor_membership(self.session, actor)
        dependencies = []
        for selection in body.selections:
            pin = selection.model_dump(mode="json")
            if isinstance(selection, InventionSelection):
                number, draft_version, _ = await self._invention(actor, pin)
                pin.update(version_number=number, draft_version=draft_version)
            else:
                file = await self.documents.resolve_download(actor, selection.document_id, selection.version)
                pin.update(version_id=str(file.version_id), grant_id=str(file.grant_id) if file.grant_id else None)
            dependencies.append(pin)

        job = ExportJobRecord(
            party_id=actor.active_party_id,
            account_id=actor.account_id,
            session_id=actor.session_id,
            membership_id=membership_id,
            expires_at=clock.now() + STAGING_LIFETIME,
            dependencies=dependencies,
        )
        await self.repository.add(job)
        job.job_id = await enqueue_job(
            self.session,
            "portability.generate_export",
            {"id": str(job.id)},
            actor_party_id=job.party_id,
        )
        await enqueue_job(self.session, "portability.cleanup_export", {"id": str(job.id)}, run_after=job.expires_at)
        await announce(self.session, job, "export", "requested")
        return await self._status(job)

    async def _status(self, job: ExportJobRecord) -> ExportStatusResponse:
        failures = await self.repository.job_failures([job.job_id] if job.job_id else [])
        error_code = None
        if job.expired:
            status: ExportStatus = "EXPIRED"
        elif job.size_bytes is not None:
            status = "SUCCEEDED"
        elif job.job_id in failures:
            status = "FAILED"
            error_code = public_error_for_code(failures[job.job_id] or "").code
        else:
            status = "PENDING"
        return ExportStatusResponse(id=job.id, status=status, expires_at=job.expires_at, error_code=error_code)

    async def _visible(self, actor: Principal, export_id: UUID) -> tuple[ExportJobRecord, Principal] | AppError:
        job = await self.repository.export_job(export_id, lock=True)
        if job is None:
            raise NotFoundError()
        require_account(actor, job.account_id)
        try:
            live = await live_actor(self.session, job)
        except _ACCESS_ERRORS as error:
            await self._expire(job)
            return error
        if job.party_id != actor.active_party_id:
            raise NotFoundError()
        if job.expires_at <= clock.now():
            await self._expire(job)
        return job, live

    async def read(self, actor: Principal, export_id: UUID) -> ExportStatusResponse | AppError:
        """Check the requester and current dependencies before returning status."""
        result = await self._visible(actor, export_id)
        if isinstance(result, AppError):
            return result
        job, live = result
        if not job.expired:
            try:
                await self._dependencies(live, job)
            except _ACCESS_ERRORS:
                await self._expire(job)
        return await self._status(job)

    async def download(self, actor: Principal, export_id: UUID) -> AsyncIterator[bytes] | AppError:
        """Recheck current authorization immediately before gateway delivery."""
        result = await self._visible(actor, export_id)
        if isinstance(result, AppError):
            return result
        job, live = result
        if job.expired:
            return FileNotAvailableError(
                "Hasil ekspor sudah kedaluwarsa. Siapkan ekspor baru dengan akses yang berlaku."
            )
        if job.size_bytes is None:
            return FileNotAvailableError("Hasil ekspor belum tersedia. Periksa status pekerjaan ekspor.")
        try:
            await self._dependencies(live, job)
            payload = await read_bounded(
                self.storage.read(artifact_key("export", job.id), 0, job.size_bytes - 1), job.size_bytes
            )
            if len(payload) != job.size_bytes or job.expires_at <= clock.now():
                raise FileNotAvailableError("Hasil ekspor sudah tidak tersedia. Siapkan ekspor baru.")
            live = await live_actor(self.session, job)
            files = await self._dependencies(live, job)
        except (FileNotFoundError, *_ACCESS_ERRORS) as error:
            await self._expire(job)
            if isinstance(error, AppError):
                return error
            return FileNotAvailableError("Berkas hasil ekspor tidak tersedia. Siapkan ekspor baru.")
        for file in files.values():
            await self.documents.record_delivery(live, file)
        await announce(self.session, job, "export", "downloaded")
        return byte_chunks(payload)

    async def _invention(
        self, actor: Principal, dependency: dict[str, Any]
    ) -> tuple[int, int | None, InventionVersionResponse]:
        current = await self.portfolio.owner_view(actor, UUID(dependency["invention_id"]))
        use_draft = dependency["version"] == "DRAFT"
        data = current.draft if use_draft else current.published
        if data is None:
            raise NotFoundError()
        draft_version = current.version if use_draft else None
        if "version_number" in dependency and (
            data.number != dependency["version_number"] or draft_version != dependency["draft_version"]
        ):
            raise FileNotAvailableError("Versi yang dipilih sudah berubah. Pilih versi terbaru untuk ekspor baru.")
        return data.number, draft_version, data

    async def _dependencies(self, actor: Principal, job: ExportJobRecord) -> dict[int, Download]:
        files = {}
        for index, dependency in enumerate(job.dependencies):
            if dependency["kind"] == "INVENTION":
                await self._invention(actor, dependency)
                continue
            grant = UUID(dependency["grant_id"]) if dependency["grant_id"] else None
            file = await self.documents.resolve_download(
                actor, UUID(dependency["document_id"]), dependency["version"], required_grant_id=grant
            )
            if str(file.version_id) != dependency["version_id"] or file.grant_id != grant:
                raise NotFoundError()
            files[index] = file
        return files

    async def generate(self, export_id: UUID) -> None:
        """Create bounded bytes only after rechecking all pinned dependencies."""
        job = await self.repository.export_job(export_id, lock=True)
        if job is None or job.expired or job.size_bytes is not None:
            return
        if job.expires_at <= clock.now():
            await self._expire(job)
            return
        try:
            actor = await live_actor(self.session, job)
            files = await self._dependencies(actor, job)
            payload = await self._package(actor, job, files)
            # Reading storage can take time. Check the same pins again before publishing a result.
            await self._dependencies(await live_actor(self.session, job), job)
        except _ACCESS_ERRORS:
            await self._expire(job)
            return
        if job.expires_at <= clock.now():
            await self._expire(job)
            return
        written = await self.storage.write(artifact_key("export", job.id), byte_chunks(payload), MAX_BYTES)
        job.size_bytes = written.size_bytes
        await announce(self.session, job, "export", "generated")

    async def _package(self, actor: Principal, job: ExportJobRecord, files: dict[int, Download]) -> bytes:
        inventions, documents = [], []
        document_bytes = 0
        for index, dependency in enumerate(job.dependencies):
            if dependency["kind"] == "INVENTION":
                _, _, version = await self._invention(actor, dependency)
                inventions.append(_portable_invention(dependency, version))
                continue
            file = files[index]
            document_bytes += 4 * ((file.size_bytes + 2) // 3)
            if document_bytes > MAX_BYTES:
                raise FileTooLargeError("20 MiB")
            try:
                raw = await read_bounded(self.storage.read(file.storage_key, 0, file.size_bytes - 1), file.size_bytes)
            except FileNotFoundError:
                raise FileNotAvailableError() from None
            if len(raw) != file.size_bytes:
                raise FileNotAvailableError()
            encoded = await to_thread.run_sync(b64encode, raw)
            documents.append(
                {
                    "document_id": dependency["document_id"],
                    "version": dependency["version"],
                    "media_type": file.media_type,
                    "content_base64": encoded.decode("ascii"),
                }
            )
        payload = await to_thread.run_sync(
            _encode,
            {
                "schema_version": 1,
                "external_system": "temuriset",
                "provenance": _EXPORT_PROVENANCE,
                "inventions": inventions,
                "documents": documents,
            },
        )
        if len(payload) > MAX_BYTES:
            raise FileTooLargeError("20 MiB")
        return payload

    async def _expire(self, job: ExportJobRecord) -> None:
        if not job.expired:
            job.expired = True
            await enqueue_job(self.session, "portability.cleanup_export", {"id": str(job.id)})
            await announce(self.session, job, "export", "expired")

    async def cleanup(self, export_id: UUID) -> None:
        """Delete bytes after live denial or the scheduled expiry, including orphaned artifacts."""
        job = await self.repository.export_job(export_id, lock=True)
        await self.storage.delete(artifact_key("export", export_id))
        if job is not None and not job.expired:
            job.expired = True
            await announce(self.session, job, "export", "expired")


def _portable_invention(dependency: dict[str, Any], version: InventionVersionResponse) -> dict[str, Any]:
    selected = PORTABLE_FIELDS | ({"private_notes"} if dependency["include_private_notes"] else set())
    data = version.model_dump(mode="json", include=selected)
    data["facts"] = [
        fact.model_dump(mode="json", exclude={"provenance", "document_version_id"}) for fact in version.facts
    ]
    return {
        "external_id": f"{dependency['invention_id']}-{dependency['version'].lower()}",
        "provenance": _EXPORT_PROVENANCE,
        "fields": data,
    }


def _encode(value: dict[str, Any]) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
