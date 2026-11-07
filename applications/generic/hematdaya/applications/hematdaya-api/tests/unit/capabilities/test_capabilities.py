"""Capability manifest tests."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.capabilities.service.service import build_manifest, validate_composition
from app.core.settings import Settings
from app.main import app, create_app


def test_manifest_describes_the_deployment() -> None:
    """
    Condition:
    - A client asks what this deployment supports.

    Expected:
    - The manifest carries the release, composition, capabilities, adapters and policies.
    """
    response = TestClient(app).get("/api/v1/capabilities")

    assert response.status_code == 200
    body = response.json()
    assert body["schema_version"] == 1
    assert body["source_release"] == "0.1.0"
    assert body["composition"] == {"id": "core-plus-optional", "version": 1}
    assert [capability["id"] for capability in body["capabilities"]] == ["core", "cost", "schedule", "output"]
    assert {policy["id"] for policy in body["policies"]} == {"baseline", "change", "stale"}


@pytest.mark.parametrize("composition", ["core-plus-optional", "core-only"])
def test_nothing_claims_more_than_exists(composition: str) -> None:
    """
    Condition:
    - The core shipped with evidence-based insights, demo shipped with simulated data, and CSV import shipped in 026.

    Expected:
    - Core and CSV are available and demo simulated. Optional capabilities and other adapters stay planned.
    """
    manifest = build_manifest(composition)
    adapters = {adapter.id: adapter.status for adapter in manifest.adapters}
    capabilities = {capability.id: capability.status for capability in manifest.capabilities}

    assert (capabilities.pop("core"), adapters.pop("demo"), adapters.pop("csv")) == (
        "available",
        "simulated",
        "available",
    )
    assert set(capabilities.values()) | set(adapters.values()) == {"planned"}


def test_core_only_composition_drops_optional_modules() -> None:
    """
    Condition:
    - The core-only composition is selected.

    Expected:
    - The manifest lists only the core capability.
    """
    manifest = build_manifest("core-only")

    assert [capability.id for capability in manifest.capabilities] == ["core"]


@pytest.mark.parametrize(
    ("capabilities", "message"),
    [
        (("cost",), "core is required"),
        (("core", "teleport"), "Unsupported capabilities: teleport"),
    ],
)
def test_invalid_compositions_are_rejected(capabilities: tuple[str, ...], message: str) -> None:
    """
    Condition:
    - A composition omits the core or names an unknown capability.

    Expected:
    - Validation rejects it with the reason.
    """
    with pytest.raises(ValueError, match=message):
        validate_composition(capabilities)


def test_unknown_composition_stops_startup() -> None:
    """
    Condition:
    - The environment selects a composition the product does not support.

    Expected:
    - The application refuses to start rather than serving an undefined product.
    """
    settings = Settings(database_url="postgresql+asyncpg://a:b@localhost/c", composition="custom-fork")

    with patch("app.main.get_settings", return_value=settings), pytest.raises(ValueError, match="custom-fork"):
        create_app()
