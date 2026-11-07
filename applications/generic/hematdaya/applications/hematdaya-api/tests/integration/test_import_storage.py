"""Import storage over real Postgres: constraints, cascade, paging, purge and the migration."""

import asyncio
import secrets
import subprocess
import sys
import time
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.database import get_session_factory
from app.imports.model.models import ImportModel, ImportRowModel, ImportRowStatus, ImportStatus
from app.imports.repository.sqlalchemy.models import ImportRecord
from app.imports.repository.sqlalchemy.repository import SqlAlchemyImportRepository
from tests.integration.conftest import COMMITTED_RESULT, execute, make_principal, make_site

pytestmark = pytest.mark.integration

NOW = datetime(2026, 11, 7, 12, tzinfo=UTC)
MAPPING = {"value_kind": "interval_energy", "streams": [{"stream_key": "router"}]}


def _import(site: UUID, **overrides: object) -> ImportModel:
    values = {
        "id": uuid4(),
        "site_id": site,
        "status": ImportStatus.PREVIEWED,
        "file_name": "data.csv",
        "content_sha256": "a" * 64,
        "mapping": MAPPING,
        "total_rows": 2,
        "accepted_rows": 1,
        "invalid_rows": 1,
        "duplicate_rows": 0,
        "conflict_rows": 0,
        "pending_rows": 0,
        "blocked": False,
        "block_reasons": [],
        "needs_acknowledgment": True,
        "questions": [],
        "assumptions": ["BOM UTF-8 dilewati."],
        "period_start": NOW,
        "period_end": NOW + timedelta(hours=1),
        "measurement_revision": 3,
        "binding_revision": 4,
        "idempotency_key": None,
        "expires_at": NOW + timedelta(hours=24),
    }
    if overrides.get("status") is ImportStatus.COMMITTED:
        values |= {"idempotency_key": secrets.token_urlsafe(16), "commit_result": COMMITTED_RESULT}
    return ImportModel(**(values | overrides))


def _invalid(data_row: int, message: str = "Baris data 1, wh: bukan angka.") -> ImportRowModel:
    return ImportRowModel(
        data_row=data_row,
        file_line=data_row + 1,
        status=ImportRowStatus.INVALID,
        reason="value_not_number",
        field="wh",
        message=message,
    )


async def _store(model: ImportModel, rows: list[ImportRowModel] | None = None) -> None:
    async with get_session_factory()() as session:
        repository = SqlAlchemyImportRepository(session)
        await repository.add_import(model)
        await repository.add_rows(model.id, rows or [])
        await session.commit()


async def _site() -> UUID:
    return await make_site(await make_principal())


async def _set_created(import_id: UUID, created: datetime) -> None:
    await execute("UPDATE imports SET created_at = :created WHERE id = :id", created=created, id=import_id)


async def _ids(site: UUID) -> set[UUID]:
    return {row[0] for row in await execute("SELECT id FROM imports WHERE site_id = :site", site=site)}


async def test_an_import_and_its_rows_round_trip() -> None:
    """
    Condition:
    - An import is stored with one accepted row holding parsed data and one invalid row.

    Expected:
    - A new session reads every field back, and the error page holds only the invalid row.
    """
    site = await _site()
    model = _import(site)
    accepted = ImportRowModel(
        data_row=1, file_line=2, status=ImportRowStatus.ACCEPTED, parsed={"identity_key": "i:x", "value": "10.000"}
    )

    await _store(model, [accepted, _invalid(2)])

    async with get_session_factory()() as session:
        repository = SqlAlchemyImportRepository(session)
        stored = await repository.get_import(model.id)
        page = await repository.error_page(model.id, 0, 10)
    assert stored is not None
    assert stored.model_dump(exclude={"created_at"}) == model.model_dump(exclude={"created_at"})
    assert stored.created_at is not None
    assert [row.data_row for row in page] == [2]
    rows = await execute("SELECT status, parsed FROM import_rows WHERE import_id = :id ORDER BY data_row", id=model.id)
    assert rows[0] == ("accepted", {"identity_key": "i:x", "value": "10.000"})


async def test_get_import_answers_none_for_an_unknown_id() -> None:
    """
    Condition:
    - No import has this ID.

    Expected:
    - The repository answers None.
    """
    async with get_session_factory()() as session:
        assert await SqlAlchemyImportRepository(session).get_import(uuid4()) is None


