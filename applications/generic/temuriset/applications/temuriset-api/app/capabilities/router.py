"""Capability manifest endpoint."""

from fastapi import APIRouter

from app.capabilities.model.schema import CapabilityManifestResponse
from app.capabilities.service.service import build_manifest
from app.core.settings import get_settings
from app.identity.service.mailbox_service import loopback_mail_enabled

router = APIRouter(prefix="/capabilities", tags=["capabilities"])


@router.get("", summary="Describe this deployment")
async def get_capabilities() -> CapabilityManifestResponse:
    """Return the non-secret manifest clients use to explain what is available.

    Returns:
        CapabilityManifestResponse: The manifest.
    """
    settings = get_settings()
    manifest = build_manifest(
        settings.composition,
        settings.composition_overrides,
        storage_adapter=settings.storage_adapter,
        scanner_adapter=settings.file_scanner,
        summary_relay_enabled=settings.summary_adapter == "local-relay",
        email_relay=loopback_mail_enabled(settings),
        calendar_enabled=settings.calendar_enabled,
    )
    manifest.demo = settings.demo_mode
    return manifest
