"""Import commit through the real application over real Postgres."""

import asyncio
import json
import logging
import secrets
import time
from collections.abc import AsyncIterator, Callable, Iterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

import pytest
from httpx import AsyncClient, Response
from sqlalchemy import text

from app.assets.model.models import MeasurementKind, ScopeKind, SourceModel, SourceOrigin, TransportStatus
from app.assets.repository.sqlalchemy.repository import SqlAlchemyAssetRepository
from app.assets.service.service import AssetService
from app.audit.dependencies import build_audit_service
from app.audit.service.service import AuditService
from app.core.database import get_session_factory
from app.core.errors.public import FALLBACK_PUBLIC_ERROR
from app.imports.repository.sqlalchemy.repository import SqlAlchemyImportRepository
from app.imports.service.mapping import source_label
from app.measurements.dependencies import build_ingest_service
from app.measurements.model.models import IngestResult, ReadingInput
from app.measurements.service.service import IngestService
from app.sites.repository.sqlalchemy.repository import SqlAlchemySiteRepository
from app.sites.service.service import SiteService
from tests.integration.conftest import (
    TEST_PRINCIPAL_HEADER,
    execute,
    make_asset,
    make_binding,
    make_principal,
    make_site,
    make_source,
    start_demo,
)

pytestmark = pytest.mark.integration

FAKE_SECRET = "Bearer RAHASIA-PALSU-123"
FAKE_KEY = "RAHASIA-PALSU-123-kunci-rahasia"
SCOPE = {"scope": "disjoint"}
OVERLAP = {"scope": "unknown_overlap"}
ANSWERED = {"scope": "disjoint", "timezone_confirmed": True}
INTERVAL_HEADER = "interval_start,interval_end,asset,energy_wh"
COUNTER_HEADER = "timestamp,asset,cumulative_wh"
TWO_ASSETS_CSV = (
    f"{INTERVAL_HEADER}\n"
    "2026-10-20T00:00:00+07:00,2026-10-20T01:00:00+07:00,Router,10\n"
    "2026-10-20T01:00:00+07:00,2026-10-20T02:00:00+07:00,Router,12\n"
    "2026-10-20T00:00:00+07:00,2026-10-20T01:00:00+07:00,Kulkas,50\n"
    "2026-10-20T01:00:00+07:00,2026-10-20T02:00:00+07:00,Kulkas,50\n"
)
TABLES = {
    "measurements": "SELECT count(*) FROM measurements m JOIN sources s ON s.id = m.source_id WHERE s.site_id = :site",
    "sources": "SELECT count(*) FROM sources WHERE site_id = :site",
    "assets": "SELECT count(*) FROM assets WHERE site_id = :site",
    "bindings": "SELECT count(*) FROM bindings WHERE site_id = :site",
    "asset_relations": "SELECT count(*) FROM asset_relations WHERE site_id = :site",
    "audit_events": "SELECT count(*) FROM audit_events WHERE site_id = :site",
}
BLOCKED_MESSAGE = "Impor ini masih diblokir. Selesaikan alasan pada pratinjau lalu coba lagi."
STALE_MESSAGE = "Pratinjau ini sudah tidak berlaku. Buat pratinjau baru lalu coba lagi."
ACK_MESSAGE = "Ada baris yang akan dilewati dan belum disetujui. Setujui baris yang dilewati lalu coba lagi."
KEY_MESSAGE = "Permintaan ini sudah dipakai untuk impor lain. Konfirmasi impornya lagi untuk mengirim permintaan baru."
RACE_TIMEOUT = 30


def csv10(bad: int = 0) -> str:
    """Build AT-30's file: ten hourly Router rows.

    Args:
        bad (int, optional): How many leading rows are negative. Defaults to 0.

    Returns:
        str: The file text. Its times are naive, so its mapping needs ``timezone_confirmed``.
    """
    lines = [f"2026-10-20 {hour:02}:00,Router,{'-1' if hour < bad else '10'}" for hour in range(10)]
    return "timestamp,perangkat,energi_wh\n" + "\n".join(lines) + "\n"


def _interval(day: int, hour: int, name: str = "Router", wh: str = "10") -> str:
    begin = datetime(2026, 10, day, hour, tzinfo=UTC) - timedelta(hours=7)
    end = begin + timedelta(hours=1)
    return f"{begin.isoformat()},{end.isoformat()},{name},{wh}"


def _intervals(*rows: str) -> str:
    return INTERVAL_HEADER + "\n" + "\n".join(rows) + "\n"


def _point(day: int, hour: int, wh: int, name: str = "Meter") -> str:
    return f"2026-10-{day:02}T{hour:02}:00:00+07:00,{name},{wh}"


def _counters(*rows: str) -> str:
    return COUNTER_HEADER + "\n" + "\n".join(rows) + "\n"


@pytest.fixture(autouse=True)
def capture_app_logs(caplog: pytest.LogCaptureFixture) -> Iterator[None]:
    """Capture the application logger, which does not propagate once configured."""
    logger = logging.getLogger("app")
    logger.addHandler(caplog.handler)
    logger.setLevel(logging.INFO)
    yield
    logger.removeHandler(caplog.handler)


@pytest.fixture
async def owner(acting: Callable[[UUID], dict[str, str]]) -> tuple[UUID, dict[str, str]]:
    """A principal and a demo-kind site, acted as through the test principal header.

    Returns:
        tuple[UUID, dict[str, str]]: The site and the request headers.
    """
    principal = await make_principal()
    return await make_site(principal), acting(principal)


def _records(caplog: pytest.LogCaptureFixture) -> list[dict]:
    prefix = "Application failure "
    return [json.loads(r.getMessage().removeprefix(prefix)) for r in caplog.records if prefix in r.getMessage()]


def _assert_failure(
    response: Response,
    caplog: pytest.LogCaptureFixture,
    *,
    expected_status: int,
    code: str,
    message: str,
    internal: str,
) -> dict:
    body = response.json()
    assert response.status_code == expected_status, body
    error = body["error"]
    assert error["code"] == code
    assert error["message"] == message
    assert error["recovery"] == {"retryable": False}
    records = _records(caplog)
    assert len(records) == 1
    assert records[0]["reference_id"] == error["request_id"]
    assert records[0]["code"] == internal
    assert "RAHASIA-PALSU-123" not in response.text
    assert "RAHASIA-PALSU-123" not in caplog.text
    return error


def _key() -> str:
    return secrets.token_urlsafe(16)


