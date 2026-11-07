"""Shared fixtures for the CSV parser tests."""

from __future__ import annotations

import io
from collections.abc import Callable
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from app.imports.model.models import MeaningAnswers, ParsedFile, RowResult


@pytest.fixture
def parse_text() -> Callable[..., tuple[ParsedFile, list[RowResult]]]:
    """Parse text or bytes in memory and read every row.

    Returns:
        Callable[..., tuple[ParsedFile, list[RowResult]]]: The parse helper.
    """
    from app.imports.service.parser import iter_rows, parse

    def _parse(
        text: str | bytes, *, answers: MeaningAnswers | None = None, site_timezone: str = "Asia/Jakarta"
    ) -> tuple[ParsedFile, list[RowResult]]:
        source = io.BytesIO(text.encode("utf-8") if isinstance(text, str) else text)
        if answers is None:
            parsed = parse(source, site_timezone=site_timezone)
        else:
            parsed = parse(source, site_timezone=site_timezone, answers=answers)
        return parsed, list(iter_rows(source, parsed))

    return _parse
