"""Startup validation: unsafe configuration never serves traffic."""

import re
from ipaddress import ip_address
from urllib.parse import SplitResult, urlsplit

from app.capabilities.service.service import select_capabilities
from app.core.errors.sanitize import REDACTED, redact_text
from app.core.secret_envelope import validated_key
from app.core.settings import Settings

# A long unbroken run of key characters is how keys and tokens look; composition values are short words.
_TOKEN_LIKE = re.compile(r"[A-Za-z0-9_+/=-]{32,}")
_EMAIL_ADDRESS = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")
_RELAY_PATH = re.compile(r"/[A-Za-z0-9_./-]{0,127}")
_DEVELOPMENT_ONLY_SCANNERS = ("development-accept",)
_SUMMARY_LOOPBACK_URL = re.compile(r"http://(?:127\.0\.0\.1|\[::1\]):([1-9][0-9]{0,4})(?:/[A-Za-z0-9/._~-]*)?")
_SUMMARY_VERSION = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")


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
    if settings.summary_adapter == "local-relay":
        _validate_summary_relay(settings)
    _validate_calendar(settings)
    return capability_ids


def _validate_summary_relay(settings: Settings) -> None:
    if settings.environment != "development":
        raise ConfigurationError("SUMMARY_ADAPTER=local-relay is allowed only in development.")
    url = settings.summary_relay_url.get_secret_value() if settings.summary_relay_url else ""
    endpoint = _SUMMARY_LOOPBACK_URL.fullmatch(url)
    if not endpoint or int(endpoint[1]) > 65535:
        raise ConfigurationError("SUMMARY_RELAY_URL requires a literal HTTP loopback endpoint with a valid port.")
    for name, value in (
        ("SUMMARY_MODEL_ID", settings.summary_model_id),
        ("SUMMARY_MODEL_VERSION", settings.summary_model_version),
        ("SUMMARY_PROMPT_VERSION", settings.summary_prompt_version),
    ):
        if not _SUMMARY_VERSION.fullmatch(value) or looks_secret(value):
            raise ConfigurationError(f"{name} requires a non-secret model or version identifier.")


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


def _validate_calendar(settings: Settings) -> None:
    if settings.calendar_adapter == "off":
        return
    if settings.environment != "development":
        raise ConfigurationError("CALENDAR_ADAPTER=loopback-oauth is allowed only in development.")
    for name in ("calendar_authorize_url", "calendar_token_url", "calendar_freebusy_url", "calendar_revoke_url"):
        endpoint = _loopback_url(getattr(settings, name))
        if endpoint is None or not re.fullmatch(r"/[A-Za-z0-9_/-]{1,128}", endpoint.path):
            raise ConfigurationError(f"{name.upper()} must be a literal loopback HTTP(S) endpoint.")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", settings.calendar_client_id):
        raise ConfigurationError("CALENDAR_CLIENT_ID must be a synthetic client identifier.")
    web = _loopback_url(settings.web_origin, allow_localhost=True)
    if web is None or web.path:
        raise ConfigurationError("WEB_ORIGIN must be a loopback origin when the local calendar is enabled.")
    callback = _loopback_url(settings.calendar_callback_origin, allow_localhost=True)
    if (
        callback is None
        or callback.path
        or callback.hostname != web.hostname
        or callback.scheme != web.scheme
        or callback.port is None
        or callback.port == (web.port or (443 if web.scheme == "https" else 80))
    ):
        raise ConfigurationError("CALENDAR_CALLBACK_ORIGIN must use the web hostname and a separate loopback API port.")
    try:
        calendar_key = validated_key(
            settings.calendar_envelope_key.get_secret_value() if settings.calendar_envelope_key else ""
        )
    except ValueError:
        raise ConfigurationError("CALENDAR_ENVELOPE_KEY must be a dedicated, valid envelope key.") from None
    email_key = getattr(settings, "email_envelope_key", None)
    if (
        settings.mailbox_adapter == "loopback-relay"
        and email_key
        and calendar_key.decode("ascii") == email_key.get_secret_value()
    ):
        raise ConfigurationError("Email and calendar require independent envelope keys.")


def _loopback_url(value: str, *, allow_localhost: bool = False) -> SplitResult | None:
    hosts = ("127.0.0.1", "::1", "localhost") if allow_localhost else ("127.0.0.1", "::1")
    if any(char in value for char in ("?", "#", "@", "\\")) or any(char.isspace() or ord(char) < 32 for char in value):
        return None
    try:
        parsed = urlsplit(value)
        if parsed.scheme not in ("http", "https") or parsed.hostname not in hosts or parsed.port == 0:
            return None
        canonical_host = "[::1]" if parsed.hostname == "::1" else parsed.hostname
        canonical_netloc = canonical_host if parsed.port is None else f"{canonical_host}:{parsed.port}"
        return parsed if parsed.netloc == canonical_netloc else None
    except ValueError:
        return None
