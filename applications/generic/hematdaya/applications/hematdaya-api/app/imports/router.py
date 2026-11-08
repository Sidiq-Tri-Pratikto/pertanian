"""CSV import preview endpoints."""

import io
from datetime import timedelta
from typing import Annotated, BinaryIO
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Header, Query, Request, status
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from starlette.datastructures import FormData, UploadFile
from starlette.types import Message

from app.core.errors.base import RequestInvalidError
from app.core.locale import locale
from app.identity.dependencies import PrincipalDep
from app.imports.dependencies import ImportCommitServiceDep, ImportPreviewServiceDep
from app.imports.model.models import ImportRowModel, ValueKind
from app.imports.model.schema import (
    ImportCommitRequest,
    ImportCommitResponse,
    ImportCommitResultResponse,
    ImportErrorPageResponse,
    ImportMappingRequest,
    ImportPeriodResponse,
    ImportPreviewResponse,
    ImportQuestionResponse,
    ImportRowErrorResponse,
)
from app.imports.service.classify import MAX_IMPORT_STREAMS
from app.imports.service.copy import QUESTION_MESSAGES, ROW_MESSAGES, STRUCTURAL_MESSAGES
from app.imports.service.errors import ImportTooLargeError
from app.imports.service.parser import MAX_BYTES
from app.imports.service.preview import StoredPreview

router = APIRouter(tags=["imports"])

BODY_LIMIT = MAX_BYTES + 64 * 1024
"""A file at the parser's limit still fits with its multipart framing and the mapping."""

_PREVIEW_BODY = {
    "requestBody": {
        "required": True,
        "content": {
            "multipart/form-data": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "file": {
                            "type": "string",
                            "format": "binary",
                            "description": "The CSV file. Send this or `text`, not both.",
                        },
                        "text": {"type": "string", "description": "Pasted CSV text. Send this or `file`, not both."},
                        "mapping": {
                            "type": "string",
                            "description": (
                                "The answers so far, as JSON text: `value_kind`, `power_meaning`, "
                                "`timezone_confirmed`, `interval_minutes` by stream key, `asset_map` from asset name "
                                'to asset ID or `"new"`, and `scope`. Omit it when there are no answers yet.'
                            ),
                        },
                    },
                }
            }
        },
    }
}


def _limited(request: Request) -> Request:
    """Wrap a request so reading stops as soon as its body passes the cap. Starlette has no total limit."""
    received = 0

    async def counting_receive() -> Message:
        nonlocal received
        message = await request.receive()
        received += len(message.get("body", b""))
        if received > BODY_LIMIT:
            raise ImportTooLargeError(
                details=[
                    {
                        "loc": ["file"],
                        "msg": STRUCTURAL_MESSAGES["too_large"]
                        if locale() == "en"
                        else "Ukuran berkas melebihi batas 10 MiB.",
                        "type": "too_large",
                    }
                ]
            )
        return message

    return Request(request.scope, counting_receive)


def _mapping(form: FormData) -> ImportMappingRequest:
    raw = form.get("mapping")
    if raw is None:
        return ImportMappingRequest()
    if not isinstance(raw, str):
        raise RequestInvalidError()
    try:
        return ImportMappingRequest.model_validate_json(raw)
    except ValidationError as error:
        items = error.errors(include_url=False, include_context=False, include_input=False)
        raise RequestValidationError([item | {"loc": ("body", "mapping", *item["loc"])} for item in items]) from error


def _upload(form: FormData) -> tuple[BinaryIO, str | None]:
    """Pick the one input of a form. Having none is the parser's ``empty_input``, so it keeps one message."""
    files, texts = form.getlist("file"), form.getlist("text")
    if len(files) + len(texts) > 1:
        raise RequestInvalidError()
    if files:
        if not isinstance(files[0], UploadFile):
            raise RequestInvalidError()
        return files[0].file, files[0].filename
    if texts:
        if not isinstance(texts[0], str):
            raise RequestInvalidError()
        return io.BytesIO(texts[0].encode("utf-8")), None
    return io.BytesIO(b""), None


def _row_error(row: ImportRowModel) -> ImportRowErrorResponse:
    assert row.field is not None and row.reason is not None and row.message is not None
    message = row.message
    if locale() == "en":
        correction = ROW_MESSAGES.get(row.reason, "Check the entry and try again.")
        message = f"Data row {row.data_row}, {row.field}: {correction}"
    return ImportRowErrorResponse(
        data_row=row.data_row, file_line=row.file_line, field=row.field, reason=row.reason, message=message
    )


def _period(stored: StoredPreview) -> ImportPeriodResponse | None:
    model = stored.model
    if model.period_start is None or model.period_end is None:
        return None
    timezone = model.mapping["timezone"]
    # An interval's end is exclusive, so its last covered instant decides the date. A counter's last point is included.
    is_point = model.mapping["value_kind"] == ValueKind.COUNTER.value
    last = model.period_end if is_point else model.period_end - timedelta(microseconds=1)
    return ImportPeriodResponse(
        start_date=model.period_start.astimezone(ZoneInfo(timezone)).date(),
        end_date=last.astimezone(ZoneInfo(timezone)).date(),
        timezone=timezone,
    )


