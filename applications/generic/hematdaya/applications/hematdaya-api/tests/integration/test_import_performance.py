"""A 150,000-row preview through the route. Run with ``IMPORT_BENCH=1 ... -s``; CI does not carry it."""

import json
import os
import time
import tracemalloc
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from httpx import AsyncClient

from tests.integration.conftest import execute, make_principal, make_site

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(os.environ.get("IMPORT_BENCH") != "1", reason="Needs IMPORT_BENCH=1"),
]

ROWS = 150_000
MAX_BYTES = 10 * 1024 * 1024
MAX_PEAK_MIB = 256


def _large_file() -> bytes:
    start = datetime(2000, 1, 1, tzinfo=UTC)
    hour = timedelta(hours=1)
    lines = ["interval_start,interval_end,asset,energy_wh"]
    for index in range(ROWS):
        begin = start + index * hour
        lines.append(f"{begin.isoformat()},{(begin + hour).isoformat()},Router,1.5")
    content = ("\n".join(lines) + "\n").encode()
    assert len(content) <= MAX_BYTES
    return content


async def _preview(client: AsyncClient, headers: dict[str, str], site: UUID, content: bytes) -> float:
    files = {"file": ("besar.csv", content, "text/csv"), "mapping": (None, json.dumps({"scope": "disjoint"}))}
    started = time.perf_counter()
    response = await client.post(f"/api/v1/sites/{site}/imports/preview", files=files, headers=headers)
    took = time.perf_counter() - started
    assert response.status_code == 201, response.text
    body = response.json()
    assert (body["total_rows"], body["accepted_rows"]) == (ROWS, ROWS)
    assert (await execute("SELECT count(*) FROM import_rows WHERE import_id = :id", id=body["id"]))[0][0] == ROWS
    await execute("DELETE FROM sites WHERE id = :site", site=site)
    return took


async def test_large_preview_runs_through_the_route(
    client: AsyncClient, acting: Callable[[UUID], dict[str, str]]
) -> None:
    """
    Condition:
    - 150,000 rows within 10 MiB, posted through the real route.

    Expected:
    - 201 with every row stored. Elapsed time is printed, because PRD §18's target belongs to 041's benchmark server.
    """
    content = _large_file()

    principal = await make_principal()
    took = await _preview(client, acting(principal), await make_site(principal), content)

    print(f"\nimport preview: {ROWS} rows, {len(content)} bytes, {took:.2f} s")


async def test_large_preview_stays_within_its_memory_bound(
    client: AsyncClient, acting: Callable[[UUID], dict[str, str]]
) -> None:
    """
    Condition:
    - The same file, with allocations traced.

    Expected:
    - Python's peak stays under 256 MiB.
    """
    content = _large_file()
    principal = await make_principal()
    headers, site = acting(principal), await make_site(principal)

    tracemalloc.start()
    try:
        took = await _preview(client, headers, site, content)
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()

    peak_mib = peak / (1024 * 1024)
    print(f"\nimport preview under tracemalloc: peak {peak_mib:.1f} MiB, {took:.2f} s")
    assert peak_mib < MAX_PEAK_MIB
