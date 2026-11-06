"""Discovery through HTTP against Postgres: projection, search, sections, saved items and feedback (spec 018)."""

from collections.abc import AsyncIterator, Callable
from typing import Any

import pytest
from httpx import AsyncClient

import app.discovery.service.projection  # noqa: F401 - registers the projection consumers
from app.core.database import get_session_factory
from app.core.settings import get_settings
from app.discovery.service.service import DiscoveryService
from app.worker.loop import dispatch_events
from app.worker.registry import registry
from tests.factories.inventors import LoadedInventors, load_inventors
from tests.factories.recipients import LoadedRecipients, load_recipients, save_profile

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("clean_tables")]


async def project() -> None:
    """Run the outbox consumers until every event is delivered."""
    while await dispatch_events(get_session_factory(), registry):
        pass


@pytest.fixture
async def inventors(new_client: Callable[[], AsyncClient], sign_up) -> AsyncIterator[LoadedInventors]:
    """F01–F06 and FRaise01, projected."""
    loaded = await load_inventors(new_client, sign_up)
    await project()
    yield loaded
    await loaded.close()


@pytest.fixture
async def partner(client: AsyncClient, sign_up) -> AsyncIterator[AsyncClient]:
    """A new partner with a profile in Air dan sanitasi and no history."""
    me = await sign_up(client, "baru@example.com", persona="mitra", name="Mitra Baru")
    client.headers["X-Acting-Party"] = me["active_party_id"]
    saved = await save_profile(
        client,
        me["active_party_id"],
        {"subtype": "Investor", "thesis": "Air bersih.", "sectors": ["Air dan sanitasi"], "stages": ["PROTOTYPE"]},
    )
    assert saved.status_code == 200, saved.text
    await project()
    yield client


async def discover(client: AsyncClient, **params: Any) -> dict[str, Any]:
    response = await client.get("/api/v1/discovery", params=params)
    assert response.status_code == 200, response.text
    return response.json()


def titles(page: dict[str, Any], section: str | None = None) -> list[str]:
    return [item["title"] for group in page["sections"] if section in (None, group["id"]) for item in group["items"]]


async def test_a_new_partner_gets_sections_from_stated_preferences(
    partner: AsyncClient, inventors: LoadedInventors
) -> None:
    """
    Condition:
    - A new partner with no history opens discovery; an operator marked F06 curated (AC28, FR-005).

    Expected:
    - "Sesuai profil Anda" holds ClearSpring by sector, "Pilihan kurator" holds GridShare, the rest are new, and
      no trend label exists anywhere.
    """
    async with get_session_factory()() as session, session.begin():
        await DiscoveryService(session).set_curated("INVENTION", inventors.inventions["F06"], True)
    page = await discover(partner)

    assert [(group["id"], group["title"]) for group in page["sections"]] == [
        ("relevant", "Sesuai profil Anda"),
        ("new", "Baru diterbitkan"),
        ("curated", "Pilihan kurator"),
    ]
    assert titles(page, "relevant") == ["ClearSpring"]
    assert titles(page, "curated") == ["GridShare"]
    assert sorted(titles(page, "new")) == ["FieldDry", "LoopMaterial", "QueueNest", "ReFormPress"]
    relevant = page["sections"][0]["items"][0]
    assert relevant["reasons"] == ["Sesuai sektor pada profil Anda: Air dan sanitasi"]
    assert "trend" not in str(page).lower()


async def test_nothing_matching_echoes_filters_and_suggests_a_deliberate_relaxation(
    partner: AsyncClient, inventors: LoadedInventors
) -> None:
    """
    Condition:
    - Filters that match nothing: sector Pertanian with stage IDEA (AC29).

    Expected:
    - No results, the filters echoed, and a suggestion to remove one filter that would find something; the search
      itself is never broadened.
    """
    page = await discover(partner, sector="Pertanian", stage="IDEA")

    assert titles(page) == []
    assert page["total_estimate"] == 0
    assert page["filters"] == {"sector": "Pertanian", "stage": "IDEA"}
    assert page["relaxation"] == {"remove": "sector", "label": "Hapus filter sektor", "total_estimate": 1}


async def test_refreshing_ones_own_invention_counts_no_trend(inventors: LoadedInventors, partner: AsyncClient) -> None:
    """
    Condition:
    - Rani reads her own invention 50 times (AC30).

    Expected:
    - Discovery for others is unchanged and carries no trend field.
    """
    before = await discover(partner)
    rani = inventors.clients["rani"]
    for _ in range(50):
        await rani.get(f"/api/v1/inventions/{inventors.inventions['F01']}/public")
    await project()

    assert await discover(partner) == before


