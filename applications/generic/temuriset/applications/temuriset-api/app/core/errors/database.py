"""Translate SQLAlchemy failures into typed errors."""

from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DisconnectionError, OperationalError, SQLAlchemyError
from sqlalchemy.exc import TimeoutError as PoolTimeoutError

from app.core.errors import codes
from app.core.errors.base import AppError
from app.core.errors.handlers import handle_app_error

_UNAVAILABLE = (OperationalError, PoolTimeoutError, DisconnectionError)
_RETRY_SAFE_METHODS = ("GET", "HEAD", "OPTIONS")


class DatabaseError(AppError):
    """A database operation failed."""

    code = codes.APP_DB_ERROR


class DatabaseUnavailableError(AppError):
    """The database cannot be reached."""

    code = codes.APP_DB_UNAVAILABLE


def resolve_database_error(error: SQLAlchemyError) -> AppError:
    """Map a SQLAlchemy error to a typed error.

    Args:
        error (SQLAlchemyError): The raw error.

    Returns:
        AppError: ``DatabaseUnavailableError`` for connection failures, ``DatabaseError`` otherwise.
    """
    if isinstance(error, _UNAVAILABLE):
        return DatabaseUnavailableError(error=error)
    return DatabaseError(error=error)


async def handle_database_error(request: Request, error: SQLAlchemyError) -> JSONResponse:
    """Render a database failure. A write may have committed, so only reads stay retryable (X-01).

    Args:
        request (Request): The current request.
        error (SQLAlchemyError): The raw error.

    Returns:
        JSONResponse: The envelope.
    """
    app_error = resolve_database_error(error)
    if request.method not in _RETRY_SAFE_METHODS:
        app_error.recovery = {"retryable": False}
    return await handle_app_error(request, app_error)