async def test_add_rows_stores_more_than_one_batch() -> None:
    """
    Condition:
    - More rows than one insert batch holds.

    Expected:
    - All are stored.
    """
    site = await _site()
    model = _import(site, total_rows=5_001, accepted_rows=0, invalid_rows=5_001, blocked=True)

    await _store(model, [_invalid(index) for index in range(1, 5_002)])

    assert (await execute("SELECT count(*) FROM import_rows WHERE import_id = :id", id=model.id))[0][0] == 5_001


@pytest.mark.parametrize(
    "overrides",
    [{"accepted_rows": 5}, {"pending_rows": 1}],
    ids=["accepted_too_high", "pending_not_counted"],
)
async def test_counts_that_do_not_reconcile_are_refused(overrides: dict) -> None:
    """
    Condition:
    - The five counts do not add up to the total.

    Expected:
    - The database refuses the row.
    """
    site = await _site()

    with pytest.raises(IntegrityError, match="imports_counts_reconcile"):
        await _store(_import(site, **overrides))

    assert await _ids(site) == set()


async def test_an_unknown_import_status_is_refused() -> None:
    """
    Condition:
    - A status outside the three known ones.

    Expected:
    - The database refuses the update.
    """
    site = await _site()
    model = _import(site)
    await _store(model)

    with pytest.raises(IntegrityError):
        await execute("UPDATE imports SET status = 'expired' WHERE id = :id", id=model.id)


@pytest.mark.parametrize(
    ("status", "message"),
    [("conflict", None), ("invalid", None), ("accepted", "Pesan"), ("duplicate", "Pesan")],
)
async def test_row_message_follows_its_status(status: str, message: str | None) -> None:
    """
    Condition:
    - An invalid or conflict row with no message, or an accepted or duplicate row with one.

    Expected:
    - The database refuses each.
    """
    site = await _site()
    model = _import(site)
    await _store(model)

    with pytest.raises(IntegrityError, match="import_rows_message"):
        await execute(
            "INSERT INTO import_rows (import_id, data_row, file_line, status, message)"
            " VALUES (:id, 1, 2, :status, :message)",
            id=model.id,
            status=status,
            message=message,
        )


async def test_deleting_the_site_removes_imports_and_rows() -> None:
    """
    Condition:
    - A site with one import and one row is deleted.

    Expected:
    - Both are gone, so demo end and purge need no extra code (D19).
    """
    site = await _site()
    model = _import(site)
    await _store(model, [_invalid(1)])

    await execute("DELETE FROM sites WHERE id = :site", site=site)

    assert (await execute("SELECT count(*) FROM imports WHERE id = :id", id=model.id))[0][0] == 0
    assert (await execute("SELECT count(*) FROM import_rows WHERE import_id = :id", id=model.id))[0][0] == 0


async def test_idempotency_key_is_unique_per_site_and_repeatable_across_sites() -> None:
    """
    Condition:
    - One key is used twice on a site, and once on another site. Two imports have no key.

    Expected:
    - Only the repeat on one site is refused.
    """
    first, second = await _site(), await _site()
    await _store(_import(first, idempotency_key="kunci"))
    await _store(_import(second, idempotency_key="kunci"))
    await _store(_import(first))
    await _store(_import(first))

    with pytest.raises(IntegrityError, match="ux_imports_site_idempotency"):
        await _store(_import(first, idempotency_key="kunci"))


async def test_error_rows_page_in_data_row_order() -> None:
    """
    Condition:
    - Error rows stored out of order, with an accepted row between them.

    Expected:
    - Pages hold invalid and conflict rows by ascending data row, starting after the given row.
    """
    site = await _site()
    model = _import(site, total_rows=4, accepted_rows=1, invalid_rows=2, conflict_rows=1, blocked=True)
    conflict = ImportRowModel(
        data_row=3, file_line=4, status=ImportRowStatus.CONFLICT, reason="conflict", field="wh", message="Baris data 3."
    )
    accepted = ImportRowModel(data_row=2, file_line=3, status=ImportRowStatus.ACCEPTED, parsed={"value": "1.000"})
    await _store(model, [_invalid(4), conflict, accepted, _invalid(1)])

    async with get_session_factory()() as session:
        repository = SqlAlchemyImportRepository(session)
        first = await repository.error_page(model.id, 0, 2)
        second = await repository.error_page(model.id, first[-1].data_row, 2)

    assert [row.data_row for row in first] == [1, 3]
    assert [row.data_row for row in second] == [4]


