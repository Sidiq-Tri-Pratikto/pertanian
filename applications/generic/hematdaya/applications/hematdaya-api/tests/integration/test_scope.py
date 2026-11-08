"""Scope selection and preview through real owned site transactions."""

import asyncio
from collections.abc import Callable
from datetime import datetime
from itertools import combinations
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import text

from app.assets.service.service import AssetService
from app.audit.service.service import AuditService
from app.core.errors.base import RequestInvalidError
from app.sites.repository.sqlalchemy.repository import SqlAlchemySiteRepository
from tests.integration.conftest import (
    execute,
    make_asset,
    make_principal,
    make_site,
    make_source,
    make_switchable_scope_site,
    scope_confirmation,
    scope_path,
    scope_state,
    start_demo,
    summary,
)

pytestmark = pytest.mark.integration
DAY = {"start_date": "2026-10-25", "end_date": "2026-10-25"}


async def test_named_overlap_preview_and_parent_save(client: AsyncClient) -> None:
    """The legacy scope reports conflicts, while saving only the parent produces exactly 10 kWh."""
    demo = await start_demo(client, "h-scope")
    path, auth = scope_path(demo["site_id"]), demo["auth"]
    initial = await client.get(path, headers=auth)
    assert initial.status_code == 200, initial.text
    base = initial.json()
    assert base["selection_revision"] == 0
    original = await summary(client, demo, **DAY)
    by_name = {item["name"]: item["asset_id"] for item in original["assets"]}
    assert set(base["selected_asset_ids"]) == set(by_name.values())
    assert original["selection_revision"] is None and original["binding_revision"] == base["binding_revision"]
    before = await scope_state(demo["site_id"])

    invalid = {"selected_asset_ids": [by_name["Meter utama"], by_name["TV"]], "period": DAY}
    preview = await client.post(f"{path}/preview", headers=auth, json=invalid)
    assert preview.status_code == 200, preview.text
    assert preview.json()["summary"]["energy_kwh"] is None
    rejected = await client.put(path, headers=auth, json=scope_confirmation(invalid, preview.json()))
    assert rejected.status_code == 409, rejected.text
    error = rejected.json()["error"]
    assert error["code"] == "SCOPE_CONFLICT"
    assert error["details"][0]["type"] == "parent_child"
    assert "Meter utama" in error["details"][0]["msg"] and "TV" in error["details"][0]["msg"]
    assert await scope_state(demo["site_id"]) == before

    valid = invalid | {"selected_asset_ids": [by_name["Meter utama"]]}
    preview = await client.post(f"{path}/preview", headers=auth, json=valid)
    assert preview.json()["summary"]["energy_kwh"] == "10.000"
    assert await scope_state(demo["site_id"]) == before
    saved = await client.put(path, headers=auth, json=scope_confirmation(valid, preview.json()))
    assert saved.status_code == 200, saved.text
    assert saved.json()["selected_asset_ids"] == valid["selected_asset_ids"]
    assert saved.json()["selection_revision"] == 1 and saved.json()["binding_revision"] == base["binding_revision"]
    saved_summary = await summary(client, demo, **DAY)
    assert saved_summary["energy_kwh"] == "10.000" and saved_summary["selection_revision"] == 1
    assert saved_summary["revision"] == original["revision"]
    assert [row["asset_id"] for row in saved_summary["scope"]["included"]] == valid["selected_asset_ids"]
    assert {row["reason"] for row in saved_summary["scope"]["excluded"]} == {"not_selected"}
    child = await summary(client, demo, f"/api/v1/assets/{by_name['TV']}/summary", **DAY)
    assert child["energy_kwh"] == "0.360"

    before_retry = await scope_state(demo["site_id"])
    retry = await client.put(path, headers=auth, json=scope_confirmation(valid, preview.json() | saved.json()))
    assert retry.status_code == 200, retry.text
    assert await scope_state(demo["site_id"]) == before_retry


