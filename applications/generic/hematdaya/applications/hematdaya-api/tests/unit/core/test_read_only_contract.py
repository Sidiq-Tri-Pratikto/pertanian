"""Monitoring-only contract (FR-20, AT-49)."""

import re

from app.main import app

ACTUATION = re.compile(
    r"control|command|relay|switch|actuat|turn[-_]?(on|off)|power[-_]?(on|off)|shutdown", re.IGNORECASE
)


def test_no_route_can_actuate_equipment() -> None:
    """
    Condition:
    - The full route table of the application.

    Expected:
    - No path or operation offers physical control.
    """
    document = app.openapi()

    for path, path_item in document["paths"].items():
        assert not ACTUATION.search(path)
        for operation in path_item.values():
            assert not ACTUATION.search(operation.get("operationId", ""))
