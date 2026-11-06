"""Contract tests for imported data and source claims."""

import json

import pytest

from app.core.errors.base import RequestInvalidError
from app.portability.service.file_format import MAX_ROWS, parse_file


def payload(**overrides: object) -> bytes:
    """Build a minimal valid import with optional variations."""
    return json.dumps(
        {
            "schema_version": 1,
            "external_system": "example-registry",
            "provenance": {"source": "Registry"},
            "inventions": [{"external_id": "123", "provenance": {"source": "Registry"}, "fields": {"title": "Filter"}}],
            **overrides,
        }
    ).encode()


@pytest.mark.parametrize(
    "raw",
    [
        b"{",
        b"{}",
        b'{"schema_version": 1, "schema_version": 1}',
        b'{"schema_version": 1, "inventions": [], "unknown": NaN}',
        payload(provenance={"source": "Bad\x00label"}),
        payload(schema_version=2),
        payload(schema_version=True),
        payload(provenance={}),
        payload(inventions=[{"external_id": "bad id"}]),
        payload(inventions=[{"external_id": "repeat", "provenance": {"source": "Registry"}, "fields": {}}] * 2),
        payload(inventions=[{}] * (MAX_ROWS + 1)),
    ],
)
def test_invalid_payload_is_rejected_safely(raw: bytes) -> None:
    """
    Condition:
    - The envelope or row violates the v1 contract.

    Expected:
    - A registered invalid-request error without parser values.
    """
    with pytest.raises(RequestInvalidError) as caught:
        parse_file(raw)
    assert "example-registry" not in str(caught.value)


def test_relationship_assertions_are_source_reported() -> None:
    """
    Condition:
    - A source asserts a confirmed relationship, mentions an organization and supplies a workspace identifier.

    Expected:
    - All content stays source-reported and identifiers have no destination authority.
    """
    parsed = parse_file(
        payload(
            inventions=[
                {
                    "external_id": "123",
                    "provenance": {"source": "Registry"},
                    "fields": {"title": "Filter", "workspace_id": "source-only"},
                    "relationship_assertions": [
                        {"organization_name": "Named Org", "kind": "PARTNERSHIP", "reported_status": "CONFIRMED"}
                    ],
                }
            ]
        )
    )
    row = parsed.inventions[0]
    assert row.relationship_assertions[0].provenance == "SOURCE_REPORTED"
    assert row.fields.model_dump(exclude_unset=True) == {"title": "Filter"}
