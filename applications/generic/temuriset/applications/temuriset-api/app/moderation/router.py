"""HTTP routes for private reports and scoped operator case handling."""

from functools import partial
from uuid import UUID

from fastapi import APIRouter, Request, Response, status
from fastapi.responses import StreamingResponse

from app.core.database import SessionDep
from app.core.security import PrincipalDep
from app.core.settings import get_settings
from app.core.types import MAX_LIMIT, Limit
from app.documents.router import stream_download
from app.documents.service.service import DocumentService
from app.moderation.model.schema import (
    CreatePrivacyRequest,
    CreateReportRequest,
    FulfillPrivacyRequest,
    OperatorActionRequest,
    OperatorReportResponse,
    PrivacyExportResponse,
    PrivacyRequestResponse,
    ReportResponse,
    ReportStatus,
)
from app.moderation.service.privacy import PrivacyService
from app.moderation.service.reports import ReportService
from app.platform.model.schema import OperationResult
from app.platform.service.idempotency import Idempotency, idempotent

router = APIRouter(tags=["moderation"])


async def private_actor(principal: PrincipalDep) -> UUID:
    """Scope retries to the account's personal party, even in organization context."""
    return principal.personal_party_id


async def operator_actor(principal: PrincipalDep, session: SessionDep) -> UUID:
    """Check the live operator grant before the platform can replay a private case response."""
    await ReportService(session).authorize_operator(principal)
    return principal.personal_party_id


@router.post("/reports", status_code=status.HTTP_201_CREATED, summary="File a private report")
async def create_report(
    body: CreateReportRequest,
    principal: PrincipalDep,
    session: SessionDep,
    operation: Idempotency = idempotent("private.reports.create", actor=private_actor),
) -> ReportResponse:
    """File a case and return its receipt."""
    report = await ReportService(session).create(principal, body, operation.operation_id)
    return await operation.respond(  # type: ignore[return-value]
        report, status_code=201, result=OperationResult(type="report", id=str(report.id))
    )


@router.get("/reports", summary="List my private reports")
async def list_reports(principal: PrincipalDep, session: SessionDep) -> list[ReportResponse]:
    """Show only the signed-in account's reports."""
    return await ReportService(session).list_mine(principal)


@router.get("/reports/{report_id}", summary="Read my report status")
async def read_report(report_id: UUID, principal: PrincipalDep, session: SessionDep) -> ReportResponse:
    """Read the reporter's case receipt."""
    return await ReportService(session).read(principal, report_id)


@router.get("/operator/reports", summary="List the scoped moderation queue")
async def operator_reports(
    principal: PrincipalDep, session: SessionDep, status: ReportStatus | None = None, limit: Limit = MAX_LIMIT
) -> list[OperatorReportResponse]:
    """Return the bounded queue to a currently authorized operator."""
    return await ReportService(session).queue(principal, status, limit)


@router.post("/operator/reports/{report_id}/actions", summary="Apply an audited case action")
async def act_on_report(
    report_id: UUID,
    body: OperatorActionRequest,
    principal: PrincipalDep,
    session: SessionDep,
    operation: Idempotency = idempotent("private.reports.act", actor=operator_actor),
) -> OperatorReportResponse:
    """Apply a versioned operator action with a private reason."""
    report = await ReportService(session).act(principal, report_id, body, operation.operation_id)
    return await operation.respond(report)  # type: ignore[return-value]


@router.get(
    "/operator/reports/{report_id}/documents/{document_id}/versions/{number}/content",
    summary="Download an explicitly granted case file",
)
async def download_case_file(
    report_id: UUID, document_id: UUID, number: int, request: Request, principal: PrincipalDep, session: SessionDep
) -> StreamingResponse:
    """Stream a protected version after checking the case and exact file grant."""
    reports = ReportService(session)
    await reports.require_case(principal, report_id)
    grant = partial(reports.file_grant, principal, report_id)
    file = await DocumentService(session, get_settings()).case_download(
        principal, report_id, document_id, number, grant
    )
    return stream_download(file, request.headers.get("range"))


@router.post("/privacy-requests", status_code=status.HTTP_201_CREATED, summary="Open a privacy request")
async def create_privacy_request(
    body: CreatePrivacyRequest,
    principal: PrincipalDep,
    session: SessionDep,
    operation: Idempotency = idempotent("private.privacy.create", actor=private_actor),
) -> PrivacyRequestResponse:
    """Return an export receipt or a policy-based deletion plan."""
    receipt = await PrivacyService(session).create(principal, body, operation.operation_id)
    return await operation.respond(  # type: ignore[return-value]
        receipt, status_code=201, result=OperationResult(type="privacy_request", id=str(receipt.id))
    )


@router.get("/privacy-requests", summary="List my privacy requests")
async def list_privacy_requests(principal: PrincipalDep, session: SessionDep) -> list[PrivacyRequestResponse]:
    """Return the signed-in account's request receipts."""
    return await PrivacyService(session).list_mine(principal)


@router.get("/privacy-requests/{request_id}", summary="Read my privacy request")
async def read_privacy_request(
    request_id: UUID, principal: PrincipalDep, session: SessionDep
) -> PrivacyRequestResponse:
    """Return a current receipt for a request the account owns."""
    return await PrivacyService(session).read(principal, request_id)


@router.get("/privacy-requests/{request_id}/export", summary="Download my authorized export")
async def download_privacy_export(
    request_id: UUID, principal: PrincipalDep, session: SessionDep, response: Response
) -> PrivacyExportResponse:
    """Produce a fresh, account-authorized JSON export."""
    result = await PrivacyService(session).export(principal, request_id)
    response.headers["Content-Disposition"] = 'attachment; filename="temuriset-data.json"'
    response.headers["Cache-Control"] = "private, no-store"
    return result


@router.get("/operator/privacy-requests", summary="List pending deletions")
async def operator_privacy_requests(
    principal: PrincipalDep, session: SessionDep, limit: Limit = MAX_LIMIT
) -> list[PrivacyRequestResponse]:
    """List pending requests under the live moderation scope."""
    return await PrivacyService(session).operator_queue(principal, limit)


@router.post("/operator/privacy-requests/{request_id}/fulfill", summary="Begin policy-based deletion")
async def fulfill_privacy_request(
    request_id: UUID,
    body: FulfillPrivacyRequest,
    principal: PrincipalDep,
    session: SessionDep,
    operation: Idempotency = idempotent("private.privacy.fulfill", actor=operator_actor),
) -> PrivacyRequestResponse:
    """Accept an authorized versioned decision and return the current processing state."""
    receipt = await PrivacyService(session).fulfill(principal, request_id, body, operation.operation_id)
    return await operation.respond(receipt)  # type: ignore[return-value]
