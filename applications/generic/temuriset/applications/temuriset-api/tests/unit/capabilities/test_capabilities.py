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
    - The manifest carries the release, composition, locale, currencies, capabilities, adapters and policies.
    """
    response = TestClient(app).get("/api/v1/capabilities")

    assert response.status_code == 200
    body = response.json()
    assert body["schema_version"] == 1
    assert body["source_release"] == "0.1.0"
    assert body["composition"] == {"id": "generic-base", "version": 1}
    assert body["default_locale"] == "id"
    assert body["supported_currencies"] == ["IDR", "USD"]
    assert [capability["id"] for capability in body["capabilities"]] == ["core", "company_funding"]
    assert {policy["id"] for policy in body["policies"]} == {
        "matching-weights",
        "fit-thresholds",
        "pitch-rate-limit",
        "resubmission-pause",
        "proposal-expiry",
        "idempotency-retention",
    }


@pytest.mark.parametrize("composition", ["generic-base", "generic-with-review", "project-support-only"])
def test_nothing_claims_more_than_exists(composition: str) -> None:
    """
    Condition:
    - Storage and scanning shipped in spec 010, company funding in spec 014, and core with the first complete
      inventor journey in spec 024; nothing else has.

    Expected:
    - Only those report available, where the composition selects them; everything else stays planned.
    """
    manifest = build_manifest(composition)

    assert {item.id: item.status for item in manifest.capabilities if item.status == "available"} == (
        {"core": "available"}
        if composition == "project-support-only"
        else {"core": "available", "company_funding": "available"}
    )
    assert {item.status for item in manifest.capabilities if item.id not in ("core", "company_funding")} <= {"planned"}
    assert {adapter.id: adapter.status for adapter in manifest.adapters} == {
        "object-storage": "available",
        "file-scanner": "available",
        "lexical-rules": "available",
        "ics-export": "planned",
    }


@pytest.mark.parametrize(
    ("composition", "capabilities"),
    [
        ("generic-with-review", ["core", "company_funding", "organization_review"]),
        ("project-support-only", ["core"]),
    ],
)
def test_supported_compositions_select_their_capabilities(composition: str, capabilities: list[str]) -> None:
    """
    Condition:
    - Review enabled, or company funding disabled (PRD section 21).

    Expected:
    - The manifest lists exactly that composition's capabilities.
    """
    manifest = build_manifest(composition)

    assert [capability.id for capability in manifest.capabilities] == capabilities


@pytest.mark.parametrize(
    ("capabilities", "message"),
    [
        (("company_funding",), "core is required"),
        (("core", "escrow"), "Unsupported capabilities: escrow"),
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
    - The application refuses to start and names the composition.
    """
    settings = Settings(database_url="postgresql+asyncpg://a:b@localhost/c", composition="client-fork")

    with patch("app.main.get_settings", return_value=settings), pytest.raises(ValueError, match="client-fork"):
        create_app()