async def test_purge_removes_expired_previews_and_never_committed_ones() -> None:
    """
    Condition:
    - One expired preview, one live preview, and one committed import past its expiry.

    Expected:
    - Only the expired preview goes, along with its rows.
    """
    site = await _site()
    expired = _import(site, expires_at=NOW - timedelta(seconds=1))
    live = _import(site, expires_at=NOW + timedelta(hours=1))
    committed = _import(site, status=ImportStatus.COMMITTED, expires_at=NOW - timedelta(days=1))
    await _store(expired, [_invalid(1)])
    await _store(live)
    await _store(committed)

    async with get_session_factory()() as session:
        removed = await SqlAlchemyImportRepository(session).delete_expired(NOW, 1_000_000)
        await session.commit()

    assert removed >= 1
    assert await _ids(site) == {live.id, committed.id}
    assert (await execute("SELECT count(*) FROM import_rows WHERE import_id = :id", id=expired.id))[0][0] == 0


async def test_purge_stops_at_its_limit() -> None:
    """
    Condition:
    - Three expired previews, older than anything the shared database may already hold, and a limit of two.

    Expected:
    - The two oldest go and the newest of the three stays.
    """
    site = await _site()
    oldest = NOW - timedelta(days=30_000)
    models = [_import(site, expires_at=oldest + timedelta(hours=hour)) for hour in range(3)]
    for model in models:
        await _store(model)

    async with get_session_factory()() as session:
        removed = await SqlAlchemyImportRepository(session).delete_expired(oldest + timedelta(days=1), 2)
        await session.commit()

    assert removed == 2
    assert await _ids(site) == {models[2].id}


async def test_the_per_site_cap_keeps_the_newest_uncommitted() -> None:
    """
    Condition:
    - Seven previews and one older committed import on one site, and an old preview on another site.

    Expected:
    - The newest five previews stay, the committed import stays, and the other site is untouched.
    """
    site, other = await _site(), await _site()
    previews = [_import(site) for _ in range(7)]
    for index, model in enumerate(previews):
        await _store(model)
        await _set_created(model.id, NOW + timedelta(minutes=index))
    committed = _import(site, status=ImportStatus.COMMITTED)
    elsewhere = _import(other)
    await _store(committed)
    await _set_created(committed.id, NOW - timedelta(days=1))
    await _store(elsewhere)
    await _set_created(elsewhere.id, NOW - timedelta(days=1))

    async with get_session_factory()() as session:
        removed = await SqlAlchemyImportRepository(session).keep_newest_uncommitted(site, 5)
        await session.commit()

    assert removed == 2
    assert await _ids(site) == {model.id for model in previews[2:]} | {committed.id}
    assert await _ids(other) == {elsewhere.id}


async def test_the_migration_downgrades_and_upgrades() -> None:
    """
    Condition:
    - The schema is at head.

    Expected:
    - Downgrading to 0007 removes both tables, and upgrading restores them.
    """
    downgrade = [sys.executable, "-m", "alembic", "downgrade", "0007"]
    upgrade = [sys.executable, "-m", "alembic", "upgrade", "head"]
    query = "SELECT to_regclass('imports') IS NOT NULL, to_regclass('import_rows') IS NOT NULL"

    subprocess.run(downgrade, check=True)
    try:
        assert (await execute(query))[0] == (False, False)
    finally:
        subprocess.run(upgrade, check=True)

    assert (await execute(query))[0] == (True, True)


async def test_mark_committed_round_trip() -> None:
    """
    Condition:
    - A preview is marked committed once, and then a second time.

    Expected:
    - The first call answers True and stores the status, key and result. The second answers False and changes nothing.
    """
    site = await _site()
    model = _import(site)
    await _store(model)
    first_result = {"import_id": str(model.id), "rows_added": 1}

    async with get_session_factory()() as session:
        repository = SqlAlchemyImportRepository(session)
        assert await repository.mark_committed(model.id, "kunci-pertama", first_result) is True
        assert await repository.mark_committed(model.id, "kunci-kedua", {"rows_added": 9}) is False
        await session.commit()

    async with get_session_factory()() as session:
        stored = await SqlAlchemyImportRepository(session).get_import(model.id)
    assert stored is not None
    assert (stored.status, stored.idempotency_key, stored.commit_result) == (
        ImportStatus.COMMITTED,
        "kunci-pertama",
        first_result,
    )


