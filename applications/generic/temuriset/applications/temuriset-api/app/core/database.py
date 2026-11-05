"""Async database engine and session management."""

from collections.abc import AsyncIterator, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime
from functools import lru_cache
from typing import Annotated, Any
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

from fastapi import Depends
from sqlalchemy import DateTime
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.core import clock
from app.core.errors.database import DatabaseUnavailableError
from app.core.settings import get_settings


class Base(DeclarativeBase):
    """Declarative base for ORM models. Every timestamp is ``timestamptz``."""

    type_annotation_map = {datetime: DateTime(timezone=True)}


# Per-table counters while fixtures are seeded, so reseeding yields the same ids (spec 021). None means random ids.
_SEEDED_IDS: ContextVar[tuple[UUID, dict[str, int]] | None] = ContextVar("seeded_ids", default=None)
# Records of what happened, not fixture content: they keep random ids, so reseeding never collides with history.
_RANDOM_ID_TABLES = frozenset(
    {"audit_events", "outbox_events", "outbox_deliveries", "jobs", "idempotency_records", "sessions", "email_codes"}
)


def new_id(context: Any) -> UUID:  # noqa: ANN401 - SQLAlchemy passes its execution context
    """Return a row id: random, or derived from the table and a counter inside ``seeded_ids``.

    Args:
        context (Any): SQLAlchemy's execution context; it names the table being written.

    Returns:
        UUID: The id.
    """
    seeded = _SEEDED_IDS.get()
    table = getattr(getattr(context, "current_column", None), "table", None)
    if seeded is None or table is None or table.name in _RANDOM_ID_TABLES:
        return uuid4()
    namespace, counters = seeded
    counters[table.name] = counters.get(table.name, 0) + 1
    return uuid5(namespace, f"{table.name}:{counters[table.name]}")


@contextmanager
def seeded_ids(name: str) -> Iterator[None]:
    """Make rows created inside the block get ids that depend only on ``name``, the table and creation order.

    Args:
        name (str): The fixture set, such as ``demo``.

    Yields:
        None: Nothing.
    """
    token = _SEEDED_IDS.set((uuid5(NAMESPACE_URL, f"temuriset:{name}"), {}))
    try:
        yield
    finally:
        _SEEDED_IDS.reset(token)


class Row:
    """Columns every table has: a UUID id and the product time it was created."""

    id: Mapped[UUID] = mapped_column(primary_key=True, default=new_id)
    created_at: Mapped[datetime] = mapped_column(default=clock.now)


class MutableRow(Row):
    """Columns every mutable table adds: when it last changed and its version for ``expected_version``."""

    updated_at: Mapped[datetime] = mapped_column(default=clock.now, onupdate=clock.now)
    version: Mapped[int] = mapped_column(default=1, server_default="1")


@lru_cache
def get_engine() -> AsyncEngine:
    """Return the shared engine. Parameters stay out of error text so they cannot reach logs.

    Returns:
        AsyncEngine: The process-wide engine.
    """
    return create_async_engine(
        get_settings().database_url.get_secret_value(),
        pool_pre_ping=True,
        hide_parameters=True,
    )


@lru_cache
def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return the shared session factory.

    Returns:
        async_sessionmaker[AsyncSession]: The session factory.
    """
    return async_sessionmaker(get_engine(), expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    """Yield one session per request, connected up front, committing when the route succeeds.

    The driver raises raw socket errors while connecting, outside SQLAlchemy's error wrapping, so an
    outage is translated here. Nothing has run yet at this point, so the failure is safe to retry.
    A route that raises never reaches the commit; closing the session rolls its work back.

    Yields:
        AsyncSession: The request's session.

    Raises:
        DatabaseUnavailableError: When the database cannot be reached.
    """
    async with get_session_factory()() as session:
        try:
            await session.connection()
        except OSError as error:
            raise DatabaseUnavailableError(error=error) from error
        yield session
        await session.commit()


# Function scope commits before the response is sent, so a failed commit can never follow a success response.
SessionDep = Annotated[AsyncSession, Depends(get_session, scope="function")]
