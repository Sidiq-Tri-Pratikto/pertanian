"""Startup validation: unsafe configuration never serves traffic."""

import re

from app.capabilities.service.service import select_capabilities
from app.core.errors.sanitize import REDACTED, redact_text
from app.core.settings import Settings

# A long unbroken run of key characters is how keys and tokens look; composition values are short words.
_TOKEN_LIKE = re.compile(r"[A-Za-z0-9_+/=-]{32,}")
_DEVELOPMENT_ONLY_SCANNERS = ("development-accept",)


class ConfigurationError(ValueError):
    """The deployment's configuration is unsafe or unsupported. The message never repeats a rejected value."""


def looks_secret(value: str) -> bool:
    """Tell whether a configuration value looks like a credential.

    Args:
        value (str): The value.

    Returns:
        bool: True for key, token, password or email patterns the sanitizer would redact, or a long token.
    """
    return REDACTED in redact_text(value) or bool(_TOKEN_LIKE.search(value))


def validate_configuration(settings: Settings) -> tuple[str, ...]:
    """Reject configuration the service must not run with (FR23, AC69).

    Composition values are published in the manifest, so a secret placed there would leak. Each check names the
    setting and never the value.

    Args:
        settings (Settings): The settings to check.

    Returns:
        tuple[str, ...]: The selected capability ids.

    Raises:
        ConfigurationError: When a composition value looks like a secret, the composition or overrides are
            unsupported, or an adapter is unsafe for the environment.
    """
    composition_values = [("COMPOSITION", settings.composition)]
    composition_values += [("COMPOSITION_OVERRIDES", key) for key in settings.composition_overrides]
    for name, value in composition_values:
        if looks_secret(value):
            raise ConfigurationError(
                f"{name} holds a value that looks like a secret. Composition settings are published in the "
                "capability manifest; keep secrets in their own settings."
            )
    try:
        capability_ids = select_capabilities(settings.composition, settings.composition_overrides)
    except ValueError as error:
        raise ConfigurationError(str(error)) from error
    if settings.environment != "development" and settings.file_scanner in _DEVELOPMENT_ONLY_SCANNERS:
        raise ConfigurationError(
            f"FILE_SCANNER={settings.file_scanner} is allowed only in development. "
            f"Use clamav in {settings.environment}."
        )
    if settings.environment != "development" and settings.mailbox_adapter == "development":
        raise ConfigurationError(
            f"MAILBOX_ADAPTER=development is allowed only in development. Configure email delivery for "
            f"{settings.environment} (spec 042)."
        )
    return capability_ids
