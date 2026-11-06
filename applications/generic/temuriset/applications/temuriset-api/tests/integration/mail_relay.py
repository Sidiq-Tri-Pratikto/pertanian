"""A real HTTP loopback double for the development-only email contract."""

import asyncio
import json
from collections import deque
from collections.abc import AsyncIterator
from dataclasses import dataclass, field

import pytest
from cryptography.fernet import Fernet
from pydantic import SecretStr

from app.capabilities.service.configuration import validate_configuration
from app.core.settings import get_settings


@dataclass
class LocalRelay:
    """Accept each idempotency key once, with scripted failures before or after acceptance."""

    monkeypatch: pytest.MonkeyPatch
    port: int = 0
    outcomes: deque[int | None] = field(default_factory=deque)
    message_received: asyncio.Event = field(default_factory=asyncio.Event)
    allow_acknowledgement: asyncio.Event | None = None
    requests: list[tuple[str, dict[str, str]]] = field(default_factory=list)
    accepted: dict[str, dict[str, str]] = field(default_factory=dict)

    def enable(self) -> None:
        """Select the real adapter with synthetic settings for this test."""
        settings = get_settings()
        self.monkeypatch.setattr(settings, "mailbox_adapter", "loopback-relay")
        self.monkeypatch.setattr(settings, "email_relay_url", SecretStr(f"http://127.0.0.1:{self.port}/deliver"))
        self.monkeypatch.setattr(settings, "email_relay_sender", SecretStr("relay@example.test"))
        self.monkeypatch.setattr(settings, "email_envelope_key", SecretStr(Fernet.generate_key().decode("ascii")))
        validate_configuration(settings)

    async def handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        """Read one HTTP message and optionally lose its acknowledgement."""
        try:
            lines = (await reader.readuntil(b"\r\n\r\n")).decode("ascii").splitlines()
            assert lines[0] == "POST /deliver HTTP/1.1"
            headers = dict(line.lower().split(": ", 1) for line in lines[1:] if line)
            assert headers["content-type"] == "application/json"
            key = headers["idempotency-key"]
            assert len(key) in (32, 64) and int(key, 16)
            message = json.loads(await reader.readexactly(int(headers["content-length"])))
            self.requests.append((key, message))
            status = self.outcomes.popleft() if self.outcomes else 202
            if status is None or 200 <= status < 300:
                self.accepted.setdefault(key, message)
            self.message_received.set()
            if self.allow_acknowledgement is not None:
                await self.allow_acknowledgement.wait()
            if status is not None:
                # Even failures may echo the request; the client must ignore the response body.
                data = b"fixture-private-relay-response " + json.dumps(message).encode("utf-8")
                writer.write(
                    f"HTTP/1.1 {status} Fixture\r\nContent-Length: {len(data)}\r\nConnection: close\r\n"
                    f"Location: http://127.0.0.1:{self.port}/unexpected\r\n\r\n".encode("ascii")
                    + data
                )
                await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()


@pytest.fixture
async def local_relay(monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[LocalRelay]:
    """Bind an isolated, synthetic relay to an ephemeral loopback port."""
    relay = LocalRelay(monkeypatch)
    async with await asyncio.start_server(relay.handle, "127.0.0.1", 0) as server:
        relay.port = server.sockets[0].getsockname()[1]
        yield relay
