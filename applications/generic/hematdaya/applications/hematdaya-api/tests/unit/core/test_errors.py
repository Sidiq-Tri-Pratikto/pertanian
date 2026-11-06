"""Failure path tests through a real application boundary."""

import json
import logging
from unittest.mock import patch

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError, OperationalError

from app.core.errors.base import AppError, NotFoundError, RequestInvalidError
from app.core.errors.database import handle_database_error
from app.core.errors.handlers import ErrorBoundaryMiddleware, register_exception_handlers
from app.core.errors.recorder import emergency_log, record_failure
from app.core.errors.sanitize import REDACTED, redact_text, sanitize

FAKE_SECRET = "sk-fakesecret123456"
FAKE_EMAIL = "person@example.com"


class Payload(BaseModel):
    """Validated body."""

    count: int


@pytest.fixture
def client() -> TestClient:
    """Application with one route per failure type."""
    app = FastAPI()
    app.add_middleware(ErrorBoundaryMiddleware)
    register_exception_handlers(app)
    app.add_exception_handler(OperationalError, handle_database_error)
    app.add_exception_handler(IntegrityError, handle_database_error)

    @app.get("/not-found")
    async def not_found() -> None:
        raise NotFoundError()

    @app.get("/unexpected")
    async def unexpected() -> None:
        raise ValueError(f"call failed with Bearer {FAKE_SECRET} for {FAKE_EMAIL}")

    @app.api_route("/db-down", methods=["GET", "POST"])
    async def db_down(request: Request) -> None:
        raise OperationalError("SELECT 1", {}, Exception("connection refused"))

    @app.get("/db-error")
    async def db_error() -> None:
        raise IntegrityError("INSERT", {}, Exception("duplicate key"))

    @app.post("/validated")
    async def validated(payload: Payload) -> None:
        return None

    @app.get("/with-details")
    async def with_details() -> None:
        raise RequestInvalidError(details=[{"loc": ["file"], "msg": "Perbaiki berkas.", "type": "structure"}])

    return TestClient(app)


def _records(caplog: pytest.LogCaptureFixture) -> list[dict]:
    """Parse failure records from captured logs."""
    prefix = "Application failure "
    return [json.loads(r.getMessage().removeprefix(prefix)) for r in caplog.records if prefix in r.getMessage()]


@pytest.fixture(autouse=True)
def capture_app_logs(caplog: pytest.LogCaptureFixture) -> None:
    """Capture the application logger, which does not propagate once configured."""
    logger = logging.getLogger("app")
    logger.addHandler(caplog.handler)
    logger.setLevel(logging.INFO)
    yield
    logger.removeHandler(caplog.handler)


def test_typed_error_returns_envelope_and_one_record(client: TestClient, caplog: pytest.LogCaptureFixture) -> None:
    """
    Condition:
    - A route raises a typed not-found error.

    Expected:
    - The envelope carries the public code, and exactly one warning record shares its reference ID.
    """
    response = client.get("/not-found")

    assert response.status_code == 404
    error = response.json()["error"]
    assert error["code"] == "NOT_FOUND"
    assert error["recovery"] == {"retryable": False}
    records = _records(caplog)
    assert len(records) == 1
    assert records[0]["reference_id"] == error["request_id"]
    assert records[0]["code"] == "APP-NOT-FOUND"
    assert records[0]["operation"] == "/not-found"


def test_typed_error_renders_its_details_in_the_envelope(client: TestClient, caplog: pytest.LogCaptureFixture) -> None:
    """
    Condition:
    - A route raises a typed error carrying details.

    Expected:
    - The envelope has its public code and message plus the details, and one record shares the request ID.
    """
    response = client.get("/with-details")

    assert response.status_code == 400
    error = response.json()["error"]
    assert error["code"] == "BAD_REQUEST"
    assert error["message"] == "Permintaan belum dapat diproses. Periksa isian Anda lalu coba lagi."
    assert error["details"] == [{"loc": ["file"], "msg": "Perbaiki berkas.", "type": "structure"}]
    assert error["recovery"] == {"retryable": False}
    records = _records(caplog)
    assert len(records) == 1
    assert records[0]["reference_id"] == error["request_id"]
    assert "Perbaiki berkas." not in caplog.text


def test_typed_error_without_details_has_no_details_key(client: TestClient) -> None:
    """
    Condition:
    - A route raises a typed error with no details.

    Expected:
    - The envelope has no ``details`` key at all, so other routes keep their shape.
    """
    response = client.get("/not-found")

    assert "details" not in response.json()["error"]


def test_wrapping_keeps_details() -> None:
    """
    Condition:
    - A typed error with details is wrapped by the base class.

    Expected:
    - The wrapper carries the same details, as it does the code and reference ID.
    """
    details = [{"loc": ["file"], "msg": "Perbaiki berkas.", "type": "structure"}]

    assert AppError(error=RequestInvalidError(details=details)).details == details


