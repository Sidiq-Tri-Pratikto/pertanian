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
CORE = "core"

# Status moves here feature by feature, in the pull request that ships it. Nothing may claim more than exists.
CAPABILITIES = {
    CORE: CapabilityResponse(id=CORE, optional=False, status=CapabilityStatus.AVAILABLE),
    "cost": CapabilityResponse(id="cost", optional=True, status=CapabilityStatus.PLANNED),
    "schedule": CapabilityResponse(id="schedule", optional=True, status=CapabilityStatus.PLANNED),
    "output": CapabilityResponse(id="output", optional=True, status=CapabilityStatus.PLANNED),
}
ADAPTERS = (
    AdapterResponse(id="demo", status=CapabilityStatus.SIMULATED),
    AdapterResponse(id="csv", status=CapabilityStatus.AVAILABLE),
    AdapterResponse(id="shelly-plug-pm-gen3", status=CapabilityStatus.PLANNED),
    AdapterResponse(id="tp-link", status=CapabilityStatus.PLANNED),
)
POLICIES = (
    PolicyResponse(id="baseline", version=1),
    PolicyResponse(id="change", version=1),
    PolicyResponse(id="stale", version=1),
)
COMPOSITIONS: dict[str, tuple[int, tuple[str, ...]]] = {
    "core-plus-optional": (1, (CORE, "cost", "schedule", "output")),
    "core-only": (1, (CORE,)),
}


def validate_composition(capability_ids: tuple[str, ...]) -> None:
    """Reject a capability selection the product does not support.

    Args:
        capability_ids (tuple[str, ...]): The selected capabilities.

    Raises:
        ValueError: When the core is missing or a capability is unknown.
    """
    if CORE not in capability_ids:
        raise ValueError("The measurement, scope, quality and evidence core is required.")
    unknown = sorted(set(capability_ids) - set(CAPABILITIES))
    if unknown:
        raise ValueError(f"Unsupported capabilities: {', '.join(unknown)}.")


def build_manifest(composition_id: str, *, meter_pilot_enabled: bool = False) -> CapabilityManifestResponse:
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
        capabilities=[CAPABILITIES[capability_id] for capability_id in capability_ids],
        adapters=[
            adapter.model_copy(update={"status": CapabilityStatus.AVAILABLE})
            if meter_pilot_enabled and adapter.id == "shelly-plug-pm-gen3"
            else adapter
            for adapter in ADAPTERS
        ],
        policies=list(POLICIES),
    )
