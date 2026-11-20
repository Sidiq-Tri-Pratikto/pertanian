"""Vercel entry point for the demo deployment (deployment/temuriset/vercel/README.md).

Vercel runs the API as a serverless function and has no long-running worker, so after each write request this
entry runs worker passes until nothing is due. Time-based jobs (expiries, weekly digest) only run when such a pass
happens. Connections are not pooled, because a function instance may serve each request on a fresh event loop.
"""

import logging
import os
from functools import partial
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy.ext import asyncio as sqlalchemy_asyncio
from sqlalchemy.pool import NullPool


def _asyncpg_url(url: str) -> str:
    """Accept the URL as Neon shows it: asyncpg wants ``ssl`` instead of ``sslmode`` and no ``channel_binding``.

    The pooler host is swapped for the direct one, because asyncpg's prepared statements break behind PgBouncer.
    """
    parts = urlsplit(url)
    scheme = "postgresql+asyncpg" if parts.scheme in ("postgres", "postgresql") else parts.scheme
    query = []
    for key, value in parse_qsl(parts.query):
        if key == "channel_binding":
            continue
        query.append(("ssl", value) if key == "sslmode" else (key, value))
    return urlunsplit((scheme, parts.netloc.replace("-pooler.", "."), parts.path, urlencode(query), parts.fragment))


if os.environ.get("DATABASE_URL"):
    os.environ["DATABASE_URL"] = _asyncpg_url(os.environ["DATABASE_URL"])

import app.core.database as database  # noqa: E402

database.create_async_engine = partial(sqlalchemy_asyncio.create_async_engine, poolclass=NullPool)

import app.worker.__main__  # noqa: E402, F401 - registers every consumer and job, as the worker does
from app.core.database import get_session_factory  # noqa: E402
from app.main import app as api  # noqa: E402
from app.worker.loop import dispatch_events, run_jobs  # noqa: E402
from app.worker.registry import registry  # noqa: E402

_READ_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})
_MAX_PASSES = 5
logger = logging.getLogger(__name__)


async def _drain() -> None:
    factory = get_session_factory()
    for _ in range(_MAX_PASSES):
        claimed = await dispatch_events(factory, registry) + await run_jobs(factory, registry)
        if claimed == 0:
            return


async def app(scope, receive, send) -> None:  # noqa: ANN001 - ASGI callable
    """Serve the API; after a write, run due worker items before the response finishes.

    The last body chunk is held back until the passes end, so the function instance stays alive for them.
    """
    if scope["type"] != "http" or scope["method"] in _READ_METHODS:
        await api(scope, receive, send)
        return

    async def send_after_drain(message) -> None:  # noqa: ANN001 - ASGI message
        if message["type"] == "http.response.body" and not message.get("more_body", False):
            try:
                await _drain()
            except Exception:  # noqa: BLE001 - a failed pass must not fail a request that already succeeded
                logger.exception("worker pass after request failed")
        await send(message)

    await api(scope, receive, send_after_drain)