@pytest.mark.parametrize("query", ["water filter", "filter air", "FILTER", "clearsprng"])
async def test_english_aliases_prefixes_and_typos_find_clearspring(
    partner: AsyncClient, inventors: LoadedInventors, query: str
) -> None:
    """
    Condition:
    - A search in English, in Indonesian, in capitals, and with a typo in the title.

    Expected:
    - ClearSpring is found each time, and nothing that lacks a word of the query.
    """
    assert titles(await discover(partner, q=query)) == ["ClearSpring"]


async def test_one_card_per_raise(partner: AsyncClient, inventors: LoadedInventors) -> None:
    """
    Condition:
    - FRaise01 links two inventions.

    Expected:
    - Funding results list it once, with both inventions and the per-investor range on its card.
    """
    page = await discover(partner, type="funding")
    items = [item for group in page["sections"] for item in group["items"]]

    assert [item["title"] for item in items] == ["Demo Circular Materials Ltd"]
    card = items[0]["card"]
    assert [invention["title"] for invention in card["inventions"]] == ["LoopMaterial", "ReFormPress"]
    assert (card["desired_min"], card["desired_max"], card["target_amount"]) == (
        "50000.0000",
        "100000.0000",
        "500000.0000",
    )


async def test_amount_filters_compare_within_one_currency(partner: AsyncClient, inventors: LoadedInventors) -> None:
    """
    Condition:
    - Funding filtered by USD 60000–80000, by IDR, and by an amount with no currency.

    Expected:
    - USD finds FRaise01, IDR finds nothing, and an amount without a currency is refused per field.
    """
    assert titles(await discover(partner, type="funding", currency="USD", amount_min="60000", amount_max="80000")) == [
        "Demo Circular Materials Ltd"
    ]
    assert titles(await discover(partner, type="funding", currency="IDR")) == []
    refused = await partner.get("/api/v1/discovery", params={"type": "funding", "amount_min": "1"})
    assert refused.status_code == 422
    assert refused.json()["error"]["code"] == "VALIDATION_FAILED"


async def test_saved_items_belong_to_one_party(partner: AsyncClient, inventors: LoadedInventors) -> None:
    """
    Condition:
    - The partner saves ClearSpring and filters to saved; Rani lists her saved items.

    Expected:
    - The partner sees only ClearSpring, marked saved; Rani's list is empty; unsaving twice is NOT_FOUND.
    """
    party = partner.headers["X-Acting-Party"]
    path = f"/api/v1/saved-items/INVENTION/{inventors.inventions['F01']}"
    saved = await partner.put(path, json={"acting_party_id": party})
    again = await partner.put(path, json={"acting_party_id": party})
    page = await discover(partner, saved="true")

    assert (saved.status_code, again.status_code) == (200, 200)
    assert titles(page) == ["ClearSpring"]
    assert page["sections"][0]["items"][0]["saved"] is True
    assert (await partner.get("/api/v1/saved-items")).json() == [
        {"subject_type": "INVENTION", "subject_id": inventors.inventions["F01"]}
    ]
    assert (await inventors.clients["rani"].get("/api/v1/saved-items")).json() == []
    assert (await partner.request("DELETE", path, json={"acting_party_id": party})).status_code == 204
    gone = await partner.request("DELETE", path, json={"acting_party_id": party})
    assert gone.status_code == 404


async def test_less_relevant_hides_for_that_party_only(partner: AsyncClient, inventors: LoadedInventors) -> None:
    """
    Condition:
    - The partner marks FieldDry "Kurang relevan".

    Expected:
    - It leaves the partner's results and stays in Rani's; undoing it brings it back.
    """
    party = partner.headers["X-Acting-Party"]
    path = f"/api/v1/discovery-feedback/INVENTION/{inventors.inventions['F02']}"
    await partner.put(path, json={"acting_party_id": party})

    assert "FieldDry" not in titles(await discover(partner))
    assert "FieldDry" in titles(await discover(inventors.clients["rani"]))
    assert (await partner.get("/api/v1/discovery-feedback")).json()[0]["subject_id"] == inventors.inventions["F02"]
    await partner.request("DELETE", path, json={"acting_party_id": party})
    assert "FieldDry" in titles(await discover(partner))


