"""Moderation failures keep submitted private data out of diagnostics."""

import logging

import pytest
from httpx import AsyncClient

from tests.integration.conftest import SignUp

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("clean_tables")]


async def test_invalid_report_has_recoverable_fields_and_one_sanitized_record(
    client: AsyncClient, sign_up: SignUp, caplog: pytest.LogCaptureFixture
) -> None:
    """
    Condition:
    - A rejected report contains a private marker in its reason.

    Expected:
    - The error has a stable code and safe recovery details, its reference names a single log record,
      and the submitted reason appears in neither response nor log.
    """
    me = await sign_up(client, "invalid-report@example.test")
    marker = "private-reason-fake-secret-71"
    with caplog.at_level(logging.WARNING):
        result = await client.post(
            "/api/v1/reports",
            json={
                "acting_party_id": me["active_party_id"],
                "expected_version": None,
                "category": "INVALID",
                "reason": marker,
            },
            headers={"Idempotency-Key": "invalid-report"},
        )
    assert result.status_code == 422
    error = result.json()["error"]
    assert error["code"] == "VALIDATION_FAILED"
    assert error["message"] and error["recovery"]["retryable"] is False
    assert error["details"][0]["loc"][-1] == "category"
    assert sum(error["request_id"] in entry.message for entry in caplog.records) == 1
    assert marker not in result.text
    assert marker not in caplog.text
