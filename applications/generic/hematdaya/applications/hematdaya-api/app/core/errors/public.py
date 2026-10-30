"""Public error definitions: the one place internal codes map to what clients see."""

from dataclasses import dataclass, field
from typing import Any

from app.core.errors import codes

_FALLBACK_MESSAGE = (
    "We could not complete the request. Contact support and provide the reference ID shown with this error."
)


@dataclass(frozen=True)
class PublicError:
    """Safe public representation of a failure.

    Attributes:
        code (str): Documented public code.
        http_status (int): Response status.
        message (str): Two-clause message: what happened, what to do next.
        recovery (dict[str, Any]): Retry guidance.
    """

    code: str
    http_status: int
    message: str
    recovery: dict[str, Any] = field(default_factory=lambda: {"retryable": False})


FALLBACK_PUBLIC_ERROR = PublicError("INTERNAL_ERROR", 500, _FALLBACK_MESSAGE)

PUBLIC_ERROR_BY_CODE: dict[str, PublicError] = {
    codes.APP_UNKNOWN: FALLBACK_PUBLIC_ERROR,
    codes.APP_REQUEST_INVALID: PublicError(
        "BAD_REQUEST", 400, "The request could not be processed. Please check the request and try again."
    ),
    codes.APP_NOT_FOUND: PublicError(
        "NOT_FOUND", 404, "The requested resource was not found. Please check the address and try again."
    ),
    codes.APP_CONFLICT: PublicError(
        "CONFLICT", 409, "The request conflicts with the current state. Please review the resource and try again."
    ),
    codes.APP_DB_ERROR: PublicError(
        "DATA_ERROR",
        500,
        "The request could not be completed because of a data error. Contact support with the reference ID.",
    ),
    codes.APP_DB_UNAVAILABLE: PublicError(
        "DATABASE_UNAVAILABLE",
        503,
        "The database is temporarily unavailable. Please try again in a few minutes.",
        {"retryable": True, "retry_after_seconds": 30, "max_attempts": 3},
    ),
}

PUBLIC_ERROR_BY_STATUS: dict[int, PublicError] = {
    400: PublicError("BAD_REQUEST", 400, "The request could not be processed. Please check the request and try again."),
    401: PublicError("UNAUTHORIZED", 401, "Authentication is required. Please provide valid credentials."),
    403: PublicError(
        "FORBIDDEN", 403, "You are not permitted to perform this request. Please contact your administrator."
    ),
    404: PublicError("NOT_FOUND", 404, "The requested resource was not found. Please check the address and try again."),
    405: PublicError("METHOD_NOT_ALLOWED", 405, "This request method is not supported. Please use a supported method."),
    409: PublicError(
        "CONFLICT", 409, "The request conflicts with the current state. Please review the resource and try again."
    ),
    422: PublicError(
        "VALIDATION_FAILED", 422, "The request contains invalid fields. Please correct them and try again."
    ),
    429: PublicError(
        "RATE_LIMITED",
        429,
        "Too many requests were received. Please wait before trying again.",
        {"retryable": True, "retry_after_seconds": 60, "max_attempts": 3},
    ),
}


def public_error_for_code(code: str) -> PublicError:
    """Resolve an internal code to its public definition.

    Args:
        code (str): Internal error code.

    Returns:
        PublicError: The mapped definition, or the fallback for an unregistered code.
    """
    return PUBLIC_ERROR_BY_CODE.get(code, FALLBACK_PUBLIC_ERROR)


def public_error_for_status(status_code: int) -> PublicError:
    """Resolve a framework HTTP status to a fixed public definition.

    Args:
        status_code (int): HTTP status raised by the framework.

    Returns:
        PublicError: A safe definition carrying that status.
    """
    known = PUBLIC_ERROR_BY_STATUS.get(status_code)
    if known is not None:
        return known
    code = "INTERNAL_ERROR" if status_code >= 500 else "HTTP_ERROR"
    return PublicError(code, status_code, _FALLBACK_MESSAGE)


def error_response(public: PublicError, request_id: str, *, details: list[dict[str, Any]] | None = None) -> dict:
    """Build the public envelope.

    Args:
        public (PublicError): The public definition.
        request_id (str): The failure's reference ID.
        details (list[dict[str, Any]] | None, optional): Safe field errors for validation failures. Defaults to None.

    Returns:
        dict: The response body.
    """
    error: dict[str, Any] = {
        "code": public.code,
        "message": public.message,
        "request_id": request_id,
        "recovery": dict(public.recovery),
    }
    if details is not None:
        error["details"] = details
    return {"error": error}
