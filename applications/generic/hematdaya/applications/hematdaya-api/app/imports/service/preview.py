"""Stores previews: parse, stage, classify and keep the result, changing nothing else."""

import asyncio
import base64
import hashlib
import re
import unicodedata
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, BinaryIO
from uuid import UUID, uuid4

from app.assets.service.service import AssetService
from app.core.clock import wall_now
from app.core.errors.base import NotFoundError, RequestInvalidError
from app.identity.model.models import PrincipalModel
from app.imports.model.models import (
    ImportModel,
    ImportRowModel,
    ImportRowStatus,
    ImportStatus,
    MeaningAnswers,
    MeaningQuestion,
    ParsedFile,
    RowError,
    StructuralError,
    StructuralReason,
    ValueKind,
)
from app.imports.model.schema import (
    ImportMappingRequest,
    ImportQuestionKind,
    ImportQuestionResponse,
    ImportStatusResponse,
)
from app.imports.repository.base_repository import ImportRepository
from app.imports.service.assumptions import build_assumptions
from app.imports.service.classify import (
    Classified,
    RowCounts,
    StagedFile,
    StagedRow,
    StoredStream,
    bound_text,
    chosen_kind,
    classify,
    row_span,
    stage_file,
    summarize,
)
from app.imports.service.columns import VALUE_ROLES, Role, resolve_columns
from app.imports.service.errors import ImportBlockedError, ImportStructureError, ImportTooLargeError
from app.imports.service.mapping import ResolvedMapping, require_active_targets, resolve_streams
from app.imports.service.parser import MAX_ROWS, parse
from app.measurements.service.service import IngestService
from app.sites.model.models import SiteModel
from app.sites.service.clock import site_clock
from app.sites.service.service import SiteService

PREVIEW_TTL = timedelta(hours=24)
"""By the wall clock, never the site's product time."""
MAX_UNCOMMITTED_PER_SITE = 5
PURGE_BATCH = 20
INLINE_ERRORS = 50
PASTE_FILE_NAME = "tempelan.csv"
_MAX_FILE_NAME = 255
_HASH_CHUNK = 1024 * 1024
_SIZE_REASONS = (StructuralReason.TOO_LARGE, StructuralReason.TOO_MANY_ROWS)


def clean_file_name(file_name: str | None) -> str:
    """Reduce an upload's name to safe display text. Cutting it hides nothing.

    Args:
        file_name (str | None): The name the client sent.

    Returns:
        str: Its last path segment without control characters, at most 255 long, or the paste name when none remains.
    """
    segment = re.split(r"[/\\]", file_name or "")[-1]
    visible = "".join(char for char in segment if not unicodedata.category(char).startswith("C")).strip()
    return visible[:_MAX_FILE_NAME] or PASTE_FILE_NAME


def encode_error_cursor(data_row: int) -> str:
    """Encode a page position. Opaque to clients.

    Args:
        data_row (int): The last data row of the page.

    Returns:
        str: The cursor.
    """
    return base64.urlsafe_b64encode(str(data_row).encode()).decode()


def decode_error_cursor(cursor: str) -> int:
    """Decode a page position.

    Args:
        cursor (str): The cursor.

    Returns:
        int: The last data row returned.

    Raises:
        RequestInvalidError: When the cursor was not issued by this API.
    """
    try:
        data_row = int(base64.urlsafe_b64decode(cursor.encode()))
    except ValueError as error:
        raise RequestInvalidError(error=error) from error
    if not 0 < data_row <= MAX_ROWS:
        raise RequestInvalidError()
    return data_row


def _structural_failure(errors: list[StructuralError]) -> ImportTooLargeError | ImportStructureError:
    details = [
        {
            "loc": ["file"] if error.file_line is None else ["file", "line", error.file_line],
            "msg": error.message,
            "type": error.reason.value,
        }
        for error in errors
    ]
    too_large = any(error.reason in _SIZE_REASONS for error in errors)
    return ImportTooLargeError(details=details) if too_large else ImportStructureError(details=details)


