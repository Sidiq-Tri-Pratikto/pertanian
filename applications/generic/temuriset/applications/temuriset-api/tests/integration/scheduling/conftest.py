"""Fixtures for scheduling: the matching world, an approved F01 pitch, and helpers."""

import asyncio
import json
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from urllib.parse import parse_qsl, urlsplit

import pytest
from cryptography.fernet import Fernet
from httpx import AsyncClient, Response
from pydantic import SecretStr
from sqlalchemy.dialects.postgresql import Range

from app.capabilities.service.configuration import validate_configuration
from app.core.database import get_session_factory
from app.core.settings import get_settings
from app.scheduling.repository.sqlalchemy.models import BookingRecord
from tests.integration.matching.conftest import World, make_world, world  # noqa: F401 - shared fixtures
from tests.integration.pitches.conftest import act, reread, submitted


async def approved(loaded: World) -> dict[str, Any]:
    """Send F01 to A1 and approve it for discussion; return Mitra A's reading."""
    mitra = loaded.recipients.clients["A"]
    pitch = await submitted(loaded)
    response = await act(mitra, pitch, "decisions", "approve", submission=1, decision="APPROVE")
    assert response.status_code == 200, response.text
    return await reread(mitra, pitch)


async def propose(client: AsyncClient, pitch: dict[str, Any], slots: list[str], key: str, **body: Any) -> Response:
    """Propose slots of 60 minutes by default, in Asia/Jakarta."""
    return await client.post(
        f"/api/v1/pitches/{pitch['id']}/schedule-proposals",
        json={
            "acting_party_id": client.headers["X-Acting-Party"],
            "slots": slots,
            "minutes": 60,
            "time_zone": "Asia/Jakarta",
            "agenda": "Membahas rencana validasi enam bulan",
            **body,
        },
        headers={"Idempotency-Key": key},
    )


async def schedule(client: AsyncClient, pitch: dict[str, Any]) -> dict[str, Any]:
    """Read a pitch's schedule."""
    return (await client.get(f"/api/v1/pitches/{pitch['id']}/schedule")).json()


async def accept(client: AsyncClient, proposal: dict[str, Any], position: int, key: str) -> Response:
    """Accept the slot at a position (1-based) of a proposal."""
    slot = next(item for item in proposal["slots"] if item["position"] == position)
    return await client.post(
        f"/api/v1/schedule-proposals/{proposal['id']}/accept",
        json={
            "acting_party_id": client.headers["X-Acting-Party"],
            "slot_id": slot["id"],
            "expected_version": proposal["version"],
        },
        headers={"Idempotency-Key": key},
    )


async def busy(party_id: str, start: datetime, end: datetime) -> None:
    """Book a party's time, as another meeting would ("Agenda lain Peserta P")."""
    async with get_session_factory()() as session, session.begin():
        session.add(BookingRecord(party_id=party_id, title="Agenda lain", during=Range(start, end, bounds="[)")))


@dataclass(frozen=True)
class RelayRequest:
    """One captured request from the real loopback HTTP transport."""

    path: str
    headers: dict[str, str]
    body: bytes


TEST_ACCESS_TOKEN = "synthetic.calendar-token-value"