async def test_same_source_cannot_count_twice_even_without_readings(
    client: AsyncClient, acting: Callable[[UUID], dict]
) -> None:
    """Positive disjointness does not override intersecting effective authority from one source."""
    owner = await make_principal()
    site = await make_site(owner)
    first, second = await make_asset(site, "Utara"), await make_asset(site, "Selatan")
    source = await make_source(site)
    start = datetime.fromisoformat("2026-10-24T17:00:00Z")
    await execute(
        "INSERT INTO bindings (id, site_id, asset_id, source_id, effective_from, authoritative) VALUES "
        "(gen_random_uuid(), :site, :first, :source, :start, true), "
        "(gen_random_uuid(), :site, :second, :source, :start, false)",
        site=site,
        first=first,
        second=second,
        source=source,
        start=start,
    )
    await execute(
        "INSERT INTO asset_relations (id, site_id, from_asset_id, to_asset_id, kind) "
        "VALUES (gen_random_uuid(), :site, :first, :second, 'disjoint')",
        site=site,
        first=first,
        second=second,
    )
    auth = acting(owner)
    path = scope_path(str(site))
    proposal = {"selected_asset_ids": [str(first), str(second)], "period": DAY}
    current = (await client.get(path, headers=auth)).json()
    assert [issue["type"] for issue in current["issues"]] == ["shared_source"]
    preview = (await client.post(f"{path}/preview", headers=auth, json=proposal)).json()
    issue = preview["summary"]["scope"]["issues"][0]
    assert issue["type"] == "shared_source" and set(issue["asset_ids"]) == set(proposal["selected_asset_ids"])
    assert preview["summary"]["energy_unavailable_reason"] == "scope_conflict"
    response = await client.put(path, headers=auth, json=scope_confirmation(proposal, preview))
    assert response.status_code == 409 and response.json()["error"]["details"][0]["type"] == "shared_source"
    body = await summary(client, {"site_id": site, "auth": auth}, **DAY)
    assert body["scope"]["issues"] == [issue]

    await execute(
        "UPDATE bindings SET effective_to = :middle WHERE asset_id = :first",
        middle=datetime.fromisoformat("2026-10-25T05:00:00Z"),
        first=first,
    )
    await execute(
        "UPDATE bindings SET effective_from = :middle WHERE asset_id = :second",
        middle=datetime.fromisoformat("2026-10-25T05:00:00Z"),
        second=second,
    )
    await execute(
        "INSERT INTO measurements (source_id, identity_key, kind, interval_start, interval_end, "
        "energy_mwh, quality, received_at) VALUES "
        "(:source, 'before', 'interval_energy', '2026-10-25T04:00:00Z', '2026-10-25T05:00:00Z', "
        "1000000, 'valid', now()), "
        "(:source, 'after', 'interval_energy', '2026-10-25T05:00:00Z', '2026-10-25T06:00:00Z', "
        "2000000, 'valid', now())",
        source=source,
    )
    adjacent = await client.post(f"{path}/preview", headers=auth, json=proposal)
    assert adjacent.json()["summary"]["scope"]["valid"] is True
    assert adjacent.json()["summary"]["energy_kwh"] == "3.000"
    confirmed = await client.put(path, headers=auth, json=scope_confirmation(proposal, adjacent.json()))
    assert confirmed.status_code == 200, confirmed.text
    assert (await summary(client, {"site_id": site, "auth": auth}, **DAY))["energy_kwh"] == "3.000"