def _parser_question(question: MeaningQuestion) -> ImportQuestionResponse:
    return ImportQuestionResponse(
        kind=ImportQuestionKind(question.kind.value),
        message=bound_text(question.message),
        streams=list(question.streams),
    )


def _instant(moment: datetime | None) -> str | None:
    return None if moment is None else moment.isoformat().replace("+00:00", "Z")


def _accepted_values(row: StagedRow) -> dict[str, Any]:
    return {
        "stream_key": row.stream_key,
        "asset_name": row.asset_name,
        "kind": row.kind.value,
        "unit": row.unit,
        "value": row.value,
        "identity_key": row.identity_key,
        "interval_start": _instant(row.interval_start),
        "interval_end": _instant(row.interval_end),
        "measured_at": _instant(row.measured_at),
        "raw_value": row.raw_value,
        "raw_start": row.raw_start,
        "raw_end": row.raw_end,
    }


def _invalid_row(error: RowError) -> ImportRowModel:
    return ImportRowModel(
        data_row=error.data_row,
        file_line=error.file_line,
        status=ImportRowStatus.INVALID,
        reason=error.reason.value,
        field=error.field,
        message=bound_text(error.message),
    )


def _columns_json(parsed: ParsedFile) -> dict[str, str | None]:
    columns = resolve_columns(parsed.headers).columns
    kind = chosen_kind(parsed)

    def header(role: Role) -> str | None:
        return parsed.headers[columns[role]] if role in columns else None

    return {
        "asset": header(Role.ASSET),
        "source": header(Role.SOURCE),
        "timestamp": header(Role.TIMESTAMP),
        "interval_start": header(Role.INTERVAL_START),
        "interval_end": header(Role.INTERVAL_END),
        "value": None if kind is None else header(VALUE_ROLES[kind]),
        "unit": None if kind is None else ("W" if kind is ValueKind.AVERAGE_POWER else "Wh"),
    }


def _hash_file(source: BinaryIO) -> str:
    digest = hashlib.sha256()
    source.seek(0)
    while chunk := source.read(_HASH_CHUNK):
        digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True, slots=True)
class StoredPreview:
    """A preview as a client reads it.

    Attributes:
        model (ImportModel): The stored import.
        status (ImportStatusResponse): Its status, or ``expired`` once an uncommitted preview has passed its expiry.
        errors (list[ImportRowModel]): Its first row errors.
        next_error_cursor (str | None): Where the next errors start, when more exist.
    """

    model: ImportModel
    status: ImportStatusResponse
    errors: list[ImportRowModel]
    next_error_cursor: str | None


@dataclass(frozen=True, slots=True)
class ErrorPage:
    """One page of row errors.

    Attributes:
        items (list[ImportRowModel]): The rows, in data row order.
        next_cursor (str | None): Where the next page starts, when more exist.
    """

    items: list[ImportRowModel]
    next_cursor: str | None


