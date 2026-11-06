"""Private upload, staged validation and preview, and authorized draft upserts."""

import hashlib
from typing import Any, Literal
from uuid import UUID

from anyio import to_thread
from sqlalchemy.ext.asyncio import AsyncSession

from app.access.service.policy import check_context, require_account
from app.core import clock
from app.core.errors.base import ConflictError, InvalidTransitionError, NotFoundError, RequestInvalidError
from app.core.errors.public import public_error_for_code
from app.core.settings import get_settings
from app.documents.service.service import FileNotAvailableError
from app.documents.service.storage_service import StorageAdapter, storage_for
from app.identity.model.models import Principal
from app.intake.model.schema import PartnerProfileResponse
from app.intake.service.service import IntakeService
from app.platform.service.outbox import enqueue_job
from app.platform.service.versions import StaleVersionError, check_expected
from app.portability.model.schema import (
    ImportActionRequest,
    ImportStatusResponse,
    PreviewRow,
    StageProgress,
    StageStatus,
    StartImportRequest,
)
from app.portability.repository.sqlalchemy.models import ExternalReferenceRecord, ImportRowRecord, ImportRunRecord
from app.portability.repository.sqlalchemy.repository import PortabilityRepository
from app.portability.service.common import (
    actor_membership,
    announce,
    artifact_key,
    byte_chunks,
    live_actor,
    read_bounded,
)
from app.portability.service.file_format import MAX_BYTES, STAGING_LIFETIME, InventionRow, PartnerRow, parse_file
from app.portability.service.preview import compare_draft
from app.portfolio.model.schema import CreateInventionRequest, DraftRequest, InventionResponse
from app.portfolio.service.service import PortfolioService

BATCH_SIZE = 50
Stage = Literal["validation", "preview", "apply"]


