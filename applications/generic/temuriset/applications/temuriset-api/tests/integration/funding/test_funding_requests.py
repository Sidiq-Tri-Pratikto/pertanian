"""Company funding requests through Postgres (spec 014)."""

from collections.abc import AsyncIterator, Callable
from typing import Any

import pytest
from httpx import AsyncClient

from app.core.settings import get_settings

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("clean_tables")]

FRAISE01 = {
    "subject_type": "EXISTING_ENTITY",
    "financing_stage": "pre_seed",
    "financing_form": "equity",
    "currency": "USD",
    "target_amount": "500000",
    "desired_min": "50000",
    "desired_max": "100000",
    "accepts_partial": True,
    "accepts_syndicated": True,
    "intended_use": "Mengembangkan dua inovasi perusahaan",
}


@pytest.fixture
async def dcm(client: AsyncClient, sign_up, published_invention) -> AsyncIterator[AsyncClient]:
    """Demo Circular Materials Ltd acting as itself, with F04 and F05 published and a declared legal entity."""
    await sign_up(client, "dcm@example.com", name="Dewi")
    organization = (
        await client.post(
            "/api/v1/organizations",
            json={"name": "Demo Circular Materials", "kind": "company"},
            headers={"Idempotency-Key": "org"},
        )
    ).json()
    party = organization["party_id"]
    await client.put("/api/v1/me/context", json={"party_id": party})
    client.headers["X-Acting-Party"] = party
    client.headers["X-F04"] = (await published_invention(client, "LoopMaterial"))["id"]
    client.headers["X-F05"] = (await published_invention(client, "ReFormPress"))["id"]
    entity = await client.post(
        "/api/v1/legal-entities",
        json={"acting_party_id": party, "name": "Demo Circular Materials Ltd", "jurisdiction": "Indonesia"},
    )
    assert entity.status_code == 201, entity.text
    client.headers["X-Entity"] = entity.json()["id"]
    yield client


def _body(client: AsyncClient, **content: Any) -> dict:
    return {
        "acting_party_id": client.headers["X-Acting-Party"],
        **FRAISE01,
        "legal_entity_id": client.headers["X-Entity"],
        "invention_ids": [client.headers["X-F04"], client.headers["X-F05"]],
        **content,
    }


async def _create(client: AsyncClient, key: str = "c1", **content: Any) -> Any:
    return await client.post(
        "/api/v1/funding-requests", json=_body(client, **content), headers={"Idempotency-Key": key}
    )


async def _update(client: AsyncClient, request: dict, version: int, key: str, **content: Any) -> Any:
    return await client.put(
        f"/api/v1/funding-requests/{request['id']}",
        json={"expected_version": version, **_body(client, **content)},
        headers={"Idempotency-Key": key},
    )


@pytest.fixture
def composition(monkeypatch: pytest.MonkeyPatch) -> Callable[[str], None]:
    """Switch the deployment's composition for the capability guard."""

    def switch(composition_id: str) -> None:
        settings = get_settings().model_copy(update={"composition": composition_id})
        monkeypatch.setattr("app.capabilities.service.guard.get_settings", lambda: settings)

    return switch


async def test_ac19_one_raise_owns_its_target_and_links_two_inventions(dcm: AsyncClient) -> None:
    """
    Condition:
    - FRaise01: target USD 500000, desired contribution USD 50000–100000, partial and syndicated funding accepted,
      linked to F04 and F05 (AC19).

    Expected:
    - One request with two links; the target is stored once, on the request, as an exact string; the entity is
      labelled as declared; activation succeeds.
    """
    created = await _create(dcm)
    body = created.json()
    party = dcm.headers["X-Acting-Party"]
    activated = await dcm.post(
        f"/api/v1/funding-requests/{body['id']}/activate", json={"acting_party_id": party, "expected_version": 1}
    )
    listed = (await dcm.get("/api/v1/funding-requests")).json()

    assert created.status_code == 201, created.text
    assert (body["target_amount"], body["desired_min"], body["desired_max"]) == (
        "500000.0000",
        "50000.0000",
        "100000.0000",
    )
    assert [(link["title"], link["version"]) for link in body["inventions"]] == [
        ("LoopMaterial", 1),
        ("ReFormPress", 1),
    ]
    assert "target_amount" not in str(body["inventions"])
    assert body["legal_entity"]["review_status"] == "declared"
    assert body["subject_label"] == "Demo Circular Materials Ltd"
    assert (body["financing_stage"], body["accepts_syndicated"]) == ("pre_seed", True)
    assert activated.json()["status"] == "ACTIVE"
    assert len(listed) == 1


