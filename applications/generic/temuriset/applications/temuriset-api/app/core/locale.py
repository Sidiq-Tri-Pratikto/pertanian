"""Request-scoped language for messages and emails, ported from HematDaya's locale middleware."""

from contextvars import ContextVar
from typing import Literal

from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

Locale = Literal["id", "en"]
LOCALE_HEADER = "X-TemuRiset-Locale"
_request_locale: ContextVar[Locale] = ContextVar("request_locale", default="id")


def locale() -> Locale:
    """Return the language of the current request; Indonesian outside a request and by default.

    Returns:
        Locale: ``id`` or ``en``.
    """
    return _request_locale.get()


def as_locale(value: str | None) -> Locale:
    """Read a stored or requested language safely.

    Args:
        value (str | None): A language tag such as ``en`` or ``id``.

    Returns:
        Locale: ``en`` for English, otherwise ``id``.
    """
    return "en" if (value or "").strip().lower() == "en" else "id"


class LocaleMiddleware:
    """Set the request language before dispatch and mark the response with it."""

    def __init__(self, app: ASGIApp) -> None:
        """Wrap an ASGI app.

        Args:
            app (ASGIApp): The application.
        """
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Run one request in its language.

        Args:
            scope (Scope): ASGI scope.
            receive (Receive): ASGI receive.
            send (Send): ASGI send.
        """
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        language = as_locale(Headers(scope=scope).get(LOCALE_HEADER))
        token = _request_locale.set(language)

        async def with_language(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers["Content-Language"] = language
                headers.add_vary_header(LOCALE_HEADER)
            await send(message)

        try:
            await self.app(scope, receive, with_language)
        finally:
            _request_locale.reset(token)
