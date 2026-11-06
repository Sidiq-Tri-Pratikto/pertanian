"""Shared validated wire types."""

import re
from decimal import Decimal
from typing import Annotated
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import AfterValidator, BeforeValidator, PlainSerializer, WithJsonSchema
from pydantic_core import PydanticCustomError


def _valid_timezone(name: str) -> str:
    try:
        ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError) as error:
        raise PydanticCustomError("timezone_invalid", "Unknown IANA timezone") from error
    return name


Timezone = Annotated[str, AfterValidator(_valid_timezone)]
"""An IANA timezone name such as ``Asia/Jakarta``, never a fixed offset."""


_DECIMAL_PATTERN = r"^-?\d+(\.\d+)?$"


def _decimal_from_string(value: object) -> Decimal:
    if not isinstance(value, str):
        raise PydanticCustomError("decimal_string_type", "Decimal values travel as strings")
    if not re.fullmatch(_DECIMAL_PATTERN, value):
        raise PydanticCustomError("decimal_parsing", "Not a plain decimal")
    return Decimal(value)


DecimalString = Annotated[
    Decimal,
    BeforeValidator(_decimal_from_string),
    PlainSerializer(str, return_type=str),
    WithJsonSchema({"type": "string", "pattern": _DECIMAL_PATTERN}),
]
"""An exact decimal that refuses JSON numbers, so no binary float ever reaches a calculation."""
