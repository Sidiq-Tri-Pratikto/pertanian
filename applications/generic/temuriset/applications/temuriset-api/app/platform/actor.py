"""The acting party of a request."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header

from app.core.security import UnauthenticatedError
from app.core.settings import get_settings


async def current_actor_party_id(x_party_id: Annotated[UUID | None, Header()] = None) -> UUID:
    """Resolve the acting party.

    ponytail: a trusted ``X-Party-Id`` header stands in for sessions until spec 007 resolves the acting party from
    the session. It is honoured only in development, so no deployed service trusts a client-chosen identity.

    Args:
        x_party_id (UUID | None, optional): The placeholder header. Defaults to None.

    Returns:
        UUID: The acting party.

    Raises:
        UnauthenticatedError: Outside development, or when the header is missing.
    """
    if get_settings().environment != "development" or x_party_id is None:
        raise UnauthenticatedError()
    return x_party_id


ActorDep = Annotated[UUID, Depends(current_actor_party_id)]
