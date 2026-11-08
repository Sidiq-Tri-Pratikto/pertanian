"""AT-41 owner isolation. Every data route joins this table in the spec that adds it."""

import secrets
from collections.abc import AsyncIterator, Callable
from uuid import UUID

import pytest
from httpx import AsyncClient

from tests.integration.conftest import (
    execute,
    failure_records,
    make_asset,
    make_binding,
    make_import,
    make_principal,
    make_site,
    make_source,
    scope_confirmation,
    scope_path,
    scope_state,
)

pytestmark = pytest.mark.integration
DAY = {"start_date": "2026-10-25", "end_date": "2026-10-25"}

# (method, path template, JSON body). Placeholders name the other owner's site, asset, source and binding.
FOREIGN_ROUTES = [
    ("GET", "/api/v1/sites/{site}", None),
    ("PATCH", "/api/v1/sites/{site}", {"name": "Diambil alih"}),
    ("GET", "/api/v1/sites/{site}/assets", None),
    ("GET", "/api/v1/sites/{site}/assets?include_archived=true", None),
    ("POST", "/api/v1/sites/{site}/assets", {"name": "Penyusup", "scope_kind": "device"}),
    ("GET", "/api/v1/assets/{asset}", None),
    ("POST", "/api/v1/assets/{asset}/bindings", {"source_id": "{source}", "effective_from": "2026-10-01T00:00:00Z"}),
    ("DELETE", "/api/v1/assets/{asset}/bindings/{binding}", None),
    ("GET", "/api/v1/sites/{site}/summary?preset=last_7_days", None),
    ("GET", "/api/v1/assets/{asset}/summary?preset=last_7_days", None),
    ("GET", "/api/v1/assets/{asset}/measurements?preset=last_7_days", None),
    ("GET", "/api/v1/assets/{asset}/comparison?preset=last_7_days", None),
    ("GET", "/api/v1/sites/{site}/insights?preset=last_7_days", None),
    ("POST", "/api/v1/sites/{site}/imports/preview", None),
    ("GET", "/api/v1/imports/{import}", None),
    ("GET", "/api/v1/imports/{import}/errors", None),
    ("POST", "/api/v1/imports/{import}/commit", {"acknowledge_skipped": False}),
    ("GET", "/api/v1/sites/{site}/insights/hidden?preset=last_7_days", None),
]


@pytest.mark.parametrize(("method", "path", "body"), FOREIGN_ROUTES)
async def test_foreign_resources_look_missing(
    client: AsyncClient, acting: Callable[[UUID], dict], method: str, path: str, body: dict | None
) -> None:
    """
    Condition:
    - Principal B calls a route on principal A's site.

    Expected:
    - NOT_FOUND, never FORBIDDEN, and A's site is unchanged.
    """
    owner, intruder = await make_principal(), await make_principal()
    site = await make_site(owner)
    asset = await make_asset(site)
    source = await make_source(site)
    binding = await make_binding(site, asset, source)
    import_id = await make_import(site)
    ids = {"site": site, "asset": asset, "source": source, "binding": binding, "import": import_id}
    if body is not None:
        body = {key: value.format(**ids) if isinstance(value, str) else value for key, value in body.items()}

    # The commit route checks this header before ownership, and it answers the same for any import.
    headers = acting(intruder) | {"Idempotency-Key": secrets.token_urlsafe(16)}

    response = await client.request(method, path.format(**ids), json=body, headers=headers)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"
    assert (await execute("SELECT status FROM imports WHERE id = :id", id=import_id))[0][0] == "previewed"
    assert (await execute("SELECT name FROM sites WHERE id = :id", id=site))[0][0] == "Rumah"
    assert (await execute("SELECT name FROM assets WHERE id = :id", id=asset))[0][0] == "Kulkas"
    assert (await execute("SELECT count(*) FROM assets WHERE site_id = :id", id=site))[0][0] == 1
    assert (await execute("SELECT effective_to FROM bindings WHERE id = :id", id=binding))[0][0] is None
    assert (await execute("SELECT count(*) FROM audit_events WHERE site_id = :id", id=site))[0][0] == 0
    assert (await execute("SELECT count(*) FROM imports WHERE site_id = :id", id=site))[0][0] == 1


@pytest.mark.usefixtures("capture_app_logs")
@pytest.mark.parametrize("change", [{"name": "FAKE_FOREIGN_EDIT_PASSWORD"}, {"archived": True}, {"archived": False}])
async def test_foreign_patch_cannot_edit_archive_or_restore(
    client: AsyncClient, acting: Callable[[UUID], dict], caplog: pytest.LogCaptureFixture, change: dict
) -> None:
    """
    Condition:
    - An intruder attempts a metadata edit, archive, or restore of another owner's asset.

    Expected:
    - One sanitized not-found failure is recorded. The owned detail, bindings and audit remain unchanged.
    """
    owner, intruder = await make_principal(), await make_principal()
    site = await make_site(owner)
    asset = await make_asset(site)
    await make_binding(site, asset, await make_source(site))
    if change.get("archived") is False:
        await execute("UPDATE assets SET archived_at = now() WHERE id = :id", id=asset)
    path = f"/api/v1/assets/{asset}"
    before = (await client.get(path, headers=acting(owner))).json()

    response = await client.patch(path, json=change, headers=acting(intruder))

    assert response.status_code == 404
    error = response.json()["error"]
    assert error["code"] == "NOT_FOUND"
    assert error["message"] == "Data yang diminta tidak ditemukan. Periksa alamatnya lalu coba lagi."
    assert error["recovery"] == {"retryable": False}
    records = failure_records(caplog)
    assert len(records) == 1
    assert records[0]["reference_id"] == error["request_id"]
    assert "FAKE_FOREIGN_EDIT_PASSWORD" not in response.text
    assert "FAKE_FOREIGN_EDIT_PASSWORD" not in caplog.text
    assert (await client.get(path, headers=acting(owner))).json() == before
    assert (await execute("SELECT count(*) FROM audit_events WHERE site_id = :id", id=site))[0][0] == 0


