"""Startup configuration validation tests (FR23, AC69)."""

import logging
from unittest.mock import patch

import pytest
from pydantic import ValidationError

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


def test_real_scanner_is_accepted_in_production() -> None:
    """
    Condition:
    - Production with ``clamav``.

    Expected:
    - Validation passes.
    """
    assert validate_configuration(_settings(environment="production", file_scanner="clamav"))
