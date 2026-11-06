"""Assets, bindings, relations and audit over real Postgres."""

import asyncio
from collections.abc import Callable
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy.exc import DBAPIError

from app.assets.model.models import RelationKind
from app.assets.repository.sqlalchemy.repository import SqlAlchemyAssetRepository
from app.assets.service.errors import AssetCycleError
from app.assets.service.service import AssetService
from app.audit.repository.sqlalchemy.repository import SqlAlchemyAuditRepository
from app.audit.service.service import AuditService
from app.core.database import get_session_factory
from app.core.errors.base import NotFoundError
from app.identity.model.models import PrincipalKind, PrincipalModel
from app.sites.repository.sqlalchemy.repository import SqlAlchemySiteRepository
from app.sites.service.service import SiteService
from tests.integration.conftest import execute, make_asset, make_binding, make_principal, make_site, make_source

pytestmark = pytest.mark.integration


async def _audit_count(site: UUID) -> int:
    return (await execute("SELECT count(*) FROM audit_events WHERE site_id = :id", id=site))[0][0]


async def _revision(site: UUID) -> int:
    return (await execute("SELECT binding_revision FROM sites WHERE id = :id", id=site))[0][0]


async def _owned_site() -> tuple[UUID, UUID]:
    owner = await make_principal()
    return owner, await make_site(owner)


async def test_rename_keeps_identity_and_bindings(client: AsyncClient, acting: Callable[[UUID], dict]) -> None:
    """
    Condition:
    - Two assets named Kulkas, one of category Pendingin, the first bound to a source, then renamed.

    Expected:
    - Both exist with distinct IDs, expected use stays unknown, and the rename keeps the ID and binding.
    """
    owner, site = await _owned_site()
    headers = acting(owner)
    first = await client.post(
        f"/api/v1/sites/{site}/assets",
        json={"name": "Kulkas", "scope_kind": "device", "category": "Pendingin"},
        headers=headers,
    )
    second = await client.post(
        f"/api/v1/sites/{site}/assets", json={"name": "Kulkas", "scope_kind": "device"}, headers=headers
    )
    asset = first.json()["id"]
    source = await make_source(site)
    bound = await client.post(
        f"/api/v1/assets/{asset}/bindings",
        json={"source_id": str(source), "effective_from": "2026-09-27T17:00:00Z"},
        headers=headers,
    )

    renamed = await client.patch(f"/api/v1/assets/{asset}", json={"name": "Kulkas dapur"}, headers=headers)
    detail = await client.get(f"/api/v1/assets/{asset}", headers=headers)

    assert first.status_code == second.status_code == bound.status_code == 201
    assert first.json()["id"] != second.json()["id"]
    assert first.json()["expected_use"] == "unknown"
    assert renamed.json()["id"] == asset
    assert detail.json()["name"] == "Kulkas dapur"
    assert [binding["id"] for binding in detail.json()["bindings"]] == [bound.json()["id"]]
    assert detail.json()["sources"][0]["origin"] == "simulated"
    assert await _audit_count(site) == 4


async def test_unchanged_patch_writes_nothing(client: AsyncClient, acting: Callable[[UUID], dict]) -> None:
    """
    Condition:
    - The owner saves an asset with the values it already has.

    Expected:
    - No audit event and no revision change.
    """
    owner, site = await _owned_site()
    asset = await make_asset(site)
    revision = await _revision(site)

    response = await client.patch(
        f"/api/v1/assets/{asset}", json={"name": "Kulkas", "archived": False}, headers=acting(owner)
    )

    assert response.status_code == 200
    assert await _audit_count(site) == 0
    assert await _revision(site) == revision


async def test_list_pages_and_archive_is_reversible(client: AsyncClient, acting: Callable[[UUID], dict]) -> None:
    """
    Condition:
    - Three assets, one archived, listed two per page; then the archived one is restored.

    Expected:
    - Active assets page by name with a cursor, archived ones appear only on request, and restoring brings it back.
    """
    owner, site = await _owned_site()
    headers = acting(owner)
    for name in ("Router", "Kulkas", "TV"):
        await make_asset(site, name)
    tv = (await execute("SELECT id FROM assets WHERE site_id = :id AND name = 'TV'", id=site))[0][0]
    await client.patch(f"/api/v1/assets/{tv}", json={"archived": True}, headers=headers)

    first = (await client.get(f"/api/v1/sites/{site}/assets?limit=1", headers=headers)).json()
    second = (
        await client.get(f"/api/v1/sites/{site}/assets?limit=1&cursor={first['next_cursor']}", headers=headers)
    ).json()
    with_archived = (await client.get(f"/api/v1/sites/{site}/assets?include_archived=true", headers=headers)).json()
    await client.patch(f"/api/v1/assets/{tv}", json={"archived": False}, headers=headers)
    restored = (await client.get(f"/api/v1/sites/{site}/assets", headers=headers)).json()
    bad_cursor = await client.get(f"/api/v1/sites/{site}/assets?cursor=zz", headers=headers)

    assert [item["name"] for item in first["items"] + second["items"]] == ["Kulkas", "Router"]
    assert second["next_cursor"] is None
    assert [item["archived"] for item in with_archived["items"]] == [False, False, True]
    assert [item["name"] for item in restored["items"]] == ["Kulkas", "Router", "TV"]
    assert bad_cursor.status_code == 400