async def test_a_foreign_preview_answers_before_its_body_is_read(
    client: AsyncClient, acting: Callable[[UUID], dict]
) -> None:
    """
    Condition:
    - Principal B streams an upload to principal A's site.

    Expected:
    - NOT_FOUND, with no part of the body consumed, so a foreign upload costs nothing.
    """
    owner, intruder = await make_principal(), await make_principal()
    site = await make_site(owner)
    consumed = {"chunks": 0}

    async def body_stream() -> AsyncIterator[bytes]:
        consumed["chunks"] += 1
        yield b"--limit\r\n"

    response = await client.post(
        f"/api/v1/sites/{site}/imports/preview",
        content=body_stream(),
        headers=acting(intruder) | {"Content-Type": "multipart/form-data; boundary=limit"},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"
    assert consumed["chunks"] == 0
    assert (await execute("SELECT count(*) FROM imports WHERE site_id = :id", id=site))[0][0] == 0


async def test_scope_owner_and_nested_site_isolation(client: AsyncClient, acting: Callable[[UUID], dict]) -> None:
    """Another owner or site cannot be addressed through any part of a proposal."""
    owner, intruder = await make_principal(), await make_principal()
    site, other_site, same_owner_site = await make_site(owner), await make_site(intruder), await make_site(owner)
    first, wrong_asset = await make_asset(site), await make_asset(site, "Utara")
    other, same_owner_other = await make_asset(other_site), await make_asset(same_owner_site)
    other_source, wrong_source = await make_source(other_site), await make_source(site)
    await make_binding(site, wrong_asset, wrong_source)
    first, other, same_owner_other = str(first), str(other), str(same_owner_other)
    path, auth = scope_path(str(site)), acting(owner)
    proposal = {"selected_asset_ids": [first], "period": DAY}
    preview = (await client.post(f"{path}/preview", headers=auth, json=proposal)).json()
    confirm = scope_confirmation(proposal, preview)
    before = await scope_state(str(site))

    for method, route, body in (
        ("GET", path, None),
        ("POST", f"{path}/preview", proposal),
        ("PUT", path, confirm),
    ):
        response = await client.request(method, route, json=body, headers=acting(intruder))
        assert response.status_code == 404 and response.json()["error"]["code"] == "NOT_FOUND"

    for changes in (
        {"selected_asset_ids": [other]},
        {"selected_asset_ids": [same_owner_other]},
        {"disjoint_confirmations": [{"first_asset_id": first, "second_asset_id": other}]},
        {"authority_actions": [{"action": "skip", "asset_id": same_owner_other}]},
        *(
            {
                "authority_actions": [
                    {
                        "action": "choose",
                        "asset_id": first,
                        "source_id": str(source),
                        "effective_from": "2026-10-24T17:00:00Z",
                    }
                ]
            }
            for source in (other_source, wrong_source)
        ),
    ):
        proposed = await client.post(f"{path}/preview", headers=auth, json=proposal | changes)
        saved = await client.put(path, headers=auth, json=confirm | changes)
        for response in (proposed, saved):
            assert response.status_code == 404 and response.json()["error"]["code"] == "NOT_FOUND"
    assert await scope_state(str(site)) == before


@pytest.mark.usefixtures("capture_app_logs")
async def test_scope_overlap_reports_safe_labels_and_correlates_one_generic_record(
    client: AsyncClient, acting: Callable[[UUID], dict], caplog: pytest.LogCaptureFixture
) -> None:
    """Conflict details identify owned labels while keeping fake credentials and emails out of the record."""
    fake_key, fake_email = "sk-fakeScopeToken12345", "scope@example.com"
    owner = await make_principal()
    site = await make_site(owner)
    meter = await make_asset(site, "Meter utama", "site_total")
    child = await make_asset(site, f"Kulkas {fake_key} {fake_email}")
    await execute("UPDATE assets SET parent_asset_id = :parent WHERE id = :child", parent=meter, child=child)
    path, auth = scope_path(str(site)), acting(owner)
    proposal = {"selected_asset_ids": [str(meter), str(child)], "period": DAY}
    preview = (await client.post(f"{path}/preview", headers=auth, json=proposal)).json()
    before = await scope_state(str(site))
    response = await client.put(path, headers=auth, json=scope_confirmation(proposal, preview))
    assert response.status_code == 409
    error = response.json()["error"]
    assert error["code"] == "SCOPE_CONFLICT" and error["recovery"] == {"retryable": False}
    (detail,) = error["details"]
    assert detail["type"] == "parent_child" and detail["loc"] == ["body", "selected_asset_ids"]
    assert "Meter utama" in detail["msg"] and "Kulkas [Filtered] [Filtered]" in detail["msg"]
    records = failure_records(caplog)
    assert len(records) == 1 and records[0]["reference_id"] == error["request_id"]
    assert records[0]["code"] == "APP-SCOPE-OVERLAP"
    assert "Meter utama" not in caplog.text and "Kulkas" not in caplog.text
    for private in (fake_key, fake_email):
        assert private not in response.text and private not in caplog.text
    assert await scope_state(str(site)) == before
