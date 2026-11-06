"""Import acceptance against the real API and worker (AC61, AC62)."""

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

import pytest
from httpx import AsyncClient, Response
from sqlalchemy import text

from app.core.database import get_engine

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("clean_tables")]
Fixture = Callable[..., Awaitable[Any]]


async def status(client: AsyncClient, run_id: str, **params: int) -> dict:
    response = await client.get(f"/api/v1/imports/{run_id}", params=params)
    assert response.status_code == 200, response.text
    return response.json()


async def act(client: AsyncClient, party: str, run: dict, action: str, *, version: int | None = None) -> Response:
    return await client.post(
        f"/api/v1/imports/{run['id']}/{action}",
        json={"acting_party_id": party, "expected_version": run["version"] if version is None else version},
        headers={"Idempotency-Key": f"{action}-{run['id']}-{version}"},
    )


async def test_thousand_row_preview_and_checkpointed_cancel(
    client: AsyncClient,
    sign_up: Fixture,
    upload: Fixture,
    work: Fixture,
) -> None:
    """
    Condition:
    - A managing party uploads 1,000 rows, requests apply after preview and cancels after a checkpoint.

    Expected:
    - Validation and preview advance independently without writes, and cancellation preserves only committed work.
    """
    party = (await sign_up(client, "large@example.com"))["active_party_id"]
    rows = [{"external_id": f"external-{index:04d}", "fields": {"title": f"Filter {index}"}} for index in range(1_000)]
    run = await upload(client, party, "large", rows)
    assert run["validation"]["status"] == "PENDING" and run["preview"]["status"] == "NOT_STARTED"
    assert (await act(client, party, run, "apply")).json()["error"]["code"] == "INVALID_TRANSITION"
    await work()
    validated = await status(client, run["id"])
    assert validated["validation"]["status"] == "SUCCEEDED"
    assert validated["preview"] == {"status": "PENDING", "processed": 0, "error_code": None}
    await work()
    assert (await status(client, run["id"]))["preview"]["processed"] == 50
    await work(drain=True)
    review = await status(client, run["id"], limit=100, offset=900)
    assert review["preview"]["status"] == "SUCCEEDED" and review["preview"]["processed"] == 1_000
    assert len(review["rows"]) == 100 and review["next_offset"] is None
    assert all(row["action"] == "CREATE" for row in review["rows"])
    assert (await client.get("/api/v1/inventions")).json() == []
    assert (await act(client, party, review, "apply", version=1)).json()["error"]["code"] == "STALE_VERSION"
    queued = await act(client, party, review, "apply")
    assert queued.status_code == 202 and queued.json()["apply"]["status"] == "PENDING", queued.text
    await work()
    working = await status(client, run["id"])
    assert working["apply"]["processed"] == working["committed"] == 50
    cancelled = await act(client, party, working, "cancel")
    assert cancelled.status_code == 202 and cancelled.json()["apply"]["status"] == "CANCELLED"
    assert cancelled.json()["committed"] == 50
    await work(drain=True)
    assert len((await client.get("/api/v1/inventions")).json()) == 50


async def test_repeated_import_preserves_omitted_fields_and_source_claims(
    client: AsyncClient,
    sign_up: Fixture,
    upload: Fixture,
    work: Fixture,
    new_client: Callable[[], AsyncClient],
) -> None:
    """
    Condition:
    - Two parties import the same key. The first party then repeats it with a partial update.

    Expected:
    - Each party owns one distinct invention, omitted fields survive and reported relationships stay separate.
    """
    party = (await sign_up(client, "first@example.com"))["active_party_id"]
    row = {
        "external_id": "x-123",
        "fields": {"title": "Original", "private_notes": "Mapped secret", "summary": "Keep"},
        "relationship_assertions": [
            {"organization_name": "Same name", "kind": "PARTNERSHIP", "reported_status": "CONFIRMED"}
        ],
    }
    first = await upload(client, party, "first", [row], map_private=True)
    replay = await upload(client, party, "first", [row], map_private=True)
    assert replay == first
    await work(drain=True)
    review = await status(client, first["id"])
    assert "private_notes" in review["rows"][0]["mapped_fields"] and "Mapped secret" not in str(review)
    assert (await act(client, party, review, "apply")).status_code == 202
    await work(drain=True)
    inventions = (await client.get("/api/v1/inventions")).json()
    assert len(inventions) == 1
    invention_id = inventions[0]["id"]
    async with new_client() as second:
        other_party = (await sign_up(second, "second@example.com"))["active_party_id"]
        run = await upload(second, other_party, "first", [row])
        await work(drain=True)
        other_review = await status(second, run["id"])
        assert other_review["rows"][0]["skipped_fields"] == ["private_notes"]
        assert (await act(second, other_party, other_review, "apply")).status_code == 202
        await work(drain=True)
        other = (await second.get("/api/v1/inventions")).json()
        assert len(other) == 1 and other[0]["id"] != invention_id
    row["fields"] = {"title": "Updated", "private_notes": "Skip this"}
    updated = await upload(client, party, "updated", [row])
    await work(drain=True)
    update_review = await status(client, updated["id"])
    assert update_review["rows"][0]["action"] == "UPDATE"
    assert (await act(client, party, update_review, "apply")).status_code == 202
    await work(drain=True)
    draft = (await client.get(f"/api/v1/inventions/{invention_id}")).json()["draft"]
    assert (draft["title"], draft["summary"], draft["private_notes"], draft["claims"]) == (
        "Updated",
        "Keep",
        "Mapped secret",
        [],
    )
    async with get_engine().connect() as connection:
        sources = (await connection.execute(text("SELECT source FROM portability_external_references"))).scalars().all()
    assert len(sources) == 2
    assert all(source["relationship_assertions"][0]["provenance"] == "SOURCE_REPORTED" for source in sources)


