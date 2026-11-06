"""Process-wide logging setup."""

import logging
import sys

CALENDAR_CALLBACK_PATH = "/api/v1/me/calendar/callback"


class _CallbackAccessFilter(logging.Filter):
    """Strip query parameters from Uvicorn access records before any handler can write them."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Preserve access metadata and remove the credential-bearing callback query."""
        args = record.args
        if isinstance(args, tuple) and len(args) == 5 and isinstance(args[2], str):
            path = args[2].partition("?")[0]
            if path.rstrip("/") == CALENDAR_CALLBACK_PATH:
                record.args = (*args[:2], path, *args[3:])
        return True


_CALLBACK_ACCESS_FILTER = _CallbackAccessFilter()

logger = logging.getLogger("app")


def setup_logging(level: str) -> None:
    """Send application logs to stdout.

    Args:
        level (str): Log level name.
    """
    logging.getLogger("uvicorn.access").addFilter(_CALLBACK_ACCESS_FILTER)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    logger.handlers = [handler]
    logger.setLevel(level)
    logger.propagate = False