async def test_parent_must_be_in_the_same_site(client: AsyncClient, acting: Callable[[UUID], dict]) -> None:
    """
    Condition:
    - A new asset names a parent from another owner's site.

    Expected:
    - NOT_FOUND and nothing is created.
    """
    owner, site = await _owned_site()
    _, other_site = await _owned_site()
    foreign_parent = await make_asset(other_site, "Meter utama", "site_total")

    response = await client.post(
        f"/api/v1/sites/{site}/assets",
        json={"name": "Kulkas", "scope_kind": "device", "parent_asset_id": str(foreign_parent)},
        headers=acting(owner),
    )

    assert response.status_code == 404
    assert (await execute("SELECT count(*) FROM assets WHERE site_id = :id", id=site))[0][0] == 0


async def test_authoritative_overlap_fails_at_the_database(client: AsyncClient, acting: Callable[[UUID], dict]) -> None:
    """
    Condition:
    - An open authoritative binding, then a second authoritative one overlapping it, then a candidate.

    Expected:
    - The overlap is CONFLICT with no audit event; a non-authoritative candidate is stored as unresolved.
    """
    owner, site = await _owned_site()
    asset, first, second = await make_asset(site), await make_source(site), await make_source(site, "Colokan")
    await make_binding(site, asset, first)
    revision = await _revision(site)

    overlap = await client.post(
        f"/api/v1/assets/{asset}/bindings",
        json={"source_id": str(second), "effective_from": "2026-10-01T00:00:00Z"},
        headers=acting(owner),
    )
    revision_after_failure = await _revision(site)
    candidate = await client.post(
        f"/api/v1/assets/{asset}/bindings",
        json={"source_id": str(second), "effective_from": "2026-10-01T00:00:00Z", "authoritative": False},
        headers=acting(owner),
    )

    assert overlap.status_code == 409
    assert overlap.json()["error"]["code"] == "CONFLICT"
    assert revision_after_failure == revision
    assert candidate.status_code == 201
    assert await _audit_count(site) == 1
    assert await _revision(site) == revision + 1


async def test_adjacent_authoritative_ranges_are_valid() -> None:
    """
    Condition:
    - One authoritative binding ends exactly when the next starts.

    Expected:
    - Both are stored: half-open ranges touch without overlapping.
    """
    _, site = await _owned_site()
    asset, first, second = await make_asset(site), await make_source(site), await make_source(site, "Baru")
    await execute(
        "INSERT INTO bindings (id, site_id, source_id, asset_id, effective_from, effective_to, authoritative)"
        " VALUES (gen_random_uuid(), :site, :source, :asset, '2026-09-28', '2026-10-10', true),"
        " (gen_random_uuid(), :site, :other, :asset, '2026-10-10', NULL, true)",
        site=site,
        source=first,
        other=second,
        asset=asset,
    )

    assert (await execute("SELECT count(*) FROM bindings WHERE asset_id = :id", id=asset))[0][0] == 2


async def test_unlink_ends_once_and_keeps_history(client: AsyncClient, acting: Callable[[UUID], dict]) -> None:
    """
    Condition:
    - An open binding is unlinked twice at once, then again.

    Expected:
    - It ends at the virtual now, stays stored, and only one audit event and revision step exist.
    """
    owner, site = await _owned_site()
    asset, source = await make_asset(site), await make_source(site)
    binding = await make_binding(site, asset, source)
    revision = await _revision(site)
    path = f"/api/v1/assets/{asset}/bindings/{binding}"

    concurrent = await asyncio.gather(*(client.delete(path, headers=acting(owner)) for _ in range(2)))
    repeated = await client.delete(path, headers=acting(owner))

    assert {response.status_code for response in [*concurrent, repeated]} == {200}
    assert {response.json()["effective_to"] for response in [*concurrent, repeated]} == {"2026-10-25T17:00:00Z"}
    assert (await execute("SELECT count(*) FROM bindings WHERE id = :id", id=binding))[0][0] == 1
    assert await _audit_count(site) == 1
    assert await _revision(site) == revision + 1