async def test_authority_and_disjoint_preview_and_commit_together(client: AsyncClient) -> None:
    """One projected state resolves alternate sources and replaces both directions of unknown evidence."""
    demo = await start_demo(client, "h-scope")
    site_id, auth = demo["site_id"], demo["auth"]
    path = scope_path(site_id)
    original = await summary(client, demo, **DAY)
    by_name = {row["name"]: row for row in original["assets"]}
    fridge, pump = (by_name[name]["asset_id"] for name in ("Kulkas", "Pompa Air"))
    source_id = by_name["Kulkas"]["conflict_sources"][0]["source_id"]
    await execute(
        """
        INSERT INTO asset_relations (id, site_id, from_asset_id, to_asset_id, kind) VALUES
        (gen_random_uuid(), CAST(:site AS uuid), CAST(:fridge AS uuid), CAST(:pump AS uuid), 'unknown_overlap'),
        (gen_random_uuid(), CAST(:site AS uuid), CAST(:pump AS uuid), CAST(:fridge AS uuid), 'unknown_overlap')
        """,
        site=site_id,
        fridge=fridge,
        pump=pump,
    )
    period = DAY | {"start_date": "2026-10-24"}
    before = await scope_state(site_id)
    choice = {
        "action": "choose",
        "asset_id": fridge,
        "source_id": source_id,
        "effective_from": "2026-10-23T17:00:00Z",
    }
    select_fridge = {"selected_asset_ids": [fridge], "period": period, "authority_actions": [choice]}
    one = await client.post(f"{path}/preview", headers=auth, json=select_fridge)
    assert one.status_code == 200, one.text
    assert one.json()["summary"]["energy_kwh"] == "2.000"
    assert len({item["binding_id"] for item in one.json()["candidates"]}) == 2

    pair = {"first_asset_id": fridge, "second_asset_id": pump}
    proposal = select_fridge | {"selected_asset_ids": [fridge, pump], "disjoint_confirmations": [pair]}
    preview = await client.post(f"{path}/preview", headers=auth, json=proposal)
    assert preview.status_code == 200, preview.text
    assert preview.json()["summary"]["scope"]["valid"]
    assert await scope_state(site_id) == before
    committed = await client.put(path, headers=auth, json=scope_confirmation(proposal, preview.json()))
    assert committed.status_code == 200, committed.text
    assert committed.json()["binding_revision"] == preview.json()["binding_revision"] + 1
    assert committed.json()["selection_revision"] == 1
    final = await summary(client, demo, **period)
    assert final["energy_kwh"] == preview.json()["summary"]["energy_kwh"]
    assert final["selection_revision"] == 1
    rows = await execute(
        "SELECT action, affected_from, affected_to, detail FROM audit_events "
        "WHERE site_id = CAST(:site AS uuid) AND action LIKE 'scope.%' ORDER BY action",
        site=site_id,
    )
    assert [row.action for row in rows] == [
        "scope.authority_changed",
        "scope.disjoint_confirmed",
        "scope.selection_changed",
    ]
    assert rows[0].affected_from == datetime.fromisoformat(choice["effective_from"]) and rows[0].affected_to is None
    assert rows[1].affected_from is None and rows[2].affected_to is None
    for row in rows[1:]:
        assert row.detail["effect"] == "site_wide"
        assert row.detail["reviewed_period"] == period | {"timezone": "Asia/Jakarta"}

    children = {
        "selected_asset_ids": [by_name[name]["asset_id"] for name in ("Kulkas", "TV", "Router")],
        "period": DAY,
    }
    child_preview = await client.post(f"{path}/preview", headers=auth, json=children)
    assert child_preview.json()["summary"]["energy_kwh"] == "1.600"
    child_saved = await client.put(path, headers=auth, json=scope_confirmation(children, child_preview.json()))
    assert child_saved.status_code == 200, child_saved.text
    child_total = await summary(client, demo, **DAY)
    assert child_total["energy_kwh"] == "1.600"
    assert {row["name"] for row in child_total["assets"]} == {"Kulkas", "TV", "Router"}

    meter = by_name["Meter utama"]["asset_id"]
    meter_pump = {"selected_asset_ids": [meter, pump], "period": DAY}
    unknown = await client.post(f"{path}/preview", headers=auth, json=meter_pump)
    assert [row["type"] for row in unknown.json()["summary"]["scope"]["issues"]] == ["unknown_overlap"]
    meter_pump["disjoint_confirmations"] = [{"first_asset_id": meter, "second_asset_id": pump}]
    disjoint = await client.post(f"{path}/preview", headers=auth, json=meter_pump)
    assert disjoint.json()["summary"]["energy_kwh"] == "10.300"
    confirmed = await client.put(path, headers=auth, json=scope_confirmation(meter_pump, disjoint.json()))
    assert confirmed.status_code == 200, confirmed.text
    assert (await summary(client, demo, **DAY))["energy_kwh"] == "10.300"


