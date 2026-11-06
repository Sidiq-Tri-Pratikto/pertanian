"""The one service-layer guard for optional capabilities. Routes and workers share it; hiding a screen is not enough."""

from app.capabilities.service.service import CAPABILITIES, COMPOSITIONS, validate_composition
from app.core.errors import codes
from app.core.errors.base import AppError
from app.core.settings import get_settings

CAPABILITY_DISABLED_REASON = "capability_disabled"
"""The stable reason beside a null optional summary value (cost 018, schedule 030, output 032)."""

_LABELS = {"cost": "biaya", "schedule": "jadwal", "output": "metrik output"}


class CapabilityDisabledError(AppError):
    """An optional capability is not part of this deployment's composition.

    Attributes:
        capability (str): The refused capability.
    """

    code = codes.APP_CAPABILITY_DISABLED

    def __init__(self, capability: str) -> None:
        """Name the refused capability.

        Args:
            capability (str): The capability ID.
        """
        super().__init__(
            f"Fitur {_LABELS.get(capability, capability)} tidak aktif pada layanan ini."
            " Gunakan fitur inti atau hubungi pengelola layanan."
        )
        self.capability = capability


class CapabilityGuard:
    """Checks a composition, never grants access: callers resolve ownership first, then require a capability."""

    def __init__(self, composition_id: str) -> None:
        """Bind to a supported composition.

        Args:
            composition_id (str): The deployment's composition.

        Raises:
            ValueError: When the composition is unsupported.
        """
        if composition_id not in COMPOSITIONS:
            raise ValueError(f"Unsupported composition: {composition_id}.")
        _, capability_ids = COMPOSITIONS[composition_id]
        validate_composition(capability_ids)
        self.composition_id = composition_id
        self.capabilities = frozenset(capability_ids)

    def enabled(self, capability: str) -> bool:
        """Tell whether a capability is part of the composition.

        Args:
            capability (str): A known capability ID.

        Returns:
            bool: True when enabled.

        Raises:
            ValueError: For an unknown capability, a programming error.
        """
        if capability not in CAPABILITIES:
            raise ValueError(f"Unknown capability: {capability}.")
        return capability in self.capabilities

    def require(self, capability: str) -> None:
        """Refuse a disabled capability.

        Args:
            capability (str): A known capability ID.

        Raises:
            CapabilityDisabledError: When the composition excludes it.
        """
        if not self.enabled(capability):
            raise CapabilityDisabledError(capability)


def get_capability_guard() -> CapabilityGuard:
    """Build the guard for this deployment; optional services receive it through their constructor.

    Returns:
        CapabilityGuard: The guard.
    """
    return CapabilityGuard(get_settings().composition)
