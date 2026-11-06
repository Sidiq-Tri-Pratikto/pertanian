"""Preflight and briefs: see exactly what would be sent, edit it, export it."""

from typing import Literal
from uuid import UUID

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from app.briefs.model.schema import BriefResponse, PreflightRequest, PreflightResponse
from app.briefs.service.service import BriefService
from app.core.database import SessionDep
from app.core.security import PrincipalDep

router = APIRouter(tags=["briefs"])


@router.post("/pitches/preflight", summary="Check a pitch before sending")
async def preflight(body: PreflightRequest, principal: PrincipalDep, session: SessionDep) -> PreflightResponse:
    """Evaluate one owned source against one opportunity and pin every version under a 30-minute token.

    Nothing is sent. Repeating it is safe and gives a new token.

    Args:
        body (PreflightRequest): Source and target.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.

    Returns:
        PreflightResponse: Recipient, versions, rows, shareable files and the template brief.
    """
    return await BriefService(session).preflight(principal, body)


@router.get("/briefs/{brief_id}", summary="Read a brief")
async def read_brief(brief_id: UUID, principal: PrincipalDep, session: SessionDep) -> BriefResponse:
    """Read one's own brief with its references.

    Args:
        brief_id (UUID): The brief.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.

    Returns:
        BriefResponse: The brief.
    """
    return await BriefService(session).read(principal, brief_id)


@router.post("/briefs/{brief_id}/summary", summary="Ask for a shorter brief")
async def summarize_brief(brief_id: UUID, principal: PrincipalDep, session: SessionDep) -> BriefResponse:
    """Ask the summarizer. When it is off, fails or adds anything untraceable, the template brief comes back.

    Args:
        brief_id (UUID): The brief.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.

    Returns:
        BriefResponse: The brief, with ``summarizer_status``.
    """
    return await BriefService(session).summarize(principal, brief_id)


@router.get(
    "/briefs/{brief_id}/export",
    summary="Export a brief",
    response_class=PlainTextResponse,
    responses={200: {"content": {"text/plain": {}, "text/markdown": {}}}},
)
async def export_brief(
    brief_id: UUID,
    principal: PrincipalDep,
    session: SessionDep,
    format: Literal["md", "txt"] = "md",  # noqa: A002
) -> PlainTextResponse:
    """Export under today's permissions; a sentence resting on a file no longer accessible is redacted.

    Args:
        brief_id (UUID): The brief.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.
        format (str, optional): ``md`` or ``txt``. Defaults to "md".

    Returns:
        PlainTextResponse: The export.
    """
    text = await BriefService(session).export(principal, brief_id, format)
    return PlainTextResponse(text, media_type="text/markdown" if format == "md" else "text/plain")
