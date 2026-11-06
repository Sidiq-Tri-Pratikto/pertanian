"""Failure envelopes and confidentiality for staged upload errors."""

from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import text

from app.core.database import get_engine
from app.portability.service.file_format import MAX_BYTES

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("clean_tables")]
Fixture = Callable[..., Awaitable[Any]]


async def test_oversized_upload_is_rejected_without_storage_or_diagnostics(
    client: AsyncClient,
    sign_up: Fixture,
    caplog: pytest.LogCaptureFixture,
    storage: Path,
) -> None:
    """
    Condition:
    - A signed-in uploader exceeds the hard limit with a chunked request containing a fake secret.

    Expected:
    - A registered error is recorded once and no raw bytes or partial artifact remain.
    """
    party = (await sign_up(client, "size@example.com"))["active_party_id"]
    secret = b"SECRET-SENTINEL-UPLOAD"

    async def stream():
        yield secret
        for _ in range(21):
            yield b"X" * (MAX_BYTES // 20)

    response = await client.post(
        "/api/v1/imports/validate",
        params={"acting_party_id": party},
        content=stream(),
        headers={"Content-Type": "application/json", "Idempotency-Key": "large"},
    )
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "FILE_TOO_LARGE"
    assert error["recovery"]["retryable"] is False
    assert "20 MiB" in error["message"] and error["request_id"].startswith("ref_")
    records = [record for record in caplog.records if error["request_id"] in record.getMessage()]
    assert len(records) == 1
    assert secret.decode() not in response.text + caplog.text
    assert not list(storage.glob("portability-import-*"))


async def test_invalid_file_and_idempotent_digest_keep_payload_private(
    client: AsyncClient,
    sign_up: Fixture,
    work: Fixture,
    caplog: pytest.LogCaptureFixture,
    storage: Path,
) -> None:
    """
    Condition:
    - A private source file fails validation and the caller retries a different file with the same key.

    Expected:
    - Validation reports only its safe code and idempotency compares upload bytes, without exposing values or keys.
    """
    party = (await sign_up(client, "diagnostics@example.com"))["active_party_id"]
    source = "SECRET-SOURCE-LABEL"
    private = "SECRET-PRIVATE-NOTE"
    args = {
        "params": {"acting_party_id": party},
        "headers": {"Idempotency-Key": "file", "Content-Type": "application/json"},
    }
    response = await client.post(
        "/api/v1/imports/validate",
        json={"schema_version": 5, "provenance": source, "private_notes": private},
        **args,
    )
    assert response.status_code == 202
    changed = await client.post("/api/v1/imports/validate", json={"schema_version": 6}, **args)
    assert changed.status_code == 409 and changed.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"
    await work(drain=True)
    read = await client.get(f"/api/v1/imports/{response.json()['id']}")
    assert read.status_code == 200 and read.json()["validation"]["error_code"] == "BAD_REQUEST"
    assert read.json()["preview"]["status"] == "NOT_STARTED"
    async with get_engine().connect() as connection:
        inputs = (await connection.execute(text("SELECT input, result_ref FROM jobs"))).all()
        details = (await connection.execute(text("SELECT detail FROM audit_events"))).all()
    key = next(storage.glob("portability-import-*")).name
    visible = response.text + changed.text + read.text + caplog.text + str(inputs) + str(details)
    assert all(secret not in visible for secret in (source, private, key))