class ImportService:
    """Manage an import whose normalized rows and preview expire together."""

    def __init__(self, session: AsyncSession, storage: StorageAdapter | None = None) -> None:
        self.session = session
        self.repository = PortabilityRepository(session)
        self.storage = storage or storage_for(get_settings())
        self.portfolio = PortfolioService(session)
        self.intake = IntakeService(session)

    async def start(
        self, actor: Principal, body: StartImportRequest, upload: bytes, sha256: str
    ) -> ImportStatusResponse:
        """Stage bytes in private storage and queue validation."""
        check_context(actor, body.acting_party_id)
        membership_id = await actor_membership(self.session, actor)
        run = ImportRunRecord(
            party_id=actor.active_party_id,
            account_id=actor.account_id,
            session_id=actor.session_id,
            membership_id=membership_id,
            expires_at=clock.now() + STAGING_LIFETIME,
            sha256=sha256,
            map_private_notes=body.map_private_notes,
        )
        await self.repository.add(run)
        await self._queue(run, "validation")
        await enqueue_job(
            self.session,
            "portability.cleanup_import",
            {"id": str(run.id)},
            run_after=run.expires_at,
        )
        await announce(self.session, run, "import", "staged")
        await self.storage.write(artifact_key("import", run.id), byte_chunks(upload), MAX_BYTES)
        return await self._status(run)

    async def read(self, actor: Principal, run_id: UUID, offset: int, limit: int) -> ImportStatusResponse:
        """Read an authorized run and at most one page of its completed preview."""
        run = await self._owned(actor, run_id)
        status = await self._status(run)
        if status.preview.status == "SUCCEEDED":
            rows = await self.repository.import_rows(run.id, offset, limit)
            status.rows = [
                PreviewRow.model_validate({**(row.comparison or {}), "outcome": row.outcome}) for row in rows
            ]
            if offset + limit < run.total:
                status.next_offset = offset + limit
        return status

    async def apply(self, actor: Principal, run_id: UUID, body: ImportActionRequest) -> ImportStatusResponse:
        """Queue apply only when the requester acknowledges the current completed preview."""
        check_context(actor, body.acting_party_id)
        run = await self._owned(actor, run_id, lock=True)
        check_expected(run.version, body.expected_version)
        status = await self._status(run)
        if status.preview.status != "SUCCEEDED" or run.apply_job_id is not None or run.cancelled_stage:
            raise InvalidTransitionError()
        run.version += 1
        await self._queue(run, "apply")
        await announce(self.session, run, "import", "apply_requested")
        return await self._status(run)

    async def cancel(self, actor: Principal, run_id: UUID, body: ImportActionRequest) -> ImportStatusResponse:
        """Stop the next unit of work and return the committed count."""
        check_context(actor, body.acting_party_id)
        run = await self._owned(actor, run_id, lock=True)
        check_expected(run.version, body.expected_version)
        status = await self._status(run)
        if run.cancelled_stage or self._expired(run):
            raise InvalidTransitionError()
        if status.validation.status == "PENDING":
            run.cancelled_stage = "validation"
        elif status.preview.status == "PENDING":
            run.cancelled_stage = "preview"
        elif status.preview.status == "SUCCEEDED" and status.apply.status in {"NOT_STARTED", "PENDING"}:
            run.cancelled_stage = "apply"
        else:
            raise InvalidTransitionError()
        run.version += 1
        await announce(self.session, run, "import", "cancelled")
        return await self._status(run)

    async def _owned(self, actor: Principal, run_id: UUID, *, lock: bool = False) -> ImportRunRecord:
        run = await self.repository.import_run(run_id, lock=lock)
        if run is None or run.party_id != actor.active_party_id:
            raise NotFoundError()
        require_account(actor, run.account_id)
        await live_actor(self.session, run)
        return run

    async def _status(self, run: ImportRunRecord) -> ImportStatusResponse:
        failures = await self.repository.job_failures(
            [job for job in (run.validation_job_id, run.preview_job_id, run.apply_job_id) if job is not None]
        )

        def stage(name: Stage, job: UUID | None, processed: int, done: bool) -> StageProgress:
            error_code = None
            if self._expired(run):
                status: StageStatus = "EXPIRED"
            elif run.cancelled_stage == name:
                status = "CANCELLED"
            elif done:
                status = "SUCCEEDED"
            elif job in failures:
                status = "FAILED"
                error_code = public_error_for_code(failures[job] or "").code
            else:
                status = "PENDING" if job is not None else "NOT_STARTED"
            return StageProgress(status=status, processed=processed, error_code=error_code)

        return ImportStatusResponse(
            id=run.id,
            version=run.version,
            total=run.total,
            committed=run.committed,
            skipped=run.skipped,
            expires_at=run.expires_at,
            validation=stage("validation", run.validation_job_id, run.total, run.external_system is not None),
            preview=stage("preview", run.preview_job_id, run.previewed, run.total > 0 and run.previewed == run.total),
            apply=stage("apply", run.apply_job_id, run.applied, run.total > 0 and run.applied == run.total),
        )

    @staticmethod
    def _expired(run: ImportRunRecord) -> bool:
        return run.expired or run.expires_at <= clock.now()

    async def _queue(self, run: ImportRunRecord, stage: Stage) -> None:
        job_id = await enqueue_job(
            self.session,
            f"portability.import_{stage}",
            {"id": str(run.id)},
            actor_party_id=run.party_id,
        )
        setattr(run, f"{stage}_job_id", job_id)

    async def _working(self, run_id: UUID) -> tuple[ImportRunRecord, Principal] | None:
        run = await self.repository.import_run(run_id, lock=True)
        if run is None or self._expired(run) or run.cancelled_stage:
            return None
        return run, await live_actor(self.session, run)

    async def validate_file(self, run_id: UUID) -> None:
        """Validate the pinned bytes, normalize eligible fields and queue a distinct preview job."""
        working = await self._working(run_id)
        if working is None:
            return
        run, _ = working
        if run.external_system is not None:
            return
        try:
            raw = await read_bounded(self.storage.read(artifact_key("import", run.id)), MAX_BYTES)
        except FileNotFoundError:
            raise FileNotAvailableError(
                "Berkas unggahan sudah tidak tersedia. Unggah kembali untuk memulai impor."
            ) from None
        if hashlib.sha256(raw).hexdigest() != run.sha256:
            raise RequestInvalidError("Berkas unggahan berubah. Unggah berkas lagi untuk memulai impor.")
        parsed = await to_thread.run_sync(parse_file, raw)
        normalized = [
            _normalize(row, parsed.provenance.model_dump(mode="json"), map_private=run.map_private_notes)
            for row in parsed.inventions
        ]
        if parsed.partner_profile is not None:
            self.intake.validate_directory_profile(parsed.partner_profile.fields)
            normalized.append(_normalize(parsed.partner_profile, parsed.provenance.model_dump(mode="json")))
        normalized.sort(key=lambda row: row["external_id"])
        await self.repository.add_import_rows(run.id, normalized)
        run.external_system, run.total = parsed.external_system, len(normalized)
        await self._queue(run, "preview")
        await announce(self.session, run, "import", "validated")

    async def preview_batch(self, run_id: UUID) -> None:
        """Compare one checkpoint against destination versions without writing inventions."""
        working = await self._working(run_id)
        if working is None:
            return
        run, actor = working
        rows = await self.repository.import_rows(run.id, run.previewed, BATCH_SIZE)
        for record in rows:
            reference = await self._reference(run, record)
            preview, pin = await self._compare(actor, record, reference)
            record.comparison = preview.model_dump(exclude={"outcome"}) | pin
        run.previewed += len(rows)
        if run.previewed < run.total:
            await self._queue(run, "preview")
        elif rows:
            run.version += 1
            await announce(self.session, run, "import", "previewed")

    async def apply_batch(self, run_id: UUID) -> None:
        """Write one checkpoint atomically, retaining the progress if later work is cancelled."""
        working = await self._working(run_id)
        if working is None:
            return
        run, actor = working
        if run.previewed != run.total or run.apply_job_id is None:
            return
        rows = await self.repository.import_rows(run.id, run.applied, BATCH_SIZE)
        for record in rows:
            record.outcome = await self._apply_row(actor, run, record)
            run.committed += int(record.outcome == "COMMITTED")
            run.skipped += int(record.outcome == "SKIPPED")
        run.applied += len(rows)
        if run.applied < run.total:
            await self._queue(run, "apply")
        elif rows:
            run.version += 1
            await announce(self.session, run, "import", "applied")

    async def _reference(
        self, run: ImportRunRecord, record: ImportRowRecord, *, lock: bool = False
    ) -> ExternalReferenceRecord | None:
        if run.external_system is None:
            raise InvalidTransitionError()
        return await self.repository.reference(
            run.party_id, run.external_system, record.payload["external_id"], lock=lock
        )

    async def _profile(self, party_id: UUID) -> PartnerProfileResponse | None:
        try:
            return await self.intake.read_profile(party_id)
        except NotFoundError:
            return None

    async def _current(self, actor: Principal, reference: ExternalReferenceRecord | None) -> InventionResponse | None:
        if reference is None or reference.invention_id is None:
            return None
        try:
            return await self.portfolio.owner_view(actor, reference.invention_id)
        except NotFoundError:
            return None

    async def _compare(
        self, actor: Principal, record: ImportRowRecord, reference: ExternalReferenceRecord | None
    ) -> tuple[PreviewRow, dict[str, Any]]:
        payload = record.payload
        resource = payload["resource"]
        view = PreviewRow(
            external_id=payload["external_id"],
            resource=resource,
            action="CREATE",
            mapped_fields=sorted(payload["fields"]),
            skipped_fields=payload["skipped_fields"],
            conflicts=[],
        )
        pin = {
            "reference_id": str(reference.id) if reference else None,
            "reference_version": reference.version if reference else None,
        }
        if resource == "PARTNER_PROFILE":
            profile = await self._profile(actor.active_party_id)
            pin["destination_version"] = profile.version if profile else None
            if profile is None:
                if reference is not None:
                    view.conflicts = ["destination"]
            elif (
                reference is None
                or reference.invention_id is not None
                or profile.availability.source == "OWNER_CONFIRMED"
            ):
                view.conflicts = ["partner_profile"]
            else:
                view.action = "UNCHANGED"
        else:
            current = await self._current(actor, reference)
            pin["destination_version"] = current.version if current else None
            if reference is not None and current is None:
                view.conflicts = ["destination"]
            else:
                compared = compare_draft(_invention(payload), current)
                view.conflicts = compared.conflicts
                if current is not None and reference is not None:
                    changed = compared.changes or reference.source != payload["source"]
                    view.action = "UPDATE" if changed else "UNCHANGED"
        if view.conflicts:
            view.action = "CONFLICT"
        return view, pin

    async def _apply_row(
        self, actor: Principal, run: ImportRunRecord, record: ImportRowRecord
    ) -> Literal["COMMITTED", "SKIPPED", "UNCHANGED"]:
        preview = record.comparison or {}
        if preview.get("action") == "CONFLICT":
            return "SKIPPED"
        reference = await self._reference(run, record, lock=True)
        fresh, pin = await self._compare(actor, record, reference)
        if fresh.conflicts or any(preview.get(key) != value for key, value in pin.items()):
            record.comparison = preview | {"conflicts": fresh.conflicts or ["destination"]}
            return "SKIPPED"
        if fresh.action == "UNCHANGED":
            return "UNCHANGED"

        try:
            async with self.session.begin_nested():
                payload = record.payload
                if fresh.resource == "PARTNER_PROFILE":
                    profile = PartnerRow.model_validate(_source_row(payload))
                    await self.intake.record_directory_profile(run.party_id, profile.fields)
                    invention_id = None
                else:
                    current = await self._current(actor, reference)
                    changes = compare_draft(_invention(payload), current)
                    if changes.conflicts or (current is not None and current.version != pin["destination_version"]):
                        raise ConflictError()
                    invention = current or await self.portfolio.create(
                        actor, CreateInventionRequest(acting_party_id=run.party_id)
                    )
                    baseline = invention.draft or invention.published
                    if current is None or changes.changes:
                        fields = baseline.model_dump() if baseline else {}
                        await self.portfolio.save_draft(
                            actor,
                            invention.id,
                            DraftRequest.model_validate(
                                fields
                                | changes.changes
                                | {
                                    "acting_party_id": run.party_id,
                                    "expected_version": invention.version,
                                }
                            ),
                        )
                    invention_id = invention.id
                if reference is None:
                    await self.repository.add(
                        ExternalReferenceRecord(
                            party_id=run.party_id,
                            external_system=run.external_system,
                            external_id=payload["external_id"],
                            invention_id=invention_id,
                            source=payload["source"],
                        )
                    )
                elif reference.source != payload["source"]:
                    reference.source = payload["source"]
                    reference.version += 1
        except (StaleVersionError, ConflictError):
            record.comparison = preview | {"conflicts": ["destination"]}
            return "SKIPPED"
        return "COMMITTED"

    async def cleanup(self, run_id: UUID) -> None:
        """Delete expired temporary bytes and normalized private rows."""
        run = await self.repository.import_run(run_id, lock=True)
        await self.storage.delete(artifact_key("import", run_id))
        if run is not None:
            run.expired = True
            await self.repository.purge_rows(run.id)


