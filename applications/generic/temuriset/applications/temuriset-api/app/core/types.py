"""Shared wire types: money, currency and cursor pagination."""

import base64
import binascii
import json
from typing import Annotated, Any

from pydantic import BaseModel, Field, StringConstraints

from app.core.errors.base import RequestInvalidError

# A decimal string: Pydantic ``Decimal`` would also accept JSON numbers, which lose precision in clients.
Money = Annotated[str, StringConstraints(strict=True, pattern=r"^\d{1,16}(\.\d{1,4})?$")]
CurrencyCode = Annotated[str, StringConstraints(strict=True, pattern=r"^[A-Z]{3}$")]

MAX_LIMIT = 100
Limit = Annotated[int, Field(ge=1, le=MAX_LIMIT)]


class Page[Item](BaseModel):
    """One page of a list. ``next_cursor`` is opaque and absent on the last page."""

    items: list[Item]
    next_cursor: str | None = None


def encode_cursor(position: dict[str, Any]) -> str:
    """Encode a list position as an opaque cursor.

    Args:
        position (dict[str, Any]): JSON-safe values of the sort keys of the last item.

    Returns:
        str: The cursor.
    """
    raw = json.dumps(position, sort_keys=True, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def decode_cursor(cursor: str) -> dict[str, Any]:
    """Decode a cursor made by ``encode_cursor``.

    Args:
        cursor (str): The cursor.

    Returns:
        dict[str, Any]: The position.

    Raises:
        RequestInvalidError: When the cursor was not made by this service.
    """
    try:
        position = json.loads(base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)))
    except (binascii.Error, ValueError) as error:
        raise RequestInvalidError(_INVALID_CURSOR, error=error) from error
    if not isinstance(position, dict):
        raise RequestInvalidError(_INVALID_CURSOR)
    return position


_INVALID_CURSOR = "Penanda halaman tidak dikenali. Muat ulang daftar dari awal lalu coba lagi."
