"""Optional minimum TKT on mandates (spec 055, US2)."""

import pytest
from httpx import AsyncClient

from tests.factories.recipients import OPPORTUNITIES, create_opportunity, save_opportunity, save_profile

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("clean_tables")]


async def _prepare_profile(partner: AsyncClient, party: str) -> None:
    resp = await save_profile(
        partner,
        party,
        {"subtype": "Investor dampak", "thesis": "Mendukung inovasi terapan.", "contact_route": "IN_APP"},
    )
    assert resp.status_code == 200, resp.text


async def test_mandate_min_tkt_saves_versions_and_is_visible_to_applicants(
    partner: AsyncClient, stranger: AsyncClient
) -> None:
    """US2.1: saving min_tkt: 5 persists across draft, activation, live version update and applicant reads."""
    party = partner.headers["X-Acting-Party"]
    await _prepare_profile(partner, party)
    content = dict(OPPORTUNITIES["A1"]["content"])

    created = await create_opportunity(
        partner, party, {"kind": "SPECIFIC", **content, "min_tkt": 5}, key="opp-min-tkt-1"
    )
    assert created.status_code == 201, created.text
    opp = created.json()
    assert opp["min_tkt"] == 5

    activated = await partner.post(
        f"/api/v1/opportunities/{opp['id']}/activate",
        json={"acting_party_id": party, "expected_version": opp["version"]},
        headers={"Idempotency-Key": "opp-min-tkt-act"},
    )
    assert activated.status_code == 200, activated.text
    assert activated.json()["min_tkt"] == 5

    # Applicant sees min_tkt on active opportunity and its version endpoint.
    seen = await stranger.get(f"/api/v1/opportunities/{opp['id']}")
    assert seen.status_code == 200, seen.text
    assert seen.json()["min_tkt"] == 5

    # Clearing min_tkt on live save creates version 2 with min_tkt=None while version 1 keeps 5.
    cleared = await save_opportunity(
        partner,
        party,
        opp["id"],
        {**content, "min_tkt": None},
        activated.json()["version"],
        key="opp-min-tkt-clear",
    )
    assert cleared.status_code == 200, cleared.text
    assert cleared.json()["min_tkt"] is None
    assert cleared.json()["number"] == 2

    v1 = await partner.get(f"/api/v1/opportunities/{opp['id']}/versions/1")
    assert v1.status_code == 200, v1.text
    assert v1.json()["min_tkt"] == 5


async def test_mandate_min_tkt_rejects_values_outside_one_to_nine(partner: AsyncClient) -> None:
    """US2.2: min_tkt outside 1-9 fails with VALIDATION_FAILED naming min_tkt."""
    party = partner.headers["X-Acting-Party"]
    for index, bad in enumerate((0, 10)):
        resp = await partner.post(
            "/api/v1/opportunities",
            json={"acting_party_id": party, "kind": "SPECIFIC", "title": "Mandat uji", "min_tkt": bad},
            headers={"Idempotency-Key": f"opp-bad-tkt-{index}"},
        )
        assert resp.status_code == 422
        assert resp.json()["error"]["code"] == "VALIDATION_FAILED"