@dataclass
class CalendarRelay:
    """A synthetic provider with controllable exchange, availability and revocation."""

    requests: list[RelayRequest] = field(default_factory=list)
    token: dict[str, object] = field(
        default_factory=lambda: {
            "access_token": TEST_ACCESS_TOKEN,
            "token_type": "Bearer",
            "expires_in": 1800,
            "scope": "freebusy.read",
        }
    )
    busy: object = field(default_factory=lambda: {"busy": []})
    busy_status: int = 200
    revoke_status: int = 200
    block_token: bool = False
    block_busy: bool = False
    token_started: asyncio.Event = field(default_factory=asyncio.Event)
    busy_started: asyncio.Event = field(default_factory=asyncio.Event)
    release_token: asyncio.Event = field(default_factory=asyncio.Event)
    release_busy: asyncio.Event = field(default_factory=asyncio.Event)

    async def serve(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        """Reply on an actual loopback socket, without running a provider or a proxy."""
        try:
            first, *lines = (await reader.readuntil(b"\r\n\r\n")).decode("ascii").strip().split("\r\n")
            path = first.split()[1]
            headers = {name.lower(): value.strip() for name, _, value in (line.partition(":") for line in lines)}
            body = await reader.readexactly(int(headers.get("content-length", 0)))
            self.requests.append(RelayRequest(path, headers, body))
            status, payload = 200, {}
            if path == "/token":
                self.token_started.set()
                if self.block_token:
                    await self.release_token.wait()
                payload = self.token
            elif path == "/freebusy":
                self.busy_started.set()
                if self.block_busy:
                    await self.release_busy.wait()
                status, payload = self.busy_status, self.busy
            elif path == "/revoke":
                status = self.revoke_status
            else:
                status = 404
            response = json.dumps(payload).encode()
            writer.write(
                f"HTTP/1.1 {status} Synthetic\r\nContent-Type: application/json\r\n"
                f"Content-Length: {len(response)}\r\nConnection: close\r\n\r\n".encode()
                + response
            )
            await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()


@pytest.fixture
async def calendar_relay(monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[CalendarRelay]:
    """Opt into the validated calendar profile using an ephemeral synthetic server."""
    relay = CalendarRelay()
    server = await asyncio.start_server(relay.serve, "127.0.0.1", 0)
    origin = f"http://127.0.0.1:{server.sockets[0].getsockname()[1]}"
    settings = get_settings()
    monkeypatch.setattr(settings, "calendar_adapter", "loopback-oauth")
    monkeypatch.setattr(settings, "calendar_client_id", "local-fixture")
    monkeypatch.setattr(settings, "calendar_envelope_key", SecretStr(Fernet.generate_key().decode()))
    monkeypatch.setattr(settings, "calendar_authorize_url", f"{origin}/authorize")
    monkeypatch.setattr(settings, "calendar_token_url", f"{origin}/token")
    monkeypatch.setattr(settings, "calendar_freebusy_url", f"{origin}/freebusy")
    monkeypatch.setattr(settings, "calendar_revoke_url", f"{origin}/revoke")
    validate_configuration(settings)
    try:
        async with server:
            yield relay
    finally:
        relay.release_token.set()
        relay.release_busy.set()


async def consent(client: AsyncClient, *, version: int = 0, key: str = "consent") -> tuple[Response, dict[str, str]]:
    """Record consent and follow the initiating session's first authorization redirect."""
    connected = await client.post(
        "/api/v1/me/calendar/connect",
        json={"expected_version": version, "consent": True},
        headers={"Idempotency-Key": key},
    )
    assert connected.status_code == 200, connected.text
    prepared = connected.json()
    authorized = await client.get(prepared["authorization_path"], params={"version": prepared["version"]})
    assert authorized.status_code == 303, authorized.text
    params = dict(parse_qsl(urlsplit(authorized.headers["location"]).query))
    return authorized, params


async def connect_calendar(client: AsyncClient) -> None:
    """Complete the synthetic OAuth flow through the API routes."""
    _, params = await consent(client)
    callback = await client.get("/api/v1/me/calendar/callback", params={"state": params["state"], "code": "test-code"})
    assert "kalender=terhubung" in callback.headers["location"], callback.text


async def disconnect_calendar(client: AsyncClient, *, key: str = "disconnect") -> Response:
    """Disconnect using the current generation returned to this signed-in account."""
    version = (await client.get("/api/v1/me/calendar")).json()["version"]
    return await client.post(
        "/api/v1/me/calendar/disconnect",
        json={"expected_version": version},
        headers={"Idempotency-Key": key},
    )
