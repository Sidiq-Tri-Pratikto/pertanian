"""Sites over real Postgres: ownership, settings and the one-clock rule."""

from collections.abc import Callable
from datetime import datetime
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.exc import IntegrityError

from tests.integration.conftest import execute, make_principal, make_site

pytestmark = pytest.mark.integration


async def test_owner_reads_and_updates_site(client: AsyncClient, acting: Callable[[UUID], dict]) -> None:
    """
    Condition:
    - Principal A owns a demo site on the virtual Monday.

    Expected:
    - A reads it with neutral defaults and the virtual now, then renames it and changes its timezone.
    """
    owner = await make_principal()
    site = await make_site(owner)

    read = await client.get(f"/api/v1/sites/{site}", headers=acting(owner))
    updated = await client.patch(
        f"/api/v1/sites/{site}", json={"name": "Rumah Bandung", "timezone": "Asia/Makassar"}, headers=acting(owner)
    )

    assert read.status_code == 200
    assert read.json() | {"id": None} == {
        "id": None,
        "name": "Rumah",
        "kind": "demo",
        "context": "unspecified",
        "timezone": "Asia/Jakarta",
        "currency": "IDR",
        "now": "2026-10-25T17:00:00Z",
    }
    assert updated.status_code == 200
    assert (updated.json()["name"], updated.json()["timezone"]) == ("Rumah Bandung", "Asia/Makassar")


async def test_invalid_timezone_changes_nothing(client: AsyncClient, acting: Callable[[UUID], dict]) -> None:
    """
    Condition:
    - The owner saves a fixed offset instead of an IANA name, together with a new name.

    Expected:
    - A field message names the timezone and neither field changes.
    """
    owner = await make_principal()
    site = await make_site(owner)

    response = await client.patch(
        f"/api/v1/sites/{site}", json={"name": "Baru", "timezone": "UTC+7"}, headers=acting(owner)
    )

    assert response.status_code == 422
    assert response.json()["error"]["details"][0]["loc"] == ["body", "timezone"]
    assert "Zona waktu" in response.json()["error"]["details"][0]["msg"]
    assert (await execute("SELECT name, timezone FROM sites WHERE id = :id", id=site))[0] == ("Rumah", "Asia/Jakarta")


async def test_missing_credentials_are_refused(client: AsyncClient) -> None:
    """
    Condition:
    - No credential, then a malformed one, on a protected route.

    Expected:
    - Both answer UNAUTHORIZED with a Bearer challenge and no reason.
    """
    site = uuid4()

    missing = await client.get(f"/api/v1/sites/{site}")
    malformed = await client.get(f"/api/v1/sites/{site}", headers={"Authorization": "Bearer a b"})

    for response in (missing, malformed):
        assert response.status_code == 401
        assert response.headers["www-authenticate"] == "Bearer"
        assert response.json()["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.parametrize(
    ("kind", "virtual_now"),
    [("standard", datetime.fromisoformat("2026-10-25T17:00:00+00:00")), ("demo", None)],
)
async def test_database_enforces_one_clock_per_site(kind: str, virtual_now: datetime | None) -> None:
    """
    Condition:
    - A standard site with a virtual time, or a demo site without one.

    Expected:
    - The database refuses both.
    """
    owner = await make_principal()

    with pytest.raises(IntegrityError, match="sites_virtual_now_only_for_demo"):
        await execute(
            "INSERT INTO sites (id, owner_principal_id, kind, name, virtual_now)"
            " VALUES (gen_random_uuid(), :owner, :kind, 'x', :virtual_now)",
            owner=owner,
            kind=kind,
            virtual_now=virtual_now,
        )
