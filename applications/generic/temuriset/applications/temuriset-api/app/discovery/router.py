"""Discovery: search, saved items and private relevance feedback."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, status
from pydantic import BaseModel

from app.core.database import SessionDep
from app.core.security import PrincipalDep
from app.core.types import Limit
from app.discovery.model.schema import DiscoveryResponse, MarkedItem, ResultType, SubjectType
from app.discovery.service.service import HIDDEN, SAVED, DiscoveryService

router = APIRouter(tags=["discovery"])


class ActingPartyRequest(BaseModel):
    """The party the client acts as."""

    acting_party_id: UUID


@router.get("/discovery", summary="Search inventions, funding requests or partners")
async def discover(  # noqa: PLR0913 - one argument per filter
    principal: PrincipalDep,
    session: SessionDep,
    type: ResultType = "inventions",  # noqa: A002 - the public query parameter is called type
    q: Annotated[str, Query(max_length=200)] = "",
    sector: str | None = None,
    stage: str | None = None,
    support_form: str | None = None,
    region: str | None = None,
    purpose: str | None = None,
    intake: str | None = None,
    currency: str | None = None,
    basis: str | None = None,
    amount_min: str | None = None,
    amount_max: str | None = None,
    saved: bool = False,
    cursor: str | None = None,
    limit: Limit = 20,
) -> DiscoveryResponse:
    """Search one result type from the public projection, in sections, with the filters echoed back.

    Args:
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.
        type (ResultType, optional): Result type. Defaults to "inventions".
        q (str, optional): Words in Indonesian or English. Defaults to "".
        sector (str | None, optional): Sector. Defaults to None.
        stage (str | None, optional): Stage. Defaults to None.
        support_form (str | None, optional): Form of support. Defaults to None.
        region (str | None, optional): Region. Defaults to None.
        purpose (str | None, optional): Relationship form. Defaults to None.
        intake (str | None, optional): Partner intake state. Defaults to None.
        currency (str | None, optional): Currency of the amount range. Defaults to None.
        basis (str | None, optional): Basis of the amount range. Defaults to None.
        amount_min (str | None, optional): Lowest amount, as a decimal string. Defaults to None.
        amount_max (str | None, optional): Highest amount, as a decimal string. Defaults to None.
        saved (bool, optional): Only saved items. Defaults to False.
        cursor (str | None, optional): From the previous page. Defaults to None.
        limit (int, optional): Page size, at most 100. Defaults to 20.

    Returns:
        DiscoveryResponse: One page.
    """
    filters = {
        "sector": sector,
        "stage": stage,
        "support_form": support_form,
        "region": region,
        "purpose": purpose,
        "intake": intake,
        "currency": currency,
        "basis": basis,
        "amount_min": amount_min,
        "amount_max": amount_max,
    }
    return await DiscoveryService(session).search(
        principal, type, text=q, filters=filters, saved=saved, cursor=cursor, limit=limit
    )


@router.get("/saved-items", summary="List my saved items")
async def list_saved(principal: PrincipalDep, session: SessionDep) -> list[MarkedItem]:
    """List what the acting party saved.

    Args:
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.

    Returns:
        list[MarkedItem]: Saved subjects.
    """
    return await DiscoveryService(session).list_marked(principal, SAVED)


@router.put("/saved-items/{subject_type}/{subject_id}", summary="Save an item")
async def save_item(
    subject_type: SubjectType, subject_id: UUID, body: ActingPartyRequest, principal: PrincipalDep, session: SessionDep
) -> MarkedItem:
    """Save a published subject for the acting party. Saving twice changes nothing.

    Args:
        subject_type (SubjectType): Subject type.
        subject_id (UUID): Subject.
        body (ActingPartyRequest): Acting party.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.

    Returns:
        MarkedItem: The saved subject.
    """
    return await DiscoveryService(session).mark(principal, body.acting_party_id, SAVED, subject_type, subject_id)


@router.delete(
    "/saved-items/{subject_type}/{subject_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Unsave an item"
)
async def unsave_item(
    subject_type: SubjectType, subject_id: UUID, body: ActingPartyRequest, principal: PrincipalDep, session: SessionDep
) -> None:
    """Remove a saved item.

    Args:
        subject_type (SubjectType): Subject type.
        subject_id (UUID): Subject.
        body (ActingPartyRequest): Acting party.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.
    """
    await DiscoveryService(session).unmark(principal, body.acting_party_id, SAVED, subject_type, subject_id)


@router.get("/discovery-feedback", summary="List items I marked less relevant")
async def list_feedback(principal: PrincipalDep, session: SessionDep) -> list[MarkedItem]:
    """List what the acting party marked "Kurang relevan".

    Args:
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.

    Returns:
        list[MarkedItem]: Hidden subjects.
    """
    return await DiscoveryService(session).list_marked(principal, HIDDEN)


@router.put("/discovery-feedback/{subject_type}/{subject_id}", summary="Mark an item less relevant")
async def hide_item(
    subject_type: SubjectType, subject_id: UUID, body: ActingPartyRequest, principal: PrincipalDep, session: SessionDep
) -> MarkedItem:
    """Hide a subject from the acting party's results only; nothing public changes.

    Args:
        subject_type (SubjectType): Subject type.
        subject_id (UUID): Subject.
        body (ActingPartyRequest): Acting party.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.

    Returns:
        MarkedItem: The hidden subject.
    """
    return await DiscoveryService(session).mark(principal, body.acting_party_id, HIDDEN, subject_type, subject_id)


@router.delete(
    "/discovery-feedback/{subject_type}/{subject_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Show an item again",
)
async def unhide_item(
    subject_type: SubjectType, subject_id: UUID, body: ActingPartyRequest, principal: PrincipalDep, session: SessionDep
) -> None:
    """Undo "Kurang relevan".

    Args:
        subject_type (SubjectType): Subject type.
        subject_id (UUID): Subject.
        body (ActingPartyRequest): Acting party.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.
    """
    await DiscoveryService(session).unmark(principal, body.acting_party_id, HIDDEN, subject_type, subject_id)
