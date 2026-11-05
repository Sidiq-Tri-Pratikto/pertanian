"""Run the worker: ``python -m app.worker``. SIGINT or SIGTERM finishes the current pass, then exits."""

import asyncio
import signal

from app.capabilities.service.configuration import validate_configuration
from app.core.database import get_engine, get_session_factory
from app.core.logging import setup_logging
from app.core.settings import get_settings
from app.worker.loop import run_forever
from app.worker.registry import registry


async def main() -> None:
    """Validate configuration, then poll until a stop signal."""
    settings = get_settings()
    setup_logging(settings.log_level)
    validate_configuration(settings)
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for signal_number in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(signal_number, stop.set)
    try:
        await run_forever(get_session_factory(), registry, stop=stop)
    finally:
        await get_engine().dispose()


if __name__ == "__main__":
    asyncio.run(main())
