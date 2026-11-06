"""Import preview through the real application over real Postgres."""

import hashlib
import json
import logging
from collections.abc import AsyncIterator, Callable, Iterator
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

import pytest
from httpx import AsyncClient

from app.assets.model.models import MeasurementKind, SourceModel, SourceOrigin, TransportStatus
from app.core.database import get_session_factory
from app.imports.service.mapping import source_label
from app.measurements.dependencies import build_ingest_service
from app.measurements.model.models import ReadingInput
from app.sites.repository.sqlalchemy.repository import SqlAlchemySiteRepository
from tests.integration.conftest import (
    execute,
    make_asset,
    make_binding,
    make_import,
    make_principal,
    make_site,
    start_demo,
)

pytestmark = pytest.mark.integration

FAKE_SECRET = "Bearer RAHASIA-PALSU-123"
SCOPE = {"scope": "disjoint"}
ANSWERED = {"scope": "disjoint", "timezone_confirmed": True}
INTERVAL_HEADER = "interval_start,interval_end,asset,energy_wh"
ONE_HOUR = "2026-10-20T00:00:00+07:00,2026-10-20T01:00:00+07:00"
OFFSET_CSV = (
    "interval_start,interval_end,asset,energy_wh\n"
    "2026-10-20T00:00:00+07:00,2026-10-20T01:00:00+07:00,Router,10\n"
    "2026-10-20T01:00:00+07:00,2026-10-20T02:00:00+07:00,Router,12.5\n"
)
NAIVE_CSV = "timestamp,asset,energy_wh\n2026-10-20 00:00,Router,10\n2026-10-20 01:00,Router,12\n"
TOO_LARGE_MESSAGE = (
    "Berkas melebihi batas impor. Perkecil menjadi paling besar 10 MiB dan 150.000 baris data lalu coba lagi."
)
STRUCTURE_MESSAGE = "Struktur berkas belum dapat dibaca. Perbaiki hal yang disebutkan lalu coba lagi."
REQUEST_MESSAGE = "Permintaan belum dapat diproses. Periksa isian Anda lalu coba lagi."
TABLES = {
    "measurements": "SELECT count(*) FROM measurements m JOIN sources s ON s.id = m.source_id WHERE s.site_id = :site",
    "sources": "SELECT count(*) FROM sources WHERE site_id = :site",
    "assets": "SELECT count(*) FROM assets WHERE site_id = :site",
    "bindings": "SELECT count(*) FROM bindings WHERE site_id = :site",
    "asset_relations": "SELECT count(*) FROM asset_relations WHERE site_id = :site",
    "audit_events": "SELECT count(*) FROM audit_events WHERE site_id = :site",
}


def csv10(bad: int = 0, *, changed: int | None = None) -> str:
    """Build AT-30's file: ten hourly Router rows.

    Args:
        bad (int, optional): How many leading rows are negative. Defaults to 0.
        changed (int | None, optional): An hour whose value becomes 11. Defaults to None.

    Returns:
        str: The file text.
    """
    lines = []
    for hour in range(10):
        value = "-1" if hour < bad else "11" if hour == changed else "10"
        lines.append(f"2026-10-20 {hour:02}:00,Router,{value}")
    return "timestamp,perangkat,energi_wh\n" + "\n".join(lines) + "\n"


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


async def _post(
    client: AsyncClient,
    site: UUID,
    headers: dict[str, str],
    text: str | bytes | None,
    mapping: dict | None = None,
    *,
    file_name: str = "data.csv",
) -> tuple[int, dict]:
    files = {"mapping": (None, json.dumps({} if mapping is None else mapping))}
    if text is not None:
        files["file"] = (file_name, text.encode() if isinstance(text, str) else text, "text/csv")
    response = await client.post(f"/api/v1/sites/{site}/imports/preview", files=files, headers=headers)
    return response.status_code, response.json()


async def _paste(
    client: AsyncClient, site: UUID, headers: dict[str, str], text: str, mapping: dict
) -> tuple[int, dict]:
    files = {"text": (None, text), "mapping": (None, json.dumps(mapping))}
    response = await client.post(f"/api/v1/sites/{site}/imports/preview", files=files, headers=headers)
    return response.status_code, response.json()


async def _table_counts(site: UUID) -> dict[str, int]:
    return {name: (await execute(sql, site=site))[0][0] for name, sql in TABLES.items()}


async def _revisions(site: UUID) -> tuple:
    return (await execute("SELECT measurement_revision, binding_revision FROM sites WHERE id = :site", site=site))[0]


async def _import_count(site: UUID) -> int:
    return (await execute("SELECT count(*) FROM imports WHERE site_id = :site", site=site))[0][0]


def _reconciles(body: dict) -> bool:
    parts = ("accepted_rows", "invalid_rows", "duplicate_rows", "conflict_rows", "pending_rows")
    return sum(body[part] for part in parts) == body["total_rows"]


# --- saved ---------------------------------------------------------------------------------------------------------


async def test_saved_preview_on_an_empty_demo_session(client: AsyncClient) -> None:
    """
    Condition:
    - A real demo session on the ``empty`` scenario posts an offset file with scope answered.

    Expected:
    - 201 with stored counts, not blocked, and a read from a new session returns the same preview, so it survives a
      restart.
    """
    session = await start_demo(client, "empty")

    status, body = await _post(client, session["site_id"], session["auth"], OFFSET_CSV, SCOPE)

    assert status == 201, body
    assert (body["status"], body["blocked"], body["total_rows"], body["accepted_rows"]) == ("previewed", False, 2, 2)
    assert body["questions"] == []
    assert _reconciles(body)
    read = await client.get(f"/api/v1/imports/{body['id']}", headers=session["auth"])
    assert read.status_code == 200
    assert read.json() == body


async def test_saved_preview_changes_nothing_else(client: AsyncClient, owner: tuple[UUID, dict]) -> None:
    """
    Condition:
    - A preview of a valid file.

    Expected:
    - FR-004: measurements, sources, assets, bindings, relations, audit events and both revisions are unchanged.
    """
    site, headers = owner
    before = await _table_counts(site), await _revisions(site)

    status, _ = await _post(client, site, headers, OFFSET_CSV, SCOPE)

    assert status == 201
    assert (await _table_counts(site), await _revisions(site)) == before


async def test_saved_preview_stores_what_commit_needs(client: AsyncClient, owner: tuple[UUID, dict]) -> None:
    """
    Condition:
    - A preview of a valid file named with path segments and a control character.

    Expected:
    - The name is its last segment, the hash covers the file's bytes, both revisions and a 24-hour expiry are stored,
      and each accepted row holds the data 026 needs, with times in UTC.
    """
    site, headers = owner

    status, body = await _post(client, site, headers, OFFSET_CSV, SCOPE, file_name="berkas/a/b\x7fc.csv")

    assert status == 201
    assert body["file_name"] == "bc.csv"
    stored = (
        await execute(
            "SELECT content_sha256, measurement_revision, binding_revision, expires_at - created_at, idempotency_key,"
            " period_start, period_end FROM imports WHERE id = :id",
            id=body["id"],
        )
    )[0]
    assert stored[0] == hashlib.sha256(OFFSET_CSV.encode()).hexdigest()
    assert stored[1:3] == (0, 0)
    assert timedelta(hours=23) < stored[3] <= timedelta(hours=24, seconds=5)
    assert stored[4] is None
    assert stored[5] == datetime(2026, 10, 19, 17, tzinfo=UTC)
    assert stored[6] == datetime(2026, 10, 19, 19, tzinfo=UTC)
    assert body["period"] == {"start_date": "2026-10-20", "end_date": "2026-10-20", "timezone": "Asia/Jakarta"}
    rows = await execute(
        "SELECT data_row, file_line, status, parsed FROM import_rows WHERE import_id = :id ORDER BY data_row",
        id=body["id"],
    )
    assert [row[:3] for row in rows] == [(1, 2, "accepted"), (2, 3, "accepted")]
    parsed = rows[1][3]
    assert parsed == {
        "stream_key": "router",
        "asset_name": "Router",
        "kind": "interval_energy",
        "unit": "Wh",
        "value": "12.500",
        "identity_key": parsed["identity_key"],
        "interval_start": "2026-10-19T18:00:00Z",
        "interval_end": "2026-10-19T19:00:00Z",
        "measured_at": None,
        "raw_value": "12.5",
        "raw_start": "2026-10-20T01:00:00+07:00",
        "raw_end": "2026-10-20T02:00:00+07:00",
    }
    assert parsed["identity_key"].startswith("i:interval_energy:")


