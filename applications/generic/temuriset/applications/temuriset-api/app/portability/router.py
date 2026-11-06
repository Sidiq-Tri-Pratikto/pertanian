"""HTTP routes for authorized workspace portability."""

import hashlib
import json
from collections.abc import Awaitable, Callable
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Request
from fastapi.routing import APIRoute
from starlette.responses import Response, StreamingResponse

from app.access.service.policy import check_context
from app.core.database import SessionDep
from app.core.errors.base import AppError
from app.core.errors.handlers import handle_app_error
from app.core.security import PrincipalDep
from app.documents.service.service import FileTooLargeError, FileTypeUnsupportedError
from app.platform.model.schema import OperationResult
from app.platform.service.idempotency import Idempotency, claim_operation
from app.portability.model.schema import (
    CreateExportRequest,
    ExportStatusResponse,
    ImportActionRequest,
    ImportStatusResponse,
    StartImportRequest,
)
from app.portability.service.common import read_bounded
from app.portability.service.exports import ExportService
from app.portability.service.file_format import MAX_BYTES
from app.portability.service.imports import ImportService

_UPLOAD_PATH = "/imports/validate"
_CONTROL_BYTES = 64 * 1024
_PRIVATE_CACHE = "private, no-store"
_IDEMPOTENCY_OPENAPI = {
    "parameters": [
        {
            "name": "Idempotency-Key",
            "in": "header",
            "required": True,
            "schema": {"type": "string", "minLength": 1, "maxLength": 128},
        }
    ],
}


class BoundedPortabilityRoute(APIRoute):
    """Keep the small control payloads bounded before FastAPI parses their JSON."""

    def get_route_handler(self) -> Callable[[Request], Awaitable[Response]]:
        """Wrap control POSTs; the upload streams with its own limit."""
        handler = super().get_route_handler()
        if "POST" not in self.methods or self.path.endswith(_UPLOAD_PATH):
            return handler

        async def bounded(request: Request) -> Response:
            raw = await read_bounded(request.stream(), _CONTROL_BYTES, limit_text="64 KiB")

            async def receive() -> dict[str, object]:
                return {"type": "http.request", "body": raw, "more_body": False}

            return await handler(Request(request.scope, receive=receive))

        return bounded


router = APIRouter(tags=["portability"], route_class=BoundedPortabilityRoute)


async def _claim(
    request: Request,
    session: SessionDep,
    principal: PrincipalDep,
    operation: str,
    body: StartImportRequest | ImportActionRequest | CreateExportRequest,
    sha256: str | None = None,
) -> Idempotency:
    check_context(principal, body.acting_party_id)
    fields = body.model_dump(mode="json")
    if sha256 is not None:
        fields["upload_sha256"] = sha256
    return await claim_operation(
        request,
        session,
        principal.active_party_id,
        operation,
        json.dumps(fields).encode(),
        owner_account_id=principal.account_id,
    )


async def _accepted(
    operation: Idempotency, result: ImportStatusResponse | ExportStatusResponse, subject: str
) -> Response:
    result.operation_id = operation.operation_id
    return await operation.respond(result, status_code=202, result=OperationResult(type=subject, id=str(result.id)))


@router.post(
    _UPLOAD_PATH,
    status_code=202,
    response_model=ImportStatusResponse,
    summary="Stage and validate a JSON import",
    openapi_extra={
        **_IDEMPOTENCY_OPENAPI,
        "requestBody": {
            "required": True,
            "content": {"application/json": {"schema": {"type": "string", "format": "binary"}}},
            "description": "Version 1 JSON file, up to 20 MiB. Its SHA-256 participates in idempotency.",
        },
    },
)
async def start_import(
    request: Request,
    metadata: Annotated[StartImportRequest, Query()],
    principal: PrincipalDep,
    session: SessionDep,
) -> Response:
    """Stage the bounded raw file in the current context and queue validation."""
    check_context(principal, metadata.acting_party_id)
    media_type = request.headers.get("content-type", "").partition(";")[0].strip().lower()
    if media_type != "application/json":
        raise FileTypeUnsupportedError("Tipe berkas ini tidak didukung. Unggah berkas JSON versi 1.")
    length = request.headers.get("content-length")
    if length and length.isdecimal() and len(length.lstrip("0")) > 8:
        raise FileTooLargeError("20 MiB")
    if length and length.isdecimal() and int(length.lstrip("0") or "0") > MAX_BYTES:
        raise FileTooLargeError("20 MiB")
    upload = await read_bounded(request.stream(), MAX_BYTES)
    sha256 = hashlib.sha256(upload).hexdigest()
    operation = await _claim(request, session, principal, "portability.import_validate", metadata, sha256)
    result = await ImportService(session).start(principal, metadata, upload, sha256)
    return await _accepted(operation, result, "import_run")