async def test_unlink_before_start_is_refused(client: AsyncClient, acting: Callable[[UUID], dict]) -> None:
    """
    Condition:
    - A binding that starts after the site's virtual now is unlinked.

    Expected:
    - BAD_REQUEST, because ending it would leave an empty range; nothing changes.
    """
    owner, site = await _owned_site()
    asset, source = await make_asset(site), await make_source(site)
    binding = await make_binding(site, asset, source, "2026-11-01T00:00:00Z")

    response = await client.delete(f"/api/v1/assets/{asset}/bindings/{binding}", headers=acting(owner))

    assert response.status_code == 400
    assert (await execute("SELECT effective_to FROM bindings WHERE id = :id", id=binding))[0][0] is None
    assert await _audit_count(site) == 0


async def test_binding_from_another_asset_is_not_found(client: AsyncClient, acting: Callable[[UUID], dict]) -> None:
    """
    Condition:
    - The owner unlinks a binding through a different asset of the same site.

    Expected:
    - NOT_FOUND; the binding stays open.
    """
    owner, site = await _owned_site()
    asset, other, source = await make_asset(site), await make_asset(site, "TV"), await make_source(site)
    binding = await make_binding(site, asset, source)

    response = await client.delete(f"/api/v1/assets/{other}/bindings/{binding}", headers=acting(owner))

    assert response.status_code == 404
    assert (await execute("SELECT effective_to FROM bindings WHERE id = :id", id=binding))[0][0] is None


async def test_relations_stay_acyclic_and_within_a_site() -> None:
    """
    Condition:
    - Meter contains Kulkas; then Kulkas contains Meter, Meter contains itself, and a relation to another site.

    Expected:
    - The first is stored; the cycle and self-reference raise AssetCycleError, the foreign asset NotFoundError.
    """
    owner, site = await _owned_site()
    meter, kulkas = await make_asset(site, "Meter utama", "site_total"), await make_asset(site)
    _, other_site = await _owned_site()
    foreign = await make_asset(other_site)
    principal = PrincipalModel(id=owner, kind=PrincipalKind.DEMO)

    async with get_session_factory()() as session:
        sites = SiteService(SqlAlchemySiteRepository(session))
        service = AssetService(
            SqlAlchemyAssetRepository(session), sites, AuditService(SqlAlchemyAuditRepository(session))
        )
        locked = await sites.lock_owned(site, principal)
        await service.relate(locked, meter, kulkas, RelationKind.CONTAINS)
        with pytest.raises(AssetCycleError):
            await service.relate(locked, kulkas, meter, RelationKind.CONTAINS)
        with pytest.raises(AssetCycleError):
            await service.relate(locked, meter, meter, RelationKind.UNKNOWN_OVERLAP)
        with pytest.raises(NotFoundError):
            await service.relate(locked, meter, foreign, RelationKind.DISJOINT)
        await session.commit()

    assert (await execute("SELECT count(*) FROM asset_relations WHERE site_id = :id", id=site))[0][0] == 1


async def test_audit_events_are_append_only() -> None:
    """
    Condition:
    - Something tries to rewrite an audit event.

    Expected:
    - The database refuses it.
    """
    owner, site = await _owned_site()
    await execute(
        "INSERT INTO audit_events (id, site_id, actor_principal_id, action, subject_type, subject_id)"
        " VALUES (gen_random_uuid(), :site, :actor, 'asset.created', 'asset', gen_random_uuid())",
        site=site,
        actor=owner,
    )

    with pytest.raises(DBAPIError, match="append-only"):
        await execute("UPDATE audit_events SET action = 'x' WHERE site_id = :id", id=site)


async def test_site_settings_change_is_audited(client: AsyncClient, acting: Callable[[UUID], dict]) -> None:
    """
    Condition:
    - The owner renames the site.

    Expected:
    - One audit event records it.
    """
    owner, site = await _owned_site()

    await client.patch(f"/api/v1/sites/{site}", json={"name": "Rumah Bandung"}, headers=acting(owner))

    assert (await execute("SELECT action FROM audit_events WHERE site_id = :id", id=site))[0][0] == "site.updated"
