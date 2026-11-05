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
    CORE: CapabilityResponse(id=CORE, optional=False, status=CapabilityStatus.AVAILABLE),
    "company_funding": CapabilityResponse(id="company_funding", optional=True, status=CapabilityStatus.AVAILABLE),
    "organization_review": CapabilityResponse(id="organization_review", optional=True, status=CapabilityStatus.PLANNED),
    # Gated retrieval (spec 045); no composition selects them, but an override may.
    "dense_retrieval": CapabilityResponse(id="dense_retrieval", optional=True, status=CapabilityStatus.PLANNED),
    "reranking": CapabilityResponse(id="reranking", optional=True, status=CapabilityStatus.PLANNED),
}
# A capability works only beside the ones it builds on.
DEPENDENCIES: dict[str, tuple[str, ...]] = {"reranking": ("dense_retrieval",)}
ADAPTERS = (
    AdapterResponse(id="object-storage", status=CapabilityStatus.AVAILABLE),
    AdapterResponse(id="file-scanner", status=CapabilityStatus.AVAILABLE),
    AdapterResponse(id="lexical-rules", status=CapabilityStatus.AVAILABLE),
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
        ValueError: When the core is missing, a capability is unknown, or a dependency is not selected.
    """
    if CORE not in capability_ids:
        raise ValueError("The portfolio, matching and collaboration core is required.")
    unknown = sorted(set(capability_ids) - set(CAPABILITIES))
    if unknown:
        raise ValueError(f"Unsupported capabilities: {', '.join(unknown)}.")
    for capability_id in capability_ids:
        missing = [needed for needed in DEPENDENCIES.get(capability_id, ()) if needed not in capability_ids]
        if missing:
            raise ValueError(f"Capability {capability_id} needs {', '.join(missing)}.")


def select_capabilities(composition_id: str, overrides: dict[str, bool] | None = None) -> tuple[str, ...]:
    """Resolve the capabilities a deployment runs: its composition, then any overrides.

    Args:
        composition_id (str): A supported composition.
        overrides (dict[str, bool] | None, optional): Capabilities to switch on (True) or off (False).
            Defaults to None.

    Returns:
        tuple[str, ...]: The selected capability ids, in catalog order.

    Raises:
        ValueError: When the composition is unsupported or the result is not a supported selection.
    """
    if composition_id not in COMPOSITIONS:
        raise ValueError(f"Unsupported composition: {composition_id}.")
    selected = set(COMPOSITIONS[composition_id][1])
    unknown = sorted(set(overrides or {}) - set(CAPABILITIES))
    if unknown:
        raise ValueError(f"Unsupported capabilities: {', '.join(unknown)}.")
    for capability_id, enabled in (overrides or {}).items():
        (selected.add if enabled else selected.discard)(capability_id)
    capability_ids = tuple(capability_id for capability_id in CAPABILITIES if capability_id in selected)
    validate_composition(capability_ids)
    return capability_ids


def build_manifest(composition_id: str, overrides: dict[str, bool] | None = None) -> CapabilityManifestResponse:
    """Build the manifest for one composition.

    Args:
        composition_id (str): A supported composition.
        overrides (dict[str, bool] | None, optional): Capability overrides. Defaults to None.

    Returns:
        CapabilityManifestResponse: The manifest. A capability that is not selected is absent, not ``planned``.

    Raises:
        ValueError: When the composition or the overrides are not supported.
    """
    capability_ids = select_capabilities(composition_id, overrides)
    return CapabilityManifestResponse(
        schema_version=MANIFEST_SCHEMA_VERSION,
        source_release=SOURCE_RELEASE,
        composition=CompositionResponse(id=composition_id, version=COMPOSITIONS[composition_id][0]),
        default_locale=DEFAULT_LOCALE,
        supported_currencies=list(SUPPORTED_CURRENCIES),
        capabilities=[CAPABILITIES[capability_id] for capability_id in capability_ids],
        adapters=list(ADAPTERS),
        policies=list(POLICIES),
    )
