"""Process-wide logging setup."""

import logging
import sys

logger = logging.getLogger("app")


def setup_logging(level: str) -> None:
    """Send application logs to stdout.

    Args:
        level (str): Log level name.
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    logger.handlers = [handler]
    logger.setLevel(level)
    logger.propagate = False
    # Dependency diagnostics can include untrusted status text or headers. Use the app's safe error recorder.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
