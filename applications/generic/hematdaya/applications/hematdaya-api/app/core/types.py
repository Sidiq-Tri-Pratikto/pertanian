"""Shared validated wire types."""

from typing import Annotated
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import AfterValidator
from pydantic_core import PydanticCustomError


def _valid_timezone(name: str) -> str:
    try:
        ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError) as error:
        raise PydanticCustomError("timezone_invalid", "Unknown IANA timezone") from error
    return name


Timezone = Annotated[str, AfterValidator(_valid_timezone)]
"""An IANA timezone name such as ``Asia/Jakarta``, never a fixed offset."""