async def test_saved_preview_never_stores_the_file(client: AsyncClient, owner: tuple[UUID, dict]) -> None:
    """
    Condition:
    - A file with an extra column holding a marker.

    Expected:
    - The marker is stored nowhere, because only row results are staged.
    """
    site, headers = owner
    text = (
        "interval_start,interval_end,asset,energy_wh,catatan\n"
        "2026-10-20T00:00:00+07:00,2026-10-20T01:00:00+07:00,Router,10,PENANDA-BERKAS\n"
    )

    status, body = await _post(client, site, headers, text, SCOPE)

    assert status == 201
    stored = await execute("SELECT i::text FROM imports i WHERE id = :id", id=body["id"])
    rows = await execute("SELECT r::text FROM import_rows r WHERE import_id = :id", id=body["id"])
    assert "PENANDA-BERKAS" not in stored[0][0] + rows[0][0]


async def test_saved_paste_uses_its_default_name(client: AsyncClient, owner: tuple[UUID, dict]) -> None:
    """
    Condition:
    - CSV pasted through ``text``.

    Expected:
    - It previews as ``tempelan.csv``.
    """
    site, headers = owner

    status, body = await _paste(client, site, headers, OFFSET_CSV, SCOPE)

    assert status == 201
    assert (body["file_name"], body["accepted_rows"]) == ("tempelan.csv", 2)


async def test_saved_paste_over_one_mebibyte_is_accepted(client: AsyncClient, owner: tuple[UUID, dict]) -> None:
    """
    Condition:
    - D8: a paste larger than Starlette's default 1 MiB part limit.

    Expected:
    - It is accepted, because the route raises that limit to the body cap.
    """
    site, headers = owner
    start = datetime(2020, 1, 1, tzinfo=UTC)
    lines = [f"{(start + timedelta(hours=hour)).isoformat()},Router,1" for hour in range(40_000)]
    text = "timestamp,asset,energy_wh\n" + "\n".join(lines) + "\n"
    assert len(text) > 1024 * 1024

    status, body = await _paste(client, site, headers, text, SCOPE)

    assert status == 201, body
    assert body["total_rows"] == 40_000


async def test_saved_naive_times_ask_then_read_in_the_site_zone(client: AsyncClient, owner: tuple[UUID, dict]) -> None:
    """
    Condition:
    - Naive timestamps, unanswered and then answered.

    Expected:
    - Unanswered: 024's question, blocked, every row pending and nothing staged. Answered: accepted rows, times in UTC.
    """
    site, headers = owner

    status, asked = await _post(client, site, headers, NAIVE_CSV, SCOPE)

    assert status == 201
    assert asked["blocked"] is True
    assert asked["block_reasons"] == ["Lengkapi pemetaan terlebih dahulu."]
    assert asked["pending_rows"] == 2
    assert asked["accepted_rows"] == 0
    assert _reconciles(asked)
    assert asked["questions"][0]["kind"] == "timezone"
    assert (
        asked["questions"][0]["message"]
        == "Waktu tanpa zona waktu. Konfirmasi bahwa waktu dibaca sebagai Asia/Jakarta."
    )
    assert (await execute("SELECT count(*) FROM import_rows WHERE import_id = :id", id=asked["id"]))[0][0] == 0

    status, answered = await _post(client, site, headers, NAIVE_CSV, ANSWERED)

    assert status == 201
    assert (answered["blocked"], answered["accepted_rows"], answered["pending_rows"]) == (False, 2, 0)
    assert "Waktu tanpa offset dibaca sebagai Asia/Jakarta." in answered["assumptions"]
    parsed = await execute("SELECT parsed FROM import_rows WHERE import_id = :id AND data_row = 1", id=answered["id"])
    assert parsed[0][0]["interval_start"] == "2026-10-19T17:00:00Z"


async def test_saved_unanswered_scope_blocks(client: AsyncClient, owner: tuple[UUID, dict]) -> None:
    """
    Condition:
    - A clean offset file with no scope answer.

    Expected:
    - The scope question is open and the preview is blocked.
    """
    site, headers = owner

    status, body = await _post(client, site, headers, OFFSET_CSV)

    assert status == 201
    assert [question["kind"] for question in body["questions"]] == ["scope"]
    assert body["questions"][0]["message"] == "Pilih apakah beban perangkat dalam berkas ini terukur terpisah."
    assert body["blocked"] is True


@pytest.mark.parametrize(
    ("bad", "accepted", "blocked", "reasons"),
    [(2, 8, False, []), (3, 7, True, ["Impor diblokir: 3 dari 10 baris tidak valid."])],
    ids=["two_of_ten", "three_of_ten"],
)
async def test_saved_at_30(
    client: AsyncClient, owner: tuple[UUID, dict], bad: int, accepted: int, blocked: bool, reasons: list[str]
) -> None:
    """
    Condition:
    - AT-30's file, answered, with two or three negative rows.

    Expected:
    - The exact counts and block reason, and the first error's exact message.
    """
    site, headers = owner

    status, body = await _post(client, site, headers, csv10(bad), ANSWERED)

    assert status == 201
    assert (body["accepted_rows"], body["invalid_rows"], body["blocked"]) == (accepted, bad, blocked)
    assert body["needs_acknowledgment"] is not blocked
    assert body["block_reasons"] == reasons
    assert _reconciles(body)
    assert body["errors"][0] == {
        "data_row": 1,
        "file_line": 2,
        "field": "energi_wh",
        "reason": "negative",
        "message": "Baris data 1, energi_wh: gunakan angka 0 atau lebih.",
    }


async def test_saved_at_32_long_name(client: AsyncClient, owner: tuple[UUID, dict]) -> None:
    """
    Condition:
    - AT-32: a 61-character asset name.

    Expected:
    - One invalid row whose message says the name is not cut, and it raises no asset question.
    """
    site, headers = owner
    text = f"{INTERVAL_HEADER}\n{ONE_HOUR},{'X' * 61},1\n"

    status, body = await _post(client, site, headers, text, SCOPE)

    assert status == 201
    assert body["invalid_rows"] == 1
    assert "tidak dipotong" in body["errors"][0]["message"]
    assert body["mapping"]["streams"] == []


async def test_saved_mapping_records_columns_and_answers(client: AsyncClient, owner: tuple[UUID, dict]) -> None:
    """
    Condition:
    - A confirmed power file with a timestamp column.

    Expected:
    - ``mapping`` holds the answers, the zone, and the asset, time and value headers with the unit.
    """
    site, headers = owner
    text = "waktu,alat,daya_w,sumber\n2026-10-20 00:00,Pompa,100,meter-1\n2026-10-20 01:00,Pompa,100,meter-1\n"
    answers = ANSWERED | {"power_meaning": "average"}

    status, body = await _post(client, site, headers, text, answers)

    assert status == 201
    mapping = body["mapping"]
    assert mapping["value_kind"] == "average_power"
    assert mapping["power_meaning"] == "average"
    assert mapping["timezone"] == "Asia/Jakarta"
    assert mapping["timezone_confirmed"] is True
    assert mapping["interval_minutes"] == {}
    assert mapping["scope"] == "disjoint"
    assert mapping["columns"] == {
        "asset": "alat",
        "source": "sumber",
        "timestamp": "waktu",
        "interval_start": None,
        "interval_end": None,
        "value": "daya_w",
        "unit": "W",
    }


async def test_saved_formula_names_stay_verbatim(client: AsyncClient, owner: tuple[UUID, dict]) -> None:
    """
    Condition:
    - An asset name that looks like a spreadsheet formula.

    Expected:
    - It is stored and returned as written, because rendering is the client's concern.
    """
    site, headers = owner
    text = f'{INTERVAL_HEADER}\n{ONE_HOUR},"=SUM(A1:A9)",1\n'

    status, body = await _post(client, site, headers, text, SCOPE)

    assert status == 201
    assert body["mapping"]["streams"][0]["asset_name"] == "=SUM(A1:A9)"
    parsed = await execute("SELECT parsed FROM import_rows WHERE import_id = :id", id=body["id"])
    assert parsed[0][0]["asset_name"] == "=SUM(A1:A9)"


