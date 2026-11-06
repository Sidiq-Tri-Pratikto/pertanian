"""The off profile and a bounded, synthetic loopback calendar transport."""

from asyncio import timeout
from base64 import urlsafe_b64encode
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from json import loads
from typing import Annotated, Literal
from urllib.parse import urlencode

import httpx
from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.core.errors import codes
from app.core.errors.base import AppError
from app.core.logging import CALENDAR_CALLBACK_PATH
from app.core.settings import Settings

_TIMEOUT = 2.0
_MAX_BODY = 16_384
_MAX_WINDOWS = 5

_UTCTimestamp = Annotated[
    str,
    StringConstraints(pattern=r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]{1,6})?(Z|\+00:00)$"),
]


class CalendarUnavailableError(AppError):
    """The local provider or stored credential could not be used safely."""

    code = codes.APP_CALENDAR_UNAVAILABLE

    def __init__(self, reason: str, cause: Exception | None = None) -> None:
        """Record a controlled diagnostic without copying provider input into error text."""
        super().__init__()
        self.debug_info["original_message"] = reason
        if cause is not None:
            self.debug_info["error_type"] = type(cause).__name__


@dataclass(frozen=True)
class CalendarWindow:
    """An interval with an inclusive start and exclusive end."""

    start: datetime
    end: datetime

    def overlaps(self, other: "CalendarWindow") -> bool:
        """Compare the intervals without treating a shared endpoint as busy."""
        return self.start < other.end and other.start < self.end

    def as_json(self) -> dict[str, str]:
        """Send only the two UTC instants."""
        return {
            "start": self.start.astimezone(UTC).isoformat().replace("+00:00", "Z"),
            "end": self.end.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        }


class _TokenResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, hide_input_in_errors=True)

    access_token: Annotated[str, StringConstraints(max_length=2048, pattern=r"^[A-Za-z0-9._~+/=-]+$")]
    token_type: Literal["Bearer", "bearer"]
    expires_in: Annotated[int, Field(gt=0, le=3600)]
    scope: Literal["freebusy.read"]


class _BusyInterval(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, hide_input_in_errors=True)

    start: _UTCTimestamp
    end: _UTCTimestamp


class _BusyResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, hide_input_in_errors=True)

    busy: Annotated[list[_BusyInterval], Field(max_length=100)]


@dataclass(frozen=True)
class CalendarToken:
    """An in-memory bearer token with its finite provider expiry."""

    access_token: str = field(repr=False)
    expires_at: datetime


class CalendarAdapter:
    """Default-off calendar. The loopback implementation is selected only in development."""

    enabled = False

    def authorization(self, state: str, verifier: str) -> str:
        """Build an authorization URL when the adapter is enabled."""
        raise CalendarUnavailableError("calendar adapter is off")

    async def exchange(self, code: str, verifier: str) -> CalendarToken:
        """Exchange a code when the adapter is enabled."""
        raise CalendarUnavailableError("calendar adapter is off")

    async def freebusy(self, token: str, windows: list[CalendarWindow]) -> list[CalendarWindow]:
        """Read busy intervals when the adapter is enabled."""
        raise CalendarUnavailableError("calendar adapter is off")

    async def revoke(self, token: str) -> None:
        """Revoke a provider credential when the adapter is enabled."""
        raise CalendarUnavailableError("calendar adapter is off")


def _json(data: bytes) -> object:
    def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result = dict(pairs)
        if len(result) != len(pairs):
            raise ValueError("Duplicate calendar response field")
        return result

    return loads(data.decode("utf-8"), object_pairs_hook=unique_object)


def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        timeout=_TIMEOUT,
        follow_redirects=False,
        trust_env=False,
        headers={"Accept-Encoding": "identity"},
    )