def _normalize(
    row: InventionRow | PartnerRow, file_source: dict[str, Any], *, map_private: bool = False
) -> dict[str, Any]:
    source: dict[str, Any] = {"file_provenance": file_source, "provenance": row.provenance.model_dump(mode="json")}
    fields = row.fields.model_dump(mode="json", exclude_unset=True)
    skipped = []
    if isinstance(row, InventionRow):
        if "private_notes" in fields and not map_private:
            fields.pop("private_notes")
            skipped.append("private_notes")
        source.update(
            {
                "rights_claims": [claim.model_dump(mode="json") for claim in row.rights_claims],
                "relationship_assertions": [item.model_dump(mode="json") for item in row.relationship_assertions],
            }
        )
    else:
        source["organization_name"] = row.organization_name
    return {
        "external_id": row.external_id,
        "fields": fields,
        "source": source,
        "skipped_fields": skipped,
        "resource": "INVENTION" if isinstance(row, InventionRow) else "PARTNER_PROFILE",
    }


def _source_row(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "external_id": payload["external_id"],
        "fields": payload["fields"],
        "provenance": payload["source"]["provenance"],
    }


def _invention(payload: dict[str, Any]) -> InventionRow:
    return InventionRow.model_validate(
        _source_row(payload)
        | {
            "rights_claims": payload["source"]["rights_claims"],
            "relationship_assertions": payload["source"]["relationship_assertions"],
        }
    )