@pytest.mark.parametrize(
    ("assignments", "constraint"),
    [
        ("status = 'committed', idempotency_key = 'kunci'", "imports_commit_result"),
        ("status = 'committed', commit_result = '{}'", "imports_commit_key"),
        ("commit_result = '{}'", "imports_commit_result"),
    ],
    ids=["committed_with_no_result", "result_with_no_key", "result_on_a_preview"],
)
async def test_a_committed_row_needs_its_result_and_key(assignments: str, constraint: str) -> None:
    """
    Condition:
    - A raw update breaking the rule that ``committed`` goes with a result and a key.

    Expected:
    - The database refuses it, naming the constraint.
    """
    site = await _site()
    model = _import(site)
    await _store(model)

    with pytest.raises(IntegrityError, match=constraint):
        await execute(f"UPDATE imports SET {assignments} WHERE id = :id", id=model.id)


async def test_a_preview_stores_sql_null_as_its_result() -> None:
    """
    Condition:
    - A preview with no result, written through the ORM.

    Expected:
    - The column holds SQL NULL, not JSON null, which the CHECK would take for a result.
    """
    site = await _site()
    model = _import(site)
    await _store(model)

    rows = await execute("SELECT commit_result IS NULL FROM imports WHERE id = :id", id=model.id)

    assert rows[0][0] is True


async def test_get_import_locked_sees_what_another_session_committed() -> None:
    """
    Condition:
    - A session holds the loaded ORM row, another commits it, then the first locks it.

    Expected:
    - The locked read returns ``committed``, not the state the identity map holds (D3). The record is kept referenced,
      because the map is weak: a dropped record is read afresh with or without ``populate_existing``.
    """
    site = await _site()
    model = _import(site)
    await _store(model)

    async with get_session_factory()() as session:
        held = await session.scalar(select(ImportRecord).where(ImportRecord.id == model.id))
        assert held is not None
        assert held.status == ImportStatus.PREVIEWED.value
        async with get_session_factory()() as other:
            assert await SqlAlchemyImportRepository(other).mark_committed(model.id, "kunci", {"rows_added": 1})
            await other.commit()

        locked = await SqlAlchemyImportRepository(session).get_import_locked(model.id)

        assert held.status == ImportStatus.COMMITTED.value
    assert locked is not None
    assert (locked.status, locked.commit_result) == (ImportStatus.COMMITTED, {"rows_added": 1})


async def test_get_import_locked_waits_and_then_sees_the_commit() -> None:
    """
    Condition:
    - A session holds the loaded ORM row, and another has committed it in a transaction still open when the first locks.

    Expected:
    - The lock waits on real Postgres, and once the other transaction ends it returns ``committed``, so a second
      concurrent commit can never write everything again.
    """
    site = await _site()
    model = _import(site)
    await _store(model)

    async with get_session_factory()() as session, get_session_factory()() as other:
        held = await session.scalar(select(ImportRecord).where(ImportRecord.id == model.id))
        assert held is not None
        assert await SqlAlchemyImportRepository(other).mark_committed(model.id, "kunci", {"rows_added": 1})
        locking = asyncio.create_task(SqlAlchemyImportRepository(session).get_import_locked(model.id))
        deadline = time.monotonic() + 5
        query = "SELECT count(*) FROM pg_stat_activity WHERE datname = current_database() AND wait_event_type = 'Lock'"
        while (await execute(query))[0][0] < 1:
            assert time.monotonic() < deadline, "The locked read never waited."
            await asyncio.sleep(0.01)
        assert not locking.done()
        await other.commit()

        locked = await asyncio.wait_for(locking, 10)

    assert locked is not None
    assert locked.status is ImportStatus.COMMITTED


async def test_get_import_locked_answers_none_for_an_unknown_id() -> None:
    """
    Condition:
    - No import has this ID.

    Expected:
    - The repository answers None.
    """
    async with get_session_factory()() as session:
        assert await SqlAlchemyImportRepository(session).get_import_locked(uuid4()) is None


