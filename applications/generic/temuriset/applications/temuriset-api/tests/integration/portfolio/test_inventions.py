"""Inventions, versions, facts and claims through the real application and Postgres (spec 009)."""

from collections.abc import AsyncIterator, Callable
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.database import get_session_factory
from app.core.errors.base import ConflictError
from app.platform.repository.sqlalchemy.models import OutboxEventRecord
from app.portfolio.service.service import submittable_version

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("clean_tables")]

COMPLETE = {
    "title": "Saringan air keramik desa",
    "summary": "Saringan air keramik untuk rumah tangga di desa tanpa listrik.",
    "problem": "Air sumur keruh dan tidak aman diminum.",
    "solution": "Saringan keramik berpori dengan perak koloid.",
    "intended_users": "Rumah tangga di desa",
    "sector": "Air bersih",
    "stage": "PROTOTYPE",
    "keywords": ["air", "keramik"],
    "facts": [
        {
            "label": "Kapasitas saring",
            "value": "10",
            "unit": "L/jam",
            "timing": "CURRENT",
            "provenance": "SELF_DECLARED",
        },
        {
            "label": "Kapasitas saring",
            "value": "20",
            "unit": "L/jam",
            "timing": "PLANNED",
            "provenance": "SELF_DECLARED",
        },
    ],
    "claims": [
        {"kind": "creator", "subject_name": "Rani", "status": "asserted", "source": "Pernyataan pemilik"},
        {
            "kind": "rights_holder",
            "subject_name": "Koperasi Tirta",
            "scope": "Desain",
            "status": "asserted",
            "source": "Perjanjian 2025",
        },
        {"kind": "authority", "subject_name": "Rani", "status": "not_established"},
    ],
    "private_notes": "Biaya produksi internal: rahasia",
}


@pytest.fixture
async def rani(client: AsyncClient, sign_up) -> AsyncIterator[AsyncClient]:
    """Rani, signed in, acting as herself."""
    me = await sign_up(client, "rani@example.com")
    client.headers["X-Acting-Party"] = me["active_party_id"]
    yield client


def _party(client: AsyncClient) -> str:
    return client.headers["X-Acting-Party"]


async def _create(client: AsyncClient, key: str = "c1") -> dict[str, Any]:
    response = await client.post(
        "/api/v1/inventions", json={"acting_party_id": _party(client)}, headers={"Idempotency-Key": key}
    )
    assert response.status_code == 201, response.text
    return response.json()


async def _save(client: AsyncClient, invention: dict, content: dict, version: int, key: str) -> Any:
    return await client.put(
        f"/api/v1/inventions/{invention['id']}/draft",
        json={"acting_party_id": _party(client), "expected_version": version, **content},
        headers={"Idempotency-Key": key},
    )


async def _publish(client: AsyncClient, invention: dict, version: int, key: str) -> Any:
    return await client.post(
        f"/api/v1/inventions/{invention['id']}/publish",
        json={"acting_party_id": _party(client), "expected_version": version},
        headers={"Idempotency-Key": key},
    )


async def _published(client: AsyncClient, key: str = "p") -> dict[str, Any]:
    invention = await _create(client, f"{key}-create")
    saved = (await _save(client, invention, COMPLETE, 1, f"{key}-save")).json()
    assert (await _publish(client, invention, saved["version"], f"{key}-publish")).status_code == 200
    return (await client.get(f"/api/v1/inventions/{invention['id']}")).json()


async def test_draft_saves_with_only_a_title(rani: AsyncClient) -> None:
    """
    Condition:
    - A draft with a title and nothing else is saved.

    Expected:
    - It is stored and versioned; no publication rule applies.
    """
    invention = await _create(rani)

    saved = await _save(rani, invention, {"title": "Ide"}, invention["version"], "s1")

    assert saved.status_code == 200
    body = saved.json()
    assert (body["status"], body["version"], body["draft"]["title"], body["published"]) == ("DRAFT", 2, "Ide", None)


@pytest.mark.parametrize(
    ("change", "field", "message"),
    [
        ({"title": "Ide"}, "title", "Judul perlu 5 sampai 120 karakter."),
        ({"title": "x" * 121}, "title", "Judul perlu 5 sampai 120 karakter."),
        ({"summary": "x" * 351}, "summary", "Ringkasan paling banyak 350 karakter."),
        ({"problem": ""}, "problem", "Isi masalah yang diselesaikan."),
        ({"solution": ""}, "solution", "Isi solusi saat ini."),
        ({"intended_users": ""}, "intended_users", "Isi siapa penggunanya."),
        ({"stage": None}, "stage", "Pilih tahap inovasi."),
        ({"facts": [COMPLETE["facts"][1]]}, "facts", "Tambahkan setidaknya satu kemampuan yang sudah ada saat ini."),
    ],
)
async def test_publication_rules_name_each_field(rani: AsyncClient, change: dict, field: str, message: str) -> None:
    """
    Condition:
    - A draft breaks one publication rule and is published.

    Expected:
    - ``VALIDATION_FAILED`` with that field's Indonesian message; the draft is unchanged and nothing is published.
    """
    invention = await _create(rani)
    saved = (await _save(rani, invention, COMPLETE | change, 1, "s")).json()

    response = await _publish(rani, invention, saved["version"], "p")
    after = (await rani.get(f"/api/v1/inventions/{invention['id']}")).json()

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "VALIDATION_FAILED"
    assert {"loc": ["body", field], "msg": message, "type": "publication"} in error["details"]
    assert (after["version"], after["published"], after["draft"]) == (saved["version"], None, saved["draft"])


