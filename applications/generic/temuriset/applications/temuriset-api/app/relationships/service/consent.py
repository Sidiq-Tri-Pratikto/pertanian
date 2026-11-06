"""Which fields of a confirmed relationship may be public: the ceiling, cut by subsets and restrictions."""

import hashlib
import json
from typing import Any

FIELDS = ("name", "type", "scope", "date", "amount", "percent")


def effective_fields(ceiling: list[str], subsets: list[list[str]], restricted: set[str]) -> list[str]:
    """Return the public fields: in the ceiling, in every party's subset, and not restricted (FR-002).

    Args:
        ceiling (list[str]): The version's upper bound.
        subsets (list[list[str]]): Each confirming party's choice; fewer than two parties means nothing is public.
        restricted (set[str]): Fields any party narrowed since.

    Returns:
        list[str]: Fields in ceiling order.
    """
    if len(subsets) < 2:
        return []
    return [field for field in ceiling if all(field in subset for subset in subsets) and field not in restricted]


def checksum(kind: str, number: int, values: dict[str, Any], ceiling: list[str]) -> str:
    """Name one version's exact content, so a confirmation binds to it (FR-001).

    Args:
        kind (str): Relationship type.
        number (int): Version number.
        values (dict[str, Any]): The summary.
        ceiling (list[str]): The public ceiling.

    Returns:
        str: A SHA-256 hex digest.
    """
    canonical = json.dumps({"type": kind, "number": number, "values": values, "ceiling": ceiling}, sort_keys=True)
    return hashlib.sha256(canonical.encode()).hexdigest()
