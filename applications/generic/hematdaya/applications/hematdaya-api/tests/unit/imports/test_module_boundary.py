"""The parser is pure: its modules import no M1 code and touch no clock, log or process-wide state."""

import ast
from pathlib import Path

import pytest

API_ROOT = Path(__file__).resolve().parents[3]
PURE_MODULES = (
    "app/imports/model/models.py",
    "app/imports/service/dialect.py",
    "app/imports/service/columns.py",
    "app/imports/service/numbers.py",
    "app/imports/service/times.py",
    "app/imports/service/cadence.py",
    "app/imports/service/parser.py",
)
FORBIDDEN_IMPORTS = (
    "app.measurements",
    "app.sites",
    "app.energy",
    "app.assets",
    "app.identity",
    "app.audit",
    "app.core.database",
    "app.core.settings",
    "sqlalchemy",
    "fastapi",
    "logging",
    "os",
    "time",
    "asyncio",
)
FORBIDDEN_CALLS = ("now", "utcnow", "field_size_limit")


def _is_forbidden_import(dotted: str) -> bool:
    return any(dotted == root or dotted.startswith(f"{root}.") for root in FORBIDDEN_IMPORTS)


def _forbidden(source: str) -> list[str]:
    """Name every forbidden import and call in a module's source.

    Args:
        source (str): Python source.

    Returns:
        list[str]: The forbidden items found, in source order.
    """
    found: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            found += [alias.name for alias in node.names if _is_forbidden_import(alias.name)]
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            for alias in node.names:
                dotted = f"{node.module}.{alias.name}"
                if _is_forbidden_import(node.module) or _is_forbidden_import(dotted):
                    found.append(dotted)
        elif isinstance(node, ast.Call):
            name = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", None)
            if name in FORBIDDEN_CALLS:
                found.append(f"{name}()")
    return found


@pytest.mark.parametrize("module", PURE_MODULES)
def test_pure_module_exists(module: str) -> None:
    """
    Condition:
    - One of the seven parser modules from D1.

    Expected:
    - The file exists.
    """
    assert (API_ROOT / module).is_file()


@pytest.mark.parametrize("module", PURE_MODULES)
def test_pure_module_has_no_forbidden_item(module: str) -> None:
    """
    Condition:
    - The source of one parser module.

    Expected:
    - It imports nothing from M1, no framework, no logging, no clock, and changes no process-wide csv limit.
    """
    assert _forbidden((API_ROOT / module).read_text(encoding="utf-8")) == []


@pytest.mark.parametrize(
    ("source", "item"),
    [
        ("from app.sites.service.service import SiteService", "app.sites.service.service.SiteService"),
        ("from app.core import database", "app.core.database"),
        ("import logging", "logging"),
        ("import os.path", "os.path"),
        ("datetime.now()", "now()"),
        ("csv.field_size_limit(1)", "field_size_limit()"),
        ("field_size_limit(1)", "field_size_limit()"),
    ],
)
def test_boundary_helper_flags_forbidden_items(source: str, item: str) -> None:
    """
    Condition:
    - A sample holding one forbidden import or call.

    Expected:
    - The helper names it, so an empty result above means something.
    """
    assert _forbidden(source) == [item]


@pytest.mark.parametrize("source", ["import csv", "from datetime import time", "datetime(2026, 1, 1)"])
def test_boundary_helper_allows_ordinary_items(source: str) -> None:
    """
    Condition:
    - A sample holding only what the parser legitimately uses.

    Expected:
    - The helper flags nothing, including ``datetime.time`` whose name resembles the ``time`` module.
    """
    assert _forbidden(source) == []