async def test_find_by_key_stays_within_its_site() -> None:
    """
    Condition:
    - A key stored on an import of one site.

    Expected:
    - It is found there, and not found for the same key in another site or for an unused key.
    """
    site, other = await _site(), await _site()
    model = _import(site, idempotency_key="kunci")
    await _store(model)

    async with get_session_factory()() as session:
        repository = SqlAlchemyImportRepository(session)
        assert await repository.find_by_key(site, "kunci") == model.id
        assert await repository.find_by_key(other, "kunci") is None
        assert await repository.find_by_key(site, "lain") is None


async def test_accepted_page_returns_accepted_rows_in_order() -> None:
    """
    Condition:
    - Accepted rows stored out of order, beside an invalid and a duplicate row.

    Expected:
    - Only accepted rows, with ``parsed``, by data row, after the given row and up to the limit.
    """
    site = await _site()
    model = _import(site, total_rows=5, accepted_rows=3, invalid_rows=1, duplicate_rows=1)

    def accepted(data_row: int) -> ImportRowModel:
        return ImportRowModel(
            data_row=data_row,
            file_line=data_row + 1,
            status=ImportRowStatus.ACCEPTED,
            parsed={"value": f"{data_row}.000"},
        )

    duplicate = ImportRowModel(data_row=2, file_line=3, status=ImportRowStatus.DUPLICATE)
    await _store(model, [accepted(5), _invalid(1), duplicate, accepted(3), accepted(4)])

    async with get_session_factory()() as session:
        repository = SqlAlchemyImportRepository(session)
        first = await repository.accepted_page(model.id, 0, 2)
        second = await repository.accepted_page(model.id, first[-1].data_row, 2)

    assert [(row.data_row, row.parsed) for row in first] == [(3, {"value": "3.000"}), (4, {"value": "4.000"})]
    assert [row.data_row for row in second] == [5]
    assert second[0].status is ImportRowStatus.ACCEPTED


async def test_keep_newest_uncommitted_never_removes_the_excluded_import() -> None:
    """
    Condition:
    - Five previews, and a new one that sorts oldest, as a tied or inverted ``created_at`` can make it.

    Expected:
    - The new one stays beside the newest four others, so a preview never purges itself (D4).
    """
    site = await _site()
    others = [_import(site) for _ in range(5)]
    for index, model in enumerate(others):
        await _store(model)
        await _set_created(model.id, NOW + timedelta(minutes=index))
    new = _import(site)
    await _store(new)
    await _set_created(new.id, NOW - timedelta(days=1))

    async with get_session_factory()() as session:
        removed = await SqlAlchemyImportRepository(session).keep_newest_uncommitted(site, 4, excluding=new.id)
        await session.commit()

    assert removed == 1
    assert await _ids(site) == {model.id for model in others[1:]} | {new.id}


async def test_the_commit_migration_downgrades_and_upgrades() -> None:
    """
    Condition:
    - A ``committed`` row exists, and the schema goes down to 0008 and back to head.

    Expected:
    - The downgrade removes ``commit_result`` and both CHECKs. The upgrade succeeds over that row, whose result is now
      gone, because both CHECKs are ``NOT VALID``, and it restores the column (D9).
    """
    site = await _site()
    committed = _import(site, status=ImportStatus.COMMITTED)
    await _store(committed)
    downgrade = [sys.executable, "-m", "alembic", "downgrade", "0008"]
    upgrade = [sys.executable, "-m", "alembic", "upgrade", "head"]
    column = (
        "SELECT count(*) FROM information_schema.columns WHERE table_name = 'imports' AND column_name = 'commit_result'"
    )
    constraints = "SELECT count(*) FROM pg_constraint WHERE conname IN ('imports_commit_result', 'imports_commit_key')"

    subprocess.run(downgrade, check=True)
    try:
        assert (await execute(column))[0][0] == 0
        assert (await execute(constraints))[0][0] == 0
    finally:
        subprocess.run(upgrade, check=True)

    assert (await execute(column))[0][0] == 1
    assert (await execute(constraints))[0][0] == 2
    assert (await execute("SELECT status FROM imports WHERE id = :id", id=committed.id))[0][0] == "committed"
    await execute("DELETE FROM sites WHERE id = :site", site=site)