async def test_saved_competing_value_columns_ask_then_read_the_chosen_one(
    client: AsyncClient, owner: tuple[UUID, dict]
) -> None:
    """
    Condition:
    - A file with an energy and a power column, unanswered and then answered with energy.

    Expected:
    - Unanswered: 024's question and every row pending, with no value header named. Answered: the energy column's rows
      are accepted, and ``mapping`` names that column.
    """
    site, headers = owner
    text = f"{INTERVAL_HEADER},daya_w\n{ONE_HOUR},Pompa,1,100\n"

    _, asked = await _post(client, site, headers, text, SCOPE)
    status, answered = await _post(client, site, headers, text, SCOPE | {"value_kind": "interval_energy"})

    assert asked["questions"][0]["kind"] == "value_kind"
    assert (asked["blocked"], asked["pending_rows"]) == (True, 1)
    assert asked["mapping"]["columns"]["value"] is None
    assert status == 201
    assert (answered["blocked"], answered["accepted_rows"]) == (False, 1)
    assert answered["mapping"]["columns"]["value"] == "energy_wh"


async def test_saved_instantaneous_power_blocks_on_its_question(client: AsyncClient, owner: tuple[UUID, dict]) -> None:
    """
    Condition:
    - A power file answered as instantaneous. 024 keeps these rows pending with kind ``average_power``.

    Expected:
    - The question stays open with 024's refusal, every row stays pending, and none is staged as accepted.
    """
    site, headers = owner
    text = "interval_start,interval_end,asset,daya_w\n2026-10-20T00:00:00+07:00,2026-10-20T00:30:00+07:00,Pompa,100\n"

    status, body = await _post(client, site, headers, text, SCOPE | {"power_meaning": "instantaneous"})

    assert status == 201
    assert body["blocked"] is True
    assert (body["pending_rows"], body["accepted_rows"]) == (1, 0)
    assert body["questions"][0]["kind"] == "power_meaning"
    assert "Daya sesaat tidak dapat diubah menjadi energi" in body["questions"][0]["message"]
    assert (await execute("SELECT count(*) FROM import_rows WHERE import_id = :id", id=body["id"]))[0][0] == 0


async def test_saved_power_with_meaning_unanswered_stays_pending(client: AsyncClient, owner: tuple[UUID, dict]) -> None:
    """
    Condition:
    - AT-27a: a power file whose meaning is unanswered, then confirmed as average.

    Expected:
    - Blocked on the question first, then 100 W over 30 minutes stages as an accepted row.
    """
    site, headers = owner
    text = (
        "interval_start,interval_end,asset,average_power_w\n"
        "2026-10-20T00:00:00+07:00,2026-10-20T00:30:00+07:00,Pompa,100\n"
    )

    _, asked = await _post(client, site, headers, text, SCOPE)
    status, confirmed = await _post(client, site, headers, text, SCOPE | {"power_meaning": "average"})

    assert (asked["blocked"], asked["pending_rows"]) == (True, 1)
    assert status == 201
    assert (confirmed["blocked"], confirmed["accepted_rows"]) == (False, 1)


async def test_saved_stream_of_invalid_rows_still_asks_its_duration(
    client: AsyncClient, owner: tuple[UUID, dict]
) -> None:
    """
    Condition:
    - A one-row stream whose only row has an invalid value. 024 still asks for its duration.

    Expected:
    - The question is returned and blocks, the row counts as invalid, and nothing fails on the stream having no rows
      to stage.
    """
    site, headers = owner
    text = "timestamp,asset,energy_wh\n2026-10-20T00:00:00+07:00,Pompa,dua\n"

    status, body = await _post(client, site, headers, text, SCOPE)

    assert status == 201
    assert [question["kind"] for question in body["questions"]] == ["interval_duration"]
    assert body["questions"][0]["streams"] == ["pompa"]
    assert (body["blocked"], body["invalid_rows"], body["pending_rows"]) == (True, 1, 0)
    assert _reconciles(body)


async def test_saved_out_of_range_duration_for_an_absent_stream_opens_the_question(
    client: AsyncClient, owner: tuple[UUID, dict]
) -> None:
    """
    Condition:
    - A declared duration out of range, keyed to a stream the file does not hold.

    Expected:
    - 024's question opens and blocks, instead of a 422 or a failure, and the stored answer keeps the key.
    """
    site, headers = owner

    status, body = await _post(client, site, headers, OFFSET_CSV, SCOPE | {"interval_minutes": {"tidak-ada": 0}})

    assert status == 201
    assert body["questions"][0]["kind"] == "interval_duration"
    assert body["questions"][0]["streams"] == ["tidak-ada"]
    assert body["questions"][0]["message"] == "Panjang interval harus bilangan bulat 1–1440 menit."
    assert body["blocked"] is True
    assert body["mapping"]["interval_minutes"] == {"tidak-ada": 0}


async def test_saved_huge_value_cell_is_stored_and_returned_bounded(
    client: AsyncClient, owner: tuple[UUID, dict]
) -> None:
    """
    Condition:
    - A value cell of 100,000 digits, which 024's ``value_too_large`` echoes in full.

    Expected:
    - The stored and returned message stays within the bound, and keeps the row prefix and the correction.
    """
    site, headers = owner
    text = (
        "interval_start,interval_end,asset,energy_wh\n"
        f"2026-10-20T00:00:00+07:00,2026-10-20T01:00:00+07:00,Pompa,{'9' * 100_000}\n"
    )

    status, body = await _post(client, site, headers, text, SCOPE)

    assert status == 201
    error = body["errors"][0]
    assert error["reason"] == "value_too_large"
    assert len(error["message"]) <= 500
    assert error["message"].startswith('Baris data 1, energy_wh: angka "999')
    assert error["message"].endswith('" terlalu besar. Periksa nilai dan satuannya.')
    stored = await execute("SELECT length(message) FROM import_rows WHERE import_id = :id", id=body["id"])
    assert stored[0][0] <= 500


async def test_saved_row_message_echoes_a_cell_only_to_its_owner(
    client: AsyncClient, owner: tuple[UUID, dict], caplog: pytest.LogCaptureFixture
) -> None:
    """
    Condition:
    - A value cell holding a fake bearer token, which 024's message echoes.

    Expected:
    - The owner's own preview shows the cell, and no log line or record does.
    """
    site, headers = owner
    text = f"{INTERVAL_HEADER}\n{ONE_HOUR},A,{FAKE_SECRET}\n"

    status, body = await _post(client, site, headers, text, SCOPE)

    assert status == 201
    assert FAKE_SECRET in body["errors"][0]["message"]
    assert "RAHASIA-PALSU-123" not in caplog.text


# --- failures ------------------------------------------------------------------------------------------------------


def _assert_failure(
    status: int,
    body: dict,
    caplog: pytest.LogCaptureFixture,
    *,
    expected_status: int,
    code: str,
    message: str,
    internal: str,
) -> dict:
    assert status == expected_status, body
    error = body["error"]
    assert error["code"] == code
    assert error["message"] == message
    assert error["recovery"] == {"retryable": False}
    records = _records(caplog)
    assert len(records) == 1
    assert records[0]["reference_id"] == error["request_id"]
    assert records[0]["code"] == internal
    assert "RAHASIA-PALSU-123" not in json.dumps(body)
    assert "RAHASIA-PALSU-123" not in caplog.text
    return error


def _padded_file(size: int) -> bytes:
    """Build a valid file of an exact byte size, using an ignored column so rows stay few and cheap.

    Args:
        size (int): Bytes wanted.

    Returns:
        bytes: The file.
    """
    header = b"interval_start,interval_end,asset,energy_wh,catatan\n"
    body = bytearray(header)
    start = datetime(2026, 1, 1, tzinfo=UTC)
    hour = 0
    while True:
        first = (start + timedelta(hours=hour)).isoformat().encode()
        second = (start + timedelta(hours=hour + 1)).isoformat().encode()
        prefix = first + b"," + second + b",Router,1,"
        left = size - len(body) - len(prefix) - 1
        if left <= 100_000:
            body += prefix + b"x" * left + b"\n"
            assert len(body) == size
            return bytes(body)
        body += prefix + b"x" * 90_000 + b"\n"
        hour += 1