def _english_blockers(stored: StoredPreview) -> list[str]:
    model = stored.model
    reasons: list[str] = []
    if model.questions or model.pending_rows:
        reasons.append("Complete the mapping first.")
    if model.invalid_rows * 5 > model.total_rows:
        reasons.append(f"{model.invalid_rows} of {model.total_rows} data rows are invalid. Fix the file and try again.")
    if model.conflict_rows:
        reasons.append("The file contains conflicting readings. Review the sources and correct the data.")
    streams = model.mapping.get("_stream_count", len(model.mapping.get("streams", [])))
    if streams > MAX_IMPORT_STREAMS:
        reasons.append(f"This file has {streams} streams. Split it into files with up to {MAX_IMPORT_STREAMS} streams.")
    if len(reasons) < len(model.block_reasons):
        reasons.append("This preview cannot be imported. Review its row errors and file limits.")
    return reasons


def _to_response(stored: StoredPreview) -> ImportPreviewResponse:
    model = stored.model
    questions = [ImportQuestionResponse(**question) for question in model.questions]
    english = locale() == "en"
    if english:
        questions = [
            question.model_copy(update={"message": QUESTION_MESSAGES[question.kind.value]}) for question in questions
        ]
    return ImportPreviewResponse(
        id=model.id,
        status=stored.status,
        file_name=model.file_name,
        expires_at=model.expires_at,
        total_rows=model.total_rows,
        accepted_rows=model.accepted_rows,
        invalid_rows=model.invalid_rows,
        duplicate_rows=model.duplicate_rows,
        conflict_rows=model.conflict_rows,
        pending_rows=model.pending_rows,
        blocked=model.blocked,
        block_reasons=_english_blockers(stored) if english else model.block_reasons,
        needs_acknowledgment=model.needs_acknowledgment,
        questions=questions,
        mapping={key: value for key, value in model.mapping.items() if key not in {"_assumptions_en", "_stream_count"}},
        assumptions=(
            model.mapping.get("_assumptions_en", ["Review the saved mapping and preview before confirming."])
            if english and model.assumptions
            else model.assumptions
        ),
        period=_period(stored),
        errors=[_row_error(row) for row in stored.errors],
        next_error_cursor=stored.next_error_cursor,
        result=None if model.commit_result is None else ImportCommitResultResponse(**model.commit_result),
    )


@router.post(
    "/sites/{site_id}/imports/preview",
    status_code=status.HTTP_201_CREATED,
    summary="Preview a CSV import without saving any reading",
    response_model=ImportPreviewResponse,
    openapi_extra=_PREVIEW_BODY,
)
async def preview_import(
    site_id: UUID, request: Request, principal: PrincipalDep, service: ImportPreviewServiceDep
) -> ImportPreviewResponse:
    """Store a preview of a file or pasted text. A blocked preview is a 201 with ``blocked`` true.

    This takes ``Request`` rather than declared form fields, because FastAPI parses those before any dependency. So
    the site is resolved first, and a foreign site answers ``NOT_FOUND`` with nothing read.

    Args:
        site_id (UUID): The site.
        request (Request): The request, whose body is read only after ownership is known.
        principal (PrincipalModel): The acting principal.
        service (ImportPreviewService): Preview rules.

    Returns:
        ImportPreviewResponse: The stored preview.
    """
    site = await service.owned_site(site_id, principal)
    form = await _limited(request).form(max_part_size=BODY_LIMIT)
    try:
        mapping = _mapping(form)
        file, file_name = _upload(form)
        return _to_response(await service.preview(site, file, file_name, mapping))
    finally:
        await form.close()


@router.get("/imports/{import_id}", summary="Read a stored import preview")
async def get_import(
    import_id: UUID, principal: PrincipalDep, service: ImportPreviewServiceDep
) -> ImportPreviewResponse:
    """Return a stored preview with its counts, assumptions and first row errors.

    Args:
        import_id (UUID): The import.
        principal (PrincipalModel): The acting principal.
        service (ImportPreviewService): Preview rules.

    Returns:
        ImportPreviewResponse: The stored preview.
    """
    return _to_response(await service.get(import_id, principal))


@router.get("/imports/{import_id}/errors", summary="Page through an import preview's row errors")
async def list_import_errors(
    import_id: UUID,
    principal: PrincipalDep,
    service: ImportPreviewServiceDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    cursor: Annotated[str | None, Query(max_length=400)] = None,
) -> ImportErrorPageResponse:
    """Return one page of invalid and conflicting rows, ordered by data row.

    Args:
        import_id (UUID): The import.
        principal (PrincipalModel): The acting principal.
        service (ImportPreviewService): Preview rules.
        limit (int, optional): Page size. Defaults to 50.
        cursor (str | None, optional): The previous page's ``next_cursor``. Defaults to None.

    Returns:
        ImportErrorPageResponse: The page.
    """
    page = await service.errors(import_id, principal, cursor, limit)
    return ImportErrorPageResponse(items=[_row_error(row) for row in page.items], next_cursor=page.next_cursor)


@router.post("/imports/{import_id}/commit", summary="Commit a previewed import in one transaction")
async def commit_import(
    import_id: UUID,
    request: ImportCommitRequest,
    principal: PrincipalDep,
    service: ImportCommitServiceDep,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", pattern=r"^[A-Za-z0-9_-]{22,128}$")],
) -> ImportCommitResponse:
    """Store every accepted row, or nothing. A repeat answers the first result with ``replayed`` true.

    Args:
        import_id (UUID): The import.
        request (ImportCommitRequest): Whether invalid rows may be skipped.
        principal (PrincipalModel): The acting principal.
        service (ImportCommitService): Commit rules.
        idempotency_key (str): Names this attempt. A failed attempt stores nothing, so it stays free.

    Returns:
        ImportCommitResponse: The first result.
    """
    outcome = await service.commit(import_id, principal, idempotency_key, request.acknowledge_skipped)
    return ImportCommitResponse(**outcome.result, replayed=outcome.replayed)
