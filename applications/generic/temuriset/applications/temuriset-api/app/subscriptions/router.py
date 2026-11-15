"""Investor quick subscriptions and teasers. No route here needs sign-in; links carry their own tokens."""

from uuid import UUID

from fastapi import APIRouter, Request, status

from app.core.database import SessionDep
from app.identity.router import _client_address
from app.subscriptions.model.schema import (
    SubscribeRequest,
    SubscribeResponse,
    SubscriptionResponse,
    TeaserResponse,
    TokenRequest,
    UpdateTopicsRequest,
)
from app.subscriptions.service.service import SubscriptionService

router = APIRouter(tags=["subscriptions"])


@router.post("/subscriptions", status_code=status.HTTP_202_ACCEPTED, summary="Subscribe to investor alerts")
async def subscribe(body: SubscribeRequest, request: Request, session: SessionDep) -> SubscribeResponse:
    """Store a pending subscription and email a confirmation link; the answer is the same for every email.

    Args:
        body (SubscribeRequest): Email, topics and locale.
        request (Request): For the client address used by the rate limit.
        session (SessionDep): Database session.

    Returns:
        SubscribeResponse: ``check_email``.
    """
    return await SubscriptionService(session).subscribe(body, _client_address(request))


@router.post("/subscriptions/confirm", summary="Confirm a subscription")
async def confirm(body: TokenRequest, session: SessionDep) -> SubscriptionResponse:
    """Activate a subscription from its emailed link, by a deliberate POST.

    Args:
        body (TokenRequest): The confirmation token.
        session (SessionDep): Database session.

    Returns:
        SubscriptionResponse: The subscription and a manage token.
    """
    return await SubscriptionService(session).confirm(body.token)


@router.post("/subscriptions/manage", summary="Read a subscription")
async def read(body: TokenRequest, session: SessionDep) -> SubscriptionResponse:
    """Read a subscription through a manage link; the token travels in the body, never in a logged URL.

    Args:
        body (TokenRequest): The manage token.
        session (SessionDep): Database session.

    Returns:
        SubscriptionResponse: The subscription.
    """
    return await SubscriptionService(session).read(body.token)


@router.put("/subscriptions/manage", summary="Change subscription topics")
async def update(body: UpdateTopicsRequest, session: SessionDep) -> SubscriptionResponse:
    """Change topics through a manage link.

    Args:
        body (UpdateTopicsRequest): The manage token and topics.
        session (SessionDep): Database session.

    Returns:
        SubscriptionResponse: The subscription.
    """
    return await SubscriptionService(session).update(body.token, body.topics)


@router.post("/subscriptions/unsubscribe", summary="Unsubscribe")
async def unsubscribe(body: TokenRequest, session: SessionDep) -> SubscriptionResponse:
    """Stop all alerts and digests to the email.

    Args:
        body (TokenRequest): A manage token.
        session (SessionDep): Database session.

    Returns:
        SubscriptionResponse: The subscription.
    """
    return await SubscriptionService(session).unsubscribe(body.token)


@router.get("/teasers/inventions/{invention_id}", summary="Read an invention teaser")
async def teaser(invention_id: UUID, session: SessionDep) -> TeaserResponse:
    """Read the brief public summary of an invention its managing party included in investor alerts.

    Args:
        invention_id (UUID): The invention.
        session (SessionDep): Database session.

    Returns:
        TeaserResponse: Title, summary, sector, stage, keywords and inventor name.
    """
    return await SubscriptionService(session).teaser(invention_id)