async def test_period_changes_stale_even_if_revisions_match(
    client: AsyncClient, acting: Callable[[UUID], dict]
) -> None:
    """A preset rollover or timezone change fences confirmation independently from scope changes."""
    owner = await make_principal()
    site = await make_site(owner)
    asset = await make_asset(site)
    path, auth = scope_path(str(site)), acting(owner)
    proposal = {"selected_asset_ids": [str(asset)], "period": {"preset": "today"}}
    preview = (await client.post(f"{path}/preview", headers=auth, json=proposal)).json()
    await execute("UPDATE sites SET timezone = 'Asia/Makassar' WHERE id = :site", site=site)
    response = await client.put(path, headers=auth, json=scope_confirmation(proposal, preview))
    assert response.status_code == 409 and response.json()["error"]["code"] == "SCOPE_STALE"

    preview = (await client.post(f"{path}/preview", headers=auth, json=proposal)).json()
    await execute("UPDATE sites SET virtual_now = virtual_now + interval '1 day' WHERE id = :site", site=site)
    response = await client.put(path, headers=auth, json=scope_confirmation(proposal, preview))
    assert response.status_code == 409 and response.json()["error"]["code"] == "SCOPE_STALE"
    assert (await client.get(path, headers=auth)).json()["selection_revision"] == 0


async def test_scope_input_limits_and_unordered_pair_uniqueness(
    client: AsyncClient, acting: Callable[[UUID], dict]
) -> None:
    """Reject oversized, duplicate, self-referential, and period-invalid requests before projection."""
    owner = await make_principal()
    site = await make_site(owner)
    a, b = str(await make_asset(site, "Utara")), str(await make_asset(site, "Selatan"))
    path, auth = scope_path(str(site)), acting(owner)
    pair = {"first_asset_id": a, "second_asset_id": b}
    reverse = {"first_asset_id": b, "second_asset_id": a}
    skip = {"action": "skip", "asset_id": a}
    proposal = {"selected_asset_ids": [a], "period": DAY}
    before = await scope_state(str(site))
    for changes in (
        {"selected_asset_ids": []},
        {"selected_asset_ids": [a, a]},
        {"selected_asset_ids": [str(uuid4()) for _ in range(101)]},
        {"authority_actions": [skip, skip]},
        {"authority_actions": [{"action": "skip", "asset_id": str(uuid4())} for _ in range(101)]},
        {"disjoint_confirmations": [pair, reverse]},
        {"disjoint_confirmations": [pair | {"second_asset_id": a}]},
        {"disjoint_confirmations": [pair] * 201},
    ):
        response = await client.post(f"{path}/preview", headers=auth, json=proposal | changes)
        assert response.status_code == 422, response.text
        assert response.json()["error"]["code"] == "VALIDATION_FAILED"
    for period, code in (
        (DAY | {"preset": "today"}, "BAD_REQUEST"),
        ({"start_date": "2026-10-25", "end_date": "2027-10-26"}, "RANGE_TOO_LARGE"),
    ):
        response = await client.post(f"{path}/preview", headers=auth, json=proposal | {"period": period})
        assert response.status_code == 400 and response.json()["error"]["code"] == code
    assert await scope_state(str(site)) == before


