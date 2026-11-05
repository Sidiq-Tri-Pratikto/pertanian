"""The acting party of a request: the session's active party, rechecked on every request (spec 007)."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends

from app.core.security import PrincipalDep


async def current_actor_party_id(principal: PrincipalDep) -> UUID:
    """Return the party the signed-in account acts as.

    Args:
        principal (PrincipalDep): Who is signed in.

    Returns:
        UUID: The active party.
    """
    return principal.active_party_id


ActorDep = Annotated[UUID, Depends(current_actor_party_id)]