async def _preview(client: AsyncClient, site: UUID | str, headers: dict[str, str], text: str, mapping: dict) -> dict:
    files = {"mapping": (None, json.dumps(mapping)), "file": ("data.csv", text.encode(), "text/csv")}
    response = await client.post(f"/api/v1/sites/{site}/imports/preview", files=files, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


async def _commit(
    client: AsyncClient,
    import_id: str,
    headers: dict[str, str],
    *,
    key: str | None = None,
    acknowledge: bool = False,
) -> Response:
    return await client.post(
        f"/api/v1/imports/{import_id}/commit",
        json={"acknowledge_skipped": acknowledge},
        headers=headers | {"Idempotency-Key": key or _key()},
    )


async def _preview_and_commit(
    client: AsyncClient,
    site: UUID | str,
    headers: dict[str, str],
    text: str,
    mapping: dict,
    *,
    acknowledge: bool = False,
) -> dict:
    preview = await _preview(client, site, headers, text, mapping)
    assert preview["blocked"] is False, preview["block_reasons"]
    response = await _commit(client, preview["id"], headers, acknowledge=acknowledge)
    assert response.status_code == 200, response.text
    return response.json()


async def _table_counts(site: UUID) -> dict[str, int]:
    return {name: (await execute(sql, site=site))[0][0] for name, sql in TABLES.items()}


async def _revisions(site: UUID) -> tuple:
    return tuple(
        (await execute("SELECT measurement_revision, binding_revision FROM sites WHERE id = :site", site=site))[0]
    )


async def _summary(client: AsyncClient, site: UUID | str, headers: dict[str, str], day: str = "2026-10-20") -> dict:
    response = await client.get(
        f"/api/v1/sites/{site}/summary", params={"start_date": day, "end_date": day}, headers=headers
    )
    assert response.status_code == 200, response.text
    return response.json()


async def _bindings(site: UUID, name: str = "Router") -> list[tuple]:
    rows = await execute(
        "SELECT b.effective_from, b.effective_to, b.authoritative FROM bindings b"
        " JOIN assets a ON a.id = b.asset_id WHERE a.site_id = :site AND a.name = :name"
        " ORDER BY b.effective_from",
        site=site,
        name=name,
    )
    return [tuple(row) for row in rows]


async def _asset_id(site: UUID, name: str) -> UUID:
    return (await execute("SELECT id FROM assets WHERE site_id = :site AND name = :name", site=site, name=name))[0][0]


async def _relations(site: UUID) -> list[str]:
    rows = await execute("SELECT kind FROM asset_relations WHERE site_id = :site", site=site)
    return sorted(row[0] for row in rows)


def _utc(day: int, hour: int) -> datetime:
    """Name a WIB hour as a UTC instant."""
    return datetime(2026, 10, day, hour, tzinfo=UTC) - timedelta(hours=7)


# --- atomic ------------------------------------------------------------------------------------------------------


async def test_atomic_commit_writes_everything_together(client: AsyncClient, owner: tuple[UUID, dict]) -> None:
    """
    Condition:
    - A valid preview of two new assets, with ``scope`` answered ``disjoint``.

    Expected:
    - FR-001: readings, device assets, historical import sources with unknown resolution and the fixed label, one open
      authoritative binding each from the earliest row, one ``disjoint`` relation, and both revisions advanced. The
      next summary adds the two assets up.
    """
    site, headers = owner
    before = await _revisions(site)

    body = await _preview_and_commit(client, site, headers, TWO_ASSETS_CSV, SCOPE)

    assert (body["status"], body["rows_added"], body["replayed"]) == ("committed", 4, False)
    counts = await _table_counts(site)
    assert (counts["assets"], counts["sources"], counts["bindings"], counts["asset_relations"]) == (2, 2, 2, 1)
    assert counts["measurements"] == 4
    assert counts["audit_events"] == 1
    assets = await execute("SELECT name, scope_kind FROM assets WHERE site_id = :site ORDER BY name", site=site)
    assert [tuple(row) for row in assets] == [("Kulkas", "device"), ("Router", "device")]
    sources = await execute(
        "SELECT label, origin, transport_status, resolution_mwh, cadence_seconds, measurement_kind FROM sources"
        " WHERE site_id = :site ORDER BY label",
        site=site,
    )
    assert [tuple(row) for row in sources] == [
        (source_label("kulkas"), "import", "historical", None, None, "interval_energy"),
        (source_label("router"), "import", "historical", None, None, "interval_energy"),
    ]
    assert await _bindings(site, "Router") == [(_utc(20, 0), None, True)]
    assert await _bindings(site, "Kulkas") == [(_utc(20, 0), None, True)]
    assert await _relations(site) == ["disjoint"]
    after = await _revisions(site)
    assert after[0] > before[0] and after[1] > before[1]
    summary = await _summary(client, site, headers)
    assert summary["energy_kwh"] == "0.122"
    assert summary["scope"]["valid"] is True
    assert summary["origins"] == ["import"]


async def test_atomic_readings_store_canonical_values_and_provenance(
    client: AsyncClient, owner: tuple[UUID, dict]
) -> None:
    """
    Condition:
    - A committed file.

    Expected:
    - ``raw_value`` is canonical, so a reimport repeats it, and ``provenance`` holds D20's keys.
    """
    site, headers = owner

    preview = await _preview(client, site, headers, TWO_ASSETS_CSV, SCOPE)
    response = await _commit(client, preview["id"], headers)

    assert response.status_code == 200, response.text
    rows = await execute(
        "SELECT m.raw_value, m.provenance FROM measurements m JOIN sources s ON s.id = m.source_id"
        " WHERE s.site_id = :site ORDER BY m.raw_value",
        site=site,
    )
    assert rows[0][0] == "10.000"
    assert rows[0][1] == {
        "import_id": preview["id"],
        "file_name": "data.csv",
        "timezone": "Asia/Jakarta",
        "timezone_confirmed": False,
        "interval_basis": "explicit",
    }


async def test_atomic_timestamp_file_stores_its_cadence(client: AsyncClient, owner: tuple[UUID, dict]) -> None:
    """
    Condition:
    - A timestamp-only file with offsets, whose cadence the parser infers.

    Expected:
    - The new source declares 3600 seconds.
    """
    site, headers = owner
    text = "timestamp,asset,energy_wh\n" + "".join(f"2026-10-20T{hour:02}:00:00+07:00,Router,10\n" for hour in range(4))

    await _preview_and_commit(client, site, headers, text, SCOPE)

    rows = await execute("SELECT cadence_seconds FROM sources WHERE site_id = :site", site=site)
    assert rows[0][0] == 3600


async def test_atomic_unknown_overlap_refuses_the_total(client: AsyncClient, owner: tuple[UUID, dict]) -> None:
    """
    Condition:
    - Two new assets, with ``scope`` answered ``unknown_overlap``.

    Expected:
    - One ``unknown_overlap`` relation, and the summary refuses the total while each asset keeps its value.
    """
    site, headers = owner

    await _preview_and_commit(client, site, headers, TWO_ASSETS_CSV, OVERLAP)

    assert await _relations(site) == ["unknown_overlap"]
    summary = await _summary(client, site, headers)
    assert (summary["energy_kwh"], summary["energy_unavailable_reason"]) == (None, "scope_conflict")
    assert {row["name"]: row["energy_kwh"] for row in summary["assets"]} == {"Kulkas": "0.100", "Router": "0.022"}


async def test_atomic_one_asset_writes_no_relation(client: AsyncClient, owner: tuple[UUID, dict]) -> None:
    """
    Condition:
    - A file with one asset.

    Expected:
    - No relation, and a valid total.
    """
    site, headers = owner

    await _preview_and_commit(client, site, headers, _intervals(_interval(20, 0)), SCOPE)

    assert await _relations(site) == []
    assert (await _summary(client, site, headers))["energy_kwh"] == "0.010"


async def test_atomic_stream_of_only_invalid_rows_creates_nothing(
    client: AsyncClient, owner: tuple[UUID, dict]
) -> None:
    """
    Condition:
    - Five valid Router rows, and one Kulkas row that is invalid, acknowledged (D11).

    Expected:
    - No asset, source or binding for Kulkas, and no relation.
    """
    site, headers = owner
    text = _intervals(*[_interval(20, hour) for hour in range(5)], _interval(20, 0, "Kulkas", "-1"))

    body = await _preview_and_commit(client, site, headers, text, SCOPE, acknowledge=True)

    assert (body["rows_added"], body["rows_skipped"]) == (5, 1)
    names = await execute("SELECT name FROM assets WHERE site_id = :site", site=site)
    assert [row[0] for row in names] == ["Router"]
    assert (await _table_counts(site))["sources"] == 1
    assert (await _table_counts(site))["bindings"] == 1
    assert await _relations(site) == []


async def test_atomic_long_name_commits_and_reimports(client: AsyncClient, owner: tuple[UUID, dict]) -> None:
    """
    Condition:
    - A 60-character name that lengthens when lower-cased, committed and then previewed again (D16).

    Expected:
    - The label fits ``sources``, and the reimport finds its source, so every row is a duplicate.
    """
    site, headers = owner
    text = _intervals(_interval(20, 0, "İ" * 60))

    await _preview_and_commit(client, site, headers, text, SCOPE)

    labels = await execute("SELECT label FROM sources WHERE site_id = :site", site=site)
    assert len(labels[0][0]) <= 120
    again = await _preview(client, site, headers, text, SCOPE)
    assert (again["accepted_rows"], again["duplicate_rows"], again["blocked"]) == (0, 1, False)


def _fail_second_ingest(monkeypatch: pytest.MonkeyPatch) -> None:
    real = IngestService.ingest
    calls = {"count": 0}

    async def failing(self: IngestService, *args: Any, **kwargs: Any) -> IngestResult:
        calls["count"] += 1
        if calls["count"] == 2:
            raise RuntimeError(f"gagal dengan {FAKE_SECRET}")
        return await real(self, *args, **kwargs)

    monkeypatch.setattr(IngestService, "ingest", failing)


def _fail_audit(monkeypatch: pytest.MonkeyPatch) -> None:
    async def failing(self: AuditService, **kwargs: Any) -> None:
        raise RuntimeError(f"gagal dengan {FAKE_SECRET}")

    monkeypatch.setattr(AuditService, "record", failing)


def _revise_on_ingest(monkeypatch: pytest.MonkeyPatch) -> None:
    async def revising(self: IngestService, *args: Any, **kwargs: Any) -> IngestResult:
        return IngestResult(revised=1)

    monkeypatch.setattr(IngestService, "ingest", revising)


def _store_nothing_on_ingest(monkeypatch: pytest.MonkeyPatch) -> None:
    async def storing_nothing(self: IngestService, *args: Any, **kwargs: Any) -> IngestResult:
        return IngestResult()

    monkeypatch.setattr(IngestService, "ingest", storing_nothing)


def _refuse_the_status_change(monkeypatch: pytest.MonkeyPatch) -> None:
    async def refusing(self: SqlAlchemyImportRepository, *args: Any, **kwargs: Any) -> bool:
        return False

    monkeypatch.setattr(SqlAlchemyImportRepository, "mark_committed", refusing)


@pytest.mark.parametrize(
    "inject",
    [_fail_second_ingest, _fail_audit, _revise_on_ingest, _store_nothing_on_ingest, _refuse_the_status_change],
    ids=[
        "ingest_on_the_second_stream",
        "audit",
        "ingest_disagrees_with_the_preview",
        "ingest_stores_too_few",
        "no_longer_a_preview",
    ],
)
async def test_atomic_failure_leaves_nothing_and_the_preview_usable(
    client: AsyncClient,
    owner: tuple[UUID, dict],
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
    inject: Callable[[pytest.MonkeyPatch], None],
) -> None:
    """
    Condition:
    - A failure inside the commit's transaction, on a file naming a fake bearer token, under a key holding a fake value.

    Expected:
    - 500 ``INTERNAL_ERROR`` with one record, no table or revision changed, the preview still ``previewed`` with no key,
      and neither fake value anywhere. With the failure gone, the same key succeeds and the rows are there once.
    """
    site, headers = owner
    text = TWO_ASSETS_CSV.replace("Kulkas", FAKE_SECRET)
    preview = await _preview(client, site, headers, text, SCOPE)
    before = await _table_counts(site), await _revisions(site)

    with monkeypatch.context() as patch:
        inject(patch)
        response = await _commit(client, preview["id"], headers, key=FAKE_KEY)

    _assert_failure(
        response,
        caplog,
        expected_status=500,
        code="INTERNAL_ERROR",
        message=FALLBACK_PUBLIC_ERROR.message,
        internal="APP-UNKNOWN",
    )
    assert FAKE_KEY not in response.text
    assert FAKE_KEY not in caplog.text
    assert (await _table_counts(site), await _revisions(site)) == before
    stored = await execute(
        "SELECT status, idempotency_key, commit_result FROM imports WHERE id = :id", id=preview["id"]
    )
    assert tuple(stored[0]) == ("previewed", None, None)
    read = await client.get(f"/api/v1/imports/{preview['id']}", headers=headers)
    assert read.status_code == 200
    assert read.json()["status"] == "previewed"

    retry = await _commit(client, preview["id"], headers, key=FAKE_KEY)

    assert retry.status_code == 200, retry.text
    assert (retry.json()["rows_added"], retry.json()["replayed"]) == (4, False)
    assert (await _table_counts(site))["measurements"] == 4


async def test_atomic_row_outside_its_mapping_rolls_back(
    client: AsyncClient, owner: tuple[UUID, dict], caplog: pytest.LogCaptureFixture
) -> None:
    """
    Condition:
    - A staged row names a stream the stored mapping no longer holds, which only a bug could cause (D22).

    Expected:
    - 500 ``INTERNAL_ERROR`` with one record, and nothing written.
    """
    site, headers = owner
    preview = await _preview(client, site, headers, _intervals(_interval(20, 0)), SCOPE)
    await execute("UPDATE imports SET mapping = jsonb_set(mapping, '{streams}', '[]') WHERE id = :id", id=preview["id"])
    before = await _table_counts(site), await _revisions(site)

    response = await _commit(client, preview["id"], headers)

    _assert_failure(
        response,
        caplog,
        expected_status=500,
        code="INTERNAL_ERROR",
        message=FALLBACK_PUBLIC_ERROR.message,
        internal="APP-UNKNOWN",
    )
    assert (await _table_counts(site), await _revisions(site)) == before


def _count_ingests(monkeypatch: pytest.MonkeyPatch) -> list[int]:
    real = IngestService.ingest
    sizes: list[int] = []

    async def counting(self: IngestService, site: Any, source: Any, readings: list, **kwargs: Any) -> IngestResult:
        sizes.append(len(readings))
        return await real(self, site, source, readings, **kwargs)

    monkeypatch.setattr(IngestService, "ingest", counting)
    return sizes


def _many_intervals(rows: int) -> str:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    hour = timedelta(hours=1)
    lines = [f"{(start + i * hour).isoformat()},{(start + (i + 1) * hour).isoformat()},Router,1" for i in range(rows)]
    return _intervals(*lines)


@pytest.mark.parametrize(
    ("rows", "sizes"),
    [(5_000, [5_000]), (5_001, [5_000, 1])],
    ids=["exactly_one_batch", "one_row_over"],
)
async def test_atomic_interval_rows_reach_ingest_in_batches(
    client: AsyncClient, owner: tuple[UUID, dict], monkeypatch: pytest.MonkeyPatch, rows: int, sizes: list[int]
) -> None:
    """
    Condition:
    - A stream of interval rows at and just over one batch (D10).

    Expected:
    - One ``ingest`` per 5,000 rows, with no empty call, and every row stored.
    """
    site, headers = owner
    preview = await _preview(client, site, headers, _many_intervals(rows), SCOPE)
    calls = _count_ingests(monkeypatch)

    response = await _commit(client, preview["id"], headers)

    assert response.status_code == 200, response.text
    assert response.json()["rows_added"] == rows
    assert calls == sizes
    assert (await _table_counts(site))["measurements"] == rows


async def test_atomic_counter_rows_reach_ingest_at_once(
    client: AsyncClient, owner: tuple[UUID, dict], monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    Condition:
    - A counter stream over one batch. ``_rederive_counter`` rereads all of a source's deltas per call (D10).

    Expected:
    - One ``ingest`` holding every point, with a delta between each pair.
    """
    site, headers = owner
    start = datetime(2026, 1, 1, tzinfo=UTC)
    lines = [f"{(start + index * timedelta(hours=1)).isoformat()},Meter,{index}" for index in range(5_001)]
    preview = await _preview(client, site, headers, _counters(*lines), SCOPE)
    calls = _count_ingests(monkeypatch)

    response = await _commit(client, preview["id"], headers)

    assert response.status_code == 200, response.text
    assert calls == [5_001]
    assert (await _table_counts(site))["measurements"] == 5_001 + 5_000


# --- atomic: bindings --------------------------------------------------------------------------------------------


async def test_atomic_earlier_rows_get_a_binding_ending_at_the_stored_one(
    client: AsyncClient, owner: tuple[UUID, dict]
) -> None:
    """
    Condition:
    - A file for 20 October, then a file for 19 October on the same asset.

    Expected:
    - A second binding ``[first earlier row, first stored row)``, and the summary of the 19th holds the earlier energy,
      which proves the rows count.
    """
    site, headers = owner
    await _preview_and_commit(client, site, headers, _intervals(_interval(20, 0)), SCOPE)

    await _preview_and_commit(client, site, headers, _intervals(_interval(19, 3, wh="25")), SCOPE)

    assert await _bindings(site) == [(_utc(19, 3), _utc(20, 0), True), (_utc(20, 0), None, True)]
    assert (await _summary(client, site, headers, "2026-10-19"))["energy_kwh"] == "0.025"
    assert (await _table_counts(site))["sources"] == 1


async def test_atomic_range_ends_at_a_later_binding(client: AsyncClient, owner: tuple[UUID, dict]) -> None:
    """
    Condition:
    - An asset with another source bound from 25 October, and a file for 20 October mapped to it by ID.

    Expected:
    - The new binding ends where the later one starts, which is unchanged, and the rows count.
    """
    site, headers = owner
    asset = await make_asset(site, "Router")
    later = await make_source(site, "Meter baru")
    start = "2026-10-25T00:00:00+00:00"
    await make_binding(site, asset, later, start)
    mapping = SCOPE | {"asset_map": {"Router": str(asset)}}

    await _preview_and_commit(client, site, headers, _intervals(_interval(20, 0)), mapping)

    later_start = datetime.fromisoformat(start)
    assert await _bindings(site) == [(_utc(20, 0), later_start, True), (later_start, None, True)]
    assert (await _summary(client, site, headers))["energy_kwh"] == "0.010"


async def test_atomic_rows_beyond_a_closed_binding_open_a_new_one(
    client: AsyncClient, owner: tuple[UUID, dict]
) -> None:
    """
    Condition:
    - A committed file whose binding the user ended, then a file with rows beyond that end.

    Expected:
    - A new open binding starts at the first of them, and the rows count.
    """
    site, headers = owner
    await _preview_and_commit(client, site, headers, _intervals(_interval(19, 0)), SCOPE)
    await execute("UPDATE bindings SET effective_to = :end WHERE site_id = :site", site=site, end=_utc(19, 1))

    await _preview_and_commit(client, site, headers, _intervals(_interval(20, 5, wh="30")), SCOPE)

    assert await _bindings(site) == [(_utc(19, 0), _utc(19, 1), True), (_utc(20, 5), None, True)]
    assert (await _summary(client, site, headers))["energy_kwh"] == "0.030"


async def test_atomic_append_inside_an_open_binding_adds_none(client: AsyncClient, owner: tuple[UUID, dict]) -> None:
    """
    Condition:
    - A committed file, then later rows that its open binding already covers.

    Expected:
    - No new binding, and ``binding_revision`` stays, while ``measurement_revision`` moves.
    """
    site, headers = owner
    await _preview_and_commit(client, site, headers, _intervals(_interval(20, 0)), SCOPE)
    before = await _revisions(site)

    await _preview_and_commit(client, site, headers, _intervals(_interval(20, 1, wh="20")), SCOPE)

    after = await _revisions(site)
    assert after[1] == before[1]
    assert after[0] > before[0]
    assert await _bindings(site) == [(_utc(20, 0), None, True)]
    assert (await _summary(client, site, headers))["energy_kwh"] == "0.030"


async def test_atomic_earlier_counter_points_bind_up_to_the_stored_stream(
    client: AsyncClient, owner: tuple[UUID, dict]
) -> None:
    """
    Condition:
    - A stored counter stream, then a file of earlier points on it.

    Expected:
    - A binding ``[first earlier point, first stored point)``, and the delta into the stored stream counts.
    """
    site, headers = owner
    await _preview_and_commit(client, site, headers, _counters(_point(20, 3, 130), _point(20, 4, 140)), SCOPE)

    await _preview_and_commit(client, site, headers, _counters(_point(20, 1, 100), _point(20, 2, 120)), SCOPE)

    assert await _bindings(site, "Meter") == [(_utc(20, 1), _utc(20, 3), True), (_utc(20, 3), None, True)]
    assert (await _summary(client, site, headers))["energy_kwh"] == "0.040"


# --- atomic: scope -------------------------------------------------------------------------------------------------


async def test_atomic_scope_relates_an_existing_and_a_new_asset(client: AsyncClient, owner: tuple[UUID, dict]) -> None:
    """
    Condition:
    - A file mapping one existing asset and one new one.

    Expected:
    - One relation between them, and a valid total.
    """
    site, headers = owner
    await make_asset(site, "Router")

    await _preview_and_commit(client, site, headers, TWO_ASSETS_CSV, SCOPE)

    assert await _relations(site) == ["disjoint"]
    assert (await _summary(client, site, headers))["scope"]["valid"] is True


@pytest.mark.parametrize(
    ("kind", "scope"),
    [("disjoint", OVERLAP), ("unknown_overlap", SCOPE)],
    ids=["existing_disjoint", "existing_unknown_overlap"],
)
async def test_atomic_scope_leaves_an_existing_relation_alone(
    client: AsyncClient, owner: tuple[UUID, dict], kind: str, scope: dict
) -> None:
    """
    Condition:
    - Two assets already related, and a file on both answering the opposite.

    Expected:
    - The existing relation is unchanged, and none is added.
    """
    site, headers = owner
    first, second = await make_asset(site, "Router"), await make_asset(site, "Kulkas")
    await execute(
        "INSERT INTO asset_relations (id, site_id, from_asset_id, to_asset_id, kind)"
        " VALUES (gen_random_uuid(), :site, :first, :second, :kind)",
        site=site,
        first=first,
        second=second,
        kind=kind,
    )

    await _preview_and_commit(client, site, headers, TWO_ASSETS_CSV, scope)

    assert await _relations(site) == [kind]


async def test_atomic_scope_leaves_a_parent_and_child_alone(client: AsyncClient, owner: tuple[UUID, dict]) -> None:
    """
    Condition:
    - Two assets in a parent and child link, and a file on both answering ``disjoint``.

    Expected:
    - No relation is written, so containment is never contradicted, and the total stays refused.
    """
    site, headers = owner
    parent, child = await make_asset(site, "Router"), await make_asset(site, "Kulkas")
    await execute("UPDATE assets SET parent_asset_id = :parent WHERE id = :child", parent=parent, child=child)

    await _preview_and_commit(client, site, headers, TWO_ASSETS_CSV, SCOPE)

    assert await _relations(site) == []
    summary = await _summary(client, site, headers)
    assert summary["energy_unavailable_reason"] == "scope_conflict"
    assert [issue["type"] for issue in summary["scope"]["issues"]] == ["parent_child"]


async def test_atomic_scope_stays_within_the_file(client: AsyncClient, owner: tuple[UUID, dict]) -> None:
    """
    Condition:
    - A second file adding one new asset beside assets outside it (D14, pinning the default).

    Expected:
    - No relation to them, so the summary refuses the total as ``unconfirmed``, while per-asset values stay.
    """
    site, headers = owner
    await _preview_and_commit(client, site, headers, TWO_ASSETS_CSV, SCOPE)

    await _preview_and_commit(client, site, headers, _intervals(_interval(20, 0, "Pompa", "70")), SCOPE)

    assert await _relations(site) == ["disjoint"]
    summary = await _summary(client, site, headers)
    assert (summary["energy_kwh"], summary["energy_unavailable_reason"]) == (None, "scope_conflict")
    assert {issue["type"] for issue in summary["scope"]["issues"]} == {"unconfirmed"}
    assert {row["name"]: row["energy_kwh"] for row in summary["assets"]} == {
        "Kulkas": "0.100",
        "Pompa": "0.070",
        "Router": "0.022",
    }


# --- replay --------------------------------------------------------------------------------------------------------


def _without_flag(body: dict) -> dict:
    return {key: value for key, value in body.items() if key != "replayed"}


async def test_replay_at_34_repeats_the_first_result(client: AsyncClient, owner: tuple[UUID, dict]) -> None:
    """
    Condition:
    - AT-34: a commit of ten rows, repeated with the same key.

    Expected:
    - 200, ``replayed`` true, the same result otherwise, and no reading, audit event or revision added.
    """
    site, headers = owner
    preview = await _preview(client, site, headers, csv10(), ANSWERED)
    key = _key()

    first = await _commit(client, preview["id"], headers, key=key)
    before = await _table_counts(site), await _revisions(site)
    second = await _commit(client, preview["id"], headers, key=key)

    assert (first.status_code, second.status_code) == (200, 200)
    assert (first.json()["replayed"], second.json()["replayed"]) == (False, True)
    assert _without_flag(first.json()) == _without_flag(second.json())
    assert before[0]["measurements"] == 10
    assert before[0]["audit_events"] == 1
    assert (await _table_counts(site), await _revisions(site)) == before


async def test_replay_a_lost_response_is_found_again(client: AsyncClient, owner: tuple[UUID, dict]) -> None:
    """
    Condition:
    - A client never reads its commit's answer.

    Expected:
    - ``GET`` says ``committed`` with that same result, and a repeat replays it with ten readings stored.
    """
    site, headers = owner
    preview = await _preview(client, site, headers, csv10(), ANSWERED)
    key = _key()
    lost = (await _commit(client, preview["id"], headers, key=key)).json()

    read = await client.get(f"/api/v1/imports/{preview['id']}", headers=headers)
    repeat = await _commit(client, preview["id"], headers, key=key)

    assert read.status_code == 200
    assert read.json()["status"] == "committed"
    assert read.json()["result"] == _without_flag(lost)
    assert repeat.json()["replayed"] is True
    assert (await _table_counts(site))["measurements"] == 10


async def test_replay_with_a_new_unused_key(client: AsyncClient, owner: tuple[UUID, dict]) -> None:
    """
    Condition:
    - A committed import, repeated under a key no import of the site stored.

    Expected:
    - It replays, and the stored key stays the first one.
    """
    site, headers = owner
    preview = await _preview(client, site, headers, csv10(), ANSWERED)
    key = _key()
    first = await _commit(client, preview["id"], headers, key=key)

    second = await _commit(client, preview["id"], headers)

    assert second.status_code == 200
    assert second.json()["replayed"] is True
    assert _without_flag(second.json()) == _without_flag(first.json())
    stored = await execute("SELECT idempotency_key FROM imports WHERE id = :id", id=preview["id"])
    assert stored[0][0] == key


async def test_replay_outlives_the_preview_expiry(client: AsyncClient, owner: tuple[UUID, dict]) -> None:
    """
    Condition:
    - A committed import whose preview expiry has passed.

    Expected:
    - A repeat still replays, and ``GET`` still says ``committed``.
    """
    site, headers = owner
    preview = await _preview(client, site, headers, csv10(), ANSWERED)
    key = _key()
    await _commit(client, preview["id"], headers, key=key)
    await execute("UPDATE imports SET expires_at = now() - interval '1 day' WHERE id = :id", id=preview["id"])

    repeat = await _commit(client, preview["id"], headers, key=key)
    read = await client.get(f"/api/v1/imports/{preview['id']}", headers=headers)

    assert (repeat.status_code, repeat.json()["replayed"]) == (200, True)
    assert read.json()["status"] == "committed"


# --- refused -------------------------------------------------------------------------------------------------------


async def _assert_refused_changed_nothing(site: UUID, import_id: str, before: tuple) -> None:
    assert (await _table_counts(site), await _revisions(site)) == before
    stored = await execute("SELECT status, idempotency_key, commit_result FROM imports WHERE id = :id", id=import_id)
    assert tuple(stored[0]) == ("previewed", None, None)


@pytest.mark.parametrize(
    ("rows", "mapping"),
    [
        ([_interval(20, 0, FAKE_SECRET, "1"), _interval(20, 0, FAKE_SECRET, "2")], SCOPE),
        ([_interval(20, 0, FAKE_SECRET, "1")], {}),
    ],
    ids=["conflict", "open_question"],
)
async def test_refused_a_blocked_preview(
    client: AsyncClient, owner: tuple[UUID, dict], caplog: pytest.LogCaptureFixture, rows: list[str], mapping: dict
) -> None:
    """
    Condition:
    - A preview blocked by a conflict or by an open question, committed anyway, with fake secrets in a name and the key.

    Expected:
    - ``IMPORT_BLOCKED`` with one record and no fake value, and nothing changes, including the key.
    """
    site, headers = owner
    preview = await _preview(client, site, headers, _intervals(*rows), mapping)
    assert preview["blocked"] is True
    before = await _table_counts(site), await _revisions(site)

    response = await _commit(client, preview["id"], headers, key=FAKE_KEY)

    _assert_failure(
        response,
        caplog,
        expected_status=409,
        code="IMPORT_BLOCKED",
        message=BLOCKED_MESSAGE,
        internal="APP-IMPORT-BLOCKED",
    )
    assert FAKE_KEY not in caplog.text
    await _assert_refused_changed_nothing(site, preview["id"], before)


async def test_refused_an_expired_preview(
    client: AsyncClient, owner: tuple[UUID, dict], caplog: pytest.LogCaptureFixture
) -> None:
    """
    Condition:
    - A preview past its 24 hours.

    Expected:
    - ``IMPORT_STALE`` naming ``expired``, with nothing changed, and ``GET`` answering ``expired``.
    """
    site, headers = owner
    preview = await _preview(client, site, headers, csv10(), ANSWERED)
    await execute("UPDATE imports SET expires_at = now() - interval '1 second' WHERE id = :id", id=preview["id"])
    before = await _table_counts(site), await _revisions(site)

    response = await _commit(client, preview["id"], headers, key=FAKE_KEY)

    error = _assert_failure(
        response, caplog, expected_status=409, code="IMPORT_STALE", message=STALE_MESSAGE, internal="APP-IMPORT-STALE"
    )
    assert error["details"] == [{"loc": ["import"], "msg": "Pratinjau sudah melewati batas 24 jam.", "type": "expired"}]
    await _assert_refused_changed_nothing(site, preview["id"], before)
    assert (await client.get(f"/api/v1/imports/{preview['id']}", headers=headers)).json()["status"] == "expired"


async def _add_asset(client: AsyncClient, site: UUID, headers: dict) -> None:
    response = await client.post(
        f"/api/v1/sites/{site}/assets", json={"name": "Lain", "scope_kind": "device"}, headers=headers
    )
    assert response.status_code == 201, response.text


async def _add_reading(client: AsyncClient, site: UUID, headers: dict) -> None:
    source_id = await make_source(site, "Meter lain")
    source = SourceModel(
        id=source_id,
        site_id=site,
        label="Meter lain",
        origin=SourceOrigin.SIMULATED,
        measurement_kind=MeasurementKind.INTERVAL_ENERGY,
        cadence_seconds=3600,
        resolution_mwh=1000,
        transport_status=TransportStatus.NONE,
    )
    reading = ReadingInput(value=Decimal(1), unit="Wh", interval_start=_utc(21, 0), interval_end=_utc(21, 1))
    async with get_session_factory()() as session:
        locked = await SqlAlchemySiteRepository(session).lock(site)
        assert locked is not None
        await build_ingest_service(session).ingest(locked, source, [reading], received_at=datetime.now(UTC))
        await session.commit()


@pytest.mark.parametrize("move", [_add_asset, _add_reading], ids=["asset", "reading"])
async def test_refused_a_revision_that_moved(
    client: AsyncClient,
    owner: tuple[UUID, dict],
    caplog: pytest.LogCaptureFixture,
    move: Callable[[AsyncClient, UUID, dict], Any],
) -> None:
    """
    Condition:
    - A change lands on the site after the preview: a new asset, or a reading on another source.

    Expected:
    - ``IMPORT_STALE`` naming ``revision_changed``, with nothing written by the commit.
    """
    site, headers = owner
    preview = await _preview(client, site, headers, csv10(), ANSWERED)
    await move(client, site, headers)
    before = await _table_counts(site), await _revisions(site)

    response = await _commit(client, preview["id"], headers, key=FAKE_KEY)

    error = _assert_failure(
        response, caplog, expected_status=409, code="IMPORT_STALE", message=STALE_MESSAGE, internal="APP-IMPORT-STALE"
    )
    assert error["details"] == [
        {
            "loc": ["import"],
            "msg": "Data pada ruang kerja ini berubah setelah pratinjau dibuat.",
            "type": "revision_changed",
        }
    ]
    await _assert_refused_changed_nothing(site, preview["id"], before)


async def test_refused_a_timezone_that_changed(
    client: AsyncClient, owner: tuple[UUID, dict], caplog: pytest.LogCaptureFixture
) -> None:
    """
    Condition:
    - The site's timezone changes after a preview of naive rows, which advances neither revision.

    Expected:
    - ``IMPORT_STALE`` naming ``timezone_changed``.
    """
    site, headers = owner
    preview = await _preview(client, site, headers, csv10(), ANSWERED)
    patched = await client.patch(f"/api/v1/sites/{site}", json={"timezone": "Asia/Makassar"}, headers=headers)
    assert patched.status_code == 200, patched.text
    before = await _table_counts(site), await _revisions(site)

    response = await _commit(client, preview["id"], headers, key=FAKE_KEY)

    error = _assert_failure(
        response, caplog, expected_status=409, code="IMPORT_STALE", message=STALE_MESSAGE, internal="APP-IMPORT-STALE"
    )
    assert error["details"] == [
        {
            "loc": ["import"],
            "msg": "Zona waktu ruang kerja berubah setelah pratinjau dibuat.",
            "type": "timezone_changed",
        }
    ]
    await _assert_refused_changed_nothing(site, preview["id"], before)


async def test_refused_after_a_demo_reset(client: AsyncClient, caplog: pytest.LogCaptureFixture) -> None:
    """
    Condition:
    - A preview on an ``empty`` demo session, which is then reset.

    Expected:
    - ``IMPORT_STALE`` naming ``revision_changed``, because even an empty reset advances both revisions.
    """
    session = await start_demo(client, "empty")
    preview = await _preview(client, session["site_id"], session["auth"], csv10(), ANSWERED)
    reset = await client.post("/api/v1/demo/sessions/current/reset", headers=session["auth"])
    assert reset.status_code < 300, reset.text
    site = UUID(session["site_id"])
    before = await _table_counts(site), await _revisions(site)

    response = await _commit(client, preview["id"], session["auth"], key=FAKE_KEY)

    error = _assert_failure(
        response, caplog, expected_status=409, code="IMPORT_STALE", message=STALE_MESSAGE, internal="APP-IMPORT-STALE"
    )
    assert error["details"][0]["type"] == "revision_changed"
    await _assert_refused_changed_nothing(site, preview["id"], before)


async def test_refused_skipped_rows_without_acknowledgment(
    client: AsyncClient, owner: tuple[UUID, dict], caplog: pytest.LogCaptureFixture
) -> None:
    """
    Condition:
    - Two of ten rows are invalid. The commit is sent first without ``acknowledge_skipped``, then with it.

    Expected:
    - ``IMPORT_ACK_REQUIRED`` naming the count, with nothing changed. The second succeeds under the same key, adding
      eight rows and skipping two.
    """
    site, headers = owner
    preview = await _preview(client, site, headers, csv10(2), ANSWERED)
    before = await _table_counts(site), await _revisions(site)
    key = _key()

    refused = await _commit(client, preview["id"], headers, key=key)

    error = _assert_failure(
        refused,
        caplog,
        expected_status=409,
        code="IMPORT_ACK_REQUIRED",
        message=ACK_MESSAGE,
        internal="APP-IMPORT-ACK-REQUIRED",
    )
    assert error["details"] == [
        {
            "loc": ["body", "acknowledge_skipped"],
            "msg": "2 baris tidak valid akan dilewati.",
            "type": "acknowledgment_required",
        }
    ]
    await _assert_refused_changed_nothing(site, preview["id"], before)

    accepted = await _commit(client, preview["id"], headers, key=key, acknowledge=True)

    assert accepted.status_code == 200, accepted.text
    assert (accepted.json()["rows_added"], accepted.json()["rows_skipped"]) == (8, 2)
    assert accepted.json()["acknowledge_skipped"] is True


async def test_refused_a_preview_purged_by_a_new_one(
    client: AsyncClient, owner: tuple[UUID, dict], caplog: pytest.LogCaptureFixture
) -> None:
    """
    Condition:
    - An expired preview that a newer preview has purged.

    Expected:
    - ``NOT_FOUND``, because it no longer exists.
    """
    site, headers = owner
    preview = await _preview(client, site, headers, csv10(), ANSWERED)
    await execute("UPDATE imports SET expires_at = now() - interval '1 day' WHERE id = :id", id=preview["id"])
    await _preview(client, site, headers, csv10(), ANSWERED)

    response = await _commit(client, preview["id"], headers, key=FAKE_KEY)

    _assert_failure(
        response,
        caplog,
        expected_status=404,
        code="NOT_FOUND",
        message="Data yang diminta tidak ditemukan. Periksa alamatnya lalu coba lagi.",
        internal="APP-NOT-FOUND",
    )


# --- key -----------------------------------------------------------------------------------------------------------


async def test_key_used_on_another_import_is_refused(
    client: AsyncClient, owner: tuple[UUID, dict], caplog: pytest.LogCaptureFixture
) -> None:
    """
    Condition:
    - A key stored on import A, sent for a separate import B of the same site.

    Expected:
    - 409 ``CONFLICT``, nothing applied, B unchanged, and the key's value in no response or record.
    """
    site, headers = owner
    first = await _preview(client, site, headers, _intervals(_interval(20, 0)), SCOPE)
    second = await _preview(client, site, headers, _intervals(_interval(21, 0)), SCOPE)
    assert (await _commit(client, first["id"], headers, key=FAKE_KEY)).status_code == 200
    caplog.clear()
    before = await _table_counts(site), await _revisions(site)

    response = await _commit(client, second["id"], headers, key=FAKE_KEY)

    _assert_failure(
        response, caplog, expected_status=409, code="CONFLICT", message=KEY_MESSAGE, internal="APP-IMPORT-KEY-CONFLICT"
    )
    await _assert_refused_changed_nothing(site, second["id"], before)


async def test_key_with_a_different_acknowledgment_is_refused(
    client: AsyncClient, owner: tuple[UUID, dict], caplog: pytest.LogCaptureFixture
) -> None:
    """
    Condition:
    - A committed import, repeated with its own key and a different ``acknowledge_skipped``.

    Expected:
    - The same 409, because that key meant something else, and nothing changes.
    """
    site, headers = owner
    preview = await _preview(client, site, headers, csv10(2), ANSWERED)
    key = _key()
    assert (await _commit(client, preview["id"], headers, key=key, acknowledge=True)).status_code == 200
    caplog.clear()
    before = await _table_counts(site), await _revisions(site)

    response = await _commit(client, preview["id"], headers, key=key, acknowledge=False)

    _assert_failure(
        response, caplog, expected_status=409, code="CONFLICT", message=KEY_MESSAGE, internal="APP-IMPORT-KEY-CONFLICT"
    )
    assert (await _table_counts(site), await _revisions(site)) == before


async def test_key_on_another_import_wins_over_a_replay(
    client: AsyncClient, owner: tuple[UUID, dict], caplog: pytest.LogCaptureFixture
) -> None:
    """
    Condition:
    - Import A committed under key K and import B committed under key L, then B is sent again with K.

    Expected:
    - 409 ``CONFLICT`` even though B is committed, as the Idempotency cases table orders it.
    """
    site, headers = owner
    first = await _preview(client, site, headers, _intervals(_interval(20, 0)), SCOPE)
    used = _key()
    assert (await _commit(client, first["id"], headers, key=used)).status_code == 200
    second = await _preview(client, site, headers, _intervals(_interval(21, 0)), SCOPE)
    assert (await _commit(client, second["id"], headers)).status_code == 200
    caplog.clear()

    response = await _commit(client, second["id"], headers, key=used)

    _assert_failure(
        response, caplog, expected_status=409, code="CONFLICT", message=KEY_MESSAGE, internal="APP-IMPORT-KEY-CONFLICT"
    )


async def test_key_is_scoped_to_its_site(client: AsyncClient, acting: Callable[[UUID], dict]) -> None:
    """
    Condition:
    - The same key in another site, on that site's own preview.

    Expected:
    - It succeeds, so keys in different sites never collide and a foreign key never leaks.
    """
    principal = await make_principal()
    first, second, headers = await make_site(principal), await make_site(principal), acting(principal)
    key = _key()
    one = await _preview(client, first, headers, csv10(), ANSWERED)
    two = await _preview(client, second, headers, csv10(), ANSWERED)

    assert (await _commit(client, one["id"], headers, key=key)).status_code == 200
    response = await _commit(client, two["id"], headers, key=key)

    assert (response.status_code, response.json()["replayed"]) == (200, False)


@pytest.mark.parametrize("extra", [{}, {"Idempotency-Key": "short"}], ids=["missing", "short"])
async def test_key_that_is_missing_or_malformed_is_refused(
    client: AsyncClient, owner: tuple[UUID, dict], caplog: pytest.LogCaptureFixture, extra: dict
) -> None:
    """
    Condition:
    - A commit with no ``Idempotency-Key``, or with one that fails its pattern.

    Expected:
    - 422 ``VALIDATION_FAILED`` naming the header, and nothing stored.
    """
    site, headers = owner
    preview = await _preview(client, site, headers, csv10(), ANSWERED)
    before = await _table_counts(site), await _revisions(site)

    response = await client.post(
        f"/api/v1/imports/{preview['id']}/commit", json={"acknowledge_skipped": False}, headers=headers | extra
    )

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "VALIDATION_FAILED"
    assert error["recovery"] == {"retryable": False}
    assert "header" in error["details"][0]["loc"]
    records = _records(caplog)
    assert len(records) == 1
    assert records[0]["reference_id"] == error["request_id"]
    await _assert_refused_changed_nothing(site, preview["id"], before)


async def test_key_refused_as_stale_stays_free(client: AsyncClient, owner: tuple[UUID, dict]) -> None:
    """
    Condition:
    - A key refused by ``IMPORT_STALE``, then sent for a fresh preview of the same file.

    Expected:
    - It commits, because a refused attempt stores nothing.
    """
    site, headers = owner
    stale = await _preview(client, site, headers, csv10(), ANSWERED)
    await _add_asset(client, site, headers)
    key = _key()
    refused = await _commit(client, stale["id"], headers, key=key)
    assert refused.json()["error"]["code"] == "IMPORT_STALE"

    fresh = await _preview(client, site, headers, csv10(), ANSWERED)
    response = await _commit(client, fresh["id"], headers, key=key)

    assert (response.status_code, response.json()["replayed"]) == (200, False)


# --- race ----------------------------------------------------------------------------------------------------------


@asynccontextmanager
async def _hold_site_lock(site: UUID) -> AsyncIterator[None]:
    """Hold the shared site lock until the block ends, so requests started inside pile up on it."""
    async with get_session_factory()() as session:
        await session.execute(text("SELECT id FROM sites WHERE id = :id FOR UPDATE"), {"id": site})
        yield
        await session.commit()


async def _blocked_count() -> int:
    rows = await execute(
        "SELECT count(*) FROM pg_stat_activity WHERE datname = current_database() AND wait_event_type = 'Lock'"
    )
    return rows[0][0]


async def _wait_blocked(count: int) -> None:
    """Wait until this many backends wait on a lock, so a race starts in the order a test means."""
    deadline = time.monotonic() + 5
    while await _blocked_count() < count:
        if time.monotonic() > deadline:
            raise AssertionError(f"Fewer than {count} requests reached the lock.")
        await asyncio.sleep(0.01)


async def _settled(*tasks: asyncio.Task) -> list[Response]:
    return list(await asyncio.wait_for(asyncio.gather(*tasks), RACE_TIMEOUT))


async def test_race_one_key_commits_once(client: AsyncClient, owner: tuple[UUID, dict]) -> None:
    """
    Condition:
    - SC-001: two commits of one import with one key, released together from behind the site lock.

    Expected:
    - Both answer 200, exactly one with ``replayed`` false, the results agree, and ten readings and one audit event
      exist. Without ``populate_existing`` the second would write everything again.
    """
    site, headers = owner
    preview = await _preview(client, site, headers, csv10(), ANSWERED)
    key = _key()

    async with _hold_site_lock(site):
        first = asyncio.create_task(_commit(client, preview["id"], headers, key=key))
        second = asyncio.create_task(_commit(client, preview["id"], headers, key=key))
        await _wait_blocked(2)
    answers = await _settled(first, second)

    assert [answer.status_code for answer in answers] == [200, 200]
    assert sorted(answer.json()["replayed"] for answer in answers) == [False, True]
    assert _without_flag(answers[0].json()) == _without_flag(answers[1].json())
    counts = await _table_counts(site)
    assert (counts["measurements"], counts["audit_events"]) == (10, 1)


async def test_race_two_keys_commit_once(client: AsyncClient, owner: tuple[UUID, dict]) -> None:
    """
    Condition:
    - SC-001: two commits of one import with two different keys.

    Expected:
    - The same outcome, and the stored key is the winner's.
    """
    site, headers = owner
    preview = await _preview(client, site, headers, csv10(), ANSWERED)
    keys = [_key(), _key()]

    async with _hold_site_lock(site):
        tasks = [asyncio.create_task(_commit(client, preview["id"], headers, key=key)) for key in keys]
        await _wait_blocked(2)
    answers = await _settled(*tasks)

    assert [answer.status_code for answer in answers] == [200, 200]
    assert sorted(answer.json()["replayed"] for answer in answers) == [False, True]
    winner = next(key for key, answer in zip(keys, answers, strict=True) if not answer.json()["replayed"])
    stored = await execute("SELECT idempotency_key FROM imports WHERE id = :id", id=preview["id"])
    assert stored[0][0] == winner
    counts = await _table_counts(site)
    assert (counts["measurements"], counts["audit_events"]) == (10, 1)


async def test_race_status_does_not_wait_for_a_commit(client: AsyncClient, owner: tuple[UUID, dict]) -> None:
    """
    Condition:
    - A commit is pending behind the site lock while a client reads the import (D19).

    Expected:
    - ``GET`` answers ``previewed`` within two seconds, taking no lock, and the commit finishes afterwards.
    """
    site, headers = owner
    preview = await _preview(client, site, headers, csv10(), ANSWERED)

    async with _hold_site_lock(site):
        pending = asyncio.create_task(_commit(client, preview["id"], headers))
        await _wait_blocked(1)
        read = await asyncio.wait_for(client.get(f"/api/v1/imports/{preview['id']}", headers=headers), 2)
        assert read.status_code == 200
        assert (read.json()["status"], read.json()["result"]) == ("previewed", None)
    answers = await _settled(pending)

    assert answers[0].status_code == 200


def _won_and_lost(answers: list[Response]) -> tuple[Response, Response]:
    assert sorted(answer.status_code for answer in answers) == [200, 409], [answer.text for answer in answers]
    return (answers[0], answers[1]) if answers[0].status_code == 200 else (answers[1], answers[0])


async def test_race_two_previews_of_one_interval(client: AsyncClient, owner: tuple[UUID, dict]) -> None:
    """
    Condition:
    - SC-002: two previews of the same rows on an empty site, committed concurrently.

    Expected:
    - One wins and the other is stale, the tables hold one result, the loser stays ``previewed``, and a new preview of
      that file finds only duplicates.
    """
    site, headers = owner
    previews = [await _preview(client, site, headers, csv10(), ANSWERED) for _ in range(2)]

    async with _hold_site_lock(site):
        tasks = [asyncio.create_task(_commit(client, preview["id"], headers)) for preview in previews]
        await _wait_blocked(2)
    won, lost = _won_and_lost(await _settled(*tasks))

    assert won.json()["rows_added"] == 10
    assert lost.json()["error"]["code"] == "IMPORT_STALE"
    assert lost.json()["error"]["details"][0]["type"] == "revision_changed"
    counts = await _table_counts(site)
    assert (counts["measurements"], counts["assets"], counts["sources"], counts["bindings"]) == (10, 1, 1, 1)
    assert counts["audit_events"] == 1
    statuses = await execute("SELECT status FROM imports WHERE site_id = :site ORDER BY status", site=site)
    assert [row[0] for row in statuses] == ["committed", "previewed"]
    again = await _preview(client, site, headers, csv10(), ANSWERED)
    assert (again["accepted_rows"], again["duplicate_rows"]) == (0, 10)


async def test_race_two_previews_of_one_binding(client: AsyncClient, owner: tuple[UUID, dict]) -> None:
    """
    Condition:
    - SC-002: two previews of different days, both mapped to one existing asset with no source.

    Expected:
    - One wins and the other is stale, with one source and one binding, so no partial change exists.
    """
    site, headers = owner
    asset = await make_asset(site, "Router")
    mapping = SCOPE | {"asset_map": {"Router": str(asset)}}
    previews = [await _preview(client, site, headers, _intervals(_interval(day, 0)), mapping) for day in (20, 21)]

    async with _hold_site_lock(site):
        tasks = [asyncio.create_task(_commit(client, preview["id"], headers)) for preview in previews]
        await _wait_blocked(2)
    won, lost = _won_and_lost(await _settled(*tasks))

    assert won.json()["rows_added"] == 1
    assert lost.json()["error"]["details"][0]["type"] == "revision_changed"
    counts = await _table_counts(site)
    assert (counts["measurements"], counts["sources"], counts["bindings"]) == (1, 1, 1)


async def test_race_a_preview_over_unrelated_rows_is_also_stale(client: AsyncClient, owner: tuple[UUID, dict]) -> None:
    """
    Condition:
    - Two previews over different assets and days, committed one after the other (D6, pinning the site-wide check).

    Expected:
    - The second is stale even though it shares nothing with the first.
    """
    site, headers = owner
    first = await _preview(client, site, headers, _intervals(_interval(20, 0, "Router")), SCOPE)
    second = await _preview(client, site, headers, _intervals(_interval(21, 0, "Kulkas")), SCOPE)

    assert (await _commit(client, first["id"], headers)).status_code == 200
    response = await _commit(client, second["id"], headers)

    assert response.status_code == 409
    assert response.json()["error"]["details"][0]["type"] == "revision_changed"


async def test_race_commit_and_preview_purge_finish_together(client: AsyncClient, owner: tuple[UUID, dict]) -> None:
    """
    Condition:
    - SC-004: five previews on a site. A commit of the oldest waits on the site lock, then a sixth preview starts, whose
      purge would remove that same import (D4).

    Expected:
    - No deadlock. The commit answers 200, the preview 201, and the import is ``committed`` and present.
    """
    site, headers = owner
    previews = [await _preview(client, site, headers, csv10(), ANSWERED) for _ in range(5)]
    oldest = previews[0]["id"]
    files = {"mapping": (None, json.dumps(ANSWERED)), "file": ("data.csv", csv10().encode(), "text/csv")}

    async with _hold_site_lock(site):
        commit = asyncio.create_task(_commit(client, oldest, headers))
        await _wait_blocked(1)
        preview = asyncio.create_task(
            client.post(f"/api/v1/sites/{site}/imports/preview", files=files, headers=headers)
        )
        await _wait_blocked(2)
    committed, previewed = await _settled(commit, preview)

    assert committed.status_code == 200, committed.text
    assert previewed.status_code == 201, previewed.text
    stored = await execute("SELECT status FROM imports WHERE id = :id", id=oldest)
    assert stored[0][0] == "committed"


async def test_race_commit_waiting_on_a_purge_finds_it_gone(
    client: AsyncClient, owner: tuple[UUID, dict], caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    Condition:
    - SC-004 the other way round: a sixth preview has purged the oldest and is still open, holding a share of the site
      row, when a commit of that import starts, still able to read it.

    Expected:
    - The commit waits, with no deadlock. Once the preview ends, it answers ``NOT_FOUND``, and the preview answers 201.
    """
    site, headers = owner
    previews = [await _preview(client, site, headers, csv10(), ANSWERED) for _ in range(5)]
    purged, proceed = asyncio.Event(), asyncio.Event()
    real = SqlAlchemyImportRepository.add_rows

    async def pausing(self: SqlAlchemyImportRepository, *args: Any, **kwargs: Any) -> None:
        purged.set()
        await proceed.wait()
        await real(self, *args, **kwargs)

    monkeypatch.setattr(SqlAlchemyImportRepository, "add_rows", pausing)
    preview = asyncio.create_task(_preview(client, site, headers, csv10(), ANSWERED))
    await asyncio.wait_for(purged.wait(), RACE_TIMEOUT)
    commit = asyncio.create_task(_commit(client, previews[0]["id"], headers))
    await _wait_blocked(1)
    proceed.set()
    stored, response = await asyncio.wait_for(asyncio.gather(preview, commit), RACE_TIMEOUT)

    assert stored["blocked"] is False
    _assert_failure(
        response,
        caplog,
        expected_status=404,
        code="NOT_FOUND",
        message="Data yang diminta tidak ditemukan. Periksa alamatnya lalu coba lagi.",
        internal="APP-NOT-FOUND",
    )
    assert (await _table_counts(site))["measurements"] == 0


# --- exact ---------------------------------------------------------------------------------------------------------


def _text_of(body: dict) -> dict:
    return {key: body[key] for key in ("rows_added", "rows_skipped", "rows_duplicate")}


async def test_exact_counts_equal_the_database(client: AsyncClient, owner: tuple[UUID, dict]) -> None:
    """
    Condition:
    - A file with one invalid row, one repeat in the file, one mapped asset and one new one, whose last rows end at
      local midnight.

    Expected:
    - Each count equals the database or the preview. Assets are named as stored. The period ends on the previous local
      date, the affected bounds match the rows, and ``committed_at`` is the wall clock's, not the demo clock's.
    """
    site, headers = owner
    router = await make_asset(site, "Router")
    text = _intervals(
        _interval(20, 22),
        _interval(20, 23),
        _interval(20, 22),
        _interval(20, 22, "Kulkas", "20"),
        _interval(20, 23, "Kulkas", "20"),
        _interval(20, 21, "Kulkas", "-1"),
    )
    preview = await _preview(client, site, headers, text, SCOPE)
    assert (preview["invalid_rows"], preview["duplicate_rows"], preview["accepted_rows"]) == (1, 1, 4)

    response = await _commit(client, preview["id"], headers, acknowledge=True)

    assert response.status_code == 200, response.text
    body = response.json()
    assert _text_of(body) == {"rows_added": 4, "rows_skipped": 1, "rows_duplicate": 1}
    stored = await execute(
        "SELECT count(*) FROM measurements m JOIN sources s ON s.id = m.source_id"
        " WHERE s.site_id = :site AND m.kind <> 'counter_delta'",
        site=site,
    )
    assert stored[0][0] == body["rows_added"]
    kulkas = await _asset_id(site, "Kulkas")
    assert body["assets_created"] == [{"id": str(kulkas), "name": "Kulkas"}]
    assert body["assets_mapped"] == [{"id": str(router), "name": "Router"}]
    assert body["period"] == {"start_date": "2026-10-20", "end_date": "2026-10-20", "timezone": "Asia/Jakarta"}
    assert datetime.fromisoformat(body["affected_from"]) == _utc(20, 22)
    assert datetime.fromisoformat(body["affected_to"]) == _utc(21, 0)
    assert abs(datetime.fromisoformat(body["committed_at"]) - datetime.now(UTC)) < timedelta(minutes=5)
    assert body["rows_after_site_clock"] == 0
    assert body["acknowledge_skipped"] is True


async def test_exact_duplicate_only_reimport(client: AsyncClient, owner: tuple[UUID, dict]) -> None:
    """
    Condition:
    - AT-33: a committed file is previewed again, and that preview is committed.

    Expected:
    - 200 with no row added, ten duplicates, no period or range, and the asset named as mapped. No domain table or
      revision changes, apart from one audit event with null dates, and a replay adds no second one.
    """
    site, headers = owner
    await _preview_and_commit(client, site, headers, csv10(), ANSWERED)
    asset = await _asset_id(site, "Router")
    before = await _table_counts(site), await _revisions(site)
    preview = await _preview(client, site, headers, csv10(), ANSWERED)
    assert preview["duplicate_rows"] == 10
    key = _key()

    response = await _commit(client, preview["id"], headers, key=key)

    assert response.status_code == 200, response.text
    body = response.json()
    assert _text_of(body) == {"rows_added": 0, "rows_skipped": 0, "rows_duplicate": 10}
    assert (body["period"], body["affected_from"], body["affected_to"]) == (None, None, None)
    assert body["assets_created"] == []
    assert body["assets_mapped"] == [{"id": str(asset), "name": "Router"}]
    assert (body["rows_after_site_clock"], body["replayed"]) == (0, False)
    counts, revisions = await _table_counts(site), await _revisions(site)
    assert revisions == before[1]
    assert counts == before[0] | {"audit_events": before[0]["audit_events"] + 1}
    events = await execute(
        "SELECT affected_from, affected_to FROM audit_events WHERE subject_id = :id", id=preview["id"]
    )
    assert [tuple(event) for event in events] == [(None, None)]
    stored = await execute("SELECT status FROM imports WHERE id = :id", id=preview["id"])
    assert stored[0][0] == "committed"

    replay = await _commit(client, preview["id"], headers, key=key)

    assert replay.json()["replayed"] is True
    assert (await _table_counts(site))["audit_events"] == counts["audit_events"]


async def _deltas(site: UUID) -> list[tuple]:
    rows = await execute(
        "SELECT m.interval_start, m.energy_mwh, m.quality FROM measurements m JOIN sources s ON s.id = m.source_id"
        " WHERE s.site_id = :site AND m.kind = 'counter_delta' ORDER BY m.interval_start",
        site=site,
    )
    return [tuple(row) for row in rows]


async def test_exact_counter_reset_has_no_energy(client: AsyncClient, owner: tuple[UUID, dict]) -> None:
    """
    Condition:
    - AT-37: points of 100, 130, 5 and 20 Wh hourly, and a repeat of the commit.

    Expected:
    - Deltas of 30 and 15 Wh, no row over the reset interval, no negative energy and a total of 0.045 kWh, unchanged by
      the repeat.
    """
    site, headers = owner
    text = _counters(_point(20, 0, 100), _point(20, 1, 130), _point(20, 2, 5), _point(20, 3, 20))
    preview = await _preview(client, site, headers, text, SCOPE)
    key = _key()

    response = await _commit(client, preview["id"], headers, key=key)

    assert response.status_code == 200, response.text
    assert response.json()["rows_added"] == 4
    assert await _deltas(site) == [(_utc(20, 0), 30_000, "valid"), (_utc(20, 2), 15_000, "valid")]
    assert (await _summary(client, site, headers))["energy_kwh"] == "0.045"

    assert (await _commit(client, preview["id"], headers, key=key)).json()["replayed"] is True
    assert (await _summary(client, site, headers))["energy_kwh"] == "0.045"


async def test_exact_counter_anchor_has_no_energy(client: AsyncClient, owner: tuple[UUID, dict]) -> None:
    """
    Condition:
    - A one-row counter file.

    Expected:
    - The point is stored as an anchor with no delta and no energy, and it counts as one row added.
    """
    site, headers = owner

    body = await _preview_and_commit(client, site, headers, _counters(_point(20, 0, 100)), SCOPE)

    assert body["rows_added"] == 1
    assert (await _table_counts(site))["measurements"] == 1
    assert await _deltas(site) == []
    assert (await _summary(client, site, headers))["energy_kwh"] is None


async def test_exact_counter_append_to_a_stored_stream(client: AsyncClient, owner: tuple[UUID, dict]) -> None:
    """
    Condition:
    - A stored stream whose last point is 20 Wh, and an appended file of 25 and 10 Wh.

    Expected:
    - A new delta of 5 Wh, the drop to 10 treated as a reset with no energy, and affected bounds covering only the
      change. The preview still says the first-reading text (D17, recording the limit), and the totals are right anyway.
    """
    site, headers = owner
    first = _counters(_point(20, 0, 100), _point(20, 1, 130), _point(20, 2, 5), _point(20, 3, 20))
    await _preview_and_commit(client, site, headers, first, SCOPE)
    preview = await _preview(client, site, headers, _counters(_point(20, 4, 25), _point(20, 5, 10)), SCOPE)
    assert "Pembacaan pertama Meter menjadi titik awal penghitung, bukan energi." in preview["assumptions"]
    key = _key()

    response = await _commit(client, preview["id"], headers, key=key)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["rows_added"] == 2
    assert await _deltas(site) == [
        (_utc(20, 0), 30_000, "valid"),
        (_utc(20, 2), 15_000, "valid"),
        (_utc(20, 3), 5_000, "valid"),
    ]
    assert datetime.fromisoformat(body["affected_from"]) == _utc(20, 3)
    assert datetime.fromisoformat(body["affected_to"]) == _utc(20, 5)
    assert (await _summary(client, site, headers))["energy_kwh"] == "0.050"

    assert (await _commit(client, preview["id"], headers, key=key)).json()["replayed"] is True
    assert (await _summary(client, site, headers))["energy_kwh"] == "0.050"


async def test_exact_counter_long_gap_is_flagged(client: AsyncClient, owner: tuple[UUID, dict]) -> None:
    """
    Condition:
    - Two counter points three hours apart, on a source with no declared cadence.

    Expected:
    - The delta is ``long_gap``, because 006 assumes one hour, and it keeps its energy.
    """
    site, headers = owner

    await _preview_and_commit(client, site, headers, _counters(_point(20, 0, 100), _point(20, 3, 130)), SCOPE)

    assert await _deltas(site) == [(_utc(20, 0), 30_000, "long_gap")]


async def test_exact_late_import_writes_one_audit_event(client: AsyncClient, owner: tuple[UUID, dict]) -> None:
    """
    Condition:
    - Rows on 20 October are committed, then late rows filling 18 October.

    Expected:
    - The second import writes one event, naming the import, the principal and only the late rows' range. Its detail
      holds counts only, with no key and no file content.
    """
    site, headers = owner
    await _preview_and_commit(client, site, headers, _intervals(_interval(20, 0)), SCOPE)
    preview = await _preview(client, site, headers, _intervals(*[_interval(18, hour) for hour in range(4)]), SCOPE)
    key = _key()

    assert (await _commit(client, preview["id"], headers, key=key)).status_code == 200

    events = await execute(
        "SELECT action, subject_type, subject_id, actor_principal_id, affected_from, affected_to, detail"
        " FROM audit_events WHERE site_id = :site AND subject_id = :id",
        site=site,
        id=preview["id"],
    )
    assert len(events) == 1
    event = events[0]
    assert (event[0], event[1], str(event[2])) == ("import.committed", "import", preview["id"])
    assert str(event[3]) == headers[TEST_PRINCIPAL_HEADER]
    assert (event[4], event[5]) == (_utc(18, 0), _utc(18, 4))
    assert event[6] == {
        "rows_added": 4,
        "rows_skipped": 0,
        "rows_duplicate": 0,
        "assets_created": 0,
        "assets_mapped": 1,
    }
    assert (await execute("SELECT count(*) FROM audit_events WHERE site_id = :site", site=site))[0][0] == 2


WEEK = {"start_date": "2026-10-19", "end_date": "2026-10-25"}


def _hourly(start: datetime, hours: int, wh: str = "100", name: str = "TV") -> str:
    rows = [
        f"{(start + timedelta(hours=hour)).isoformat()},{(start + timedelta(hours=hour + 1)).isoformat()},{name},{wh}"
        for hour in range(hours)
    ]
    return _intervals(*rows)


async def _read_insights(client: AsyncClient, session: dict) -> dict:
    response = await client.get(f"/api/v1/sites/{session['site_id']}/insights", params=WEEK, headers=session["auth"])
    assert response.status_code == 200, response.text
    return response.json()


async def test_insight_imported_data_stays_descriptive(client: AsyncClient) -> None:
    """
    Condition:
    - On an ``empty`` session, one week is committed, then the three weeks before it (D2, AT-20).

    Expected:
    - First the asset is learning. Then it is comparable with no observation, because imported sources have unknown
      resolution, and its comparison says ``descriptive``.
    """
    session = await start_demo(client, "empty")
    site, auth = session["site_id"], session["auth"]
    current = _utc(19, 0)
    await _preview_and_commit(client, site, auth, _hourly(current, 7 * 24), SCOPE)

    learning = await _read_insights(client, session)

    assert (learning["learning_count"], learning["comparable_count"]) == (1, 0)

    await _preview_and_commit(client, site, auth, _hourly(current - timedelta(weeks=3), 21 * 24), SCOPE)

    compared = await _read_insights(client, session)
    assert (compared["learning_count"], compared["comparable_count"]) == (0, 1)
    assert compared["observations"] == []
    asset = await _asset_id(UUID(site), "TV")
    comparison = await client.get(f"/api/v1/assets/{asset}/comparison", params=WEEK, headers=auth)
    assert comparison.status_code == 200, comparison.text
    assert comparison.json()["state"] == "descriptive"


async def _seed_known_resolution_source(site: UUID) -> None:
    """Store four weeks on an imported source of known resolution, with a qualifying change and one hour missing."""
    start = _utc(19, 0) - timedelta(weeks=3)
    gap = _utc(22, 12)
    readings = []
    for hour in range(28 * 24):
        begin = start + timedelta(hours=hour)
        if begin == gap:
            continue
        wh = 200 if begin >= _utc(19, 0) else 100
        readings.append(
            ReadingInput(value=Decimal(wh), unit="Wh", interval_start=begin, interval_end=begin + timedelta(hours=1))
        )
    async with get_session_factory()() as session:
        sites = SiteService(SqlAlchemySiteRepository(session))
        assets = AssetService(SqlAlchemyAssetRepository(session), sites, build_audit_service(session))
        locked = await sites.lock(site)
        asset = await assets.add_asset(locked, name="TV", scope_kind=ScopeKind.DEVICE)
        source = await assets.create_source(
            locked,
            label=source_label("tv"),
            origin=SourceOrigin.IMPORT,
            measurement_kind=MeasurementKind.INTERVAL_ENERGY,
            cadence_seconds=3600,
            resolution_mwh=1000,
            transport_status=TransportStatus.HISTORICAL,
        )
        await assets.add_binding(
            locked, asset_id=asset.id, source_id=source.id, effective_from=start, authoritative=True
        )
        await build_ingest_service(session).ingest(locked, source, readings, received_at=datetime.now(UTC))
        await sites.advance_binding_revision(locked)
        await session.commit()


async def test_insight_late_import_publishes_a_revision_and_keeps_the_first(client: AsyncClient) -> None:
    """
    Condition:
    - A stored imported source of known resolution has an observation at revision 1, and a CSV fills a gap in its week
      (D1: the commit calls nothing in ``app/insights``).

    Expected:
    - The next read shows revision 2 as current. Revision 1 is readable with its first evidence, superseded, and a
      repeat of the commit makes no revision 3.
    """
    session = await start_demo(client, "empty")
    site, auth = session["site_id"], session["auth"]
    await _seed_known_resolution_source(UUID(site))
    first = (await _read_insights(client, session))["observations"]
    assert [item["revision"] for item in first] == [1]
    preview = await _preview(client, site, auth, _intervals(_interval(22, 12, "TV", "200")), SCOPE)
    assert (preview["accepted_rows"], preview["blocked"]) == (1, False)
    key = _key()

    assert (await _commit(client, preview["id"], auth, key=key)).status_code == 200

    current = (await _read_insights(client, session))["observations"]
    assert [item["revision"] for item in current] == [2]
    assert current[0]["id"] == first[0]["id"]
    old = (await client.get(f"/api/v1/insights/{first[0]['id']}?revision=1", headers=auth)).json()
    assert old["evidence"] == first[0]["evidence"]
    assert (old["revision"], old["superseded"], old["current_revision"]) == (1, True, 2)

    assert (await _commit(client, preview["id"], auth, key=key)).json()["replayed"] is True
    assert [item["revision"] for item in (await _read_insights(client, session))["observations"]] == [2]


async def test_exact_rows_after_site_clock_stay_invisible(client: AsyncClient) -> None:
    """
    Condition:
    - On an ``empty`` session, whose clock is fixed at 26 October 00.00 WIB, a file dated 1 November, then a file ending
      exactly at that clock (D18).

    Expected:
    - The first commits with every row counted as after the clock, its readings are stored, and a summary of that date
      answers 200 with no energy. The second counts none, because an interval ending at now is included.
    """
    session = await start_demo(client, "empty")
    site, auth = session["site_id"], session["auth"]
    late = (
        "interval_start,interval_end,asset,energy_wh\n2026-11-01T00:00:00+07:00,2026-11-01T01:00:00+07:00,Router,10\n"
    )

    body = await _preview_and_commit(client, site, auth, late, SCOPE)

    assert (body["rows_added"], body["rows_after_site_clock"]) == (1, 1)
    assert (await _table_counts(UUID(site)))["measurements"] == 1
    read = await _summary(client, site, auth, "2026-11-01")
    assert (read["energy_kwh"], read["energy_unavailable_reason"]) == (None, "no_data")

    edge = await _preview_and_commit(client, site, auth, _intervals(_interval(25, 23)), SCOPE)

    assert (edge["rows_added"], edge["rows_after_site_clock"]) == (1, 0)


async def test_exact_imported_data_is_historical(client: AsyncClient) -> None:
    """
    Condition:
    - Old rows are committed on an ``empty`` session, and the site's insights are read.

    Expected:
    - The source is ``historical``, and no ``stale`` notice names it, however old its rows are: a historical source is
      never a disconnected live meter.
    """
    session = await start_demo(client, "empty")
    site, auth = session["site_id"], session["auth"]

    await _preview_and_commit(client, site, auth, _hourly(_utc(19, 0) - timedelta(weeks=1), 6), SCOPE)

    notices = (await _read_insights(client, session))["notices"]
    assert [notice for notice in notices if "stale" in notice["kind"]] == []
    rows = await execute("SELECT transport_status FROM sources WHERE site_id = :site", site=UUID(site))
    assert rows[0][0] == "historical"


async def test_builtin_valid_example_keeps_historical_range_and_gaps(client: AsyncClient) -> None:
    """Use the two S10 sample streams in an empty demo and verify the full Jakarta calendar day."""
    session = await start_demo(client, "empty")
    lines = [f"2026-10-20 {hour:02}:00,Lampu Teras,40" for hour in range(6, 12)]
    lines.extend(f"2026-10-20 {hour:02}:00,Dispenser,15" for hour in range(18, 24))
    csv = "timestamp,perangkat,energi_wh\n" + "\n".join(lines) + "\n"
    result = await _preview_and_commit(client, session["site_id"], session["auth"], csv, ANSWERED)
    assert result["rows_added"] == 12
    body = await _summary(client, session["site_id"], session["auth"])
    assert body["energy_kwh"] == "0.330" and body["origins"] == ["import"]
    assert body["window"]["timezone"] == "Asia/Jakarta"
    assert body["coverage"] == {"minimum": "0.250", "concurrent": "0.000", "allocated_estimate": False}
    assert body["latest_measurement_at"] == "2026-10-20T17:00:00Z"
    assert all(row["gaps"] for row in body["assets"])
    assert {source["state"] for source in body["source_freshness"]} == {"historical"}
    assert {source["origin"] for source in body["source_freshness"]} == {"import"}
    assert {source["historical_range"]["start"] for source in body["source_freshness"]} == {
        "2026-10-19T23:00:00Z",
        "2026-10-20T11:00:00Z",
    }
    assert max(source["last_capture_at"] for source in body["source_freshness"]) == body["latest_measurement_at"]