async def test_a_pilot_can_confirm_all_190_pairs(client: AsyncClient, acting: Callable[[UUID], dict]) -> None:
    """A full 20-asset selection can add every necessary confirmation in one revision."""
    owner = await make_principal()
    site = await make_site(owner)
    rows = await execute(
        "INSERT INTO assets (id, site_id, name, scope_kind) "
        "SELECT gen_random_uuid(), :site, 'Aset ' || n, 'device' FROM generate_series(1, 20) n RETURNING id",
        site=site,
    )
    members = [str(row.id) for row in rows]
    proposal = {
        "selected_asset_ids": members,
        "period": DAY,
        "disjoint_confirmations": [{"first_asset_id": a, "second_asset_id": b} for a, b in combinations(members, 2)],
    }
    path, auth = scope_path(str(site)), acting(owner)
    unconfirmed = proposal | {"disjoint_confirmations": []}
    refused = (await client.post(f"{path}/preview", headers=auth, json=unconfirmed)).json()
    assert len(refused["summary"]["scope"]["issues"]) == 190
    request = scope_confirmation(unconfirmed, refused)
    first = await client.put(path, headers=auth, json=request)
    second = await client.put(path, headers=auth, json=request)
    assert first.status_code == second.status_code == 409
    details = first.json()["error"]["details"]
    assert len(details) == 20 and details == second.json()["error"]["details"]
    preview = await client.post(f"{path}/preview", headers=auth, json=proposal)
    assert preview.status_code == 200 and preview.json()["summary"]["scope"]["valid"]
    response = await client.put(path, headers=auth, json=scope_confirmation(proposal, preview.json()))
    assert response.status_code == 200, response.text
    assert response.json()["binding_revision"] == 1
    assert len(response.json()["relations"]) == 190

    before = await scope_state(str(site))
    retry = await client.put(path, headers=auth, json=scope_confirmation(proposal, preview.json() | response.json()))
    assert retry.status_code == 200, retry.text
    assert await scope_state(str(site)) == before


async def test_moving_cutoff_requires_revalidation_without_changing_period(
    client: AsyncClient, acting: Callable[[UUID], dict]
) -> None:
    """A source scheduled inside today's window can invalidate a proposal before the dates roll over."""
    owner = await make_principal()
    site = await make_site(owner, virtual_now=datetime.fromisoformat("2026-10-25T00:00:00Z"))
    first, second = await make_asset(site, "Utara"), await make_asset(site, "Selatan")
    source = await make_source(site)
    await execute(
        "INSERT INTO bindings (id, site_id, asset_id, source_id, effective_from, authoritative) VALUES "
        "(gen_random_uuid(), :site, :first, :source, '2026-10-24T17:00:00Z', true), "
        "(gen_random_uuid(), :site, :second, :source, '2026-10-25T01:00:00Z', true)",
        site=site,
        first=first,
        second=second,
        source=source,
    )
    proposal = {
        "selected_asset_ids": [str(first), str(second)],
        "period": {"preset": "today"},
        "disjoint_confirmations": [{"first_asset_id": str(first), "second_asset_id": str(second)}],
    }
    path, auth = scope_path(str(site)), acting(owner)
    preview = await client.post(f"{path}/preview", headers=auth, json=proposal)
    assert preview.json()["summary"]["scope"]["valid"]
    before = await scope_state(str(site))
    await execute("UPDATE sites SET virtual_now = virtual_now + interval '2 hours' WHERE id = :site", site=site)
    response = await client.put(path, headers=auth, json=scope_confirmation(proposal, preview.json()))
    assert response.status_code == 409
    assert response.json()["error"]["details"][0]["type"] == "shared_source"
    assert await scope_state(str(site)) == before


async def _wait_for_lock(pid: int) -> None:
    async with asyncio.timeout(5):
        while not (await execute("SELECT pg_blocking_pids(:pid)", pid=pid))[0][0]:
            await asyncio.sleep(0.01)


