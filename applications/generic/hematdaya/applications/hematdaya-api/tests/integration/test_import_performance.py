"""150,000 rows previewed and committed through the routes. Run with ``IMPORT_BENCH=1 ... -s``; CI does not carry it."""

import asyncio
import json
import os
import secrets
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
STREAMS = 100
HEARTBEAT_SECONDS = 0.01


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


def _counter_file() -> bytes:
    start = datetime(2000, 1, 1, tzinfo=UTC)
    hour = timedelta(hours=1)
    lines = ["timestamp,asset,cumulative_wh"]
    lines += [f"{(start + index * hour).isoformat()},Meter,{index}" for index in range(ROWS)]
    content = ("\n".join(lines) + "\n").encode()
    assert len(content) <= MAX_BYTES
    return content


def _many_streams_file() -> bytes:
    start = datetime(2000, 1, 1, tzinfo=UTC)
    hour = timedelta(hours=1)
    lines = ["interval_start,interval_end,asset,energy_wh"]
    for stream in range(STREAMS):
        for index in range(ROWS // STREAMS):
            begin = start + index * hour
            lines.append(f"{begin.isoformat()},{(begin + hour).isoformat()},P{stream},1.5")
    content = ("\n".join(lines) + "\n").encode()
    assert len(content) <= MAX_BYTES
    return content


class _Stalls:
    """Measures the largest gap in a task meant to wake every 10 ms, which is how long the event loop was blocked."""

    def __init__(self) -> None:
        """Start with no gap."""
        self.largest = 0.0
        self.task: asyncio.Task | None = None

    async def _beat(self) -> None:
        last = time.perf_counter()
        while True:
            await asyncio.sleep(HEARTBEAT_SECONDS)
            now = time.perf_counter()
            self.largest = max(self.largest, now - last - HEARTBEAT_SECONDS)
            last = now

    async def __aenter__(self) -> "_Stalls":
        """Start the heartbeat.

        Returns:
            _Stalls: This measure.
        """
        self.task = asyncio.create_task(self._beat())
        return self

    async def __aexit__(self, *_: object) -> None:
        """Stop the heartbeat."""
        assert self.task is not None
        self.task.cancel()


async def _store_preview(
    client: AsyncClient, headers: dict[str, str], site: UUID, content: bytes
) -> tuple[str, float, float]:
    files = {"file": ("besar.csv", content, "text/csv"), "mapping": (None, json.dumps({"scope": "disjoint"}))}
    async with _Stalls() as stalls:
        started = time.perf_counter()
        response = await client.post(f"/api/v1/sites/{site}/imports/preview", files=files, headers=headers)
        took = time.perf_counter() - started
    assert response.status_code == 201, response.text
    body = response.json()
    assert (body["accepted_rows"], body["blocked"]) == (ROWS, False), body["block_reasons"]
    return body["id"], took, stalls.largest


async def _commit(client: AsyncClient, headers: dict[str, str], import_id: str) -> tuple[float, float]:
    keyed = headers | {"Idempotency-Key": secrets.token_urlsafe(16)}
    async with _Stalls() as stalls:
        started = time.perf_counter()
        response = await client.post(
            f"/api/v1/imports/{import_id}/commit", json={"acknowledge_skipped": False}, headers=keyed, timeout=None
        )
        took = time.perf_counter() - started
    assert response.status_code == 200, response.text
    assert response.json()["rows_added"] == ROWS
    return took, stalls.largest


async def _stored_rows(site: UUID) -> int:
    rows = await execute(
        "SELECT count(*) FROM measurements m JOIN sources s ON s.id = m.source_id"
        " WHERE s.site_id = :site AND m.kind <> 'counter_delta'",
        site=site,
    )
    return rows[0][0]


COMMIT_FILES = [(_large_file, "interval"), (_counter_file, "counter"), (_many_streams_file, "100 streams")]


@pytest.mark.parametrize(("build", "label"), COMMIT_FILES, ids=["interval", "counter", "streams"])
async def test_large_commit_runs_through_the_route(
    client: AsyncClient, acting: Callable[[UUID], dict[str, str]], build: Callable[[], bytes], label: str
) -> None:
    """
    Condition:
    - A file of 150,000 rows within 10 MiB, previewed and committed through the real routes on a fresh site.

    Expected:
    - 200, and every row stored. Seconds and the largest event-loop stall are printed, with no time assertion, because
      PRD §18's target belongs to 041's benchmark server.
    """
    content = build()
    principal = await make_principal()
    headers, site = acting(principal), await make_site(principal)

    import_id, preview_took, preview_stall = await _store_preview(client, headers, site, content)
    commit_took, commit_stall = await _commit(client, headers, import_id)

    assert await _stored_rows(site) == ROWS
    await execute("DELETE FROM sites WHERE id = :site", site=site)
    print(
        f"\nimport commit, {label}: {ROWS} rows, {len(content)} bytes, preview {preview_took:.2f} s"
        f" (stall {preview_stall:.2f} s), commit {commit_took:.2f} s (stall {commit_stall:.2f} s),"
        f" together {preview_took + commit_took:.2f} s"
    )


@pytest.mark.parametrize(("build", "label"), COMMIT_FILES, ids=["interval", "counter", "streams"])
async def test_large_commit_memory(
    client: AsyncClient, acting: Callable[[UUID], dict[str, str]], build: Callable[[], bytes], label: str
) -> None:
    """
    Condition:
    - The same files, with allocations traced only during the commit request, once the preview has returned.

    Expected:
    - Interval rows stay under 256 MiB. The peak of the other two is printed with no bound: a counter's one ``ingest``
      holds the whole file, by D10.
    """
    content = build()
    principal = await make_principal()
    headers, site = acting(principal), await make_site(principal)
    import_id, _, _ = await _store_preview(client, headers, site, content)
    del content

    tracemalloc.start()
    try:
        await _commit(client, headers, import_id)
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()

    assert await _stored_rows(site) == ROWS
    await execute("DELETE FROM sites WHERE id = :site", site=site)
    peak_mib = peak / (1024 * 1024)
    print(f"\nimport commit under tracemalloc, {label}: peak {peak_mib:.1f} MiB")
    if label == "interval":
        assert peak_mib < MAX_PEAK_MIB
