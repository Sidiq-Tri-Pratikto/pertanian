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
            subjects = await reset(session, settings)
        print(f"Demo siap: {len(subjects) - 1} inovasi dan satu pendanaan perusahaan.")  # noqa: T201 - a command's output
    finally:
        await get_engine().dispose()


if __name__ == "__main__":
    asyncio.run(main())