async def test_failure_file_one_byte_over_the_limit(
    client: AsyncClient, owner: tuple[UUID, dict], caplog: pytest.LogCaptureFixture
) -> None:
    """
    Condition:
    - A file of 10,485,761 bytes, which still fits the body cap.

    Expected:
    - 413 with the parser's exact size, one record, and nothing stored.
    """
    site, headers = owner

    status, body = await _post(client, site, headers, _padded_file(10_485_761), SCOPE)

    error = _assert_failure(
        status,
        body,
        caplog,
        expected_status=413,
        code="IMPORT_TOO_LARGE",
        message=TOO_LARGE_MESSAGE,
        internal="APP-IMPORT-TOO-LARGE",
    )
    assert error["details"] == [{"loc": ["file"], "msg": "Ukuran 10,1 MiB melebihi batas 10 MiB.", "type": "too_large"}]
    assert await _import_count(site) == 0


async def test_failure_file_of_exactly_the_limit_is_accepted(client: AsyncClient, owner: tuple[UUID, dict]) -> None:
    """
    Condition:
    - A file of exactly 10,485,760 bytes.

    Expected:
    - It is a stored preview, not a failure.
    """
    site, headers = owner

    status, body = await _post(client, site, headers, _padded_file(10_485_760), SCOPE)

    assert status == 201, body
    assert body["total_rows"] > 0


async def test_failure_too_many_rows(
    client: AsyncClient, owner: tuple[UUID, dict], caplog: pytest.LogCaptureFixture
) -> None:
    """
    Condition:
    - 150,001 data rows within the byte limit, one holding a fake token.

    Expected:
    - 413 with the exact count, nothing stored, and the token nowhere.
    """
    site, headers = owner
    text = f"timestamp,asset,energy_wh\n{FAKE_SECRET},A,1\n" + "2026-10-20 00:00,A,1\n" * 150_000

    status, body = await _post(client, site, headers, text, SCOPE)

    error = _assert_failure(
        status,
        body,
        caplog,
        expected_status=413,
        code="IMPORT_TOO_LARGE",
        message=TOO_LARGE_MESSAGE,
        internal="APP-IMPORT-TOO-LARGE",
    )
    assert error["details"] == [
        {"loc": ["file"], "msg": "150001 baris data melebihi batas 150.000 baris.", "type": "too_many_rows"}
    ]
    assert await _import_count(site) == 0


async def test_failure_body_over_the_cap_is_not_fully_read(
    client: AsyncClient, owner: tuple[UUID, dict], caplog: pytest.LogCaptureFixture
) -> None:
    """
    Condition:
    - A 20 MiB multipart body, delivered in chunks.

    Expected:
    - 413 naming the limit, with the size unknown, and reading stops near the cap instead of consuming the body.
    """
    site, headers = owner
    chunk = b"x" * (64 * 1024)
    chunks = 20 * 1024 * 1024 // len(chunk)
    sent = {"bytes": 0}

    async def body_stream() -> AsyncIterator[bytes]:
        opening = (
            b'--limit\r\nContent-Disposition: form-data; name="file"; filename="a.csv"\r\n'
            b"Content-Type: text/csv\r\n\r\n"
        )
        sent["bytes"] += len(opening)
        yield opening
        for _ in range(chunks):
            sent["bytes"] += len(chunk)
            yield chunk
        yield b"\r\n--limit--\r\n"

    response = await client.post(
        f"/api/v1/sites/{site}/imports/preview",
        content=body_stream(),
        headers=headers | {"Content-Type": "multipart/form-data; boundary=limit"},
    )

    error = _assert_failure(
        response.status_code,
        response.json(),
        caplog,
        expected_status=413,
        code="IMPORT_TOO_LARGE",
        message=TOO_LARGE_MESSAGE,
        internal="APP-IMPORT-TOO-LARGE",
    )
    assert error["details"] == [{"loc": ["file"], "msg": "Ukuran berkas melebihi batas 10 MiB.", "type": "too_large"}]
    assert sent["bytes"] < 11 * 1024 * 1024
    assert await _import_count(site) == 0


async def test_failure_unreadable_header_lists_each_problem(
    client: AsyncClient, owner: tuple[UUID, dict], caplog: pytest.LogCaptureFixture
) -> None:
    """
    Condition:
    - A file with the headers ``foo,bar`` and a row holding a fake token.

    Expected:
    - 400 with three details in order, naming only aliases, and nothing stored.
    """
    site, headers = owner

    status, body = await _post(client, site, headers, f"foo,bar\n{FAKE_SECRET},2\n", SCOPE)

    error = _assert_failure(
        status,
        body,
        caplog,
        expected_status=400,
        code="IMPORT_INVALID",
        message=STRUCTURE_MESSAGE,
        internal="APP-IMPORT-STRUCTURE",
    )
    assert [(detail["loc"], detail["type"]) for detail in error["details"]] == [
        (["file"], "missing_asset"),
        (["file"], "missing_time"),
        (["file"], "missing_value"),
    ]
    assert error["details"][0]["msg"].startswith("Kolom perangkat tidak ditemukan.")
    assert await _import_count(site) == 0


async def test_failure_a_structural_line_is_named_in_the_location(
    client: AsyncClient, owner: tuple[UUID, dict], caplog: pytest.LogCaptureFixture
) -> None:
    """
    Condition:
    - An unterminated quote on file line 2.

    Expected:
    - 400 whose detail names the line in ``loc``.
    """
    site, headers = owner

    status, body = await _post(client, site, headers, 'timestamp,asset,energy_wh\n"2026-10-20 00:00,A,1\n', SCOPE)

    error = _assert_failure(
        status,
        body,
        caplog,
        expected_status=400,
        code="IMPORT_INVALID",
        message=STRUCTURE_MESSAGE,
        internal="APP-IMPORT-STRUCTURE",
    )
    assert error["details"][0]["loc"] == ["file", "line", 2]
    assert error["details"][0]["type"] == "quote_unclosed"


async def test_failure_not_utf8(
    client: AsyncClient, owner: tuple[UUID, dict], caplog: pytest.LogCaptureFixture
) -> None:
    """
    Condition:
    - Bytes that are not UTF-8, beside a fake token.

    Expected:
    - 400 with reason ``not_utf8`` and nothing stored.
    """
    site, headers = owner
    content = f"timestamp,asset,energy_wh\n{FAKE_SECRET},A,1\n".encode() + b"\xff\xfe\n"

    status, body = await _post(client, site, headers, content, SCOPE)

    error = _assert_failure(
        status,
        body,
        caplog,
        expected_status=400,
        code="IMPORT_INVALID",
        message=STRUCTURE_MESSAGE,
        internal="APP-IMPORT-STRUCTURE",
    )
    assert [detail["type"] for detail in error["details"]] == ["not_utf8"]
    assert await _import_count(site) == 0


async def test_failure_no_file_and_no_text(
    client: AsyncClient, owner: tuple[UUID, dict], caplog: pytest.LogCaptureFixture
) -> None:
    """
    Condition:
    - A multipart body holding only the mapping.

    Expected:
    - 400 with reason ``empty_input`` and nothing stored.
    """
    site, headers = owner

    status, body = await _post(client, site, headers, None, SCOPE)

    error = _assert_failure(
        status,
        body,
        caplog,
        expected_status=400,
        code="IMPORT_INVALID",
        message=STRUCTURE_MESSAGE,
        internal="APP-IMPORT-STRUCTURE",
    )
    assert [detail["type"] for detail in error["details"]] == ["empty_input"]
    assert await _import_count(site) == 0