async def test_publish_without_patent_or_company_and_keep_claims_separate(rani: AsyncClient) -> None:
    """
    Condition:
    - An inventor with no patent and no company publishes a creator, a different rights holder and an authority
      claim not yet established (AC10, AC11).

    Expected:
    - Publication succeeds; each claim keeps its kind, scope, source and status, and nothing infers ownership.
    """
    invention = await _published(rani)

    claims = invention["published"]["claims"]
    assert [(claim["kind"], claim["subject_name"], claim["status"]) for claim in claims] == [
        ("creator", "Rani", "asserted"),
        ("rights_holder", "Koperasi Tirta", "asserted"),
        ("authority", "Rani", "not_established"),
    ]
    assert claims[1]["scope"] == "Desain" and claims[1]["source"] == "Perjanjian 2025"


async def test_facts_keep_timing_and_provenance(rani: AsyncClient) -> None:
    """
    Condition:
    - "10 L/jam" CURRENT and "20 L/jam" PLANNED are published.

    Expected:
    - Each keeps its timing and provenance.
    """
    invention = await _published(rani)

    facts = invention["published"]["facts"]
    assert [(fact["value"], fact["timing"], fact["provenance"]) for fact in facts] == [
        ("10", "CURRENT", "SELF_DECLARED"),
        ("20", "PLANNED", "SELF_DECLARED"),
    ]


async def test_two_inventions_stay_separate(rani: AsyncClient) -> None:
    """
    Condition:
    - One party publishes two inventions (AC07).

    Expected:
    - Each keeps its own versions, facts and claims, and both are listed.
    """
    first = await _published(rani, "a")
    second_draft = await _create(rani, "b-create")
    other = COMPLETE | {
        "title": "Alat pengering kopi",
        "facts": [COMPLETE["facts"][0] | {"value": "50", "unit": "kg/hari"}],
    }
    saved = (await _save(rani, second_draft, other, 1, "b-save")).json()
    await _publish(rani, second_draft, saved["version"], "b-publish")
    second = (await rani.get(f"/api/v1/inventions/{second_draft['id']}")).json()
    listed = (await rani.get("/api/v1/inventions")).json()

    assert first["published"]["title"] != second["published"]["title"]
    assert [fact["value"] for fact in second["published"]["facts"]] == ["50"]
    assert len(first["published"]["claims"]) == 3 and len(second["published"]["claims"]) == 3
    assert {item["id"] for item in listed} == {first["id"], second["id"]}


async def test_republishing_keeps_the_old_version_unchanged(rani: AsyncClient) -> None:
    """
    Condition:
    - A published version is edited and republished (AC08).

    Expected:
    - Editing starts draft 2 while version 1 stays visible; republishing makes version 2 and version 1's content
      is unchanged and superseded.
    """
    invention = await _published(rani)
    edited = (
        await _save(rani, invention, COMPLETE | {"title": "Saringan air keramik desa v2"}, invention["version"], "e")
    ).json()
    listed = {item["id"]: item for item in (await rani.get("/api/v1/inventions")).json()}

    assert (edited["draft"]["number"], edited["published"]["number"], edited["published"]["title"]) == (
        2,
        1,
        COMPLETE["title"],
    )
    assert listed[invention["id"]]["has_draft"] is True

    published = await _publish(rani, invention, edited["version"], "e-publish")
    after = (await rani.get(f"/api/v1/inventions/{invention['id']}")).json()

    assert published.json()["version"] == 2
    assert (after["published"]["number"], after["published"]["title"], after["draft"], after["history"]) == (
        2,
        "Saringan air keramik desa v2",
        None,
        [1, 2],
    )


async def test_two_tabs_saving_one_draft(rani: AsyncClient) -> None:
    """
    Condition:
    - Two tabs read version 1; the first saves, the second saves with the old version.

    Expected:
    - The second is ``STALE_VERSION`` with the current version and does not overwrite.
    """
    invention = await _create(rani)
    await _save(rani, invention, {"title": "Tab satu"}, 1, "t1")

    stale = await _save(rani, invention, {"title": "Tab dua"}, 1, "t2")
    after = (await rani.get(f"/api/v1/inventions/{invention['id']}")).json()

    assert stale.status_code == 409
    assert stale.json()["error"]["current_version"] == 2
    assert after["draft"]["title"] == "Tab satu"


