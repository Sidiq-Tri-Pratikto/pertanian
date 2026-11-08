"""Request-scoped language selection for display copy."""

from contextvars import ContextVar
from typing import Literal

from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

Locale = Literal["id", "en"]
MONTH_NAMES: dict[Locale, tuple[str, ...]] = {
    "id": ("Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober",
           "November", "Desember"),
    "en": ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
           "November", "December"),
}  # fmt: skip
LOCALE_HEADER = "X-HematDaya-Locale"
_request_locale: ContextVar[Locale] = ContextVar("request_locale", default="id")
_opted_in: ContextVar[bool] = ContextVar("bilingual_copy", default=False)


def locale() -> Locale:
    """Return the language selected for this request."""
    return _request_locale.get()


def wants_bilingual_copy() -> bool:
    """Return whether the client explicitly selected a supported language."""
    return _opted_in.get()


class LocaleMiddleware:
    """Set the request locale before dispatch and mark localized responses."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        requested = Headers(scope=scope).get(LOCALE_HEADER, "").strip().lower()
        language: Locale = "en" if requested == "en" else "id"
        token = _request_locale.set(language)
        opt_in = _opted_in.set(requested in {"id", "en"})

        async def with_language(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers["Content-Language"] = language
                headers.add_vary_header(LOCALE_HEADER)
            await send(message)

        try:
            await self.app(scope, receive, with_language)
        finally:
            _opted_in.reset(opt_in)
            _request_locale.reset(token)
