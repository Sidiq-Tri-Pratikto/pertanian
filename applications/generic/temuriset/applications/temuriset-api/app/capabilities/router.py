"""Capability manifest endpoint."""

from fastapi import APIRouter

from app.capabilities.model.schema import CapabilityManifestResponse
from app.capabilities.service.service import build_manifest
from app.core.settings import get_settings

router = APIRouter(prefix="/capabilities", tags=["capabilities"])


@router.get("", summary="Describe this deployment")
async def get_capabilities() -> CapabilityManifestResponse:
    """Return the non-secret manifest clients use to explain what is available.

    Returns:
        CapabilityManifestResponse: The manifest.
    """
    return build_manifest(get_settings().composition)
