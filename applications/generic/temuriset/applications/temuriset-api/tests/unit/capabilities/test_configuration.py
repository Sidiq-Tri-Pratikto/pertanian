"""Startup configuration validation tests (FR23, AC69)."""

import logging
from unittest.mock import patch

import pytest
from cryptography.fernet import Fernet
from pydantic import SecretStr, ValidationError

from app.capabilities.router import get_capabilities
from app.capabilities.service.configuration import ConfigurationError, looks_secret, validate_configuration
from app.capabilities.service.service import build_manifest
from app.core.settings import Settings
from app.main import create_app

FAKE_KEY = "sk-fakeprodkey1234567890"
FAKE_TOKEN = "ghp_0123456789abcdefABCDEF0123456789abcd"


def _settings(**values: object) -> Settings:
    return Settings(database_url="postgresql+asyncpg://a:b@localhost/c", **values)


def test_valid_configuration_selects_capabilities() -> None:
    """
    Condition:
    - Default settings.

    Expected:
    - Validation passes and returns the composition's capabilities.
    """
    assert validate_configuration(_settings()) == ("core", "company_funding")


def test_override_enables_a_capability_and_the_manifest_lists_it() -> None:
    """
    Condition:
    - ``generic-base`` with organization review switched on.

    Expected:
    - It is selected and appears in the manifest.
    """
    overrides = {"organization_review": True}

    assert "organization_review" in validate_configuration(_settings(composition_overrides=overrides))
    manifest = build_manifest("generic-base", overrides)
    assert [capability.id for capability in manifest.capabilities] == ["core", "company_funding", "organization_review"]


def test_missing_dependency_stops_startup() -> None:
    """
    Condition:
    - ``COMPOSITION_OVERRIDES`` enables reranking without dense retrieval.

    Expected:
    - Startup fails naming the dependency.
    """
    settings = _settings(composition_overrides={"reranking": True})

    with (
        patch("app.main.get_settings", return_value=settings),
        pytest.raises(ConfigurationError, match="dense_retrieval"),
    ):
        create_app()


def test_dependency_satisfied_passes() -> None:
    """
    Condition:
    - Reranking and dense retrieval are both switched on.

    Expected:
    - Validation passes.
    """
    overrides = {"dense_retrieval": True, "reranking": True}

    assert validate_configuration(_settings(composition_overrides=overrides))[-2:] == ("dense_retrieval", "reranking")


@pytest.mark.parametrize(
    ("overrides", "message"),
    [({"escrow": True}, "Unsupported capabilities: escrow"), ({"core": False}, "core is required")],
)
def test_unsupported_overrides_stop_startup(overrides: dict[str, bool], message: str) -> None:
    """
    Condition:
    - An override names an unknown capability, or switches the core off.

    Expected:
    - Validation fails with the reason.
    """
    with pytest.raises(ConfigurationError, match=message):
        validate_configuration(_settings(composition_overrides=overrides))


@pytest.mark.parametrize(
    "values",
    [
        {"composition": FAKE_KEY},
        {"composition": f"password={FAKE_KEY}"},
        {"composition_overrides": {FAKE_TOKEN: True}},
    ],
)
def test_secret_in_composition_stops_startup_without_logging_it(
    values: dict[str, object], caplog: pytest.LogCaptureFixture, capsys: pytest.CaptureFixture[str]
) -> None:
    """
    Condition:
    - A key, password or token is written into composition configuration (AC69).

    Expected:
    - Startup fails, and the value is absent from the error, the logs and the console.
    """
    settings = _settings(**values)

    with (
        caplog.at_level(logging.DEBUG),
        patch("app.main.get_settings", return_value=settings),
        pytest.raises(ConfigurationError, match="looks like a secret") as raised,
    ):
        create_app()

    captured = capsys.readouterr()
    for surface in (str(raised.value), caplog.text, captured.out, captured.err):
        assert FAKE_KEY not in surface
        assert FAKE_TOKEN not in surface


def test_invalid_override_value_is_not_echoed() -> None:
    """
    Condition:
    - A secret is pasted as an override value, which must be true or false.

    Expected:
    - Settings validation fails without repeating the value.
    """
    with patch.dict("os.environ", {"COMPOSITION_OVERRIDES": f'{{"core": "{FAKE_KEY}"}}'}):
        with pytest.raises(ValidationError) as raised:
            _settings()

    assert FAKE_KEY not in str(raised.value)


@pytest.mark.parametrize("value", ["generic-base", "project-support-only", "organization_review"])
def test_ordinary_values_do_not_look_secret(value: str) -> None:
    """
    Condition:
    - A normal composition or capability id.

    Expected:
    - Not mistaken for a secret.
    """
    assert not looks_secret(value)


@pytest.mark.parametrize("environment", ["production", "staging"])
def test_development_scanner_is_refused_outside_development(environment: str) -> None:
    """
    Condition:
    - ``development-accept`` as the file scanner outside development.

    Expected:
    - Startup fails naming the setting.
    """
    with pytest.raises(ConfigurationError, match="FILE_SCANNER=development-accept"):
        validate_configuration(_settings(environment=environment, file_scanner="development-accept"))


def test_production_also_needs_real_email() -> None:
    """
    Condition:
    - Production with ``clamav`` but the development mailbox, the only adapter until spec 042.

    Expected:
    - Startup fails naming the mailbox, so no deployment sends sign-in codes into a table.
    """
    with pytest.raises(ConfigurationError, match="MAILBOX_ADAPTER=development"):
        validate_configuration(_settings(environment="production", file_scanner="clamav"))


