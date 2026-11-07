"""Commits a stored preview: every accepted row, asset, source, binding and relation, or nothing."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from app.assets.model.models import (
    BindingModel,
    MeasurementKind,
    RelationKind,
    ScopeKind,
    SourceModel,
    SourceOrigin,
    TransportStatus,
)
from app.assets.service.service import AssetService, SiteSnapshot
from app.audit.service.service import AuditService
from app.core.clock import wall_now
from app.core.errors.base import AppError, NotFoundError
from app.identity.model.models import PrincipalModel
from app.imports.model.models import ImportModel, ImportStatus, ValueKind
from app.imports.repository.base_repository import ImportRepository
from app.imports.service.commit_plan import (
    EXPIRED,
    REVISION_CHANGED,
    TIMEZONE_CHANGED,
    CommitStream,
    CommitTotals,
    affected_period,
    committable_streams,
    reading_from_parsed,
    row_bounds,
    stale_reason,
    uncovered_ranges,
)
from app.imports.service.errors import ImportAckRequiredError, ImportKeyConflictError, ImportStaleError
from app.imports.service.preview import ImportPreviewService
from app.measurements.model.models import ReadingInput
from app.measurements.service.service import IngestService
from app.scope.service.validity import IssueType, scope_issues
from app.sites.model.models import SiteModel
from app.sites.service.clock import site_clock
from app.sites.service.service import SiteService

COMMIT_PAGE = 5000
"""Rows read and handed to ``ingest`` at a time. One call for a whole file stalled the event loop for 2 s (D10)."""
_STALE_TEXT = {
    EXPIRED: "Pratinjau sudah melewati batas 24 jam.",
    REVISION_CHANGED: "Data pada ruang kerja ini berubah setelah pratinjau dibuat.",
    TIMEZONE_CHANGED: "Zona waktu ruang kerja berubah setelah pratinjau dibuat.",
}


def _instant(moment: datetime | None) -> str | None:
    return None if moment is None else moment.isoformat().replace("+00:00", "Z")


@dataclass(frozen=True, slots=True)
class CommitOutcome:
    """What a commit request answers.

    Attributes:
        result (dict[str, Any]): The first result, as stored.
        replayed (bool): Whether this request only repeated it.
    """

    result: dict[str, Any]
    replayed: bool


@dataclass(slots=True)
class _StreamWork:
    """One stream with accepted rows: its target, the rows waiting for ``ingest``, and the span they cover."""

    stream: CommitStream
    asset_id: UUID
    source: SourceModel
    start: datetime
    end: datetime
    readings: list[ReadingInput] = field(default_factory=list)


@dataclass(slots=True)
class _Run:
    """What one commit knows and has done so far."""

    site: SiteModel
    model: ImportModel
    snapshot: SiteSnapshot
    received_at: datetime
    streams: dict[str, CommitStream]
    totals: CommitTotals = field(default_factory=CommitTotals)
    works: dict[str, _StreamWork] = field(default_factory=dict)
    created_assets: dict[str, UUID] = field(default_factory=dict)
    changed_scope: bool = False
    rows_after_site_clock: int = 0


class ImportCommitService:
    """Applies a preview in the request's one transaction, which ``SessionDep`` commits or rolls back.

    Lock order is the site row, then the import row, then writes. No other holder of the site lock takes an import row
    first, and a preview purges only after its own insert holds a share of the site row, so this cannot deadlock.
    """

    def __init__(
        self,
        repository: ImportRepository,
        sites: SiteService,
        assets: AssetService,
        ingest: IngestService,
        audit: AuditService,
    ) -> None:
        """Bind to storage and neighbouring services.

        Args:
            repository (ImportRepository): Import storage.
            sites (SiteService): Site ownership, lock and revisions.
            assets (AssetService): The site's assets, sources, bindings and relations.
            ingest (IngestService): The one path readings are stored by.
            audit (AuditService): Audit trail.
        """
        self.repository = repository
        self.sites = sites
        self.assets = assets
        self.ingest = ingest
        self.audit = audit

    async def commit(
        self, import_id: UUID, principal: PrincipalModel, key: str, acknowledge_skipped: bool
    ) -> CommitOutcome:
        """Commit a stored preview, or repeat the first result of one already committed.

        Args:
            import_id (UUID): The import.
            principal (PrincipalModel): The acting principal.
            key (str): The request's idempotency key.
            acknowledge_skipped (bool): Whether the user accepts that invalid rows will be skipped.

        Returns:
            CommitOutcome: The first result, and whether this request only repeated it.

        Raises:
            NotFoundError: When the import is missing, purged, or someone else's.
            ImportKeyConflictError: When the key belongs to another import, or to a different acknowledgment.
            ImportBlockedError: When the preview is blocked.
            ImportStaleError: When the preview expired, or its site changed.
            ImportAckRequiredError: When invalid rows would be skipped without acknowledgment.
        """
        unlocked = await self.repository.get_import(import_id)
        if unlocked is None:
            raise NotFoundError()
        site = await self.sites.lock_owned(unlocked.site_id, principal)
        model = await self.repository.get_import_locked(import_id)
        if model is None:  # Purged by a preview while this request waited on the site lock.
            raise NotFoundError()
        replay = await self._gate(model, site, key, acknowledge_skipped)
        if replay is not None:
            return CommitOutcome(result=replay, replayed=True)
        return CommitOutcome(result=await self._apply(model, site, principal, key, acknowledge_skipped), replayed=False)

    async def _gate(
        self, model: ImportModel, site: SiteModel, key: str, acknowledge_skipped: bool
    ) -> dict[str, Any] | None:
        """Decide what a request may do, under both locks and before any write, returning a result to repeat.

        A refusal raises and the route rolls back, so its key is stored nowhere and stays free.
        """
        holder = await self.repository.find_by_key(site.id, key)
        if holder is not None and holder != model.id:
            raise ImportKeyConflictError()
        if model.status is ImportStatus.COMMITTED:
            assert model.commit_result is not None  # A CHECK ties the status to the result.
            if model.idempotency_key == key and model.commit_result["acknowledge_skipped"] != acknowledge_skipped:
                raise ImportKeyConflictError()
            return model.commit_result
        ImportPreviewService.require_committable(model)
        reason = stale_reason(model, site, wall_now())
        if reason is not None:
            raise ImportStaleError(details=[{"loc": ["import"], "msg": _STALE_TEXT[reason], "type": reason}])
        if model.needs_acknowledgment and not acknowledge_skipped:
            raise ImportAckRequiredError(
                details=[
                    {
                        "loc": ["body", "acknowledge_skipped"],
                        "msg": f"{model.invalid_rows} baris tidak valid akan dilewati.",
                        "type": "acknowledgment_required",
                    }
                ]
            )
        return None

    async def _apply(
        self, model: ImportModel, site: SiteModel, principal: PrincipalModel, key: str, acknowledge_skipped: bool
    ) -> dict[str, Any]:
        run = _Run(
            site=site,
            model=model,
            snapshot=await self.assets.snapshot(site),
            received_at=wall_now(),
            streams={stream.stream_key: stream for stream in committable_streams(model.mapping)},
        )
        await self._ingest_rows(run)
        if run.totals.added != model.accepted_rows:
            raise AppError(error=RuntimeError("Ingestion stored a different number of rows than the preview accepted."))
        await self._add_bindings(run)
        await self._add_relations(run)
        if run.created_assets or run.changed_scope:
            await self.sites.advance_binding_revision(site)
        await self.audit.record(
            site_id=site.id,
            actor_principal_id=principal.id,
            action="import.committed",
            subject_type="import",
            subject_id=model.id,
            affected_from=run.totals.affected_from,
            affected_to=run.totals.affected_to,
            detail={
                "rows_added": run.totals.added,
                "rows_skipped": model.invalid_rows,
                "rows_duplicate": model.duplicate_rows,
                "assets_created": len(run.created_assets),
                "assets_mapped": sum(stream.asset_id is not None for stream in run.streams.values()),
            },
        )
        result = self._result(run, acknowledge_skipped)
        if not await self.repository.mark_committed(model.id, key, result):
            raise AppError(error=RuntimeError("An import held under its lock stopped being a preview."))
        return result

    async def _ingest_rows(self, run: _Run) -> None:
        clock = site_clock(run.site)
        after_row = 0
        while page := await self.repository.accepted_page(run.model.id, after_row, COMMIT_PAGE):
            for row in page:
                assert row.parsed is not None
                work = await self._work_for(run, row.parsed)
                start, end = row_bounds(row.parsed)
                work.start, work.end = min(work.start, start), max(work.end, end)
                work.readings.append(reading_from_parsed(row.parsed))
                if datetime.fromisoformat(row.parsed["interval_end"] or row.parsed["measured_at"]) > clock:
                    run.rows_after_site_clock += 1
                # A counter needs one call: ``_rederive_counter`` rereads all of a source's deltas per call.
                if work.stream.kind is not ValueKind.COUNTER and len(work.readings) >= COMMIT_PAGE:
                    await self._flush(run, work)
            after_row = page[-1].data_row
        for work in run.works.values():
            await self._flush(run, work)

    async def _work_for(self, run: _Run, parsed: dict[str, Any]) -> _StreamWork:
        stream_key = parsed["stream_key"]
        work = run.works.get(stream_key)
        if work is not None:
            return work
        stream = run.streams.get(stream_key)
        if stream is None:
            raise AppError(error=RuntimeError("A staged row names a stream its mapping does not hold."))
        asset_id = await self._asset_for(run, stream)
        source = await self._source_for(run, stream)
        start, end = row_bounds(parsed)
        work = _StreamWork(stream=stream, asset_id=asset_id, source=source, start=start, end=end)
        run.works[stream_key] = work
        return work

    async def _asset_for(self, run: _Run, stream: CommitStream) -> UUID:
        if stream.asset_id is not None:
            return stream.asset_id
        asset = await self.assets.add_asset(run.site, name=stream.asset_name, scope_kind=ScopeKind.DEVICE)
        run.created_assets[stream.stream_key] = asset.id
        return asset.id

    async def _source_for(self, run: _Run, stream: CommitStream) -> SourceModel:
        if stream.source_id is not None:
            return next(source for source in run.snapshot.sources if source.id == stream.source_id)
        return await self.assets.create_source(
            run.site,
            label=stream.label,
            origin=SourceOrigin.IMPORT,
            measurement_kind=MeasurementKind(stream.kind.value),
            cadence_seconds=stream.cadence_seconds,
            transport_status=TransportStatus.HISTORICAL,
        )

    async def _flush(self, run: _Run, work: _StreamWork) -> None:
        if not work.readings:
            return
        provenance = {
            "import_id": str(run.model.id),
            "file_name": run.model.file_name,
            "timezone": run.model.mapping["timezone"],
            "timezone_confirmed": run.model.mapping["timezone_confirmed"],
            "interval_basis": work.stream.interval_basis,
        }
        result = await self.ingest.ingest(
            run.site, work.source, work.readings, received_at=run.received_at, provenance=provenance
        )
        run.totals.add(result)
        work.readings = []

    async def _add_bindings(self, run: _Run) -> None:
        for work in run.works.values():
            existing: list[BindingModel] = [
                binding for binding in run.snapshot.bindings if binding.asset_id == work.asset_id
            ]
            for start, end in uncovered_ranges(work.start, work.end, existing):
                await self.assets.add_binding(
                    run.site,
                    asset_id=work.asset_id,
                    source_id=work.source.id,
                    effective_from=start,
                    effective_to=end,
                    authoritative=True,
                )
                run.changed_scope = True

    async def _add_relations(self, run: _Run) -> None:
        if not run.totals.added:
            return
        asset_ids = [
            asset_id
            for stream in run.streams.values()
            if (asset_id := stream.asset_id or run.created_assets.get(stream.stream_key)) is not None
        ]
        kind = RelationKind(run.model.mapping["scope"])
        issues = scope_issues(asset_ids, run.snapshot.containment, run.snapshot.relations, set())
        for issue in issues:
            if issue.type is IssueType.UNCONFIRMED:
                await self.assets.relate(run.site, issue.asset_ids[0], issue.asset_ids[1], kind)
                run.changed_scope = True

    @staticmethod
    def _result(run: _Run, acknowledge_skipped: bool) -> dict[str, Any]:
        model, totals = run.model, run.totals
        stored_names = {asset.id: asset.name for asset in run.snapshot.assets}
        return {
            "import_id": str(model.id),
            "status": ImportStatus.COMMITTED.value,
            "rows_added": totals.added,
            "rows_skipped": model.invalid_rows,
            "rows_duplicate": model.duplicate_rows,
            "assets_created": [
                {"id": str(run.created_assets[stream.stream_key]), "name": stream.asset_name}
                for stream in run.streams.values()
                if stream.stream_key in run.created_assets
            ],
            "assets_mapped": [
                {"id": str(stream.asset_id), "name": stored_names[stream.asset_id]}
                for stream in run.streams.values()
                if stream.asset_id is not None
            ],
            "period": affected_period(totals.affected_from, totals.affected_to, run.site.timezone),
            "affected_from": _instant(totals.affected_from),
            "affected_to": _instant(totals.affected_to),
            "rows_after_site_clock": run.rows_after_site_clock,
            "acknowledge_skipped": acknowledge_skipped,
            "committed_at": _instant(run.received_at),
        }
