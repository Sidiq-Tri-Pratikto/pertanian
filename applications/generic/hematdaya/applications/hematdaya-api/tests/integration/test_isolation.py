"""AT-41 owner isolation. Every data route joins this table in the spec that adds it."""

from collections.abc import Callable
from uuid import UUID

import pytest
from httpx import AsyncClient

from tests.integration.conftest import execute, make_principal, make_site

pytestmark = pytest.mark.integration

# (method, path template, JSON body). ``{site}`` is the other owner's site.
FOREIGN_ROUTES = [
    ("GET", "/api/v1/sites/{site}", None),
    ("PATCH", "/api/v1/sites/{site}", {"name": "Diambil alih"}),
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

    response = await client.request(method, path.format(site=site), json=body, headers=acting(intruder))

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"
    assert (await execute("SELECT name FROM sites WHERE id = :id", id=site))[0][0] == "Rumah"
