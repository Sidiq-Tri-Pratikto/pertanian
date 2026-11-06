"""Import storage over real Postgres: constraints, cascade, paging, purge and the migration."""

import subprocess
import sys
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.database import get_session_factory
from app.imports.model.models import ImportModel, ImportRowModel, ImportRowStatus, ImportStatus
from app.imports.repository.sqlalchemy.repository import SqlAlchemyImportRepository
from tests.integration.conftest import execute, make_principal, make_site

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
    - Downgrading to 0006 removes both tables, and upgrading restores them.
    """
    downgrade = [sys.executable, "-m", "alembic", "downgrade", "0006"]
    upgrade = [sys.executable, "-m", "alembic", "upgrade", "head"]
    query = "SELECT to_regclass('imports') IS NOT NULL, to_regclass('import_rows') IS NOT NULL"

    subprocess.run(downgrade, check=True)
    try:
        assert (await execute(query))[0] == (False, False)
    finally:
        subprocess.run(upgrade, check=True)

    assert (await execute(query))[0] == (True, True)