async def test_failure_malformed_multipart_uses_the_envelope(
    client: AsyncClient, owner: tuple[UUID, dict], caplog: pytest.LogCaptureFixture
) -> None:
    """
    Condition:
    - A multipart request with no boundary.

    Expected:
    - The framework's refusal becomes the normal envelope, with nothing stored.
    """
    site, headers = owner

    response = await client.post(
        f"/api/v1/sites/{site}/imports/preview",
        content=b"tidak terbaca",
        headers=headers | {"Content-Type": "multipart/form-data"},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "BAD_REQUEST"
    assert _records(caplog)[0]["reference_id"] == response.json()["error"]["request_id"]
    assert await _import_count(site) == 0


async def test_failure_a_request_that_is_not_a_form_is_empty_input(
    client: AsyncClient, owner: tuple[UUID, dict], caplog: pytest.LogCaptureFixture
) -> None:
    """
    Condition:
    - A JSON body, which holds no form parts.

    Expected:
    - The same ``empty_input``, with nothing stored.
    """
    site, headers = owner

    response = await client.post(f"/api/v1/sites/{site}/imports/preview", json={"text": "x"}, headers=headers)

    error = _assert_failure(
        response.status_code,
        response.json(),
        caplog,
        expected_status=400,
        code="IMPORT_INVALID",
        message=STRUCTURE_MESSAGE,
        internal="APP-IMPORT-STRUCTURE",
    )
    assert [detail["type"] for detail in error["details"]] == ["empty_input"]


async def test_failure_two_files(
    client: AsyncClient, owner: tuple[UUID, dict], caplog: pytest.LogCaptureFixture
) -> None:
    """
    Condition:
    - Two file parts in one request.

    Expected:
    - 400 with the request error, because a preview covers one file.
    """
    site, headers = owner
    files = [("file", ("a.csv", OFFSET_CSV.encode(), "text/csv")), ("file", ("b.csv", OFFSET_CSV.encode(), "text/csv"))]

    response = await client.post(f"/api/v1/sites/{site}/imports/preview", files=files, headers=headers)

    _assert_failure(
        response.status_code,
        response.json(),
        caplog,
        expected_status=400,
        code="BAD_REQUEST",
        message=REQUEST_MESSAGE,
        internal="APP-REQUEST-INVALID",
    )
    assert await _import_count(site) == 0


async def test_failure_file_and_text_together(
    client: AsyncClient, owner: tuple[UUID, dict], caplog: pytest.LogCaptureFixture
) -> None:
    """
    Condition:
    - Both a file part and a text field, the text holding a fake token.

    Expected:
    - 400 with the request error, and nothing stored.
    """
    site, headers = owner
    files = {"file": ("a.csv", OFFSET_CSV.encode(), "text/csv"), "text": (None, FAKE_SECRET)}

    response = await client.post(f"/api/v1/sites/{site}/imports/preview", files=files, headers=headers)

    _assert_failure(
        response.status_code,
        response.json(),
        caplog,
        expected_status=400,
        code="BAD_REQUEST",
        message=REQUEST_MESSAGE,
        internal="APP-REQUEST-INVALID",
    )
    assert await _import_count(site) == 0


@pytest.mark.parametrize(
    ("mapping", "location", "kind"),
    [
        ("{bukan json", ["body", "mapping"], "json_invalid"),
        (json.dumps({"scope": FAKE_SECRET}), ["body", "mapping", "scope"], "enum"),
        (json.dumps({"interval_minutes": {"a": 1.5}}), ["body", "mapping", "interval_minutes", "a"], "int_from_float"),
        (json.dumps({"asset_map": {"a": "bukan-uuid"}}), ["body", "mapping", "asset_map", "a"], None),
        (json.dumps({"interval_minutes": {"a\u0000b": 60}}), ["body", "mapping", "interval_minutes", "a\u0000b"], None),
    ],
    ids=["not_json", "unknown_scope", "fractional_minutes", "bad_asset_id", "nul_in_a_key"],
)
async def test_failure_bad_mapping(
    client: AsyncClient,
    owner: tuple[UUID, dict],
    caplog: pytest.LogCaptureFixture,
    mapping: str,
    location: list[str],
    kind: str | None,
) -> None:
    """
    Condition:
    - A mapping that is not valid JSON or does not validate, one holding a fake token.

    Expected:
    - The normal 422 naming the field, with no submitted value, and nothing stored.
    """
    site, headers = owner
    files = {"file": ("a.csv", OFFSET_CSV.encode(), "text/csv"), "mapping": (None, mapping)}

    response = await client.post(f"/api/v1/sites/{site}/imports/preview", files=files, headers=headers)

    error = _assert_failure(
        response.status_code,
        response.json(),
        caplog,
        expected_status=422,
        code="VALIDATION_FAILED",
        message="Ada isian yang belum valid. Perbaiki isian tersebut lalu coba lagi.",
        internal="APP-UNKNOWN",
    )
    assert error["details"][0]["loc"][: len(location)] == location
    if kind is not None:
        assert error["details"][0]["type"] == kind
    assert await _import_count(site) == 0


@pytest.mark.parametrize(
    "files",
    [
        {"mapping": ("mapping.json", b"{}", "application/json"), "text": (None, OFFSET_CSV)},
        {"file": (None, OFFSET_CSV)},
        {"text": ("a.csv", OFFSET_CSV.encode(), "text/csv")},
    ],
    ids=["mapping_as_a_file", "file_as_a_field", "text_as_a_file"],
)
async def test_failure_a_part_of_the_wrong_shape(
    client: AsyncClient, owner: tuple[UUID, dict], caplog: pytest.LogCaptureFixture, files: dict
) -> None:
    """
    Condition:
    - A part sent as a file where a field belongs, or the other way round.

    Expected:
    - 400 with the request error, and nothing stored.
    """
    site, headers = owner

    response = await client.post(f"/api/v1/sites/{site}/imports/preview", files=files, headers=headers)

    _assert_failure(
        response.status_code,
        response.json(),
        caplog,
        expected_status=400,
        code="BAD_REQUEST",
        message=REQUEST_MESSAGE,
        internal="APP-REQUEST-INVALID",
    )
    assert await _import_count(site) == 0


# --- lifecycle -----------------------------------------------------------------------------------------------------


def _with_invalid_rows(invalid: int, total: int) -> str:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    lines = []
    for index in range(total):
        begin, end = start + timedelta(hours=index), start + timedelta(hours=index + 1)
        lines.append(f"{begin.isoformat()},{end.isoformat()},Router,{'dua' if index < invalid else '1'}")
    return "interval_start,interval_end,asset,energy_wh\n" + "\n".join(lines) + "\n"


async def test_lifecycle_errors_page_by_cursor(client: AsyncClient, owner: tuple[UUID, dict]) -> None:
    """
    Condition:
    - 60 invalid rows in 400.

    Expected:
    - 50 errors inline with a cursor, the read returns the same, and the error route returns the rest in order, with
      counts always covering the whole file.
    """
    site, headers = owner

    status, body = await _post(client, site, headers, _with_invalid_rows(60, 400), SCOPE)

    assert status == 201
    assert (body["invalid_rows"], body["accepted_rows"]) == (60, 340)
    assert [error["data_row"] for error in body["errors"]] == list(range(1, 51))
    assert body["next_error_cursor"]
    read = (await client.get(f"/api/v1/imports/{body['id']}", headers=headers)).json()
    assert read["errors"] == body["errors"]
    assert read["next_error_cursor"] == body["next_error_cursor"]

    response = await client.get(
        f"/api/v1/imports/{body['id']}/errors", params={"cursor": body["next_error_cursor"]}, headers=headers
    )

    assert response.status_code == 200
    page = response.json()
    assert [error["data_row"] for error in page["items"]] == list(range(51, 61))
    assert page["next_cursor"] is None


async def test_lifecycle_error_pages_honor_their_limit(client: AsyncClient, owner: tuple[UUID, dict]) -> None:
    """
    Condition:
    - 60 invalid rows, paged 25 at a time from the start.

    Expected:
    - Three pages cover every error once, in order.
    """
    site, headers = owner
    _, body = await _post(client, site, headers, _with_invalid_rows(60, 400), SCOPE)

    found: list[int] = []
    cursor = None
    pages = 0
    while True:
        params = {"limit": 25} | ({"cursor": cursor} if cursor else {})
        page = (await client.get(f"/api/v1/imports/{body['id']}/errors", params=params, headers=headers)).json()
        found += [error["data_row"] for error in page["items"]]
        pages += 1
        cursor = page["next_cursor"]
        if cursor is None:
            break

    assert pages == 3
    assert found == list(range(1, 61))


async def test_lifecycle_a_preview_at_exactly_the_inline_limit_has_no_cursor(
    client: AsyncClient, owner: tuple[UUID, dict]
) -> None:
    """
    Condition:
    - Exactly 50 invalid rows.

    Expected:
    - All are inline and no cursor is offered.
    """
    site, headers = owner

    _, body = await _post(client, site, headers, _with_invalid_rows(50, 400), SCOPE)

    assert len(body["errors"]) == 50
    assert body["next_error_cursor"] is None


async def test_lifecycle_limit_out_of_range(
    client: AsyncClient, owner: tuple[UUID, dict], caplog: pytest.LogCaptureFixture
) -> None:
    """
    Condition:
    - An error page with ``limit=101``.

    Expected:
    - The normal 422.
    """
    site, headers = owner
    import_id = await make_import(site)

    response = await client.get(f"/api/v1/imports/{import_id}/errors", params={"limit": 101}, headers=headers)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_FAILED"
    assert _records(caplog)[0]["reference_id"] == response.json()["error"]["request_id"]


@pytest.mark.parametrize(
    "cursor", ["!!!", "bm90LWpzb24", "WyJ4Il0=", "LTE="], ids=["garbage", "text", "list", "negative"]
)
async def test_lifecycle_bad_cursor(
    client: AsyncClient, owner: tuple[UUID, dict], caplog: pytest.LogCaptureFixture, cursor: str
) -> None:
    """
    Condition:
    - A cursor this API did not issue.

    Expected:
    - 400 with the request error, its record and no retry.
    """
    site, headers = owner
    import_id = await make_import(site)

    response = await client.get(f"/api/v1/imports/{import_id}/errors", params={"cursor": cursor}, headers=headers)

    _assert_failure(
        response.status_code,
        response.json(),
        caplog,
        expected_status=400,
        code="BAD_REQUEST",
        message=REQUEST_MESSAGE,
        internal="APP-REQUEST-INVALID",
    )


async def test_lifecycle_expired_preview_reads_as_expired(client: AsyncClient, owner: tuple[UUID, dict]) -> None:
    """
    Condition:
    - A preview past its expiry, and a committed import past its expiry.

    Expected:
    - The preview reads ``expired``, and the committed import keeps its status.
    """
    site, headers = owner
    past = datetime.now(UTC) - timedelta(seconds=1)
    preview = await make_import(site, expires_at=past)
    committed = await make_import(site, status="committed", expires_at=past)

    assert (await client.get(f"/api/v1/imports/{preview}", headers=headers)).json()["status"] == "expired"
    assert (await client.get(f"/api/v1/imports/{committed}", headers=headers)).json()["status"] == "committed"


async def test_lifecycle_a_new_preview_purges_the_expired(client: AsyncClient, owner: tuple[UUID, dict]) -> None:
    """
    Condition:
    - An expired preview on another site, older than anything else in the shared database, and an expired committed
      import.

    Expected:
    - A new preview anywhere removes the expired preview and never the committed one.
    """
    site, headers = owner
    other = await make_site(await make_principal())
    ancient = datetime(1990, 1, 1, tzinfo=UTC)
    expired = await make_import(other, expires_at=ancient)
    committed = await make_import(other, status="committed", expires_at=ancient)

    status, _ = await _post(client, site, headers, OFFSET_CSV, SCOPE)

    assert status == 201
    remaining = {row[0] for row in await execute("SELECT id FROM imports WHERE site_id = :site", site=other)}
    assert expired not in remaining
    assert committed in remaining


async def test_lifecycle_the_sixth_preview_removes_the_oldest(client: AsyncClient, owner: tuple[UUID, dict]) -> None:
    """
    Condition:
    - Six previews on one site, plus one committed import.

    Expected:
    - The oldest preview is gone, five previews remain, and the committed import stays.
    """
    site, headers = owner
    committed = await make_import(site, status="committed")
    ids = []
    for _ in range(6):
        status, body = await _post(client, site, headers, OFFSET_CSV, SCOPE)
        assert status == 201
        ids.append(UUID(body["id"]))

    remaining = {row[0] for row in await execute("SELECT id FROM imports WHERE site_id = :site", site=site)}

    assert remaining == set(ids[1:]) | {committed}
    assert (await client.get(f"/api/v1/imports/{ids[0]}", headers=headers)).status_code == 404


async def test_lifecycle_ending_a_demo_session_removes_its_imports(client: AsyncClient) -> None:
    """
    Condition:
    - A demo session with a stored preview ends.

    Expected:
    - The import and its rows are gone with the workspace.
    """
    session = await start_demo(client, "empty")
    _, body = await _post(client, session["site_id"], session["auth"], OFFSET_CSV, SCOPE)

    response = await client.delete("/api/v1/demo/sessions/current", headers=session["auth"])

    assert response.status_code < 300
    assert (await execute("SELECT count(*) FROM imports WHERE id = :id", id=body["id"]))[0][0] == 0
    assert (await execute("SELECT count(*) FROM import_rows WHERE import_id = :id", id=body["id"]))[0][0] == 0


async def test_lifecycle_a_preview_still_answers_after_demo_reset(client: AsyncClient) -> None:
    """
    Condition:
    - A demo session with a stored preview is reset.

    Expected:
    - The read still answers. The stored revisions predate the reset, so 026 would refuse a commit.
    """
    session = await start_demo(client, "empty")
    _, body = await _post(client, session["site_id"], session["auth"], OFFSET_CSV, SCOPE)

    response = await client.post("/api/v1/demo/sessions/current/reset", headers=session["auth"])

    assert response.status_code < 300
    assert (await client.get(f"/api/v1/imports/{body['id']}", headers=session["auth"])).status_code == 200


async def test_lifecycle_rows_after_product_time_become_an_assumption(client: AsyncClient) -> None:
    """
    Condition:
    - D20: the ``empty`` scenario's clock sits at 2026-10-26 00.00 WIB, and one row ends after it.

    Expected:
    - The row is accepted, and the assumption says it is not yet counted.
    """
    session = await start_demo(client, "empty")
    text = "interval_start,interval_end,asset,energy_wh\n2026-11-02T00:00:00+07:00,2026-11-02T01:00:00+07:00,Router,1\n"

    status, body = await _post(client, session["site_id"], session["auth"], text, SCOPE)

    assert status == 201
    assert body["accepted_rows"] == 1
    assert (
        "1 baris berakhir setelah waktu ruang kerja 26 Oktober 2026 00.00; baris itu belum dihitung pada ringkasan."
        in body["assumptions"]
    )


async def test_lifecycle_read_of_a_missing_import_is_not_found(
    client: AsyncClient, owner: tuple[UUID, dict], caplog: pytest.LogCaptureFixture
) -> None:
    """
    Condition:
    - An import ID that does not exist, on both read routes.

    Expected:
    - NOT_FOUND, with one record each.
    """
    _, headers = owner
    missing = "00000000-0000-4000-8000-000000000000"

    first = await client.get(f"/api/v1/imports/{missing}", headers=headers)
    second = await client.get(f"/api/v1/imports/{missing}/errors", headers=headers)

    assert (first.status_code, second.status_code) == (404, 404)
    assert first.json()["error"]["code"] == second.json()["error"]["code"] == "NOT_FOUND"
    assert len(_records(caplog)) == 2


# --- conflicts -----------------------------------------------------------------------------------------------------


def _hourly_readings(values: list[str]) -> list[ReadingInput]:
    start = datetime(2026, 10, 19, 17, tzinfo=UTC)
    return [
        ReadingInput(
            value=Decimal(value),
            unit="Wh",
            interval_start=start + timedelta(hours=hour),
            interval_end=start + timedelta(hours=hour + 1),
        )
        for hour, value in enumerate(values)
    ]


async def _seed(
    site: UUID,
    readings: list[ReadingInput],
    *,
    name: str = "Router",
    stream: str = "router",
    kind: MeasurementKind = MeasurementKind.INTERVAL_ENERGY,
) -> tuple[UUID, UUID]:
    """Store readings as an earlier import would: an asset, its labelled source, a binding and ingestion.

    Args:
        site (UUID): The site.
        readings (list[ReadingInput]): What to store.
        name (str, optional): Asset name. Defaults to Router.
        stream (str, optional): Stream key. Defaults to router.
        kind (MeasurementKind, optional): What the source's values mean. Defaults to interval energy.

    Returns:
        tuple[UUID, UUID]: The asset and the source.
    """
    asset = await make_asset(site, name)
    label = source_label(stream)
    rows = await execute(
        "INSERT INTO sources (id, site_id, label, origin, measurement_kind, cadence_seconds, transport_status)"
        " VALUES (gen_random_uuid(), :site, :label, 'import', :kind, 3600, 'historical') RETURNING id",
        site=site,
        label=label,
        kind=kind.value,
    )
    source_id = rows[0][0]
    await make_binding(site, asset, source_id, "2026-01-01T00:00:00Z")
    source = SourceModel(
        id=source_id,
        site_id=site,
        label=label,
        origin=SourceOrigin.IMPORT,
        measurement_kind=kind,
        cadence_seconds=3600,
        resolution_mwh=None,
        transport_status=TransportStatus.HISTORICAL,
    )
    async with get_session_factory()() as session:
        locked = await SqlAlchemySiteRepository(session).lock(site)
        assert locked is not None
        await build_ingest_service(session).ingest(locked, source, readings, received_at=datetime.now(UTC))
        await session.commit()
    return asset, source_id


async def test_conflicts_at_33_reimport_is_a_no_op(client: AsyncClient, owner: tuple[UUID, dict]) -> None:
    """
    Condition:
    - AT-33: the file's rows are already stored under the asset and source a commit would have made.

    Expected:
    - Ten duplicates, nothing accepted, not blocked, and no asset, source, binding or reading is created.
    """
    site, headers = owner
    asset, source = await _seed(site, _hourly_readings(["10.000"] * 10))
    before = await _table_counts(site), await _revisions(site)

    status, body = await _post(client, site, headers, csv10(), ANSWERED | {"asset_map": {"Router": str(asset)}})

    assert status == 201, body
    assert (body["duplicate_rows"], body["accepted_rows"], body["blocked"]) == (10, 0, False)
    assert _reconciles(body)
    assert body["mapping"]["streams"][0]["source_id"] == str(source)
    assert body["period"] is None
    assert (await _table_counts(site), await _revisions(site)) == before
    rows = await execute("SELECT DISTINCT status, parsed FROM import_rows WHERE import_id = :id", id=body["id"])
    assert rows == [("duplicate", None)]


async def test_conflicts_at_34_one_changed_value_blocks(client: AsyncClient, owner: tuple[UUID, dict]) -> None:
    """
    Condition:
    - AT-34: one stored hour has a different value in the file, with no invalid row.

    Expected:
    - One conflict, listed in ``errors`` with its exact message, nine duplicates, blocked.
    """
    site, headers = owner
    asset, _ = await _seed(site, _hourly_readings(["10.000"] * 10))

    status, body = await _post(
        client, site, headers, csv10(changed=0), ANSWERED | {"asset_map": {"Router": str(asset)}}
    )

    assert status == 201
    assert (body["conflict_rows"], body["duplicate_rows"], body["invalid_rows"]) == (1, 9, 0)
    assert body["blocked"] is True
    assert body["block_reasons"] == [
        "Nilai berbeda ditemukan untuk sumber dan interval yang sama. "
        "Pilih sumber atau perbaiki data sebelum melanjutkan."
    ]
    assert _reconciles(body)
    assert body["errors"] == [
        {
            "data_row": 1,
            "file_line": 2,
            "field": "energi_wh",
            "reason": "conflict",
            "message": "Baris data 1, energi_wh: nilai berbeda untuk sumber dan interval yang sama.",
        }
    ]


async def test_conflicts_a_stored_raw_value_decides_like_a_commit_would(
    client: AsyncClient, owner: tuple[UUID, dict]
) -> None:
    """
    Condition:
    - The stored row has the same energy but a differently written raw value, which 006 would store as a revision.

    Expected:
    - The preview calls it a conflict rather than a duplicate, so preview and commit agree.
    """
    site, headers = owner
    asset, _ = await _seed(site, _hourly_readings(["10"] * 10))

    status, body = await _post(client, site, headers, csv10(), ANSWERED | {"asset_map": {"Router": str(asset)}})

    assert status == 201
    assert (body["conflict_rows"], body["duplicate_rows"]) == (10, 0)
    assert body["blocked"] is True


async def test_conflicts_overlap_with_a_stored_interval_blocks(client: AsyncClient, owner: tuple[UUID, dict]) -> None:
    """
    Condition:
    - A two-hour stored interval, and a file row covering its second hour under another identity.

    Expected:
    - The row is an ``interval_overlap`` conflict naming the start header, and the preview is blocked.
    """
    site, headers = owner
    start = datetime(2026, 10, 19, 17, tzinfo=UTC)
    stored = ReadingInput(
        value=Decimal("5.000"), unit="Wh", interval_start=start, interval_end=start + timedelta(hours=2)
    )
    asset, _ = await _seed(site, [stored])
    text = f"{INTERVAL_HEADER}\n2026-10-20T01:00:00+07:00,2026-10-20T03:00:00+07:00,Router,1\n"

    status, body = await _post(client, site, headers, text, SCOPE | {"asset_map": {"Router": str(asset)}})

    assert status == 201
    assert (body["conflict_rows"], body["blocked"]) == (1, True)
    assert body["errors"][0]["reason"] == "interval_overlap"
    assert body["errors"][0]["field"] == "interval_start"
    assert body["errors"][0]["message"] == (
        "Baris data 1, interval_start: interval bertumpang tindih dengan data lain pada sumber yang sama."
    )


async def test_conflicts_adjacent_to_a_stored_interval_is_accepted(
    client: AsyncClient, owner: tuple[UUID, dict]
) -> None:
    """
    Condition:
    - A stored hour, and a file row starting exactly where it ends.

    Expected:
    - Half-open intervals do not overlap, so the row is accepted.
    """
    site, headers = owner
    asset, _ = await _seed(site, _hourly_readings(["5.000"]))
    text = f"{INTERVAL_HEADER}\n2026-10-20T01:00:00+07:00,2026-10-20T02:00:00+07:00,Router,1\n"

    status, body = await _post(client, site, headers, text, SCOPE | {"asset_map": {"Router": str(asset)}})

    assert status == 201
    assert (body["accepted_rows"], body["conflict_rows"], body["blocked"]) == (1, 0, False)


async def test_conflicts_in_a_file_with_no_stored_data(client: AsyncClient, owner: tuple[UUID, dict]) -> None:
    """
    Condition:
    - A new asset's file with a repeated row, a changed row and two overlapping rows.

    Expected:
    - One accepted plus one duplicate, two value conflicts and two overlaps, counted once each and blocked.
    """
    site, headers = owner
    text = (
        f"{INTERVAL_HEADER}\n"
        "2026-10-20T00:00:00+07:00,2026-10-20T01:00:00+07:00,Router,1\n"
        "2026-10-20T00:00:00+07:00,2026-10-20T01:00:00+07:00,Router,1.0\n"
        "2026-10-20T01:00:00+07:00,2026-10-20T02:00:00+07:00,Router,1\n"
        "2026-10-20T01:00:00+07:00,2026-10-20T02:00:00+07:00,Router,2\n"
        "2026-10-20T03:00:00+07:00,2026-10-20T05:00:00+07:00,Router,1\n"
        "2026-10-20T04:00:00+07:00,2026-10-20T06:00:00+07:00,Router,1\n"
    )

    status, body = await _post(client, site, headers, text, SCOPE)

    assert status == 201
    assert (body["accepted_rows"], body["duplicate_rows"], body["conflict_rows"]) == (1, 1, 4)
    assert _reconciles(body)
    assert body["blocked"] is True
    assert [(error["data_row"], error["reason"]) for error in body["errors"]] == [
        (3, "conflict"),
        (4, "conflict"),
        (5, "interval_overlap"),
        (6, "interval_overlap"),
    ]


async def test_conflicts_repeated_counter_points_against_stored(client: AsyncClient, owner: tuple[UUID, dict]) -> None:
    """
    Condition:
    - A counter file whose first point is stored, whose second point is stored with a changed value, and whose third
      is new.

    Expected:
    - One duplicate, one conflict and one accepted point: points never overlap.
    """
    site, headers = owner
    start = datetime(2026, 10, 19, 17, tzinfo=UTC)
    stored = [
        ReadingInput(value=Decimal("100.000"), unit="Wh", measured_at=start),
        ReadingInput(value=Decimal("130.000"), unit="Wh", measured_at=start + timedelta(hours=1)),
    ]
    asset, _ = await _seed(site, stored, kind=MeasurementKind.COUNTER)
    text = (
        "timestamp,asset,cumulative_wh\n"
        "2026-10-20T00:00:00+07:00,Router,100\n"
        "2026-10-20T01:00:00+07:00,Router,131\n"
        "2026-10-20T02:00:00+07:00,Router,140\n"
    )

    status, body = await _post(client, site, headers, text, SCOPE | {"asset_map": {"Router": str(asset)}})

    assert status == 201
    assert (body["duplicate_rows"], body["conflict_rows"], body["accepted_rows"]) == (1, 1, 1)
    assert body["errors"][0]["reason"] == "conflict"


async def test_conflicts_jittered_timestamps_block_on_overlap(client: AsyncClient, owner: tuple[UUID, dict]) -> None:
    """
    Condition:
    - D21: timestamps with up to a second of jitter, so an inferred interval reaches past the next timestamp.

    Expected:
    - The overlapping rows carry the ``interval_overlap`` message, and the preview is blocked.
    """
    site, headers = owner
    seconds = [0, 3601, 7199, *(hour * 3600 for hour in range(3, 20))]
    start = datetime(2026, 10, 20, tzinfo=UTC)
    lines = [f"{(start + timedelta(seconds=second)).isoformat()},Router,1" for second in seconds]
    text = "timestamp,asset,energy_wh\n" + "\n".join(lines) + "\n"

    status, body = await _post(client, site, headers, text, SCOPE)

    assert status == 201
    assert body["conflict_rows"] == 2
    assert {error["reason"] for error in body["errors"]} == {"interval_overlap"}
    assert body["blocked"] is True
    assert _reconciles(body)


# --- identity ------------------------------------------------------------------------------------------------------


async def test_identity_two_same_name_assets_ask_then_clear(client: AsyncClient, owner: tuple[UUID, dict]) -> None:
    """
    Condition:
    - US3: two ``Kulkas`` assets, unanswered and then answered by ID.

    Expected:
    - The question with both candidates and blocked, then neither once one is chosen.
    """
    site, headers = owner
    first, second = await make_asset(site, "Kulkas"), await make_asset(site, "Kulkas")
    text = f"{INTERVAL_HEADER}\n{ONE_HOUR},Kulkas,1\n"

    _, asked = await _post(client, site, headers, text, SCOPE)

    assert asked["blocked"] is True
    assert [question["kind"] for question in asked["questions"]] == ["asset_choice"]
    assert {candidate["id"] for candidate in asked["questions"][0]["candidates"]} == {str(first), str(second)}
    assert set(asked["questions"][0]["candidates"][0]) == {"id", "name", "location", "category", "scope_kind"}

    status, chosen = await _post(client, site, headers, text, SCOPE | {"asset_map": {"Kulkas": str(first)}})

    assert status == 201
    assert (chosen["blocked"], chosen["questions"]) == (False, [])
    assert chosen["mapping"]["streams"][0]["asset_id"] == str(first)


async def test_identity_a_demo_seeded_source_asks_until_new_is_chosen(client: AsyncClient) -> None:
    """
    Condition:
    - A demo asset whose seeded source covers the file's period, by its default mapping and then mapped to new.

    Expected:
    - ``other_source`` with the exact text and blocked, then cleared, and nothing is ever added to the asset.
    """
    session = await start_demo(client, "h-base")
    site, auth = session["site_id"], session["auth"]
    assets = (await client.get(f"/api/v1/sites/{site}/assets", headers=auth)).json()["items"]
    name = assets[0]["name"]
    text = f'{INTERVAL_HEADER}\n2026-10-20T00:00:00+07:00,2026-10-20T01:00:00+07:00,"{name}",1\n'
    before = await _table_counts(UUID(site))

    _, asked = await _post(client, site, auth, text, SCOPE)

    assert [question["kind"] for question in asked["questions"]] == ["other_source"]
    assert asked["questions"][0]["message"] == (
        f"{name} sudah memiliki sumber lain. Sumber ganda untuk satu beban tidak dijumlahkan; "
        'pilih "Buat perangkat baru" lalu tentukan sumber acuan di Cakupan & sumber.'
    )
    assert asked["blocked"] is True

    status, cleared = await _post(client, site, auth, text, SCOPE | {"asset_map": {name: "new"}})

    assert status == 201
    assert (cleared["blocked"], cleared["questions"]) == (False, [])
    assert cleared["mapping"]["streams"][0]["asset_id"] is None
    assert await _table_counts(UUID(site)) == before


async def test_identity_another_owners_asset_looks_missing(
    client: AsyncClient, owner: tuple[UUID, dict], caplog: pytest.LogCaptureFixture
) -> None:
    """
    Condition:
    - The mapping names an asset of another owner's site.

    Expected:
    - NOT_FOUND with one record, and nothing stored.
    """
    site, headers = owner
    foreign = await make_asset(await make_site(await make_principal()), "Kulkas")

    status, body = await _post(
        client,
        site,
        headers,
        f"{INTERVAL_HEADER}\n{ONE_HOUR},Kulkas,1\n",
        SCOPE | {"asset_map": {"Kulkas": str(foreign)}},
    )

    _assert_failure(
        status,
        body,
        caplog,
        expected_status=404,
        code="NOT_FOUND",
        message="Data yang diminta tidak ditemukan. Periksa alamatnya lalu coba lagi.",
        internal="APP-NOT-FOUND",
    )
    assert await _import_count(site) == 0


async def test_identity_an_archived_asset_looks_missing(client: AsyncClient, owner: tuple[UUID, dict]) -> None:
    """
    Condition:
    - The mapping names an archived asset of this site, before any row is parsed.

    Expected:
    - NOT_FOUND even though the file itself is unreadable, with nothing stored.
    """
    site, headers = owner
    asset = await make_asset(site, "Kulkas")
    await execute("UPDATE assets SET archived_at = now() WHERE id = :id", id=asset)

    status, body = await _post(client, site, headers, "foo,bar\n1,2\n", SCOPE | {"asset_map": {"Kulkas": str(asset)}})

    assert status == 404
    assert body["error"]["code"] == "NOT_FOUND"
    assert await _import_count(site) == 0


async def test_identity_unknown_overlap_is_stored_and_not_blocked(
    client: AsyncClient, owner: tuple[UUID, dict]
) -> None:
    """
    Condition:
    - US3 scenario 3: unknown overlap is confirmed.

    Expected:
    - Not blocked, and the answer is stored, so 026 records the relation and totals stay refused.
    """
    site, headers = owner

    status, body = await _post(client, site, headers, OFFSET_CSV, {"scope": "unknown_overlap"})

    assert status == 201
    assert body["blocked"] is False
    assert body["mapping"]["scope"] == "unknown_overlap"
    stored = await execute("SELECT mapping -> 'scope' FROM imports WHERE id = :id", id=body["id"])
    assert stored[0][0] == "unknown_overlap"


async def test_identity_reimport_with_the_default_mapping_finds_its_source(
    client: AsyncClient, owner: tuple[UUID, dict]
) -> None:
    """
    Condition:
    - A file's rows are stored, and the same file is previewed with no asset answer.

    Expected:
    - The name resolves to the asset, the label to the source, every row is a duplicate, and nothing is created.
    """
    site, headers = owner
    asset, source = await _seed(site, _hourly_readings(["10.000"] * 10))
    before = await _table_counts(site)

    status, body = await _post(client, site, headers, csv10(), ANSWERED)

    assert status == 201
    assert (body["duplicate_rows"], body["accepted_rows"], body["blocked"]) == (10, 0, False)
    assert body["questions"] == []
    stream = body["mapping"]["streams"][0]
    assert (stream["asset_id"], stream["source_id"]) == (str(asset), str(source))
    assert await _table_counts(site) == before


async def test_identity_mapping_streams_hold_every_field(client: AsyncClient, owner: tuple[UUID, dict]) -> None:
    """
    Condition:
    - A new asset's stream with an inferred cadence.

    Expected:
    - ``mapping.streams`` holds every field of the plan's Data Model, as stored and as returned.
    """
    site, headers = owner

    status, body = await _post(client, site, headers, csv10(), ANSWERED)

    assert status == 201
    assert body["mapping"]["streams"] == [
        {
            "stream_key": "router",
            "label": "Impor CSV · router",
            "asset_name": "Router",
            "asset_id": None,
            "source_id": None,
            "kind": "interval_energy",
            "unit": "Wh",
            "cadence_seconds": 3600,
            "period_start": "2026-10-19T17:00:00Z",
            "period_end": "2026-10-20T03:00:00Z",
            "interval_basis": "inferred",
        }
    ]
    stored = await execute("SELECT mapping FROM imports WHERE id = :id", id=body["id"])
    assert stored[0][0]["streams"] == body["mapping"]["streams"]


async def test_identity_two_streams_on_one_asset_block(client: AsyncClient, owner: tuple[UUID, dict]) -> None:
    """
    Condition:
    - One asset name fed by two source cells.

    Expected:
    - The ``asset_streams`` question blocks, so the two are never added.
    """
    site, headers = owner
    text = (
        "interval_start,interval_end,asset,energy_wh,sumber\n"
        f"{ONE_HOUR},Kulkas,1,meter-1\n"
        f"{ONE_HOUR},Kulkas,2,meter-2\n"
    )

    status, body = await _post(client, site, headers, text, SCOPE)

    assert status == 201
    assert [question["kind"] for question in body["questions"]] == ["asset_streams"]
    assert body["questions"][0]["streams"] == ["meter-1", "meter-2"]
    assert body["blocked"] is True
