"""SC-002: a full-size file reads inside the target, one row at a time."""

import io
import time
import tracemalloc
from datetime import datetime, timedelta

import pytest

from app.imports.model.models import MeaningAnswers, RowStatus
from app.imports.service.parser import iter_rows, parse

ROWS = 150_000
MAX_BYTES = 10 * 1024 * 1024
TARGET_SECONDS = 60
MIB = 1024 * 1024


@pytest.fixture(scope="module")
def explicit_offsets() -> bytes:
    """Build the largest explicit-interval file: 150,000 rows of offset times.

    Returns:
        bytes: The file.
    """
    rows = (
        f"2026-01-01T00:00:00+07:00,2026-01-01T01:00:00+07:00,Mesin {index % 40},123.456\n" for index in range(ROWS)
    )
    return ("interval_start,interval_end,asset,energy_wh\n" + "".join(rows)).encode()


def test_explicit_shape_reads_inside_the_target(explicit_offsets: bytes) -> None:
    """
    Condition:
    - 150,000 explicit-offset rows within 10 MiB.

    Expected:
    - ``parse`` plus a full read finishes in under 60 seconds with every row valid.
    """
    assert len(explicit_offsets) <= MAX_BYTES
    source = io.BytesIO(explicit_offsets)
    started = time.perf_counter()
    parsed = parse(source, site_timezone="Asia/Jakarta")
    statuses = {RowStatus.PARSED: 0, RowStatus.INVALID: 0, RowStatus.PENDING: 0}
    for row in iter_rows(source, parsed):
        statuses[row.status] += 1
    elapsed = time.perf_counter() - started
    print(f"\nshape=explicit rows={parsed.total_rows} bytes={len(explicit_offsets)} seconds={elapsed:.2f}")
    assert parsed.total_rows == ROWS
    assert statuses == {RowStatus.PARSED: ROWS, RowStatus.INVALID: 0, RowStatus.PENDING: 0}
    assert elapsed < TARGET_SECONDS


def test_first_row_arrives_after_reading_only_the_start(explicit_offsets: bytes) -> None:
    """
    Condition:
    - One row taken from a full-size file.

    Expected:
    - Under 1 MiB of the source has been read: rows are not built ahead of the caller.
    """
    source = io.BytesIO(explicit_offsets)
    parsed = parse(source, site_timezone="Asia/Jakarta")
    rows = iter_rows(source, parsed)
    next(rows)
    position = source.tell()
    rows.close()
    print(f"\nshape=explicit position_after_first_row={position}")
    assert position < MIB


def test_peak_memory_stays_far_below_a_list_of_rows(explicit_offsets: bytes) -> None:
    """
    Condition:
    - A full-size file under ``tracemalloc``, with rows discarded as they are read.

    Expected:
    - Peak is under 64 MiB for ``parse`` and under 16 MiB for ``iter_rows``. A list of rows would peak near 249 MiB.
    """
    source = io.BytesIO(explicit_offsets)
    tracemalloc.start()
    try:
        parsed = parse(source, site_timezone="Asia/Jakarta")
        _, parse_peak = tracemalloc.get_traced_memory()
        tracemalloc.reset_peak()
        for _ in iter_rows(source, parsed):
            pass
        _, rows_peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    print(f"\nshape=explicit parse_peak_mib={parse_peak / MIB:.2f} rows_peak_mib={rows_peak / MIB:.2f}")
    assert parse_peak < 64 * MIB
    assert rows_peak < 16 * MIB


STREAMS = 40
CONFIRMED = MeaningAnswers(timezone_confirmed=True)


@pytest.fixture(scope="module")
def timestamp_only_streams() -> bytes:
    """Build 150,000 naive timestamp-only rows over 40 hourly streams.

    Returns:
        bytes: The file.
    """
    start = datetime(2026, 1, 1)
    rows = (
        f"{start + timedelta(hours=index // STREAMS):%Y-%m-%d %H:%M},Mesin {index % STREAMS},123.456\n"
        for index in range(ROWS)
    )
    return ("timestamp,asset,energy_wh\n" + "".join(rows)).encode()


def test_timestamp_only_shape_reads_inside_the_target(timestamp_only_streams: bytes) -> None:
    """
    Condition:
    - 150,000 confirmed naive rows over 40 streams, the shape that also needs cadence and zone resolution.

    Expected:
    - ``parse`` plus a full read finishes in under 60 seconds, with one cadence per stream and every row valid.
    """
    assert len(timestamp_only_streams) <= MAX_BYTES
    source = io.BytesIO(timestamp_only_streams)
    started = time.perf_counter()
    parsed = parse(source, site_timezone="Asia/Jakarta", answers=CONFIRMED)
    statuses = {RowStatus.PARSED: 0, RowStatus.INVALID: 0, RowStatus.PENDING: 0}
    for row in iter_rows(source, parsed):
        statuses[row.status] += 1
    elapsed = time.perf_counter() - started
    print(f"\nshape=timestamp_only rows={parsed.total_rows} bytes={len(timestamp_only_streams)} seconds={elapsed:.2f}")
    assert parsed.questions == []
    assert set(parsed.cadences.values()) == {timedelta(hours=1)}
    assert len(parsed.cadences) == STREAMS
    assert statuses == {RowStatus.PARSED: ROWS, RowStatus.INVALID: 0, RowStatus.PENDING: 0}
    assert elapsed < TARGET_SECONDS


def test_timestamp_only_peak_memory_holds_only_the_timestamps(timestamp_only_streams: bytes) -> None:
    """
    Condition:
    - The same file under ``tracemalloc``, where the first pass keeps per-stream timestamps.

    Expected:
    - Peak stays under the same limits: 64 MiB for ``parse`` and 16 MiB for ``iter_rows``.
    """
    source = io.BytesIO(timestamp_only_streams)
    tracemalloc.start()
    try:
        parsed = parse(source, site_timezone="Asia/Jakarta", answers=CONFIRMED)
        _, parse_peak = tracemalloc.get_traced_memory()
        tracemalloc.reset_peak()
        for _ in iter_rows(source, parsed):
            pass
        _, rows_peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    print(f"\nshape=timestamp_only parse_peak_mib={parse_peak / MIB:.2f} rows_peak_mib={rows_peak / MIB:.2f}")
    assert parse_peak < 64 * MIB
    assert rows_peak < 16 * MIB
