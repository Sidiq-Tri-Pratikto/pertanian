"""Startup validation: unsafe configuration never serves traffic."""

import re
from ipaddress import ip_address
from urllib.parse import urlsplit

from app.capabilities.service.service import select_capabilities
from app.core.errors.sanitize import REDACTED, redact_text
from app.core.secret_envelope import validated_key
from app.core.settings import Settings

# A long unbroken run of key characters is how keys and tokens look; composition values are short words.
_TOKEN_LIKE = re.compile(r"[A-Za-z0-9_+/=-]{32,}")
_EMAIL_ADDRESS = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")
_RELAY_PATH = re.compile(r"/[A-Za-z0-9_./-]{0,127}")
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
    if settings.environment != "development" and settings.demo_mode and not settings.demo_deployment:
        raise ConfigurationError(
            f"DEMO_MODE=true is allowed in {settings.environment} only on a deployment marked as a demonstration. "
            "Set DEMO_DEPLOYMENT=true there, or turn demo mode off."
        )
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
    if settings.mailbox_adapter == "loopback-relay":
        _validate_email_relay(settings)
    if settings.environment != "development" and settings.storage_adapter != "s3":
        raise ConfigurationError("STORAGE_ADAPTER=s3 is required outside development.")
    if settings.storage_adapter == "s3":
        if not all(
            (
                settings.s3_endpoint_url,
                settings.s3_bucket,
                settings.s3_region,
                settings.s3_access_key,
                settings.s3_secret_key,
            )
        ):
            raise ConfigurationError("S3 requires endpoint, bucket, region and scoped credentials.")
        try:
            endpoint = urlsplit(settings.s3_endpoint_url.get_secret_value())
            valid_endpoint = (
                endpoint.scheme in ("https", "http")
                and endpoint.hostname is not None
                and not any((endpoint.username, endpoint.password, endpoint.query, endpoint.fragment))
                and endpoint.path in ("", "/")
            )
        except ValueError:
            valid_endpoint = False
        if not valid_endpoint:
            raise ConfigurationError("S3 endpoint must be an HTTP(S) origin without embedded credentials.")
    return capability_ids


def _validate_email_relay(settings: Settings) -> None:
    if settings.environment != "development":
        raise ConfigurationError("MAILBOX_ADAPTER=loopback-relay is allowed only in development.")
    endpoint = settings.email_relay_url.get_secret_value() if settings.email_relay_url else ""
    try:
        url = urlsplit(endpoint)
        host = url.hostname or ""
        literal = f"[{host}]" if ":" in host else host
        authority = literal if url.port is None else f"{literal}:{url.port}"
        valid_endpoint = (
            url.scheme in {"http", "https"}
            and ip_address(host).is_loopback
            and (url.port is None or url.port > 0)
            and url.netloc.lower() == authority
            and not any(char in endpoint for char in "@?#%")
            and all(33 <= ord(char) <= 126 for char in endpoint)
            and (not url.path or _RELAY_PATH.fullmatch(url.path))
        )
    except ValueError:
        valid_endpoint = False
    if not valid_endpoint:
        raise ConfigurationError("EMAIL_RELAY_URL must be an HTTP(S) endpoint on a literal loopback address.")
    sender = settings.email_relay_sender.get_secret_value() if settings.email_relay_sender else ""
    if len(sender) > 254 or not sender.isprintable() or not _EMAIL_ADDRESS.fullmatch(sender):
        raise ConfigurationError("EMAIL_RELAY_SENDER must be a single valid sender address.")
    key = settings.email_envelope_key.get_secret_value() if settings.email_envelope_key else ""
    try:
        validated_key(key)
    except ValueError:
        raise ConfigurationError("EMAIL_ENVELOPE_KEY must be a valid Fernet key.") from None