@router.get("/imports/{run_id}", response_model=ImportStatusResponse, summary="Read import stage status and preview")
async def get_import(
    run_id: UUID,
    principal: PrincipalDep,
    session: SessionDep,
    response: Response,
    offset: Annotated[int, Query(ge=0, le=2_000)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> ImportStatusResponse:
    """Only the requester in the owning context can read preview rows."""
    response.headers["Cache-Control"] = _PRIVATE_CACHE
    return await ImportService(session).read(principal, run_id, offset, limit)


@router.post(
    "/imports/{run_id}/apply",
    status_code=202,
    response_model=ImportStatusResponse,
    summary="Apply reviewed import",
    openapi_extra=_IDEMPOTENCY_OPENAPI,
)
async def apply_import(
    run_id: UUID,
    body: ImportActionRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> Response:
    """Queue apply against the exact completed preview version."""
    operation = await _claim(request, session, principal, "portability.import_apply", body)
    result = await ImportService(session).apply(principal, run_id, body)
    return await _accepted(operation, result, "import_run")


@router.post(
    "/imports/{run_id}/cancel",
    status_code=202,
    response_model=ImportStatusResponse,
    summary="Cancel import work",
    openapi_extra=_IDEMPOTENCY_OPENAPI,
)
async def cancel_import(
    run_id: UUID,
    body: ImportActionRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> Response:
    """Stop the next checkpoint and report how many records committed."""
    operation = await _claim(request, session, principal, "portability.import_cancel", body)
    result = await ImportService(session).cancel(principal, run_id, body)
    return await _accepted(operation, result, "import_run")


@router.post(
    "/exports",
    status_code=202,
    response_model=ExportStatusResponse,
    summary="Queue an authorized JSON export",
    openapi_extra=_IDEMPOTENCY_OPENAPI,
)
async def start_export(
    body: CreateExportRequest,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> Response:
    """Queue export of explicitly chosen invention and document versions."""
    operation = await _claim(request, session, principal, "portability.export", body)
    result = await ExportService(session).start(principal, body)
    return await _accepted(operation, result, "export_job")


@router.get("/exports/{export_id}", response_model=ExportStatusResponse, summary="Read export status and expiry")
async def get_export(
    export_id: UUID,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
    response: Response,
) -> ExportStatusResponse | Response:
    """Read owner-only status. A live authorization loss permanently expires the result."""
    result = await ExportService(session).read(principal, export_id)
    if isinstance(result, AppError):
        # Return the registered envelope so the invalidation transaction can commit.
        denied = await handle_app_error(request, result)
        denied.headers["Cache-Control"] = _PRIVATE_CACHE
        return denied
    response.headers["Cache-Control"] = _PRIVATE_CACHE
    return result


@router.get(
    "/exports/{export_id}/download",
    response_class=StreamingResponse,
    responses={200: {"content": {"application/json": {"schema": {"type": "string", "format": "binary"}}}}},
    summary="Download an export with fresh authorization",
)
async def download_export(
    export_id: UUID,
    request: Request,
    principal: PrincipalDep,
    session: SessionDep,
) -> Response:
    """Serve a private JSON attachment only while every pinned dependency remains authorized."""
    content = await ExportService(session).download(principal, export_id)
    if isinstance(content, AppError):
        denied = await handle_app_error(request, content)
        denied.headers["Cache-Control"] = _PRIVATE_CACHE
        return denied
    return StreamingResponse(
        content,
        media_type="application/json",
        headers={
            "Content-Disposition": 'attachment; filename="temuriset-export.json"',
            "Cache-Control": _PRIVATE_CACHE,
            "X-Content-Type-Options": "nosniff",
        },
    )
