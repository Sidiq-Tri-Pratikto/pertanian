"""Base error and concrete typed errors."""

from traceback import walk_tb
from typing import Any, ClassVar, NotRequired, Required, TypedDict, cast
from uuid import uuid4

from app.core.errors import codes
from app.core.errors.public import public_error_for_code
from app.core.errors.sanitize import build_debug_info, sanitize

_MAX_CHAIN = 8
_MAX_TRACEBACK_FRAMES = 32


class DebugInfo(TypedDict):
    """Sanitized diagnostics; never sent to clients."""

    error_type: str
    original_message: str
    traceback: NotRequired[str]
    original_code: NotRequired[str]


class RecoveryInfo(TypedDict, total=False):
    """Retry guidance; ``escalate_when`` is internal only."""

    retryable: Required[bool]
    retry_after_seconds: int
    max_attempts: int
    escalate_when: str


def new_reference_id() -> str:
    """Return a unique failure occurrence identifier.

    Returns:
        str: The reference ID.
    """
    return f"ref_{uuid4().hex}"


class AppError(Exception):
    """Base for every application failure. ``str()`` renders the safe message only.

    Attributes:
        code (str): Stable internal code. Wrapping with the base class keeps the wrapped code.
        message (str): Safe two-clause message.
        reference_id (str): Failure occurrence ID, preserved through wrapping.
        debug_info (DebugInfo): Sanitized diagnostics.
        recovery (RecoveryInfo): Retry guidance.
        headers (dict[str, str]): Protocol headers the response must carry.
    """

    code: ClassVar[str] = codes.APP_UNKNOWN
    headers: ClassVar[dict[str, str]] = {}

    def __init__(self, message: str | None = None, *, error: BaseException | None = None) -> None:
        """Initialize a typed failure.

        Args:
            message (str | None, optional): Safe message replacing the catalog default. Defaults to None.
            error (BaseException | None, optional): The cause. Defaults to None.
        """
        self.error = error
        wrapped = error if isinstance(error, AppError) else None
        if wrapped is not None and type(self).code == codes.APP_UNKNOWN:
            self.code = wrapped.code

        public = public_error_for_code(self.code)
        self.message = public.message if message is None else message
        self.recovery = cast(RecoveryInfo, dict(public.recovery))
        self.reference_id = wrapped.reference_id if wrapped is not None else new_reference_id()
        self._recorded = wrapped._recorded if wrapped is not None else False
        self.debug_info = self._build_debug_info(wrapped)
        super().__init__(self.message)

    def __str__(self) -> str:
        """Return only the user-safe message.

        Returns:
            str: The message.
        """
        return self.message

    def _build_debug_info(self, wrapped: "AppError | None") -> DebugInfo:
        if wrapped is not None:
            return wrapped.debug_info
        info: dict[str, Any] = build_debug_info(self if self.error is None else self.error)
        trace = _safe_traceback(self.error) if self.error is not None else None
        if trace:
            info["traceback"] = trace
        info["original_code"] = self.code
        return cast(DebugInfo, sanitize(info))


def _safe_traceback(error: BaseException) -> str | None:
    """List stack frames without source lines or exception text."""
    lines: list[str] = []
    current: BaseException | None = error
    for _ in range(_MAX_CHAIN):
        if current is None:
            break
        for frame, line_number in walk_tb(current.__traceback__):
            lines.append(f"{type(current).__name__} in {frame.f_code.co_name} at line {line_number}")
        current = current.__cause__ or current.__context__
    return "\n".join(lines[:_MAX_TRACEBACK_FRAMES]) or None


class RequestInvalidError(AppError):
    """The request violates a business rule."""

    code = codes.APP_REQUEST_INVALID


class NotFoundError(AppError):
    """A requested resource does not exist."""

    code = codes.APP_NOT_FOUND


class ConflictError(AppError):
    """The request conflicts with current state."""

    code = codes.APP_CONFLICT


class UnauthorizedError(AppError):
    """The request carries no credential the API accepts."""

    code = codes.APP_AUTH_REQUIRED
    headers = {"WWW-Authenticate": "Bearer"}
