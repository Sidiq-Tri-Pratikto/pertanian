"""Access log privacy for credential-bearing email routes."""

import logging

import pytest

from app.core.logging import _redact_email_access


@pytest.mark.parametrize(
    ("path", "safe_path"),
    [
        ("/api/v1/invitations/private-fixture-token", "/api/v1/invitations/{id}"),
        ("/api/v1/invitations/private-fixture-token/accept", "/api/v1/invitations/{id}/accept"),
        ("/api/v1/dev/mailbox?email=fixture@example.test", "/api/v1/dev/mailbox"),
        ("/api/v1/capabilities?fixture=1", "/api/v1/capabilities?fixture=1"),
    ],
)
def test_access_logs_keep_email_route_secrets_out(path: str, safe_path: str) -> None:
    """
    Condition:
    - Uvicorn emits an access log for an invitation, development mailbox, or an ordinary route.

    Expected:
    - Secrets are removed from email paths while status, method and ordinary paths are preserved.
    """
    access_logger = logging.Logger("uvicorn.access")
    access_logger.addFilter(_redact_email_access)
    record = access_logger.makeRecord(
        access_logger.name,
        logging.INFO,
        __file__,
        1,
        '%s - "%s %s HTTP/%s" %d',
        ("127.0.0.1", "GET", path, "1.1", 200),
        None,
    )
    assert access_logger.filter(record)
    assert record.getMessage() == f'127.0.0.1 - "GET {safe_path} HTTP/1.1" 200'
