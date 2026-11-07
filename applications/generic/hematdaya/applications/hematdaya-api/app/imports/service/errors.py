"""Import failures."""

from app.core.errors import codes
from app.core.errors.base import AppError


class ImportTooLargeError(AppError):
    """An upload over the body cap, or a file over the byte or row limit."""

    code = codes.APP_IMPORT_TOO_LARGE


class ImportStructureError(AppError):
    """A file whose structure cannot be read."""

    code = codes.APP_IMPORT_STRUCTURE


class ImportBlockedError(AppError):
    """A commit of a preview that is still blocked."""

    code = codes.APP_IMPORT_BLOCKED


class ImportStaleError(AppError):
    """A commit of a preview that has expired, or whose site changed after it was made."""

    code = codes.APP_IMPORT_STALE


class ImportAckRequiredError(AppError):
    """A commit that would skip invalid rows the user has not acknowledged."""

    code = codes.APP_IMPORT_ACK_REQUIRED


class ImportKeyConflictError(AppError):
    """A key already used for another import of the site, or with a different acknowledgment."""

    code = codes.APP_IMPORT_KEY_CONFLICT
