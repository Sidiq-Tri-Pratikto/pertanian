"""Async database engine and session management."""

from collections.abc import AsyncIterator
from datetime import datetime
from functools import lru_cache
from typing import Annotated
from uuid import UUID, uuid4

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


class Row:
    """Columns every table has: a UUID id and the product time it was created."""

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
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
