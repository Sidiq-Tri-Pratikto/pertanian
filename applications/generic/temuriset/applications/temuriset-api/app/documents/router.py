"""Documents: upload intents, streamed upload, owner views, grants, and the download gateway."""

import re
from uuid import UUID

from fastapi import APIRouter, Request, status
from fastapi.responses import StreamingResponse

from app.core.database import SessionDep
from app.core.security import PrincipalDep
from app.core.settings import get_settings
from app.documents.model.schema import (
    DocumentResponse,
    GrantRequest,
    GrantResponse,
    RevokedResponse,
    RevokeRequest,
    UploadedResponse,
    UploadIntentRequest,
    UploadIntentResponse,
)
from app.documents.service.service import DocumentService, Download
from app.documents.service.storage_service import LocalStorage
from app.platform.model.schema import OperationResult
from app.platform.service.idempotency import Idempotency, idempotent

router = APIRouter(tags=["documents"])
_RANGE = re.compile(r"^bytes=(\d*)-(\d*)$")


@router.post("/documents/upload-intents", status_code=status.HTTP_201_CREATED, summary="Declare an upload")
async def create_upload_intent(
    body: UploadIntentRequest, principal: PrincipalDep, session: SessionDep
) -> UploadIntentResponse:
    """Refuse an unsupported type or a size over the limit before any byte is sent.

    Args:
        body (UploadIntentRequest): Title, kind, media type and size.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.

    Returns:
        UploadIntentResponse: Where to send the bytes.
    """
    return await DocumentService(session, get_settings()).create_intent(principal, body)


@router.put(
    "/documents/upload-intents/{intent_id}/content", status_code=status.HTTP_202_ACCEPTED, summary="Send the bytes"
)
async def upload_content(
    intent_id: UUID, request: Request, principal: PrincipalDep, session: SessionDep
) -> UploadedResponse:
    """Stream the file into quarantine; it becomes available only after the scan.

    Args:
        intent_id (UUID): The intent.
        request (Request): The streamed body.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.

    Returns:
        UploadedResponse: The new version and its file state.
    """
    return await DocumentService(session, get_settings()).receive(principal, intent_id, request.stream())


@router.get("/documents", summary="List my documents")
async def list_documents(principal: PrincipalDep, session: SessionDep) -> list[DocumentResponse]:
    """List the acting party's documents.

    Args:
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.

    Returns:
        list[DocumentResponse]: Documents with versions and grants.
    """
    return await DocumentService(session, get_settings()).list_mine(principal)


@router.get("/documents/{document_id}", summary="Read a document as its owner")
async def read_document(document_id: UUID, principal: PrincipalDep, session: SessionDep) -> DocumentResponse:
    """Read versions, their three states, and grants.

    Args:
        document_id (UUID): The document.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.

    Returns:
        DocumentResponse: The document.
    """
    return await DocumentService(session, get_settings()).owner_view(principal, document_id)


@router.post("/documents/{document_id}/grants", status_code=status.HTTP_201_CREATED, summary="Share one version")
async def grant_document(
    document_id: UUID,
    body: GrantRequest,
    principal: PrincipalDep,
    session: SessionDep,
    operation: Idempotency = idempotent("documents.grant"),
) -> GrantResponse:
    """Share one version with one party for one purpose.

    Args:
        document_id (UUID): The document.
        body (GrantRequest): Version, grantee and purpose.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.
        operation (Idempotency): Replays a retried request.

    Returns:
        GrantResponse: The grant.
    """
    grant = await DocumentService(session, get_settings()).grant(principal, document_id, body)
    return await operation.respond(  # type: ignore[return-value]
        grant, status_code=201, result=OperationResult(type="document_grant", id=str(grant.id))
    )


@router.post("/grants/{grant_id}/revoke", summary="Revoke a grant")
async def revoke_grant(
    grant_id: UUID,
    body: RevokeRequest,
    principal: PrincipalDep,
    session: SessionDep,
    operation: Idempotency = idempotent("documents.revoke"),
) -> RevokedResponse:
    """Block new downloads. Copies already delivered cannot be recalled, and the answer says so.

    Args:
        grant_id (UUID): The grant.
        body (RevokeRequest): Acting party.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.
        operation (Idempotency): Replays a retried request.

    Returns:
        RevokedResponse: The outcome.
    """
    result = await DocumentService(session, get_settings()).revoke(principal, grant_id, body.acting_party_id)
    return await operation.respond(result, result=OperationResult(type="document_grant", id=str(grant_id)))  # type: ignore[return-value]


@router.get("/documents/{document_id}/versions/{number}/content", summary="Download a version")
async def download(
    document_id: UUID, number: int, request: Request, principal: PrincipalDep, session: SessionDep
) -> StreamingResponse:
    """Stream a version after re-authorizing this exact request, ranges included. No storage URL is ever issued.

    Args:
        document_id (UUID): The document.
        number (int): The version.
        request (Request): Carries the optional ``Range`` header.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.

    Returns:
        StreamingResponse: The bytes, or the requested range with 206.
    """
    byte_range = request.headers.get("range")
    file = await DocumentService(session, get_settings()).authorize_download(principal, document_id, number, byte_range)
    return stream_download(file, byte_range)


def stream_download(file: Download, byte_range: str | None) -> StreamingResponse:
    """Stream an already authorized document using the shared range and cache policy."""
    start, end, partial = 0, file.size_bytes - 1, False
    match = _RANGE.match(byte_range or "")
    if match and (match[1] or match[2]):
        if match[1]:
            start = int(match[1])
            end = min(int(match[2]), end) if match[2] else end
        else:
            start = max(file.size_bytes - int(match[2]), 0)
        partial = start <= end
        if not partial:
            start, end = 0, file.size_bytes - 1
    headers = {
        "Content-Disposition": f'attachment; filename="{file.filename}"',
        "Content-Length": str(end - start + 1),
        "Accept-Ranges": "bytes",
        "Cache-Control": "private, no-store",
        "X-Content-Type-Options": "nosniff",
    }
    if partial:
        headers["Content-Range"] = f"bytes {start}-{end}/{file.size_bytes}"
    storage = LocalStorage(get_settings().storage_path)
    return StreamingResponse(
        storage.read(file.storage_key, start, end),
        status_code=206 if partial else 200,
        media_type=file.media_type,
        headers=headers,
    )
