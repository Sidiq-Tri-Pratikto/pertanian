"""Public profiles read without sign-in, computed from publication and consent on every request (spec 031)."""

from collections.abc import Callable
from uuid import uuid4

import pytest
from httpx import AsyncClient

import app.discovery.service.projection  # noqa: F401 - registers the projection consumers
from app.core.database import get_session_factory
from app.worker.loop import dispatch_events
from app.worker.registry import registry
from tests.integration.matching.conftest import World
from tests.integration.pitches.conftest import client_of
from tests.integration.relationships.conftest import ALL, VALUES, confirm, met, partnership_action, propose_partnership

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("clean_tables")]

PRIVATE = "Rahasia catatan pertemuan sk-fakeprofilesecret222"


async def _project() -> None:
    while await dispatch_events(get_session_factory(), registry):
        pass


async def _confirmed(world: World, mitra_subset: list[str]) -> tuple[dict, dict]:
    """F01 and Mitra A confirm version 2 after a correction, Rani allowing everything."""
    mitra = world.recipients.clients["A"]
    rani, _ = client_of(world, "F01")
    pitch = await met(world)
    proposed = (await propose_partnership(rani, pitch, values={**VALUES, "evidence": PRIVATE})).json()
    v2 = (
        await partnership_action(
            mitra,
            proposed,
            "corrections",
            "fix",
            version=1,
            values={**VALUES, "evidence": PRIVATE, "scope": "Enam bulan"},
        )
    ).json()
    await confirm(rani, v2, ALL, "r")
    done = (await confirm(mitra, v2, mitra_subset, "m")).json()
    return pitch, done


async def test_only_fields_both_allowed_appear_and_a_restriction_applies_on_the_next_read(
    world: World, new_client: Callable[[], AsyncClient]
) -> None:
    """
    Condition:
    - Version 2 is confirmed with amount allowed by Rani only; a signed-out visitor reads Rani's profile, then Rani
      restricts date, then Mitra A proposes version 3 adding amount and only Mitra A confirms (AC55).

    Expected:
    - Amount is absent; date disappears after the restriction; the pending expansion adds nothing.
    """
    mitra = world.recipients.clients["A"]
    rani, rani_party = client_of(world, "F01")
    _, done = await _confirmed(world, ["name", "type", "scope", "date"])
    async with new_client() as visitor:
        first = (await visitor.get(f"/api/v1/profiles/{rani_party}")).json()
        await partnership_action(rani, done, "restrictions", "hide", field="date")
        narrowed = (await visitor.get(f"/api/v1/profiles/{rani_party}")).json()
        v3 = (await partnership_action(mitra, done, "corrections", "more", version=2, values=VALUES)).json()
        await confirm(mitra, v3, ALL, "m3")
        expanded = (await visitor.get(f"/api/v1/profiles/{rani_party}")).json()

    [relationship] = first["relationships"]
    assert set(relationship["fields"]) == {"name", "type", "scope", "date"}
    assert (relationship["role"], relationship["counterpart_name"]) == ("Penerima dukungan proyek", "Mitra A")
    assert "date" not in narrowed["relationships"][0]["fields"]
    assert set(expanded["relationships"][0]["fields"]) == {"name", "type", "scope"}


async def test_one_equity_relationship_over_two_inventions_appears_once(
    world: World, new_client: Callable[[], AsyncClient]
) -> None:
    """
    Condition:
    - Bima's FRaise01 equity relationship with B1 links two published inventions; both confirm name, type and
      percent (AC56).

    Expected:
    - Bima's public profile lists it once, with both inventions and one percent, labelled by role.
    """
    investor = world.recipients.clients["B"]
    bima, bima_party = client_of(world, "FRaise01")
    pitch = await met(world, "FRaise01", "B1", "B")
    fields = ["name", "type", "percent"]
    proposed = (
        await propose_partnership(
            bima,
            pitch,
            type="EQUITY",
            values={**VALUES, "name": "Demo Circular Materials Ltd", "percent": "12.5", "percent_date": "2027-01-01"},
            ceiling=fields,
            subset=fields,
        )
    ).json()
    await confirm(investor, proposed, fields, "b")
    await _project()
    async with new_client() as visitor:
        profile = (await visitor.get(f"/api/v1/profiles/{bima_party}")).json()

    [relationship] = profile["relationships"]
    assert relationship["role"] == "Perusahaan penerima investasi"
    assert len(relationship["inventions"]) == 2
    assert relationship["fields"]["percent"] == {"percent": "12.5", "effective_date": "2027-01-01"}
    assert len(profile["inventions"]) >= 2


async def test_a_contested_claim_is_hidden_publicly_and_kept_privately(
    world: World, new_client: Callable[[], AsyncClient]
) -> None:
    """
    Condition:
    - A confirmed relationship; Mitra A contests it (AC57).

    Expected:
    - The public profile no longer lists it; both parties still read its history.
    """
    mitra, mitra_party = world.recipients.clients["A"], world.recipients.parties["A"]
    rani, _ = client_of(world, "F01")
    _, done = await _confirmed(world, ["name", "type", "scope", "date"])
    await partnership_action(mitra, done, "request-review", "review", reason="Tidak sesuai")
    async with new_client() as visitor:
        public = (await visitor.get(f"/api/v1/profiles/{mitra_party}")).json()
    private = (await rani.get(f"/api/v1/partnerships/{done['id']}")).json()

    assert public["relationships"] == []
    assert (private["contested"], len(private["versions"])) == (True, 2)


async def test_private_strings_never_reach_a_public_profile_and_a_bio_needs_publishing(
    world: World, new_client: Callable[[], AsyncClient]
) -> None:
    """
    Condition:
    - A confirmed relationship with private evidence and an amount Mitra A did not allow; Rani saves a bio without
      publishing, then publishes it.

    Expected:
    - Neither the evidence, the amount nor the unpublished bio appears; the published bio does.
    """
    rani, rani_party = client_of(world, "F01")
    await _confirmed(world, ["name", "type", "scope", "date"])
    mine = (await rani.get("/api/v1/profiles/me")).json()
    hidden = await rani.put(
        "/api/v1/profiles/me",
        json={
            "acting_party_id": rani_party,
            "expected_version": mine["version"],
            "bio": "Bio draf",
            "published": False,
        },
    )
    async with new_client() as visitor:
        before = await visitor.get(f"/api/v1/profiles/{rani_party}")
        published = await rani.put(
            "/api/v1/profiles/me",
            json={
                "acting_party_id": rani_party,
                "expected_version": hidden.json()["version"],
                "bio": "Inovator air bersih",
                "published": True,
            },
        )
        after = (await visitor.get(f"/api/v1/profiles/{rani_party}")).json()

    for secret in (PRIVATE, "25000", "Bio draf"):
        assert secret not in before.text
    assert published.json()["published"] is True
    assert after["bio"] == "Inovator air bersih"


async def test_an_unknown_party_is_not_found_and_an_empty_profile_says_so(
    world: World, new_client: Callable[[], AsyncClient]
) -> None:
    """
    Condition:
    - A signed-out visitor reads a party that does not exist, then Mitra C, which published nothing.

    Expected:
    - ``NOT_FOUND`` for the first; the second says nothing is published.
    """
    async with new_client() as visitor:
        missing = await visitor.get(f"/api/v1/profiles/{uuid4()}")
        empty = (await visitor.get(f"/api/v1/profiles/{world.recipients.parties['C']}")).json()

    assert missing.status_code == 404
    assert (empty["nothing_published"], empty["bio"], empty["relationships"]) == (True, None, [])
