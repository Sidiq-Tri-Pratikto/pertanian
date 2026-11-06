"""Process-wide logging setup."""

import logging
import sys

logger = logging.getLogger("app")


def _redact_email_access(record: logging.LogRecord) -> bool:
    args = record.args
    if isinstance(args, tuple) and len(args) == 5 and isinstance(args[2], str):
        path = args[2].partition("?")[0]
        if path.startswith("/api/v1/invitations/"):
            prefix = "/api/v1/invitations/"
            action = path.removeprefix(prefix).partition("/")[2].rstrip("/")
            safe_path = f"{prefix}{{id}}"
            if action in {"accept", "revoke"}:
                safe_path = f"{safe_path}/{action}"
            record.args = (*args[:2], safe_path, *args[3:])
        elif path.rstrip("/") == "/api/v1/dev/mailbox":
            record.args = (*args[:2], path, *args[3:])
    return True


def setup_logging(level: str) -> None:
    """Send application logs to stdout.

    Args:
        level (str): Log level name.
    """
    logging.getLogger("uvicorn.access").addFilter(_redact_email_access)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    logger.handlers = [handler]
    logger.setLevel(level)
    logger.propagate = False