@pytest.mark.parametrize("published", [False, True])
async def test_reviewed_rights_survive_import(
    client: AsyncClient,
    sign_up: Fixture,
    upload: Fixture,
    work: Fixture,
    published: bool,
) -> None:
    """
    Condition:
    - A reviewed rights fact exists in the current draft or published version.

    Expected:
    - Preview reports the conflict and apply skips the row without changing the invention.
    """
    party = (await sign_up(client, "rights@example.com"))["active_party_id"]
    original = {
        "title": "Sample invention",
        "summary": "Demo",
        "problem": "P",
        "solution": "S",
        "intended_users": "Users",
        "stage": "PROTOTYPE",
        "facts": [{"key": "rights-owner", "label": "Rights owner", "value": "Owner A", "timing": "CURRENT"}],
    }
    row = {"external_id": "rights", "fields": original}
    run = await upload(client, party, "rights", [row])
    await work(drain=True)
    assert (await act(client, party, await status(client, run["id"]), "apply")).status_code == 202
    await work(drain=True)
    invented = (await client.get("/api/v1/inventions")).json()[0]
    original["facts"][0]["provenance"] = "REVIEWED"
    path = f"/api/v1/inventions/{invented['id']}"
    reviewed = await client.put(
        f"{path}/draft",
        json={"acting_party_id": party, "expected_version": invented["version"], **original},
        headers={"Idempotency-Key": "reviewed"},
    )
    assert reviewed.status_code == 200, reviewed.text
    if published:
        publication = await client.post(
            f"{path}/publish",
            json={"acting_party_id": party, "expected_version": reviewed.json()["version"]},
            headers={"Idempotency-Key": "published"},
        )
        assert publication.status_code == 200, publication.text
    previous = (await client.get(path)).json()
    incoming = {
        "external_id": "rights",
        "fields": {
            "title": "New title",
            "facts": [{"key": "rights-owner", "label": "Rights owner", "value": "Owner B", "timing": "CURRENT"}],
        },
    }
    repeated = await upload(client, party, "different", [incoming])
    await work(drain=True)
    review = await status(client, repeated["id"])
    assert review["rows"][0]["action"] == "CONFLICT" and review["rows"][0]["conflicts"] == ["facts"]
    assert (await act(client, party, review, "apply")).status_code == 202
    await work(drain=True)
    assert (await status(client, repeated["id"]))["skipped"] == 1
    assert (await client.get(path)).json() == previous


async def test_concurrent_first_applies_require_a_fresh_preview_for_the_loser(
    client: AsyncClient,
    sign_up: Fixture,
    upload: Fixture,
    work: Fixture,
) -> None:
    """
    Condition:
    - Two completed previews propose to create the same new external reference, and workers race.

    Expected:
    - One invention commits and the stale plan skips the row.
    """
    party = (await sign_up(client, "race@example.com"))["active_party_id"]
    rows = [{"external_id": "race", "fields": {"title": "Only one"}}]
    runs = [await upload(client, party, key, rows) for key in ("race1", "race2")]
    await work(drain=True)
    previews = [await status(client, run["id"]) for run in runs]
    assert all(preview["rows"][0]["action"] == "CREATE" for preview in previews)
    results = await asyncio.gather(*(act(client, party, preview, "apply") for preview in previews))
    assert [response.status_code for response in results] == [202, 202]
    await asyncio.gather(work(), work())
    results = [await status(client, run["id"]) for run in runs]
    assert sorted(row["committed"] for row in results) == [0, 1]
    assert sorted(row["skipped"] for row in results) == [0, 1]
    assert len((await client.get("/api/v1/inventions")).json()) == 1


async def test_first_profile_stays_source_reported_and_owner_confirmation_wins(
    client: AsyncClient,
    sign_up: Fixture,
    upload: Fixture,
    work: Fixture,
) -> None:
    """
    Condition:
    - A profile import names another organization, repeats, and then the owner confirms a profile.

    Expected:
    - The acting party alone receives a source-reported profile and later imports respect the owner's version.
    """
    party = (await sign_up(client, "profile@example.com"))["active_party_id"]
    profile = {
        "external_id": "partner",
        "organization_name": "Different company",
        "fields": {"thesis": "Source thesis"},
    }
    profile_path = f"/api/v1/partners/{party}"
    for key, action in (("p1", "CREATE"), ("p2", "UNCHANGED")):
        run = await upload(client, party, key, [], profile=profile)
        await work(drain=True)
        preview = await status(client, run["id"])
        assert preview["rows"][0]["action"] == action
        assert (await act(client, party, preview, "apply")).status_code == 202
        await work(drain=True)
    reported = await client.get(profile_path)
    assert reported.status_code == 200, reported.text
    assert reported.json()["availability"]["source"] == "SOURCE_REPORTED"
    confirmed = await client.put(
        profile_path,
        json={"acting_party_id": party, "expected_version": 1, "thesis": "Owner thesis"},
        headers={"Idempotency-Key": "confirm"},
    )
    assert confirmed.status_code == 200, confirmed.text
    run = await upload(client, party, "p3", [], profile=profile)
    await work(drain=True)
    preview = await status(client, run["id"])
    assert preview["rows"][0]["conflicts"] == ["partner_profile"]