def test_unexpected_error_is_safe_on_every_surface(client: TestClient, caplog: pytest.LogCaptureFixture) -> None:
    """
    Condition:
    - A route raises a raw error whose text holds a fake token and email.

    Expected:
    - The fallback envelope is returned, and neither value reaches the response or the record.
    """
    response = client.get("/unexpected")

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL_ERROR"
    captured = response.text + caplog.text
    assert FAKE_SECRET not in captured
    assert FAKE_EMAIL not in captured
    record = _records(caplog)[0]
    assert record["debug_info"]["error_type"] == "ValueError"
    assert record["reference_id"] == response.json()["error"]["request_id"]


@pytest.mark.parametrize(
    "method,retryable,retry_after",
    [("GET", True, "30"), ("POST", False, None)],
)
def test_database_outage_is_retryable_only_for_reads(
    client: TestClient, method: str, retryable: bool, retry_after: str | None
) -> None:
    """
    Condition:
    - The database is unreachable during a read or a write.

    Expected:
    - Reads are retryable with Retry-After. Writes are not, because they may have committed.
    """
    response = client.request(method, "/db-down")

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "DATABASE_UNAVAILABLE"
    assert response.json()["error"]["recovery"]["retryable"] is retryable
    assert response.headers.get("retry-after") == retry_after


def test_database_error_hides_sql(client: TestClient) -> None:
    """
    Condition:
    - A statement fails on a constraint.

    Expected:
    - The client gets the data error envelope with no SQL text.
    """
    response = client.get("/db-error")

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "DATA_ERROR"
    assert "INSERT" not in response.text


def test_validation_error_lists_fields_without_values(client: TestClient) -> None:
    """
    Condition:
    - A body field holds a value of the wrong type.

    Expected:
    - The envelope names the field and does not echo the submitted value.
    """
    response = client.post("/validated", json={"count": FAKE_SECRET})

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "VALIDATION_FAILED"
    assert error["details"][0]["loc"] == ["body", "count"]
    assert error["details"][0]["msg"] == "Isi dengan bilangan bulat."
    assert FAKE_SECRET not in response.text


def test_unknown_route_uses_envelope(client: TestClient) -> None:
    """
    Condition:
    - The path does not exist.

    Expected:
    - The framework 404 becomes the envelope.
    """
    response = client.get("/missing")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_logging_failure_does_not_hide_response(client: TestClient) -> None:
    """
    Condition:
    - The logger raises while recording a failure.

    Expected:
    - The client still gets the envelope, through the emergency path.
    """
    with (
        patch("app.core.errors.recorder.logger.error", side_effect=OSError("disk full")),
        patch("app.core.errors.recorder.emergency_log") as emergency,
    ):
        response = client.get("/unexpected")

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL_ERROR"
    emergency.assert_called_once()


def test_emergency_log_writes_to_stderr(capfd: pytest.CaptureFixture) -> None:
    """
    Condition:
    - The emergency path runs.

    Expected:
    - One JSON line reaches stderr.
    """
    emergency_log("ref_abc", "APP-UNKNOWN")

    assert json.loads(capfd.readouterr().err)["reference_id"] == "ref_abc"


def test_wrapping_keeps_identity_and_records_once(caplog: pytest.LogCaptureFixture) -> None:
    """
    Condition:
    - A typed error is wrapped by the base class and both are recorded.

    Expected:
    - The wrapper keeps the code and reference ID, and only one record exists.
    """
    inner = RequestInvalidError()
    outer = AppError(error=inner)

    record_failure(outer, operation="job", http_status=400)
    record_failure(inner, operation="job", http_status=400)

    assert outer.code == inner.code
    assert outer.reference_id == inner.reference_id
    assert len(_records(caplog)) == 1


def test_str_renders_message_only() -> None:
    """
    Condition:
    - An error wraps a cause holding sensitive text.

    Expected:
    - Default rendering is the safe message.
    """
    error = AppError(error=ValueError(FAKE_SECRET))

    assert str(error) == error.message
    assert FAKE_SECRET not in str(error)


@pytest.mark.parametrize(
    "value,leaked",
    [
        (f"Bearer {FAKE_SECRET}", FAKE_SECRET),
        (f"failed for {FAKE_EMAIL}", FAKE_EMAIL),
        ("postgres://user:hunter2@db/app", "hunter2"),
        ('{"password": "hunter2"}', "hunter2"),
    ],
)
def test_redact_text_removes_secrets(value: str, leaked: str) -> None:
    """
    Condition:
    - Diagnostic text holds a credential or email.

    Expected:
    - The value is gone.
    """
    assert leaked not in redact_text(value)


def test_sanitize_filters_sensitive_keys_and_unknown_types() -> None:
    """
    Condition:
    - A nested structure holds a sensitive key and an unsupported object.

    Expected:
    - Both are replaced and safe values stay.
    """
    result = sanitize({"api_key": "abc", "nested": [{"count": 1, "obj": object()}]})

    assert result == {"api_key": REDACTED, "nested": [{"count": 1, "obj": REDACTED}]}
