"""The one refusal for a capability this deployment does not run."""

from fastapi import Depends
from fastapi.params import Depends as DependsParam

from app.capabilities.service.service import CAPABILITIES, select_capabilities
from app.core.errors import codes
from app.core.errors.base import AppError
from app.core.settings import get_settings


class CapabilityUnavailableError(AppError):
    """The request needs a capability that is not selected for this deployment."""

    code = codes.APP_CAPABILITY_UNAVAILABLE


def require_capability(capability_id: str) -> DependsParam:
    """Guard a route with a capability, whatever client calls it (FR23).

    Use it in ``dependencies=[...]``. FastAPI runs it before the request body is validated, so a disabled
    capability never reports field errors and its route never runs.

    Args:
        capability_id (str): A capability from the catalog.

    Returns:
        DependsParam: The dependency.

    Raises:
        ValueError: At import time, when the capability is not in the catalog.
    """
    if capability_id not in CAPABILITIES:
        raise ValueError(f"Unknown capability: {capability_id}.")

    async def guard() -> None:
        settings = get_settings()
        if capability_id not in select_capabilities(settings.composition, settings.composition_overrides):
            raise CapabilityUnavailableError()

    return Depends(guard)