async def test_a_proposed_company_has_no_legal_entity(dcm: AsyncClient) -> None:
    """
    Condition:
    - The raise is for a company not founded yet, then wrongly mixed with an entity, then an existing one without.

    Expected:
    - "Perusahaan belum didirikan" with no entity; the mixed and missing cases name ``legal_entity_id``.
    """
    proposed = await _create(dcm, "p1", subject_type="PROPOSED_ENTITY", legal_entity_id=None, proposed_name="PT Loop")
    mixed = await _create(dcm, "p2", subject_type="PROPOSED_ENTITY")
    missing = await _create(dcm, "p3", legal_entity_id=None)

    assert proposed.status_code == 201, proposed.text
    assert (proposed.json()["subject_label"], proposed.json()["legal_entity"]) == ("Perusahaan belum didirikan", None)
    for refused in (mixed, missing):
        assert refused.status_code == 422
        assert refused.json()["error"]["details"][0]["loc"] == ["body", "legal_entity_id"]


async def test_changing_the_target_makes_a_new_version_and_the_old_one_stays(dcm: AsyncClient) -> None:
    """
    Condition:
    - The target changes from USD 500000 to USD 750000.

    Expected:
    - Version 2 has the new target; version 1, which a sent pitch would point at, keeps the old one.
    """
    created = (await _create(dcm)).json()
    changed = (await _update(dcm, created, 1, "v2", target_amount="750000")).json()
    old = (await dcm.get(f"/api/v1/funding-requests/{created['id']}/versions/1")).json()
    stale = await _update(dcm, created, 1, "stale", target_amount="1")

    assert (changed["version"], changed["target_amount"]) == (2, "750000.0000")
    assert old["target_amount"] == "500000.0000"
    assert stale.status_code == 409 and stale.json()["error"]["code"] == "STALE_VERSION"


@pytest.mark.parametrize(
    ("content", "field", "message"),
    [
        ({"target_amount": "0"}, "target_amount", "Isi target pendanaan lebih dari nol."),
        (
            {"desired_min": "100000", "desired_max": "50000"},
            "desired_max",
            "Batas atas tidak boleh lebih kecil dari batas bawah.",
        ),
        ({"desired_min": "-1"}, "desired_min", "Isi angka tanpa tanda minus."),
        ({"target_amount": "lima ratus"}, "target_amount", "Isi dengan angka desimal, misalnya 500000 atau 500000.50."),
        ({"currency": "EUR"}, "currency", "Mata uang ini belum didukung. Pilih IDR atau USD."),
    ],
)
async def test_invalid_amounts_name_the_field_and_store_nothing(
    dcm: AsyncClient, content: dict, field: str, message: str
) -> None:
    """
    Condition:
    - An amount breaks a rule.

    Expected:
    - ``VALIDATION_FAILED`` with the field's Indonesian message; no request exists.
    """
    response = await _create(dcm, **content)

    assert response.status_code == 422
    assert {"loc": ["body", field], "msg": message, "type": "funding"} in response.json()["error"]["details"]
    assert (await dcm.get("/api/v1/funding-requests")).json() == []


@pytest.mark.parametrize("extra", [{"valuation": "5000000"}, {"share_count": 1000}, {"equity_percentage": "10"}])
async def test_no_valuation_shares_or_percentage_is_accepted(dcm: AsyncClient, extra: dict) -> None:
    """
    Condition:
    - The request carries a valuation, a share count or a percentage.

    Expected:
    - Refused as an unknown field; nothing is stored or derived.
    """
    response = await _create(dcm, **extra)

    assert response.status_code == 422
    assert (await dcm.get("/api/v1/funding-requests")).json() == []


async def test_an_archived_invention_cannot_be_linked(dcm: AsyncClient) -> None:
    """
    Condition:
    - F05 is archived, then linked.

    Expected:
    - ``CONFLICT``; nothing is stored.
    """
    f05 = (await dcm.get(f"/api/v1/inventions/{dcm.headers['X-F05']}")).json()
    await dcm.post(
        f"/api/v1/inventions/{f05['id']}/archive",
        json={"acting_party_id": dcm.headers["X-Acting-Party"], "expected_version": f05["version"]},
    )

    response = await _create(dcm)

    assert response.status_code == 409
    assert (await dcm.get("/api/v1/funding-requests")).json() == []


