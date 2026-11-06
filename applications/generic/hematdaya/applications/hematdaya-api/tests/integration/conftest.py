"""Full-stack fixtures over real Postgres. Start it with ``make run-dependencies``."""

import subprocess
import sys
from collections.abc import AsyncIterator, Callable, Iterator
from datetime import datetime
from uuid import UUID

import pytest
from fastapi import Request
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.core.database import get_session_factory
from app.identity.dependencies import get_current_principal
from app.identity.model.models import PrincipalKind, PrincipalModel
from app.main import app

TEST_PRINCIPAL_HEADER = "x-test-principal"


@pytest.fixture(scope="session", autouse=True)
def migrated_database() -> Iterator[None]:
    """Apply migrations once; a failure here means Postgres is not running."""
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True)
    yield


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    """Client bound to the real application and its real credential resolvers."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as async_client:
        yield async_client


@pytest.fixture
def acting() -> Iterator[Callable[[UUID], dict[str, str]]]:
    """Let a test act as any principal, standing in for credentials that arrive in later specs.

    Yields:
        Callable[[UUID], dict[str, str]]: Builds the headers that act as a principal.
    """

    async def as_header_principal(request: Request) -> PrincipalModel:
        return PrincipalModel(id=UUID(request.headers[TEST_PRINCIPAL_HEADER]), kind=PrincipalKind.DEMO)

    app.dependency_overrides[get_current_principal] = as_header_principal
    yield lambda principal_id: {TEST_PRINCIPAL_HEADER: str(principal_id)}
    app.dependency_overrides.pop(get_current_principal, None)


async def execute(sql: str, **params: object) -> list:
    """Run SQL in its own committed transaction.

    Args:
        sql (str): Statement.
        **params (object): Bound parameters.

    Returns:
        list: Returned rows, if any.
    """
    async with get_session_factory()() as session:
        result = await session.execute(text(sql), params)
        rows = list(result) if result.returns_rows else []
        await session.commit()
        return rows


async def make_principal() -> UUID:
    """Insert a demo principal.

    Returns:
        UUID: Its ID.
    """
    rows = await execute("INSERT INTO principals (id, kind) VALUES (gen_random_uuid(), 'demo') RETURNING id")
    return rows[0][0]


async def make_site(
    owner: UUID, *, kind: str = "demo", virtual_now: datetime | None = None, name: str = "Rumah"
) -> UUID:
    """Insert a site.

    Args:
        owner (UUID): Owner principal.
        kind (str, optional): Site kind. Defaults to demo.
        virtual_now (datetime | None, optional): Demo clock; demo sites default to 2026-10-26 00.00 WIB.
        name (str, optional): Name. Defaults to Rumah.

    Returns:
        UUID: Its ID.
    """
    if kind == "demo" and virtual_now is None:
        virtual_now = datetime.fromisoformat("2026-10-25T17:00:00+00:00")
    rows = await execute(
        "INSERT INTO sites (id, owner_principal_id, kind, name, virtual_now)"
        " VALUES (gen_random_uuid(), :owner, :kind, :name, :virtual_now) RETURNING id",
        owner=owner,
        kind=kind,
        name=name,
        virtual_now=virtual_now,
    )
    return rows[0][0]