async def test_retried_save_with_the_same_key_is_replayed(rani: AsyncClient) -> None:
    """
    Condition:
    - A save is retried with the same key after its response was lost.

    Expected:
    - The stored response is replayed instead of a stale-version failure.
    """
    invention = await _create(rani)
    first = await _save(rani, invention, {"title": "Ide"}, 1, "same")

    retry = await _save(rani, invention, {"title": "Ide"}, 1, "same")

    assert retry.status_code == 200
    assert retry.headers["Idempotent-Replayed"] == "true"
    assert retry.json() == first.json()


async def test_archive_hides_publicly_refuses_new_use_and_keeps_history(rani: AsyncClient) -> None:
    """
    Condition:
    - A published invention is archived (AC09).

    Expected:
    - Its public view is ``NOT_FOUND``, a new reference is refused, edits are refused, and the owner still reads
      its history.
    """
    invention = await _published(rani)
    archived = await rani.post(
        f"/api/v1/inventions/{invention['id']}/archive",
        json={"acting_party_id": _party(rani), "expected_version": invention["version"]},
    )

    public = await rani.get(f"/api/v1/inventions/{invention['id']}/public")
    edit = await _save(rani, invention, COMPLETE, archived.json()["version"], "after-archive")
    owner = (await rani.get(f"/api/v1/inventions/{invention['id']}")).json()

    assert archived.json()["status"] == "ARCHIVED"
    assert public.status_code == 404
    assert edit.status_code == 409
    assert owner["published"]["title"] == COMPLETE["title"] and owner["history"] == [1]
    async with get_session_factory()() as session:
        with pytest.raises(ConflictError):
            await submittable_version(session, invention["id"])


async def test_public_view_shows_the_published_version_without_private_notes(
    rani: AsyncClient, new_client: Callable[[], AsyncClient], sign_up
) -> None:
    """
    Condition:
    - A partner reads a published invention that also has an unpublished draft.

    Expected:
    - The published version and the managing party's name; no private notes, no draft text, no document links.
    """
    invention = await _published(rani)
    await _save(rani, invention, COMPLETE | {"title": "Draf rahasia baru"}, invention["version"], "d")

    async with new_client() as partner:
        await sign_up(partner, "bima@example.com", persona="mitra", name="Bima")
        public = await partner.get(f"/api/v1/inventions/{invention['id']}/public")

    assert public.status_code == 200
    body = public.json()
    assert (body["title"], body["managing_party_name"], body["number"]) == (COMPLETE["title"], "Rani", 1)
    assert "rahasia" not in public.text and "private_notes" not in body and "document_version_id" not in public.text


async def test_publication_and_archive_emit_one_event_each(rani: AsyncClient) -> None:
    """
    Condition:
    - An invention is published, the publish is retried with the same key, then it is archived.

    Expected:
    - One ``invention.published`` and one ``invention.archived`` event for the search projection (018).
    """
    invention = await _create(rani)
    saved = (await _save(rani, invention, COMPLETE, 1, "s")).json()
    await _publish(rani, invention, saved["version"], "once")
    await _publish(rani, invention, saved["version"], "once")
    after = (await rani.get(f"/api/v1/inventions/{invention['id']}")).json()
    await rani.post(
        f"/api/v1/inventions/{invention['id']}/archive",
        json={"acting_party_id": _party(rani), "expected_version": after["version"]},
    )

    async with get_session_factory()() as session:
        topics = [
            event.topic
            for event in await session.scalars(select(OutboxEventRecord).order_by(OutboxEventRecord.created_at))
        ]
    assert topics == ["invention.published", "invention.archived"]


async def test_member_without_edit_capability_cannot_save(
    client: AsyncClient, new_client: Callable[[], AsyncClient], sign_up
) -> None:
    """
    Condition:
    - A member with only ``schedule`` acts as the organization and tries to start an invention.

    Expected:
    - ``FORBIDDEN``.
    """
    await sign_up(client, "bima@example.com", persona="mitra", name="Bima")
    organization = (
        await client.post(
            "/api/v1/organizations", json={"name": "Org", "kind": "company"}, headers={"Idempotency-Key": "o"}
        )
    ).json()
    await client.put("/api/v1/me/context", json={"party_id": organization["party_id"]})
    await client.post(
        f"/api/v1/organizations/{organization['id']}/invitations",
        json={"acting_party_id": organization["party_id"], "email": "eve@example.com", "capabilities": ["schedule"]},
        headers={"Idempotency-Key": "i"},
    )
    token = (
        (await client.get("/api/v1/dev/mailbox", params={"email": "eve@example.com"}))
        .json()[0]["body"]
        .rsplit("/", 1)[1]
    )
    async with new_client() as eve:
        await sign_up(eve, "eve@example.com", name="Eve")
        await eve.post(f"/api/v1/invitations/{token}/accept")
        await eve.put("/api/v1/me/context", json={"party_id": organization["party_id"]})

        response = await eve.post(
            "/api/v1/inventions", json={"acting_party_id": organization["party_id"]}, headers={"Idempotency-Key": "x"}
        )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"