async def test_activation_needs_a_target_and_an_invention(dcm: AsyncClient) -> None:
    """
    Condition:
    - A draft without a target or links is activated, and a closed one is reactivated.

    Expected:
    - The first names both fields; the second is ``INVALID_TRANSITION``.
    """
    empty = (
        await _create(dcm, target_amount=None, desired_min=None, desired_max=None, currency=None, invention_ids=[])
    ).json()
    party = dcm.headers["X-Acting-Party"]
    refused = await dcm.post(
        f"/api/v1/funding-requests/{empty['id']}/activate", json={"acting_party_id": party, "expected_version": 1}
    )
    closed = await dcm.post(
        f"/api/v1/funding-requests/{empty['id']}/close", json={"acting_party_id": party, "expected_version": 1}
    )
    reopened = await dcm.post(
        f"/api/v1/funding-requests/{empty['id']}/activate", json={"acting_party_id": party, "expected_version": 2}
    )

    assert [item["loc"][-1] for item in refused.json()["error"]["details"]] == ["target_amount", "invention_ids"]
    assert closed.json()["status"] == "CLOSED"
    assert reopened.json()["error"]["code"] == "INVALID_TRANSITION"


async def test_another_partys_entity_is_not_found(
    dcm: AsyncClient, new_client: Callable[[], AsyncClient], sign_up
) -> None:
    """
    Condition:
    - Bima names Demo Circular Materials' legal entity in his own raise.

    Expected:
    - ``NOT_FOUND``.
    """
    async with new_client() as bima:
        me = await sign_up(bima, "bima@example.com", name="Bima")
        response = await bima.post(
            "/api/v1/funding-requests",
            json={"acting_party_id": me["active_party_id"], **FRAISE01, "legal_entity_id": dcm.headers["X-Entity"]},
            headers={"Idempotency-Key": "b"},
        )

    assert response.status_code == 404


@pytest.mark.parametrize(
    ("composition_id", "mutations_allowed"),
    [("generic-base", True), ("generic-with-review", True), ("project-support-only", False)],
)
async def test_ac67_funding_follows_the_composition_and_stays_readable(
    dcm: AsyncClient, composition: Callable[[str], None], composition_id: str, mutations_allowed: bool
) -> None:
    """
    Condition:
    - A raise exists; the deployment then runs each of the three compositions (AC67).

    Expected:
    - Without ``company_funding`` every funding mutation is ``CAPABILITY_UNAVAILABLE`` and changes nothing; with it,
      they work. In every composition the owner still reads the raise, its versions and entities, and project
      support keeps working.
    """
    created = (await _create(dcm)).json()
    party = dcm.headers["X-Acting-Party"]
    composition(composition_id)

    mutations = [
        await _create(dcm, "again"),
        await _update(dcm, created, 1, "u", target_amount="600000"),
        await dcm.post(
            f"/api/v1/funding-requests/{created['id']}/pause", json={"acting_party_id": party, "expected_version": 1}
        ),
        await dcm.post("/api/v1/legal-entities", json={"acting_party_id": party, "name": "PT Lain"}),
    ]
    reads = [
        await dcm.get("/api/v1/funding-requests"),
        await dcm.get(f"/api/v1/funding-requests/{created['id']}"),
        await dcm.get(f"/api/v1/funding-requests/{created['id']}/versions/1"),
        await dcm.get("/api/v1/legal-entities"),
    ]
    support = await dcm.post(
        "/api/v1/support-requests",
        json={"acting_party_id": party, "invention_id": dcm.headers["X-F04"], "outcome": "Uji pasar"},
        headers={"Idempotency-Key": "support"},
    )

    if mutations_allowed:
        assert [response.status_code for response in mutations] == [201, 200, 409, 201]  # pause from DRAFT is refused
    else:
        assert {response.json()["error"]["code"] for response in mutations} == {"CAPABILITY_UNAVAILABLE"}
        assert (await dcm.get(f"/api/v1/funding-requests/{created['id']}")).json()["target_amount"] == "500000.0000"
    assert [response.status_code for response in reads] == [200, 200, 200, 200]
    assert reads[1].json()["id"] == created["id"]
    assert support.status_code == 201