async def test_unpublished_subjects_cannot_be_saved(partner: AsyncClient, inventors: LoadedInventors) -> None:
    """
    Condition:
    - The partner saves an id that is not in the projection, and saves with a stale acting party.

    Expected:
    - NOT_FOUND, and STALE_CONTEXT, with nothing stored.
    """
    missing = await partner.put(
        f"/api/v1/saved-items/INVENTION/{inventors.parties['rani']}",
        json={"acting_party_id": partner.headers["X-Acting-Party"]},
    )
    stale = await partner.put(
        f"/api/v1/saved-items/INVENTION/{inventors.inventions['F01']}",
        json={"acting_party_id": inventors.parties["rani"]},
    )

    assert missing.status_code == 404 and missing.json()["error"]["request_id"]
    assert stale.json()["error"]["code"] == "STALE_CONTEXT"
    assert (await partner.get("/api/v1/saved-items")).json() == []


async def test_archiving_removes_the_row_and_private_text_is_never_searchable(
    partner: AsyncClient, inventors: LoadedInventors
) -> None:
    """
    Condition:
    - ClearSpring's private note holds "7731"; then Rani archives it and the consumers run.

    Expected:
    - The private word finds nothing before; after archiving, ClearSpring is gone from every search.
    """
    assert titles(await discover(partner, q="7731")) == []
    assert titles(await discover(partner, q="rahasia")) == []
    rani, invention = inventors.clients["rani"], inventors.inventions["F01"]
    current = (await rani.get(f"/api/v1/inventions/{invention}")).json()
    archived = await rani.post(
        f"/api/v1/inventions/{invention}/archive",
        json={"acting_party_id": inventors.parties["rani"], "expected_version": current["version"]},
        headers={"Idempotency-Key": "archive"},
    )
    assert archived.status_code == 200, archived.text
    await project()

    assert "ClearSpring" not in titles(await discover(partner))


async def test_pages_follow_an_opaque_cursor(partner: AsyncClient, inventors: LoadedInventors) -> None:
    """
    Condition:
    - Six published inventions read two at a time; a limit above 100 and a forged cursor.

    Expected:
    - Three pages with every invention once; the limit is refused and the forged cursor is BAD_REQUEST.
    """
    seen, cursor = [], None
    for _ in range(3):
        page = await discover(partner, limit=2, **({"cursor": cursor} if cursor else {}))
        seen += titles(page)
        cursor = page["next_cursor"]
    assert cursor is None
    assert sorted(seen) == ["ClearSpring", "FieldDry", "GridShare", "LoopMaterial", "QueueNest", "ReFormPress"]
    assert (await partner.get("/api/v1/discovery", params={"limit": 101})).status_code == 422
    forged = await partner.get("/api/v1/discovery", params={"cursor": "!!"})
    assert forged.json()["error"]["code"] == "BAD_REQUEST"


async def test_inventors_find_partners_with_their_availability(
    inventors: LoadedInventors, new_client: Callable[[], AsyncClient], sign_up
) -> None:
    """
    Condition:
    - Recipients A–E saved, opportunities active; Rani searches partners.

    Expected:
    - All five appear, Mitra A first by her sector, E labelled source-reported and unconfirmed; "intake=OPEN" leaves E
      out; "lisensi" finds D through its opportunity.
    """
    recipients: LoadedRecipients = await load_recipients(new_client, sign_up)
    try:
        await project()
        rani = inventors.clients["rani"]
        page = await discover(rani, type="partners")
        cards = {item["title"]: item["card"] for group in page["sections"] for item in group["items"]}

        assert sorted(cards) == ["Dana Riset E", "Distributor C", "Investor B", "Mitra A", "Mitra Lisensi D"]
        assert "Mitra A" in titles(page, "relevant")
        assert (cards["Dana Riset E"]["source_label"], cards["Dana Riset E"]["availability_label"]) == (
            "Dilaporkan sumber",
            "Ketersediaan belum dikonfirmasi",
        )
        assert len(cards["Mitra A"]["opportunities"]) == 3
        assert "Dana Riset E" not in titles(await discover(rani, type="partners", intake="OPEN"))
        assert titles(await discover(rani, type="partners", q="lisensi")) == ["Mitra Lisensi D"]
    finally:
        await recipients.close()


async def test_funding_results_are_empty_without_company_funding(
    partner: AsyncClient, inventors: LoadedInventors, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    Condition:
    - The ``project-support-only`` composition.

    Expected:
    - Funding results are empty; inventions still show.
    """
    monkeypatch.setattr(get_settings(), "composition", "project-support-only")

    assert titles(await discover(partner, type="funding")) == []
    assert titles(await discover(partner))
