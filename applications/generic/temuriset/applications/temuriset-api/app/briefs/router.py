"""Preflight and briefs: see exactly what would be sent, edit it, export it."""

from functools import partial
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.responses import PlainTextResponse

from app.briefs.model.schema import BriefResponse, PreflightRequest, PreflightResponse, SummaryProvenance
from app.briefs.service.service import BriefService
from app.briefs.service.summarizer_service import LocalRelaySummarizer, OffSummarizer, SummarizerPort
from app.core.database import SessionDep
from app.core.security import PrincipalDep, current_principal
from app.core.settings import get_settings

router = APIRouter(tags=["briefs"])


def get_summarizer() -> SummarizerPort:
    """Resolve the summary adapter from startup-validated settings."""
    settings = get_settings()
    if settings.summary_adapter != "local-relay" or settings.summary_relay_url is None:
        return OffSummarizer()
    return LocalRelaySummarizer(
        endpoint=settings.summary_relay_url,
        provenance=SummaryProvenance(
            model_id=settings.summary_model_id,
            model_version=settings.summary_model_version,
            prompt_version=settings.summary_prompt_version,
        ),
    )


SummarizerDep = Annotated[SummarizerPort, Depends(get_summarizer)]


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
async def summarize_brief(
    brief_id: UUID, request: Request, session: SessionDep, summarizer: SummarizerDep
) -> BriefResponse:
    """Ask for an extractive suggestion. A failed or disabled adapter returns the editable template.

    Args:
        brief_id (UUID): The brief.
        request (Request): The request carrying the live session cookie.
        session (SessionDep): Database session.
        summarizer (SummarizerDep): The configured adapter.

    Returns:
        BriefResponse: The brief with its summary status.
    """
    return await BriefService(session, summarizer).summarize(brief_id, partial(current_principal, request, session))


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