@pytest.mark.parametrize("read", ["get", "preview", "summary"])
async def test_scope_reader_waits_at_one_state_against_authority_write(
    client: AsyncClient, acting: Callable[[UUID], dict], monkeypatch: pytest.MonkeyPatch, read: str
) -> None:
    """Hold an owned reader at its snapshot and observe the writer blocked by PostgreSQL itself."""
    owner, site, asset, current, candidate = await make_switchable_scope_site()
    path, auth = scope_path(str(site)), acting(owner)
    proposal = {"selected_asset_ids": [str(asset)], "period": DAY}
    preview = (await client.post(f"{path}/preview", headers=auth, json=proposal)).json()
    first = (await client.put(path, headers=auth, json=scope_confirmation(proposal, preview))).json()
    assert first["selection_revision"] == 1 and first["binding_revision"] == 0
    choice = {
        "action": "choose",
        "asset_id": str(asset),
        "source_id": str(candidate),
        "effective_from": "2026-10-24T17:00:00Z",
    }
    update = scope_confirmation(proposal | {"authority_actions": [choice]}, preview | first)

    reader_entered, release_reader = asyncio.Event(), asyncio.Event()
    writer_pid = asyncio.get_running_loop().create_future()
    real_snapshot = AssetService.snapshot
    real_lock = SqlAlchemySiteRepository.get_owned

    async def hold_first_snapshot(self, locked_site):
        snapshot = await real_snapshot(self, locked_site)
        if locked_site.id == site and not reader_entered.is_set():
            reader_entered.set()
            await release_reader.wait()
        return snapshot

    async def identify_writer(self, site_id, owner_id, *, lock=False):
        if site_id == site and lock is True and not writer_pid.done():
            writer_pid.set_result(await self.session.scalar(text("SELECT pg_backend_pid()")))
        return await real_lock(self, site_id, owner_id, lock=lock)

    async def read_current() -> dict:
        if read == "get":
            response = await client.get(path, headers=auth)
        elif read == "preview":
            response = await client.post(f"{path}/preview", headers=auth, json=proposal)
        else:
            response = await client.get(f"/api/v1/sites/{site}/summary", headers=auth, params=DAY)
        assert response.status_code == 200, response.text
        return response.json()

    monkeypatch.setattr(AssetService, "snapshot", hold_first_snapshot)
    monkeypatch.setattr(SqlAlchemySiteRepository, "get_owned", identify_writer)
    reader = asyncio.create_task(read_current())
    writer = None
    try:
        await asyncio.wait_for(reader_entered.wait(), timeout=5)
        writer = asyncio.create_task(client.put(path, headers=auth, json=update))
        await _wait_for_lock(await asyncio.wait_for(writer_pid, timeout=5))
        assert not writer.done()
    finally:
        release_reader.set()
        if writer is not None:
            after_write = await asyncio.wait_for(writer, timeout=5)
        before = await asyncio.wait_for(reader, timeout=5)
    assert after_write.status_code == 200, after_write.text
    after = await read_current()
    assert before["selection_revision"] == after["selection_revision"] == 1
    assert (before["binding_revision"], after["binding_revision"]) == (0, 1)
    if read == "get":
        assert [row["source_id"] for row in before["authority"]] == [str(current)]
        assert [row["source_id"] for row in after["authority"]] == [str(candidate)]
    else:
        old_summary = before["summary"] if read == "preview" else before
        new_summary = after["summary"] if read == "preview" else after
        assert (old_summary["energy_kwh"], new_summary["energy_kwh"]) == ("1.000", "2.000")
        assert (old_summary["revision"], new_summary["revision"]) == (0, 1)


