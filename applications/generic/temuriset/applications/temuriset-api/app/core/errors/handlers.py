"""The single public error boundary."""

from dataclasses import replace

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.errors.base import AppError
from app.core.errors.public import (
    FALLBACK_PUBLIC_ERROR,
    PublicError,
    error_response,
    field_message,
    public_error_for_code,
    public_error_for_status,
)
from app.core.errors.recorder import record_failure

_FORWARDED_HEADERS = ("allow", "www-authenticate")


def respond(
    public: PublicError,
    request_id: str,
    *,
    details: list[dict] | None = None,
    headers: dict[str, str] | None = None,
    extra: dict | None = None,
) -> JSONResponse:
    """Build an envelope response, adding ``Retry-After`` when retry timing exists.

    Args:
        public (PublicError): The public definition.
        request_id (str): The failure's reference ID.
        details (list[dict] | None, optional): Safe field errors. Defaults to None.
        headers (dict[str, str] | None, optional): Protocol headers. Defaults to None.
        extra (dict | None, optional): Safe typed fields for the envelope. Defaults to None.

    Returns:
        JSONResponse: The response.
    """
    response_headers = dict(headers or {})
    retry_after = public.recovery.get("retry_after_seconds")
    if retry_after is not None:
        response_headers["Retry-After"] = str(retry_after)
    return JSONResponse(
        status_code=public.http_status,
        content=error_response(public, request_id, details=details, extra=extra),
        headers=response_headers,
    )


def _record(request: Request, error: AppError, status_code: int) -> None:
    route = request.scope.get("route")
    record_failure(
        error,
        operation=getattr(route, "path", "unmatched"),
        http_status=status_code,
        caller_request_id=request.headers.get("x-request-id"),
    )


async def handle_app_error(request: Request, error: AppError) -> JSONResponse:
    """Render and record a typed error.

    Args:
        request (Request): The current request.
        error (AppError): The failure.

    Returns:
        JSONResponse: The envelope.
    """
    public = replace(public_error_for_code(error.code), message=error.message, recovery=dict(error.recovery))
    _record(request, error, public.http_status)
    return respond(public, error.reference_id, extra=error.public_fields)


async def handle_http_error(request: Request, error: StarletteHTTPException) -> JSONResponse:
    """Replace framework error text with catalog text.

    Args:
        request (Request): The current request.
        error (StarletteHTTPException): The framework failure.

    Returns:
        JSONResponse: The envelope.
    """
    public = public_error_for_status(error.status_code)
    internal = AppError()
    _record(request, internal, public.http_status)
    headers = {key: value for key, value in (error.headers or {}).items() if key.lower() in _FORWARDED_HEADERS}
    return respond(public, internal.reference_id, headers=headers)


async def handle_validation_error(request: Request, error: RequestValidationError) -> JSONResponse:
    """Report invalid fields without echoing submitted values.

    Args:
        request (Request): The current request.
        error (RequestValidationError): The validation failure.

    Returns:
        JSONResponse: The envelope with field errors in ``details``.
    """
    public = public_error_for_status(422)
    internal = AppError()
    _record(request, internal, public.http_status)
    details = [
        {
            "loc": item.get("loc", ()),
            "msg": field_message(item.get("type", "value_error")),
            "type": item.get("type", "value_error"),
        }
        for item in error.errors()[:100]
    ]
    return respond(public, internal.reference_id, details=details)


class ErrorBoundaryMiddleware:
    """Last boundary: answer uncaught failures with the envelope and keep them out of raw server logs.

    A Starlette ``Exception`` handler re-raises after responding, so the server would log an unsanitized
    traceback. Catching here ends the failure at the recorder.
    """

    def __init__(self, app: ASGIApp) -> None:
        """Wrap the application.

        Args:
            app (ASGIApp): The downstream application.
        """
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Run the request, converting any uncaught failure.

        Args:
            scope (Scope): ASGI scope.
            receive (Receive): ASGI receive.
            send (Send): ASGI send.
        """
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        started = False

        async def send_tracked(message: Message) -> None:
            nonlocal started
            started = started or message["type"] == "http.response.start"
            await send(message)

        try:
            await self.app(scope, receive, send_tracked)
        except Exception as error:  # noqa: BLE001 - last boundary; anything escaping bypasses the sanitizer
            internal = AppError(error=error)
            _record(Request(scope), internal, FALLBACK_PUBLIC_ERROR.http_status)
            # Once headers are sent, closing is the only safe move (X-05).
            if not started:
                await respond(FALLBACK_PUBLIC_ERROR, internal.reference_id)(scope, receive, send)


def register_exception_handlers(app: FastAPI) -> None:
    """Install the typed handlers.

    Args:
        app (FastAPI): The application.
    """
    app.add_exception_handler(AppError, handle_app_error)
    app.add_exception_handler(StarletteHTTPException, handle_http_error)
    app.add_exception_handler(RequestValidationError, handle_validation_error)
