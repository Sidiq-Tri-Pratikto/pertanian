"""Supported product compositions and the capability manifest."""

from app.capabilities.model.schema import (
    AdapterResponse,
    CapabilityManifestResponse,
    CapabilityResponse,
    CapabilityStatus,
    CompositionResponse,
    PolicyResponse,
)

MANIFEST_SCHEMA_VERSION = 1
SOURCE_RELEASE = "0.1.0"
DEFAULT_LOCALE = "id"
# Amounts are compared only within one currency; there is no conversion (PRD section 10).
SUPPORTED_CURRENCIES = ("IDR", "USD")
CORE = "core"

# Status moves here feature by feature, in the pull request that ships it. Nothing may claim more than exists.
CAPABILITIES = {
    CORE: CapabilityResponse(id=CORE, optional=False, status=CapabilityStatus.PLANNED),
    "company_funding": CapabilityResponse(id="company_funding", optional=True, status=CapabilityStatus.PLANNED),
    "organization_review": CapabilityResponse(id="organization_review", optional=True, status=CapabilityStatus.PLANNED),
}
ADAPTERS = (
    AdapterResponse(id="object-storage", status=CapabilityStatus.PLANNED),
    AdapterResponse(id="file-scanner", status=CapabilityStatus.PLANNED),
    AdapterResponse(id="lexical-rules", status=CapabilityStatus.PLANNED),
    AdapterResponse(id="ics-export", status=CapabilityStatus.PLANNED),
)
POLICIES = (
    PolicyResponse(id="matching-weights", version=1),
    PolicyResponse(id="fit-thresholds", version=1),
    PolicyResponse(id="pitch-rate-limit", version=1),
    PolicyResponse(id="resubmission-pause", version=1),
    PolicyResponse(id="proposal-expiry", version=1),
    PolicyResponse(id="idempotency-retention", version=1),
)
# The three compositions PRD section 21 asks to prove: the generic base, review enabled, company funding disabled.
COMPOSITIONS: dict[str, tuple[int, tuple[str, ...]]] = {
    "generic-base": (1, (CORE, "company_funding")),
    "generic-with-review": (1, (CORE, "company_funding", "organization_review")),
    "project-support-only": (1, (CORE,)),
}


def validate_composition(capability_ids: tuple[str, ...]) -> None:
    """Reject a capability selection the product does not support.

    Args:
        capability_ids (tuple[str, ...]): The selected capabilities.

    Raises:
        ValueError: When the core is missing or a capability is unknown.
    """
    if CORE not in capability_ids:
        raise ValueError("The portfolio, matching and collaboration core is required.")
    unknown = sorted(set(capability_ids) - set(CAPABILITIES))
    if unknown:
        raise ValueError(f"Unsupported capabilities: {', '.join(unknown)}.")


def build_manifest(composition_id: str) -> CapabilityManifestResponse:
    """Build the manifest for one composition.

    Args:
        composition_id (str): A supported composition.

    Returns:
        CapabilityManifestResponse: The manifest.

    Raises:
        ValueError: When the composition is not supported.
    """
    if composition_id not in COMPOSITIONS:
        raise ValueError(f"Unsupported composition: {composition_id}.")
    version, capability_ids = COMPOSITIONS[composition_id]
    validate_composition(capability_ids)
    return CapabilityManifestResponse(
        schema_version=MANIFEST_SCHEMA_VERSION,
        source_release=SOURCE_RELEASE,
        composition=CompositionResponse(id=composition_id, version=version),
        default_locale=DEFAULT_LOCALE,
        supported_currencies=list(SUPPORTED_CURRENCIES),
        capabilities=[CAPABILITIES[capability_id] for capability_id in capability_ids],
        adapters=list(ADAPTERS),
        policies=list(POLICIES),
    )
