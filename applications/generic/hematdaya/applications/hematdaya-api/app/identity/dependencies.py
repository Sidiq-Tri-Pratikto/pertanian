"""The acting principal of a request, resolved in one place for every route."""

from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import SessionDep
from app.core.errors.base import UnauthorizedError
from app.identity.model.models import PrincipalModel

PrincipalResolver = Callable[[str, AsyncSession], Awaitable[PrincipalModel | None]]
"""Maps a bearer token to its principal, returns None when the token is not its kind, or raises a typed error."""

_resolvers: list[PrincipalResolver] = []


def register_principal_resolver(resolver: PrincipalResolver) -> None:
    """Accept another credential kind. Demo sessions register in 008, accounts in 036.

    Args:
        resolver (PrincipalResolver): The resolver to try, in registration order.
    """
    if resolver not in _resolvers:
        _resolvers.append(resolver)


def bearer_token(request: Request) -> str | None:
    """Read the bearer token without judging it.

    Args:
        request (Request): The current request.

    Returns:
        str | None: The token, or None when the header is missing or malformed.
    """
    scheme, _, token = request.headers.get("authorization", "").partition(" ")
    token = token.strip()
    if scheme.lower() != "bearer" or not token or " " in token:
        return None
    return token


async def get_current_principal(request: Request, session: SessionDep) -> PrincipalModel:
    """Resolve the acting principal, failing closed.

    Args:
        request (Request): The current request.
        session (AsyncSession): The request's session.

    Returns:
        PrincipalModel: The principal the credential belongs to.

    Raises:
        UnauthorizedError: When no resolver accepts the request. The reason is never disclosed.
    """
    token = bearer_token(request)
    if token is not None:
        for resolver in _resolvers:
            principal = await resolver(token, session)
            if principal is not None:
                return principal
    raise UnauthorizedError()


PrincipalDep = Annotated[PrincipalModel, Depends(get_current_principal)]
