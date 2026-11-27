"""Seed the labelled demo: ``python -m app.demo``. Recreates only demo rows; real accounts are untouched."""

import asyncio

from app.core.database import get_engine, get_session_factory
from app.core.settings import get_settings
from app.demo.service.fixtures import reset


async def main() -> None:
    """Reset the demo in one transaction."""
    settings = get_settings()
    try:
        async with get_session_factory()() as session, session.begin():
            await reset(session, settings)
        print("Demo siap: Inovator A dengan Produk A, Investor A, dan Investor B yang masih kosong.")  # noqa: T201 - a command's output
    finally:
        await get_engine().dispose()


if __name__ == "__main__":
    asyncio.run(main())