class LoopbackCalendarAdapter(CalendarAdapter):
    """OAuth code + S256 PKCE and a free/busy-only synthetic calendar protocol."""

    enabled = True

    def __init__(self, settings: Settings) -> None:
        """Bind to the deployment's startup-validated endpoints and web callback."""
        self.settings = settings
        self.callback = settings.calendar_callback_origin + CALENDAR_CALLBACK_PATH

    def authorization(self, state: str, verifier: str) -> str:
        """Build the fixed-scope authorization request for the browser."""
        challenge = urlsafe_b64encode(sha256(verifier.encode("ascii")).digest()).rstrip(b"=").decode("ascii")
        return (
            self.settings.calendar_authorize_url
            + "?"
            + urlencode(
                {
                    "client_id": self.settings.calendar_client_id,
                    "redirect_uri": self.callback,
                    "response_type": "code",
                    "scope": self.settings.calendar_scope,
                    "state": state,
                    "code_challenge": challenge,
                    "code_challenge_method": "S256",
                }
            )
        )

    async def exchange(self, code: str, verifier: str) -> CalendarToken:
        """Exchange the code and require the exact scope and finite expiry."""
        started = datetime.now(UTC)
        data = await self._post(
            self.settings.calendar_token_url,
            data={
                "grant_type": "authorization_code",
                "client_id": self.settings.calendar_client_id,
                "redirect_uri": self.callback,
                "code": code,
                "code_verifier": verifier,
            },
        )
        try:
            token = _TokenResponse.model_validate(_json(data))
        except (ValueError, RecursionError) as error:
            raise CalendarUnavailableError("invalid calendar token response", error) from error
        return CalendarToken(token.access_token, started + timedelta(seconds=token.expires_in))

    async def freebusy(self, token: str, windows: list[CalendarWindow]) -> list[CalendarWindow]:
        """Send at most five short windows and accept bounded UTC busy intervals only."""
        if not 1 <= len(windows) <= _MAX_WINDOWS or any(
            not timedelta(0) < window.end - window.start <= timedelta(hours=1) for window in windows
        ):
            raise CalendarUnavailableError("calendar query window limit exceeded")
        data = await self._post(
            self.settings.calendar_freebusy_url,
            headers={"Authorization": f"Bearer {token}"},
            json={"windows": [window.as_json() for window in windows]},
        )
        try:
            busy = _BusyResponse.model_validate(_json(data)).busy
            parsed = [
                CalendarWindow(datetime.fromisoformat(item.start), datetime.fromisoformat(item.end)) for item in busy
            ]
            if any(interval.end <= interval.start for interval in parsed):
                raise ValueError("Invalid busy interval")
        except (ValueError, RecursionError) as error:
            raise CalendarUnavailableError("invalid calendar free/busy response", error) from error
        return parsed

    async def revoke(self, token: str) -> None:
        """Request revocation using only the credential and synthetic client ID."""
        await self._post(
            self.settings.calendar_revoke_url,
            data={"token": token, "token_type_hint": "access_token", "client_id": self.settings.calendar_client_id},
            read_json=False,
        )

    async def _post(
        self,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        data: dict[str, str] | None = None,
        json: dict[str, list[dict[str, str]]] | None = None,
        read_json: bool = True,
    ) -> bytes:
        try:
            async with (
                timeout(_TIMEOUT),
                _client() as client,
                client.stream(
                    "POST",
                    url,
                    headers=headers,
                    data=data,
                    json=json,
                ) as response,
            ):
                if not response.is_success:
                    raise CalendarUnavailableError("calendar provider refused the request")
                if not read_json:
                    if response.status_code not in (200, 204):
                        raise CalendarUnavailableError("calendar provider did not confirm revocation")
                    return b""
                if (
                    response.headers.get("content-type", "").partition(";")[0].strip().lower() != "application/json"
                    or response.headers.get("content-encoding", "identity").lower() != "identity"
                ):
                    raise CalendarUnavailableError("unsupported calendar response encoding")
                body = bytearray()
                async for chunk in response.aiter_bytes(chunk_size=4096):
                    if len(body) + len(chunk) > _MAX_BODY:
                        raise CalendarUnavailableError("calendar response exceeded the size limit")
                    body.extend(chunk)
                return bytes(body)
        except (httpx.HTTPError, TimeoutError) as error:
            raise CalendarUnavailableError("calendar provider transport failed", error) from error


def calendar_adapter(settings: Settings) -> CalendarAdapter:
    """Select a validated development-only adapter, or fail closed."""
    if settings.calendar_enabled:
        return LoopbackCalendarAdapter(settings)
    return CalendarAdapter()