class ImportPreviewService:
    """Classifies a file against the site's stored data. It changes nothing but ``imports`` and ``import_rows``."""

    def __init__(
        self, repository: ImportRepository, sites: SiteService, assets: AssetService, ingest: IngestService
    ) -> None:
        """Bind to storage and neighbouring services.

        Args:
            repository (ImportRepository): Import storage.
            sites (SiteService): Site ownership.
            assets (AssetService): The site's assets, sources and bindings.
            ingest (IngestService): Stored readings.
        """
        self.repository = repository
        self.sites = sites
        self.assets = assets
        self.ingest = ingest

    async def owned_site(self, site_id: UUID, principal: PrincipalModel) -> SiteModel:
        """Resolve the target site. It runs before any body is read, so a foreign upload costs nothing.

        Args:
            site_id (UUID): The site.
            principal (PrincipalModel): The acting principal.

        Returns:
            SiteModel: The site, carrying the revisions a commit will compare.

        Raises:
            NotFoundError: When it does not exist or belongs to someone else.
        """
        return await self.sites.get_owned(site_id, principal)

    async def preview(
        self, site: SiteModel, file: BinaryIO, file_name: str | None, mapping: ImportMappingRequest
    ) -> StoredPreview:
        """Parse, stage and store a preview. A blocked preview is a stored result, not an error.

        Args:
            site (SiteModel): The site from ``owned_site``. Its revisions are the first thing this preview read.
            file (BinaryIO): A seekable file. It stays open.
            file_name (str | None): The upload's name; None for a paste.
            mapping (ImportMappingRequest): The user's answers.

        Returns:
            StoredPreview: The stored preview.

        Raises:
            NotFoundError: When the mapping names anything but an active asset of this site.
            ImportTooLargeError: When the file is over a limit.
            ImportStructureError: When its structure cannot be read.
        """
        snapshot = await self.assets.snapshot(site)
        require_active_targets(mapping, snapshot)
        answers = MeaningAnswers(
            value_kind=mapping.value_kind,
            power_meaning=mapping.power_meaning,
            timezone_confirmed=mapping.timezone_confirmed,
            interval_minutes=mapping.interval_minutes,
        )
        parsed = await asyncio.to_thread(parse, file, site_timezone=site.timezone, answers=answers)
        if not parsed.ok:
            raise _structural_failure(parsed.structural_errors)
        staged_file = await asyncio.to_thread(stage_file, file, parsed)
        content_sha256 = await asyncio.to_thread(_hash_file, file)
        resolved = await asyncio.to_thread(resolve_streams, staged_file.streams, mapping, snapshot)
        questions = [_parser_question(question) for question in parsed.questions] + resolved.questions
        stored = await self._stored_streams(staged_file, resolved)
        classified = await asyncio.to_thread(classify, staged_file.staged, stored)
        accepted = [item.row for item in classified if item.status is ImportRowStatus.ACCEPTED]
        counts = RowCounts(
            total=parsed.total_rows,
            accepted=len(accepted),
            invalid=len(staged_file.errors),
            duplicate=sum(item.status is ImportRowStatus.DUPLICATE for item in classified),
            conflict=sum(item.status is ImportRowStatus.CONFLICT for item in classified),
            pending=staged_file.pending,
        )
        summary = summarize(counts, open_questions=len(questions))
        spans = [row_span(row) for row in accepted]
        now = wall_now()
        model = ImportModel(
            id=uuid4(),
            site_id=site.id,
            status=ImportStatus.PREVIEWED,
            file_name=clean_file_name(file_name),
            content_sha256=content_sha256,
            mapping=self._mapping_json(site, parsed, mapping, resolved),
            total_rows=counts.total,
            accepted_rows=counts.accepted,
            invalid_rows=counts.invalid,
            duplicate_rows=counts.duplicate,
            conflict_rows=counts.conflict,
            pending_rows=counts.pending,
            blocked=summary.blocked,
            block_reasons=summary.block_reasons,
            needs_acknowledgment=summary.needs_acknowledgment,
            questions=[question.model_dump(mode="json") for question in questions],
            assumptions=build_assumptions(parsed, accepted, now=site_clock(site), timezone=site.timezone),
            period_start=min((start for start, _ in spans), default=None),
            period_end=max((end for _, end in spans), default=None),
            measurement_revision=site.measurement_revision,
            binding_revision=site.binding_revision,
            idempotency_key=None,
            expires_at=now + PREVIEW_TTL,
        )
        await self.repository.delete_expired(now, PURGE_BATCH)
        await self.repository.keep_newest_uncommitted(site.id, MAX_UNCOMMITTED_PER_SITE - 1)
        await self.repository.add_import(model)
        await self.repository.add_rows(model.id, self._rows(classified, staged_file.errors))
        return await self._stored(model)

    async def get(self, import_id: UUID, principal: PrincipalModel) -> StoredPreview:
        """Read a stored preview through its owner.

        Args:
            import_id (UUID): The import.
            principal (PrincipalModel): The acting principal.

        Returns:
            StoredPreview: The preview, with its first row errors.

        Raises:
            NotFoundError: When it does not exist or belongs to someone else.
        """
        return await self._stored(await self._owned(import_id, principal))

    async def errors(self, import_id: UUID, principal: PrincipalModel, cursor: str | None, limit: int) -> ErrorPage:
        """Read one page of a stored preview's row errors.

        Args:
            import_id (UUID): The import.
            principal (PrincipalModel): The acting principal.
            cursor (str | None): Where to start; None for the first page.
            limit (int): Maximum rows.

        Returns:
            ErrorPage: The page.

        Raises:
            NotFoundError: When it does not exist or belongs to someone else.
            RequestInvalidError: When the cursor was not issued by this API.
        """
        model = await self._owned(import_id, principal)
        after_row = 0 if cursor is None else decode_error_cursor(cursor)
        items, next_cursor = await self._page(model.id, after_row, limit)
        return ErrorPage(items=items, next_cursor=next_cursor)

    @staticmethod
    def require_committable(model: ImportModel) -> None:
        """Refuse a blocked preview. Called first by the commit route in 026.

        Args:
            model (ImportModel): The stored preview.

        Raises:
            ImportBlockedError: When it is blocked.
        """
        if model.blocked:
            raise ImportBlockedError()

    async def _owned(self, import_id: UUID, principal: PrincipalModel) -> ImportModel:
        model = await self.repository.get_import(import_id)
        if model is None:
            raise NotFoundError()
        await self.sites.get_owned(model.site_id, principal)
        return model

    async def _stored(self, model: ImportModel) -> StoredPreview:
        errors, next_cursor = await self._page(model.id, 0, INLINE_ERRORS)
        expired = model.status is ImportStatus.PREVIEWED and model.expires_at <= wall_now()
        status = ImportStatusResponse.EXPIRED if expired else ImportStatusResponse(model.status.value)
        return StoredPreview(model=model, status=status, errors=errors, next_error_cursor=next_cursor)

    async def _page(self, import_id: UUID, after_row: int, limit: int) -> tuple[list[ImportRowModel], str | None]:
        rows = await self.repository.error_page(import_id, after_row, limit + 1)
        items = rows[:limit]
        return items, encode_error_cursor(items[-1].data_row) if len(rows) > limit else None

    async def _stored_streams(self, staged_file: StagedFile, resolved: ResolvedMapping) -> dict[str, StoredStream]:
        """Read what each resolved source holds, bounded to its stream's identities and period."""
        identities: dict[str, set[str]] = {
            stream.facts.stream_key: set() for stream in resolved.streams if stream.source is not None
        }
        for row in staged_file.staged:
            if row.stream_key in identities:
                identities[row.stream_key].add(row.identity_key)
        stored: dict[str, StoredStream] = {}
        for stream in resolved.streams:
            facts = stream.facts
            if stream.source is None or facts.period_start is None or facts.period_end is None:
                continue
            intervals = []
            if facts.kind is not ValueKind.COUNTER:
                intervals = await self.ingest.stored_intervals(stream.source.id, facts.period_start, facts.period_end)
            current = await self.ingest.current_rows(stream.source.id, sorted(identities[facts.stream_key]))
            stored[facts.stream_key] = StoredStream(current=current, intervals=intervals)
        return stored

    @staticmethod
    def _rows(classified: list[Classified], errors: list[RowError]) -> Iterator[ImportRowModel]:
        for item in classified:
            row = item.row
            yield ImportRowModel(
                data_row=row.data_row,
                file_line=row.file_line,
                status=item.status,
                reason=item.reason,
                field=item.field,
                message=item.message,
                parsed=_accepted_values(row) if item.status is ImportRowStatus.ACCEPTED else None,
            )
        for error in errors:
            yield _invalid_row(error)

    @staticmethod
    def _mapping_json(
        site: SiteModel, parsed: ParsedFile, mapping: ImportMappingRequest, resolved: ResolvedMapping
    ) -> dict[str, Any]:
        kind = chosen_kind(parsed)
        return {
            "value_kind": None if kind is None else kind.value,
            "power_meaning": None if mapping.power_meaning is None else mapping.power_meaning.value,
            "timezone": site.timezone,
            "timezone_confirmed": mapping.timezone_confirmed,
            "interval_minutes": mapping.interval_minutes,
            "scope": None if mapping.scope is None else mapping.scope.value,
            "columns": _columns_json(parsed),
            "streams": [stream.as_json() for stream in resolved.streams],
        }
