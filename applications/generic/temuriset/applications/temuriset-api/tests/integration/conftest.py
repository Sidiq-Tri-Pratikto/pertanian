"""Integration fixtures: one migrated Postgres for the session, empty platform tables per test."""

import subprocess
import sys
from collections.abc import AsyncIterator, Awaitable, Callable, Iterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.core.database import get_engine
from app.main import app

TABLES = (
    "idempotency_records, audit_events, outbox_deliveries, outbox_events, jobs, "
    "invitations, memberships, sessions, email_codes, mailbox_messages, parties, organizations, accounts"
)
WEB_ORIGIN = "http://localhost:3020"


@pytest.fixture(scope="session", autouse=True)
def migrated_database() -> Iterator[None]:
    """Apply migrations once; a failure here means Postgres is not running (``make run-dependencies``)."""
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True)
    yield


@pytest.fixture
async def clean_tables() -> AsyncIterator[None]:
    """Start each test with empty tables. TRUNCATE bypasses the audit table's row trigger."""
    async with get_engine().begin() as connection:
        await connection.execute(text(f"TRUNCATE {TABLES} CASCADE"))
    yield


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    """Client bound to the real application."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test", headers={"Origin": WEB_ORIGIN}
    ) as async_client:
        yield async_client


async def _sign_up(client: AsyncClient, email: str, *, persona: str = "inovator", name: str = "Rani") -> dict:
    """Sign up through the API and the development mailbox; the client keeps the session cookie.

    Args:
        client (AsyncClient): Client to sign in.
        email (str): New email.
        persona (str, optional): Persona. Defaults to "inovator".
        name (str, optional): Display name. Defaults to "Rani".

    Returns:
        dict: The ``/me`` body.
    """
    sent = await client.post(
        "/api/v1/auth/code",
        json={
            "email": email,
            "purpose": "sign_up",
            "display_name": name,
            "time_zone": "Asia/Jakarta",
            "persona": persona,
        },
    )
    assert sent.status_code == 202, sent.text
    response = await client.post(
        "/api/v1/auth/verify", json={"email": email, "code": await _latest_code(client, email)}
    )
    assert response.status_code == 200, response.text
    return response.json()


async def _latest_code(client: AsyncClient, email: str) -> str:
    """Read the newest code mailed to an email.

    Args:
        client (AsyncClient): Any client.
        email (str): Recipient.

    Returns:
        str: The six-digit code.
    """
    messages = (await client.get("/api/v1/dev/mailbox", params={"email": email})).json()
    return next(word.rstrip(".") for word in messages[0]["body"].split() if word.rstrip(".").isdigit())


SignUp = Callable[..., Awaitable[dict]]
LatestCode = Callable[[AsyncClient, str], Awaitable[str]]


@pytest.fixture
def sign_up() -> SignUp:
    """Sign up a client through the API and the development mailbox."""
    return _sign_up


@pytest.fixture
def latest_code() -> LatestCode:
    """Read the newest mailed code."""
    return _latest_code


@pytest.fixture
def new_client() -> Callable[[], AsyncClient]:
    """Make another browser: its own cookie jar, same web origin."""
    return lambda: AsyncClient(transport=ASGITransport(app=app), base_url="http://test", headers={"Origin": WEB_ORIGIN})
