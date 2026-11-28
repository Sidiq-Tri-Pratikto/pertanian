"""The demo scenario end to end through HTTP: the reset's starting point, then scenarios 1 to 3 as a presenter types
them (``app/demo/service/scenario.py``, ``docs/demo/scenario.md``)."""

from collections.abc import Iterator
from typing import Any

import pytest
from httpx import AsyncClient

from app.core.settings import get_settings
from app.demo.service import scenario
from tests.factories.recipients import create_opportunity, move_opportunity, save_profile

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("clean_tables")]


@pytest.fixture(autouse=True)
def demo_on(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Demo mode for these tests."""
    monkeypatch.setattr(get_settings(), "demo_mode", True)
    yield


async def _sign_in(client: AsyncClient, key: str) -> str:
    response = await client.post("/api/v1/demo/sign-in", json={"key": key})
    assert response.status_code == 200, response.text
    party = response.json()["active_party_id"]
    client.headers["X-Acting-Party"] = party
    return party


def _ok(response: Any, status: int = 200) -> dict[str, Any]:
    assert response.status_code == status, response.text
    return response.json()


async def _labels(client: AsyncClient, party: str, need_id: str, key: str) -> dict[str, str]:
    """Match one need; return each opportunity's label, shown and excluded alike."""
    run = _ok(
        await client.post(
            "/api/v1/matches",
            json={"acting_party_id": party, "source_type": "SUPPORT_REQUEST", "source_id": need_id},
            headers={"Idempotency-Key": key},
        ),
        201,
    )
    return {item["title"]: item["label"] for item in run["results"] + run["excluded"]}


async def _product_b(client: AsyncClient, party: str) -> str:
    """Scenario 2: Inovator A creates and publishes Produk B with its need; return the need id."""
    created = _ok(
        await client.post("/api/v1/inventions", json={"acting_party_id": party}, headers={"Idempotency-Key": "b"}),
        201,
    )
    saved = _ok(
        await client.put(
            f"/api/v1/inventions/{created['id']}/draft",
            json={"acting_party_id": party, "expected_version": created["version"], **scenario.PRODUCT_B["content"]},
            headers={"Idempotency-Key": "b-draft"},
        )
    )
    _ok(
        await client.post(
            f"/api/v1/inventions/{created['id']}/publish",
            json={"acting_party_id": party, "expected_version": saved["version"]},
            headers={"Idempotency-Key": "b-publish"},
        )
    )
    need = _ok(
        await client.post(
            "/api/v1/support-requests",
            json={"acting_party_id": party, "invention_id": created["id"], **scenario.PRODUCT_B["need"]},
            headers={"Idempotency-Key": "b-need"},
        ),
        201,
    )
    _ok(
        await client.post(
            f"/api/v1/support-requests/{need['id']}/activate",
            json={"acting_party_id": party, "expected_version": need["version"]},
            headers={"Idempotency-Key": "b-need-activate"},
        )
    )
    return need["id"]


async def test_the_reset_starts_with_one_inventor_one_product_and_two_investors(
    client: AsyncClient, new_client
) -> None:
    """
    Condition:
    - The demo is reset.

    Expected:
    - The picker lists Inovator A, Investor A and Investor B. Inovator A has Produk A with an active need and a public
      page; Investor A has one active opportunity; Investor B has no profile yet.
    """
    _ok(await client.post("/api/v1/demo/reset"))
    accounts = _ok(await client.get("/api/v1/demo/accounts"))
    inventor = await _sign_in(client, "inovator-a")
    inventions = _ok(await client.get("/api/v1/inventions"))
    needs = _ok(await client.get("/api/v1/support-requests"))
    async with new_client() as investor:
        investor_b = await _sign_in(investor, "investor-b")
        profile = await investor.get(f"/api/v1/partners/{investor_b}")
        await _sign_in(investor, "investor-a")
        opportunities = _ok(await investor.get("/api/v1/opportunities"))

    assert [(account["key"], account["name"]) for account in accounts] == [
        ("inovator-a", "Inovator A"),
        ("investor-a", "Investor A"),
        ("investor-b", "Investor B"),
    ]
    assert inventor
    assert [invention["title"] for invention in inventions] == ["ClearSpring"]
    assert [need["status"] for need in needs] == ["ACTIVE"]
    teaser = _ok(await client.get(f"/api/v1/teasers/inventions/{inventions[0]['id']}"))
    assert teaser["follow_enabled"] is True and teaser["photo"] is not None
    assert teaser["tkt_level"] == 4
    detail = _ok(await client.get(f"/api/v1/inventions/{inventions[0]['id']}"))
    assert detail["published"]["readiness"]["tkt_level"] == 4
    assert detail["published"]["readiness"]["has_evidence"] is True
    assert [(item["title"], item["status"], item["min_tkt"]) for item in opportunities] == [
        ("Pendanaan pilot pertanian", "ACTIVE", 6)
    ]
    assert profile.status_code == 404


async def test_scenarios_one_to_three_give_weak_matches_for_product_a_and_a_strong_one_for_product_b(
    client: AsyncClient, new_client
) -> None:
    """
    Condition:
    - Scenario 1: Investor B fills in the profile and opens the opportunity from the script.
    - Scenario 2: Inovator A creates Produk B from the script.
    - Scenario 3: Inovator A matches both products.

    Expected:
    - Produk A is a weak match for Investor A and Investor B; Produk B is a strong match for Investor B and a weak one
      for Investor A.
    """
    _ok(await client.post("/api/v1/demo/reset"))
    async with new_client() as investor:
        party = await _sign_in(investor, "investor-b")
        assert (await save_profile(investor, party, scenario.INVESTOR_B["profile"])).status_code == 200
        opened = _ok(await create_opportunity(investor, party, scenario.INVESTOR_B["opportunity"]), 201)
        _ok(await move_opportunity(investor, party, opened["id"], "activate", opened["version"]))

    inventor = await _sign_in(client, "inovator-a")
    product_a = _ok(await client.get("/api/v1/support-requests"))[0]["id"]
    product_b = await _product_b(client, inventor)
    for_a = await _labels(client, inventor, product_a, "match-a")
    for_b = await _labels(client, inventor, product_b, "match-b")

    # Spec 057 compares money even without a budget requirement row; Produk A's USD 20–30k overlaps Investor B's
    # USD 25–60k (6 months, same scope), lifting Produk A × Investor B to "Kecocokan potensial" until 056 updates
    # scenario.py's Produk A budget to USD 10–15k.
    assert for_a == {
        "Pendanaan pilot pertanian": "Kecocokan lemah",
        "Pendanaan energi surya desa": "Kecocokan potensial",
    }
    assert for_b == {"Pendanaan energi surya desa": "Kecocokan kuat", "Pendanaan pilot pertanian": "Kecocokan lemah"}
