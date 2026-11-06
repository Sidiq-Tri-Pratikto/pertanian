"""Optimistic concurrency: stale intent never overwrites."""

from app.core.errors import codes
from app.core.errors.base import AppError


class StaleVersionError(AppError):
    """The client changed an older version than the one stored."""

    code = codes.APP_STALE_VERSION

    def __init__(self, current_version: int) -> None:
        """Report the stored version so the client can reload it.

        Args:
            current_version (int): The stored version.
        """
        super().__init__(public_fields={"current_version": current_version})


def check_expected(current: int, expected: int) -> None:
    """Refuse a change made against another version.

    Args:
        current (int): The stored version.
        expected (int): The ``expected_version`` the client sent.

    Raises:
        StaleVersionError: When they differ.
    """
    if expected != current:
        raise StaleVersionError(current)
