"""AT-41 owner isolation. Every data route joins this table in the spec that adds it."""

from collections.abc import Callable
from uuid import UUID

import pytest
from httpx import AsyncClient

from tests.integration.conftest import (
    execute,
    make_asset,
    make_binding,
    make_principal,
    make_site,
    make_source,
)

pytestmark = pytest.mark.integration

# (method, path template, JSON body). Placeholders name the other owner's site, asset, source and binding.
FOREIGN_ROUTES = [
    ("GET", "/api/v1/sites/{site}", None),
    ("PATCH", "/api/v1/sites/{site}", {"name": "Diambil alih"}),
    ("GET", "/api/v1/sites/{site}/assets", None),
    ("POST", "/api/v1/sites/{site}/assets", {"name": "Penyusup", "scope_kind": "device"}),
    ("GET", "/api/v1/assets/{asset}", None),
    ("PATCH", "/api/v1/assets/{asset}", {"name": "Diambil alih"}),
    ("POST", "/api/v1/assets/{asset}/bindings", {"source_id": "{source}", "effective_from": "2026-10-01T00:00:00Z"}),
    ("DELETE", "/api/v1/assets/{asset}/bindings/{binding}", None),
    ("GET", "/api/v1/sites/{site}/summary?preset=last_7_days", None),
    ("GET", "/api/v1/assets/{asset}/summary?preset=last_7_days", None),
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
    ids = {"site": site, "asset": asset, "source": source, "binding": binding}
    if body is not None:
        body = {key: value.format(**ids) if isinstance(value, str) else value for key, value in body.items()}

    response = await client.request(method, path.format(**ids), json=body, headers=acting(intruder))

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"
    assert (await execute("SELECT name FROM sites WHERE id = :id", id=site))[0][0] == "Rumah"
    assert (await execute("SELECT name FROM assets WHERE id = :id", id=asset))[0][0] == "Kulkas"
    assert (await execute("SELECT count(*) FROM assets WHERE site_id = :id", id=site))[0][0] == 1
    assert (await execute("SELECT effective_to FROM bindings WHERE id = :id", id=binding))[0][0] is None
    assert (await execute("SELECT count(*) FROM audit_events WHERE site_id = :id", id=site))[0][0] == 0
