"""Centralized, sanitized failure recording."""

import json
import os
import re
from datetime import UTC, datetime
from typing import Any

from app.core.errors.base import AppError
from app.core.errors.sanitize import sanitize
from app.core.logging import logger
from app.core.settings import get_settings

_MAX_OPERATION_LENGTH = 128
_SAFE_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def emergency_log(reference_id: str, code: str) -> None:
    """Write a minimal record straight to stderr, bypassing the logger that just failed.

    Args:
        reference_id (str): Failure occurrence ID.
        code (str): Internal error code.
    """
    try:
        payload = json.dumps({"event": "failure_record_unavailable", "reference_id": reference_id, "code": code})
        os.write(2, f"{payload}\n".encode())
    except Exception:  # noqa: BLE001 - no further sink is safe; the caller can still respond (EH-10)
        return


def record_failure(
    error: AppError,
    *,
    operation: str,
    http_status: int,
    caller_request_id: str | None = None,
) -> None:
    """Record one sanitized failure. Client errors log at warning, the rest at error.

    Args:
        error (AppError): The failure.
        operation (str): Route template or job name.
        http_status (int): Resulting status.
        caller_request_id (str | None, optional): Inbound correlation ID, kept apart from the
            occurrence ID. Defaults to None.
    """
    if error._recorded:
        return
    _mark_recorded(error)
    try:
        record: dict[str, Any] = {
            "reference_id": error.reference_id,
            "code": error.code,
            "http_status": http_status,
            "service": get_settings().service_name,
            "operation": sanitize(operation[:_MAX_OPERATION_LENGTH]),
            "timestamp": datetime.now(UTC).isoformat(),
            "debug_info": sanitize(dict(error.debug_info)),
        }
        if caller_request_id is not None and _SAFE_ID.fullmatch(caller_request_id):
            record["caller_request_id"] = caller_request_id
        line = f"Application failure {json.dumps(record, sort_keys=True)}"
        if 400 <= http_status < 500:
            logger.warning(line)
        else:
            logger.error(line)
    except Exception:  # noqa: BLE001 - error handling must not fail while handling an error (EH-10)
        emergency_log(error.reference_id, error.code)


def _mark_recorded(error: AppError) -> None:
    current: BaseException | None = error
    while isinstance(current, AppError):
        current._recorded = True
        current = current.error