@pytest.mark.parametrize(
    ("environment", "explicit", "secure"),
    [("development", None, False), ("production", None, True), ("development", True, True), ("staging", False, False)],
)
def test_session_cookie_is_secure_outside_development(environment: str, explicit: bool | None, secure: bool) -> None:
    """
    Condition:
    - Each environment, with and without ``SESSION_COOKIE_SECURE``.

    Expected:
    - ``Secure`` unless development, and the explicit setting wins.
    """
    assert _settings(environment=environment, session_cookie_secure=explicit).cookie_secure is secure


def test_staging_requires_configured_s3() -> None:
    """
    Condition:
    - A non-development deployment disables mail and uses ClamAV.

    Expected:
    - Startup accepts an explicitly configured private S3 backend and refuses missing settings.
    """
    configuration = {
        "environment": "staging",
        "file_scanner": "clamav",
        "mailbox_adapter": "disabled",
        "storage_adapter": "s3",
    }
    with pytest.raises(ConfigurationError, match="S3"):
        validate_configuration(_settings(**configuration))
    assert validate_configuration(
        _settings(
            **configuration,
            s3_endpoint_url="http://minio:9000",
            s3_bucket="temuriset-documents",
            s3_access_key="synthetic-key",
            s3_secret_key="synthetic-secret",
        )
    ) == ("core", "company_funding")


def test_manifest_reports_storage_implementation() -> None:
    """
    Condition:
    - A deployment configures S3 object storage.

    Expected:
    - The existing adapter ID reports S3 without configuration or credentials.
    """
    manifest = build_manifest("generic-base", storage_adapter="s3")
    adapter = next(adapter for adapter in manifest.adapters if adapter.id == "object-storage")
    assert adapter.implementation == "s3"


@pytest.mark.parametrize(
    "url",
    [
        "http://localhost:8090/deliver",
        "http://192.0.2.1:8090/deliver",
        "http://127.0.0.1@192.0.2.1:8090/deliver",
        "http://127.0.0.1:8090/deliver?token=fixture",
        "http://127.0.0.1:8090/deliver#fixture",
        "http://127.0.0.1:8090/\\deliver",
        "http://127.0.0.1:65536/deliver",
        "http://[::1]junk/deliver",
        "file:///tmp/relay",
    ],
)
def test_loopback_mail_rejects_unsafe_relay_urls(url: str) -> None:
    """
    Condition:
    - An explicitly enabled relay has an unsafe or nonliteral address.

    Expected:
    - Startup fails without echoing the address.
    """
    settings = _settings(
        mailbox_adapter="loopback-relay",
        email_relay_url=url,
        email_relay_sender="relay@example.test",
        email_envelope_key=Fernet.generate_key().decode("ascii"),
    )
    with pytest.raises(ConfigurationError, match="EMAIL_RELAY_URL") as raised:
        validate_configuration(settings)
    assert url not in str(raised.value)


@pytest.mark.parametrize("url", ["http://127.0.0.1:8090/deliver", "https://[::1]:8090/deliver"])
def test_loopback_mail_needs_development_and_valid_credentials(url: str) -> None:
    """
    Condition:
    - Startup selects a loopback relay with a literal endpoint.

    Expected:
    - Only development with a sender and a valid envelope key is accepted.
    """
    settings = _settings(
        mailbox_adapter="loopback-relay",
        email_relay_url=url,
        email_relay_sender="relay@example.test",
        email_envelope_key=Fernet.generate_key().decode("ascii"),
    )
    assert validate_configuration(settings) == ("core", "company_funding")
    for updates, message in (
        ({"environment": "staging", "file_scanner": "clamav"}, "MAILBOX_ADAPTER=loopback-relay"),
        ({"email_relay_sender": None}, "EMAIL_RELAY_SENDER"),
        ({"email_envelope_key": None}, "EMAIL_ENVELOPE_KEY"),
        ({"email_envelope_key": SecretStr(FAKE_KEY)}, "EMAIL_ENVELOPE_KEY"),
    ):
        with pytest.raises(ConfigurationError, match=message) as raised:
            validate_configuration(settings.model_copy(update=updates))
        assert FAKE_KEY not in str(raised.value)


@pytest.mark.parametrize(
    ("mode", "status", "implementation"),
    [
        ("development", "planned", None),
        ("disabled", "planned", None),
        ("loopback-relay", "available", "loopback-relay"),
    ],
)
async def test_manifest_reports_local_email_without_configuration(
    mode: str, status: str, implementation: str | None
) -> None:
    """
    Condition:
    - The validated deployment selects the development table, disabled mail, or the loopback relay.

    Expected:
    - Only the loopback relay is available, and the manifest includes no endpoint, sender or key.
    """
    key = Fernet.generate_key().decode("ascii")
    url, sender = "http://127.0.0.1:8090/deliver", "relay@example.test"
    settings = _settings(mailbox_adapter=mode, email_relay_url=url, email_relay_sender=sender, email_envelope_key=key)
    validate_configuration(settings)
    with patch("app.capabilities.router.get_settings", return_value=settings):
        manifest = await get_capabilities()
    adapter = next(item for item in manifest.adapters if item.id == "email")
    assert (adapter.status, adapter.implementation) == (status, implementation)
    assert all(private not in manifest.model_dump_json() for private in (key, url, sender))
