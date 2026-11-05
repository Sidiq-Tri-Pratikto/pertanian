"""The one source of product time. Tests freeze it; security checks use the wall clock directly."""

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime

_frozen: datetime | None = None


def now() -> datetime:
    """Return the current product time.

    Returns:
        datetime: An aware UTC instant, or the frozen instant inside ``frozen()``.
    """
    return _frozen if _frozen is not None else datetime.now(UTC)


@contextmanager
def frozen(at: datetime) -> Iterator[None]:
    """Freeze product time, for tests.

    Args:
        at (datetime): An aware instant.

    Yields:
        None: While frozen.

    Raises:
        ValueError: When ``at`` has no time zone.
    """
    global _frozen
    if at.tzinfo is None:
        raise ValueError("Product time must be time zone aware.")
    previous, _frozen = _frozen, at.astimezone(UTC)
    try:
        yield
    finally:
        _frozen = previous
