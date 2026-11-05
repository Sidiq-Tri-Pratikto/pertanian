"""Who is calling: the session principal, and the Origin check that protects cookie-bearing writes."""

from typing import Annotated

from fastapi import Depends, Request
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.database import SessionDep
from app.core.errors import codes
from app.core.errors.base import AppError
from app.core.errors.handlers import respond
from app.core.errors.public import public_error_for_code
from app.core.errors.recorder import record_failure
from app.core.settings import get_settings
from app.identity.service.service import IdentityService, Principal

SESSION_COOKIE = "tr_session"
_SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


class UnauthenticatedError(AppError):
    """The request has no live session."""

    code = codes.APP_UNAUTHENTICATED


class ForbiddenError(AppError):
    """The caller may see the resource but not do this."""

    code = codes.APP_FORBIDDEN


async def current_principal(request: Request, session: SessionDep) -> Principal:
    """Resolve the session cookie to a principal, on every request.

    Args:
        request (Request): The request.
        session (SessionDep): Database session.

    Returns:
        Principal: Who is signed in.

    Raises:
        UnauthenticatedError: No cookie, or an unknown, expired or revoked session.
    """
    token = request.cookies.get(SESSION_COOKIE)
    principal = await IdentityService(session, get_settings()).principal_for(token) if token else None
    if principal is None:
        raise UnauthenticatedError()
    return principal


PrincipalDep = Annotated[Principal, Depends(current_principal)]


class OriginCheckMiddleware:
    """Refuse an unsafe request that carries the session cookie unless it comes from the web origin.

    Browsers send ``Origin`` on every cross-site and same-site POST, so a forged form on another site never reaches
    a handler. Requests without the cookie have nothing to forge.
    """

    def __init__(self, app: ASGIApp) -> None:
        """Wrap the application.

        Args:
            app (ASGIApp): The downstream application.
        """
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Check the origin before any handler runs.

        Args:
            scope (Scope): ASGI scope.
            receive (Receive): ASGI receive.
            send (Send): ASGI send.
        """
        if scope["type"] == "http" and scope["method"] not in _SAFE_METHODS:
            request = Request(scope)
            if SESSION_COOKIE in request.cookies and request.headers.get("origin") != get_settings().web_origin:
                error = ForbiddenError()
                public = public_error_for_code(error.code)
                record_failure(error, operation=scope.get("path", "unmatched"), http_status=public.http_status)
                await respond(public, error.reference_id)(scope, receive, send)
                return
        await self.app(scope, receive, send)