async def test_late_failure_rolls_back_every_scope_edit(
    client: AsyncClient, acting: Callable[[UUID], dict], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Fail after bindings, relation, selection, revisions and audits all flushed."""
    owner, site, asset, _, candidate = await make_switchable_scope_site()
    second = await make_asset(site, "Terpisah")
    path, auth = scope_path(str(site)), acting(owner)
    proposal = {
        "selected_asset_ids": [str(asset), str(second)],
        "period": DAY,
        "authority_actions": [
            {
                "action": "choose",
                "asset_id": str(asset),
                "source_id": str(candidate),
                "effective_from": "2026-10-24T17:00:00Z",
            }
        ],
        "disjoint_confirmations": [{"first_asset_id": str(asset), "second_asset_id": str(second)}],
    }
    before = await scope_state(str(site))
    preview = await client.post(f"{path}/preview", headers=auth, json=proposal)
    assert preview.status_code == 200 and await scope_state(str(site)) == before
    request = scope_confirmation(proposal, preview.json())
    real_audit = AuditService.record
    events = []

    async def fail_after_auditing(self, **fields):
        await real_audit(self, **fields)
        events.append(fields["action"])
        if fields["action"] == "scope.disjoint_confirmed":
            raise RequestInvalidError()

    with monkeypatch.context() as patch:
        patch.setattr(AuditService, "record", fail_after_auditing)
        response = await client.put(path, headers=auth, json=request)
    assert response.status_code == 400, response.text
    assert events == ["scope.selection_changed", "scope.authority_changed", "scope.disjoint_confirmed"]
    assert await scope_state(str(site)) == before
    success = await client.put(path, headers=auth, json=request)
    assert success.status_code == 200, success.text
    assert (success.json()["selection_revision"], success.json()["binding_revision"]) == (1, 1)


async def test_same_base_put_can_only_commit_once(client: AsyncClient, acting: Callable[[UUID], dict]) -> None:
    """Different membership changes using one base are serialized on the site row."""
    owner = await make_principal()
    site = await make_site(owner)
    first, second = await make_asset(site, "Satu"), await make_asset(site, "Dua")
    path, auth = scope_path(str(site)), acting(owner)
    proposal = {"selected_asset_ids": [str(first)], "period": DAY}
    preview = (await client.post(f"{path}/preview", headers=auth, json=proposal)).json()
    one, two = await asyncio.gather(
        client.put(path, headers=auth, json=scope_confirmation(proposal, preview)),
        client.put(
            path, headers=auth, json=scope_confirmation(proposal | {"selected_asset_ids": [str(second)]}, preview)
        ),
    )
    assert sorted([one.status_code, two.status_code]) == [200, 409]
    loser = two if two.status_code == 409 else one
    assert loser.json()["error"]["code"] == "SCOPE_STALE"
    rows = await execute(
        "SELECT count(*) FROM audit_events WHERE site_id = :site AND action = 'scope.selection_changed'", site=site
    )
    assert rows[0][0] == 1


async def test_scope_put_rechecks_binding_fence_after_waiting_for_writer(
    client: AsyncClient, acting: Callable[[UUID], dict], monkeypatch: pytest.MonkeyPatch
) -> None:
    """An ordinary binding writer makes a waiting scope confirmation stale."""
    owner, site, asset, _, _ = await make_switchable_scope_site()
    additional = await make_source(site, "Sumber tambahan")
    path, auth = scope_path(str(site)), acting(owner)
    proposal = {"selected_asset_ids": [str(asset)], "period": DAY}
    preview = (await client.post(f"{path}/preview", headers=auth, json=proposal)).json()

    binding_audited, release_binding = asyncio.Event(), asyncio.Event()
    scope_pid = asyncio.get_running_loop().create_future()
    real_audit = AuditService.record
    real_lock = SqlAlchemySiteRepository.get_owned

    async def hold_binding_write(self, **fields):
        await real_audit(self, **fields)
        if fields["site_id"] == site:
            binding_audited.set()
            await release_binding.wait()

    async def identify_scope_put(self, site_id, owner_id, *, lock=False):
        if site_id == site and lock is True and binding_audited.is_set() and not scope_pid.done():
            scope_pid.set_result(await self.session.scalar(text("SELECT pg_backend_pid()")))
        return await real_lock(self, site_id, owner_id, lock=lock)

    monkeypatch.setattr(AuditService, "record", hold_binding_write)
    monkeypatch.setattr(SqlAlchemySiteRepository, "get_owned", identify_scope_put)
    binding_writer = asyncio.create_task(
        client.post(
            f"/api/v1/assets/{asset}/bindings",
            headers=auth,
            json={"source_id": str(additional), "effective_from": "2026-10-24T17:00:00Z", "authoritative": False},
        )
    )
    scope_writer = None
    try:
        await asyncio.wait_for(binding_audited.wait(), timeout=5)
        scope_writer = asyncio.create_task(client.put(path, headers=auth, json=scope_confirmation(proposal, preview)))
        await _wait_for_lock(await asyncio.wait_for(scope_pid, timeout=5))
    finally:
        release_binding.set()
        binding_response = await asyncio.wait_for(binding_writer, timeout=5)
        if scope_writer is not None:
            scope_response = await asyncio.wait_for(scope_writer, timeout=5)
    assert binding_response.status_code == 201, binding_response.text
    assert scope_response.status_code == 409 and scope_response.json()["error"]["code"] == "SCOPE_STALE"
    current = (await client.get(path, headers=auth)).json()
    assert (current["selection_revision"], current["binding_revision"]) == (0, 1)


async def test_skip_keeps_authority_and_cannot_hide_unresolved_candidates(
    client: AsyncClient, acting: Callable[[UUID], dict]
) -> None:
    """Skipping leaves an established source authoritative and does not resolve competing candidates."""
    owner, site, asset, _, _ = await make_switchable_scope_site()
    path, auth = scope_path(str(site)), acting(owner)
    proposal = {
        "selected_asset_ids": [str(asset)],
        "period": DAY,
        "authority_actions": [{"action": "skip", "asset_id": str(asset)}],
    }
    preview = (await client.post(f"{path}/preview", headers=auth, json=proposal)).json()
    assert preview["summary"]["energy_kwh"] == "1.000"
    saved = await client.put(path, headers=auth, json=scope_confirmation(proposal, preview))
    assert saved.status_code == 200 and saved.json()["binding_revision"] == preview["binding_revision"]

    await execute("UPDATE bindings SET authoritative = false WHERE asset_id = :asset", asset=asset)
    before = await scope_state(str(site))
    unresolved = (await client.post(f"{path}/preview", headers=auth, json=proposal)).json()
    assert unresolved["summary"]["energy_kwh"] is None
    assert [row["type"] for row in unresolved["summary"]["scope"]["issues"]] == ["source_conflict"]
    denied = await client.put(path, headers=auth, json=scope_confirmation(proposal, unresolved))
    assert denied.status_code == 409 and await scope_state(str(site)) == before


async def test_containment_refuses_proposal_even_before_any_time_elapsed(client: AsyncClient) -> None:
    """The refusal remains visible at local midnight, including for an explicit disjoint confirmation."""
    demo = await start_demo(client, "h-scope")
    path, auth = scope_path(demo["site_id"]), demo["auth"]
    original = await summary(client, demo, **DAY)
    by_name = {row["name"]: row["asset_id"] for row in original["assets"]}
    meter, child = by_name["Meter utama"], by_name["TV"]
    proposal = {"selected_asset_ids": [meter, child], "period": {"preset": "today"}}
    preview = (await client.post(f"{path}/preview", headers=auth, json=proposal)).json()
    report = preview["summary"]
    assert report["window"]["effective_end"] == report["window"]["start"]
    assert report["energy_unavailable_reason"] == "scope_conflict"
    assert [issue["type"] for issue in report["scope"]["issues"]] == ["parent_child"]
    denied = await client.post(
        f"{path}/preview",
        headers=auth,
        json=proposal | {"disjoint_confirmations": [{"first_asset_id": meter, "second_asset_id": child}]},
    )
    assert denied.status_code == 409 and denied.json()["error"]["details"][0]["type"] == "parent_child"
