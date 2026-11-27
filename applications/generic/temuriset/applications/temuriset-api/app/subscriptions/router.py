"""Investor quick subscriptions and teasers. No route here needs sign-in; links carry their own tokens."""

from uuid import UUID

from fastapi import APIRouter, Request, Response, status

from app.core.database import SessionDep
from app.identity.router import _client_address
from app.subscriptions.model.schema import (
    FollowLanguageRequest,
    FollowRequest,
    FollowResponse,
    SubscribeRequest,
    SubscribeResponse,
    SubscriptionResponse,
    TeaserResponse,
    TokenRequest,
    UpdateTopicsRequest,
)
from app.subscriptions.service.follows import FollowService
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
    """Read the brief public summary of an invention whose page is published or that is included in alerts.

    Args:
        invention_id (UUID): The invention.
        session (SessionDep): Database session.

    Returns:
        TeaserResponse: Title, summary, sector, stage, keywords and inventor name.
    """
    return await SubscriptionService(session).teaser(invention_id)


@router.get(
    "/teasers/inventions/{invention_id}/photo",
    summary="Read the public page's photo",
    response_class=Response,
    responses={200: {"content": {"image/jpeg": {}, "image/png": {}, "image/webp": {}}}},
)
async def teaser_photo(invention_id: UUID, session: SessionDep) -> Response:
    """Serve the photo the managing party published on the public page, without its metadata.

    Every request checks the page switch, the publication, archive and suspension, and the file again.

    Args:
        invention_id (UUID): The invention.
        session (SessionDep): Database session.

    Returns:
        Response: The image bytes.
    """
    image = await SubscriptionService(session).teaser_photo(invention_id)
    return Response(
        content=image.data,
        media_type=image.media_type,
        headers={
            "X-Content-Type-Options": "nosniff",
            "Content-Security-Policy": "default-src 'none'; sandbox",
            "Cache-Control": "public, max-age=300",
        },
    )


@router.post("/follows", status_code=status.HTTP_202_ACCEPTED, summary="Follow an invention's public updates")
async def follow(body: FollowRequest, request: Request, session: SessionDep) -> SubscribeResponse:
    """Email a confirmation link; the same answer for every address. Needs the invention's public page.

    Args:
        body (FollowRequest): The invention, email and language.
        request (Request): For the client address used by the rate limit.
        session (SessionDep): Database session.

    Returns:
        SubscribeResponse: ``check_email``.
    """
    return await FollowService(session).follow(body, _client_address(request))


@router.post("/follows/preview", summary="Show what a follow confirmation link confirms")
async def preview_follow(body: TokenRequest, session: SessionDep) -> FollowResponse:
    """Read a pending follow without confirming it, so opening the link alone changes nothing.

    Args:
        body (TokenRequest): The confirmation token.
        session (SessionDep): Database session.

    Returns:
        FollowResponse: The follow.
    """
    return await FollowService(session).preview(body.token)


@router.post("/follows/confirm", summary="Confirm following an invention")
async def confirm_follow(body: TokenRequest, session: SessionDep) -> FollowResponse:
    """Start following; only updates first published from now on are sent.

    Args:
        body (TokenRequest): The confirmation token.
        session (SessionDep): Database session.

    Returns:
        FollowResponse: The follow and a manage token.
    """
    return await FollowService(session).confirm(body.token)


@router.post("/follows/manage", summary="Read a follow")
async def read_follow(body: TokenRequest, session: SessionDep) -> FollowResponse:
    """Read a follow through a manage link.

    Args:
        body (TokenRequest): The manage token.
        session (SessionDep): Database session.

    Returns:
        FollowResponse: The follow.
    """
    return await FollowService(session).read(body.token)


@router.put("/follows/manage", summary="Change the follow email language")
async def set_follow_language(body: FollowLanguageRequest, session: SessionDep) -> FollowResponse:
    """Change the language of future update emails.

    Args:
        body (FollowLanguageRequest): The manage token and language.
        session (SessionDep): Database session.

    Returns:
        FollowResponse: The follow.
    """
    return await FollowService(session).set_language(body.token, body.locale)


@router.post("/follows/unfollow", summary="Unfollow an invention")
async def unfollow(body: TokenRequest, session: SessionDep) -> FollowResponse:
    """Stop updates for this invention; repeating it changes nothing.

    Args:
        body (TokenRequest): A manage token.
        session (SessionDep): Database session.

    Returns:
        FollowResponse: The follow.
    """
    return await FollowService(session).unfollow(body.token)
