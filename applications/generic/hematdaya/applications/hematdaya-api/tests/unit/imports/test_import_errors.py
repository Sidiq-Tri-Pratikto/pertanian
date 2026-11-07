"""The three import failures through a real application boundary."""

import json
import logging
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.errors.base import AppError
from app.core.errors.handlers import ErrorBoundaryMiddleware, register_exception_handlers
from app.imports.model.models import ImportModel, ImportStatus
from app.imports.service.errors import (
    ImportAckRequiredError,
    ImportBlockedError,
    ImportKeyConflictError,
    ImportStaleError,
    ImportStructureError,
    ImportTooLargeError,
)

CATALOG = Path(__file__).resolve().parents[5] / "docs/error-handling/catalog.md"
FAKE_TOKEN = "Bearer RAHASIA-PALSU-123"
FAKE_EMAIL = "fake@example.com"
DETAILS = [{"loc": ["file"], "msg": "Perbaiki berkas.", "type": "too_large"}]
ERRORS = [
    (
        ImportTooLargeError,
        "APP-IMPORT-TOO-LARGE",
        "IMPORT_TOO_LARGE",
        413,
        "Berkas melebihi batas impor. Perkecil menjadi paling besar 10 MiB dan 150.000 baris data lalu coba lagi.",
    ),
    (
        ImportStructureError,
        "APP-IMPORT-STRUCTURE",
        "IMPORT_INVALID",
        400,
        "Struktur berkas belum dapat dibaca. Perbaiki hal yang disebutkan lalu coba lagi.",
    ),
    (
        ImportBlockedError,
        "APP-IMPORT-BLOCKED",
        "IMPORT_BLOCKED",
        409,
        "Impor ini masih diblokir. Selesaikan alasan pada pratinjau lalu coba lagi.",
    ),
    (
        ImportStaleError,
        "APP-IMPORT-STALE",
        "IMPORT_STALE",
        409,
        "Pratinjau ini sudah tidak berlaku. Buat pratinjau baru lalu coba lagi.",
    ),
    (
        ImportAckRequiredError,
        "APP-IMPORT-ACK-REQUIRED",
        "IMPORT_ACK_REQUIRED",
        409,
        "Ada baris yang akan dilewati dan belum disetujui. Setujui baris yang dilewati lalu coba lagi.",
    ),
    (
        ImportKeyConflictError,
        "APP-IMPORT-KEY-CONFLICT",
        "CONFLICT",
        409,
        "Permintaan ini sudah dipakai untuk impor lain. Konfirmasi impornya lagi untuk mengirim permintaan baru.",
    ),
]


@pytest.fixture(autouse=True)
def capture_app_logs(caplog: pytest.LogCaptureFixture) -> Iterator[None]:
    """Capture the application logger, which does not propagate once configured."""
    logger = logging.getLogger("app")
    logger.addHandler(caplog.handler)
    logger.setLevel(logging.INFO)
    yield
    logger.removeHandler(caplog.handler)


def _records(caplog: pytest.LogCaptureFixture) -> list[dict]:
    prefix = "Application failure "
    return [json.loads(r.getMessage().removeprefix(prefix)) for r in caplog.records if prefix in r.getMessage()]


def _client_raising(error: AppError) -> TestClient:
    app = FastAPI()
    app.add_middleware(ErrorBoundaryMiddleware)
    register_exception_handlers(app)

    @app.get("/fails")
    async def fails() -> None:
        raise error

    return TestClient(app)


@pytest.mark.parametrize(("error_class", "code", "public_code", "status", "message"), ERRORS)
def test_import_error_renders_its_catalog_entry(
    caplog: pytest.LogCaptureFixture,
    error_class: type[AppError],
    code: str,
    public_code: str,
    status: int,
    message: str,
) -> None:
    """
    Condition:
    - A route raises the typed error, carrying details and a cause holding a fake token and email.

    Expected:
    - Exact public code, status and message, not retryable, its details, one record sharing the request ID, and
      neither fake value on any surface.
    """
    cause = ValueError(f"gagal dengan {FAKE_TOKEN} untuk {FAKE_EMAIL}")

    response = _client_raising(error_class(details=DETAILS, error=cause)).get("/fails")

    assert response.status_code == status
    error = response.json()["error"]
    assert error["code"] == public_code
    assert error["message"] == message
    assert error["recovery"] == {"retryable": False}
    assert error["details"] == DETAILS
    records = _records(caplog)
    assert len(records) == 1
    assert records[0]["reference_id"] == error["request_id"]
    assert records[0]["code"] == code
    assert code not in response.text
    for secret in (FAKE_TOKEN, "RAHASIA-PALSU-123", FAKE_EMAIL):
        assert secret not in response.text
        assert secret not in caplog.text


@pytest.mark.parametrize(("error_class", "code", "public_code", "status", "message"), ERRORS)
def test_import_error_has_its_catalog_row(
    error_class: type[AppError], code: str, public_code: str, status: int, message: str
) -> None:
    """
    Condition:
    - The error catalog document.

    Expected:
    - Each code has one row with its public code, status, default message and retry guidance.
    """
    row = next((line for line in CATALOG.read_text(encoding="utf-8").splitlines() if f"| `{code}` |" in line), "")

    assert f"| `{public_code}` | {status} | {message} |" in row
    assert "| false | - | - |" in row


def _model(*, blocked: bool) -> ImportModel:
    return ImportModel(
        id=uuid4(),
        site_id=uuid4(),
        status=ImportStatus.PREVIEWED,
        file_name="a.csv",
        content_sha256="0" * 64,
        mapping={},
        total_rows=1,
        accepted_rows=0 if blocked else 1,
        invalid_rows=1 if blocked else 0,
        duplicate_rows=0,
        conflict_rows=0,
        pending_rows=0,
        blocked=blocked,
        block_reasons=["Impor diblokir: 1 dari 1 baris tidak valid."] if blocked else [],
        needs_acknowledgment=False,
        questions=[],
        assumptions=[],
        period_start=None,
        period_end=None,
        measurement_revision=0,
        binding_revision=0,
        idempotency_key=None,
        expires_at=datetime(2026, 11, 8, tzinfo=UTC),
    )


def test_require_committable_refuses_a_blocked_preview() -> None:
    """
    Condition:
    - A stored preview with ``blocked`` true.

    Expected:
    - It raises the typed error 026's route will surface.
    """
    from app.imports.service.preview import ImportPreviewService

    with pytest.raises(ImportBlockedError):
        ImportPreviewService.require_committable(_model(blocked=True))


def test_require_committable_passes_an_unblocked_preview() -> None:
    """
    Condition:
    - A stored preview with ``blocked`` false.

    Expected:
    - It returns without raising.
    """
    from app.imports.service.preview import ImportPreviewService

    assert ImportPreviewService.require_committable(_model(blocked=False)) is None
