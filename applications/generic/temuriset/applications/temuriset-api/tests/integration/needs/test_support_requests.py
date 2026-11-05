"""Support requests and project budgets through Postgres (spec 013)."""

import logging
from collections.abc import AsyncIterator, Callable
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select

from app.core.database import get_session_factory
from app.platform.repository.sqlalchemy.models import AuditEventRecord, OutboxEventRecord

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("clean_tables")]

F01_BUDGET = {
    "min": "20000",
    "max": "30000",
    "currency": "USD",
    "period": "6 bulan",
    "scope": "biaya pilot enam bulan",
    "estimated_on": "2026-10-30",
    "assumptions": "Uji lapangan di dua lokasi",
}


@pytest.fixture
async def rani(client: AsyncClient, sign_up, published_invention) -> AsyncIterator[AsyncClient]:
    """Rani with one published invention."""
    me = await sign_up(client, "rani@example.com")
    client.headers["X-Acting-Party"] = me["active_party_id"]
    client.headers["X-Invention"] = (await published_invention(client))["id"]
    yield client


def _body(client: AsyncClient, **content: Any) -> dict:
    return {
        "acting_party_id": client.headers["X-Acting-Party"],
        "outcome": "Validasi prototipe enam bulan",
        "support_forms": ["project_funding", "testing_support"],
        "relationship_form": "PROJECT",
        "scope": "Validasi prototipe",
        "months": 6,
        "region": "Indonesia",
        "accepts_partial": True,
        **content,
    }


async def _create(client: AsyncClient, key: str = "c1", **content: Any) -> Any:
    return await client.post(
        "/api/v1/support-requests",
        json={"invention_id": client.headers["X-Invention"], **_body(client, **content)},
        headers={"Idempotency-Key": key},
    )


async def _update(client: AsyncClient, request: dict, version: int, key: str, **content: Any) -> Any:
    return await client.put(
        f"/api/v1/support-requests/{request['id']}",
        json={"expected_version": version, **_body(client, **content)},
        headers={"Idempotency-Key": key},
    )


async def _move(client: AsyncClient, request: dict, action: str, version: int, key: str | None = None) -> Any:
    return await client.post(
        f"/api/v1/support-requests/{request['id']}/{action}",
        json={"acting_party_id": client.headers["X-Acting-Party"], "expected_version": version},
        headers={"Idempotency-Key": key or f"{action}-{version}"},
    )


async def test_f01_budget_is_stored_exactly_and_returned_as_strings(rani: AsyncClient) -> None:
    """
    Condition:
    - F01's request "Validasi prototipe enam bulan" with budget USD 20000–30000 over six months.

    Expected:
    - Amounts come back as ``"20000.0000"`` and ``"30000.0000"`` with currency, period, scope and assumptions; the
      request names its invention version.
    """
    response = await _create(rani, budget=F01_BUDGET)

    assert response.status_code == 201, response.text
    body = response.json()
    assert (body["status"], body["version"], body["invention_version"], body["invention_title"]) == (
        "DRAFT",
        1,
        1,
        "Saringan air keramik desa",
    )
    assert body["support_forms"] == ["project_funding", "testing_support"] and body["relationship_form"] == "PROJECT"
    assert body["budget"] | {"lines": None} == {
        "min": "20000.0000",
        "max": "30000.0000",
        "currency": "USD",
        "basis": "total_period",
        "period": "6 bulan",
        "scope": "biaya pilot enam bulan",
        "estimated_on": "2026-10-30",
        "assumptions": "Uji lapangan di dua lokasi",
        "unknown_reason": None,
        "financial": True,
        "lines": None,
        "lines_total": None,
        "lines_explanation": "",
    }


@pytest.mark.parametrize(
    ("budget", "field", "message"),
    [
        ({"min": "-1", "max": "100"}, "min", "Biaya minimum tidak boleh negatif."),
        ({"min": "300", "max": "200"}, "max", "Biaya maksimum tidak boleh lebih kecil dari biaya minimum."),
        ({"min": "abc", "max": "200"}, "min", "Isi dengan angka desimal, misalnya 20000 atau 20000.50."),
        ({"min": None, "max": None}, "unknown_reason", "Pilih alasan bila kisaran biaya belum diketahui."),
        (
            {"min": "100", "max": "200", "currency": "EUR"},
            "currency",
            "Mata uang ini belum didukung. Pilih IDR atau USD.",
        ),
    ],
)
async def test_invalid_budget_names_the_field_and_keeps_previous_values(
    rani: AsyncClient, budget: dict, field: str, message: str
) -> None:
    """
    Condition:
    - A saved request is changed with an invalid budget (AC16).

    Expected:
    - ``VALIDATION_FAILED`` with the Indonesian message for that field; the request keeps its previous version and
      budget.
    """
    created = (await _create(rani, budget=F01_BUDGET)).json()

    response = await _update(rani, created, 1, "bad", budget={"currency": "USD", **budget})
    after = (await rani.get(f"/api/v1/support-requests/{created['id']}")).json()

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "VALIDATION_FAILED"
    assert {"loc": ["body", "budget", field], "msg": message, "type": "budget"} in error["details"]
    assert (after["version"], after["budget"]["min"], after["budget"]["max"]) == (1, "20000.0000", "30000.0000")


async def test_unknown_money_is_null_with_a_reason_never_zero(rani: AsyncClient) -> None:
    """
    Condition:
    - A non-cash validation request whose money is not determined yet (AC17), then completed later.

    Expected:
    - min and max read ``null`` with ``not_determined``; completing the range makes a new version.
    """
    created = (
        await _create(rani, accepts_noncash=True, budget={"min": None, "max": None, "unknown_reason": "not_determined"})
    ).json()
    completed = (await _update(rani, created, 1, "complete", budget=F01_BUDGET)).json()

    assert (created["budget"]["min"], created["budget"]["max"], created["budget"]["unknown_reason"]) == (
        None,
        None,
        "not_determined",
    )
    assert created["budget"]["currency"] is None
    assert (completed["version"], completed["budget"]["min"], completed["budget"]["unknown_reason"]) == (
        2,
        "20000.0000",
        None,
    )


async def test_zero_needs_an_explicitly_non_financial_request(rani: AsyncClient) -> None:
    """
    Condition:
    - A zero amount on a financial budget, then on one marked non-financial.

    Expected:
    - The first is refused; the second is stored.
    """
    refused = await _create(rani, "z1", budget={"min": "0", "max": "0", "currency": "IDR"})
    allowed = await _create(rani, "z2", budget={"min": "0", "max": "0", "currency": "IDR", "financial": False})

    assert refused.status_code == 422
    assert "nonfinansial" in refused.json()["error"]["details"][0]["msg"]
    assert allowed.status_code == 201 and allowed.json()["budget"]["min"] == "0.0000"


async def test_lines_add_up_exactly_or_need_an_explanation(rani: AsyncClient) -> None:
    """
    Condition:
    - Lines of 0.1 and 0.2 (SC-001), then lines whose sum falls outside the range.

    Expected:
    - Totals are exact (``"0.3000"``, no float drift); a range that differs from the sum needs an explanation such
      as "cakupan sebagian".
    """
    lines = [
        {"label": "Bahan", "quantity": "1", "unit_cost": "0.1"},
        {"label": "Ongkos", "quantity": "1", "unit_cost": "0.2"},
    ]
    exact = await _create(rani, "l1", budget={"min": "0.3", "max": "0.3", "currency": "IDR", "lines": lines})
    big_lines = [{"label": "Uji lapangan", "quantity": "2", "unit_cost": "5000"}]
    unexplained = await _create(rani, "l2", budget={**F01_BUDGET, "lines": big_lines})
    explained = await _create(
        rani, "l3", budget={**F01_BUDGET, "lines": big_lines, "lines_explanation": "cakupan sebagian"}
    )

    assert exact.json()["budget"]["lines_total"] == "0.3000"
    assert [line["total"] for line in exact.json()["budget"]["lines"]] == ["0.1000", "0.2000"]
    assert unexplained.status_code == 422
    assert unexplained.json()["error"]["details"][0]["loc"] == ["body", "budget", "lines_explanation"]
    assert explained.status_code == 201 and explained.json()["budget"]["lines_total"] == "10000.0000"


async def test_status_moves_and_activation_needs_outcome_and_forms(rani: AsyncClient) -> None:
    """
    Condition:
    - A draft without support forms is activated, then completed, activated, paused, reactivated and closed.

    Expected:
    - The first activation names the missing field; then DRAFT → ACTIVE → PAUSED → ACTIVE → CLOSED, and a closed
      request cannot be reactivated or edited.
    """
    created = (await _create(rani, support_forms=[], budget=F01_BUDGET)).json()

    refused = await _move(rani, created, "activate", 1)
    completed = (await _update(rani, created, 1, "forms", support_forms=["mentoring"])).json()
    statuses, version = [], completed["version"]
    for action in ("activate", "pause", "activate", "close"):
        moved = (await _move(rani, created, action, version)).json()
        statuses.append(moved["status"])
        version = moved["version"]
    reopened = await _move(rani, created, "activate", version)
    edit_closed = await _update(rani, created, version, "after-close")

    assert refused.json()["error"]["details"] == [
        {"loc": ["body", "support_forms"], "msg": "Pilih setidaknya satu bentuk dukungan.", "type": "activation"}
    ]
    assert statuses == ["ACTIVE", "PAUSED", "ACTIVE", "CLOSED"]
    assert (reopened.status_code, reopened.json()["error"]["code"]) == (409, "INVALID_TRANSITION")
    assert edit_closed.status_code == 409
    final = (await rani.get(f"/api/v1/support-requests/{created['id']}")).json()
    assert final["budget"]["min"] == "20000.0000"


@pytest.mark.parametrize(("action", "needs_active"), [("activate", False), ("pause", True), ("close", True)])
async def test_retried_status_change_is_replayed_and_happens_once(
    rani: AsyncClient, action: str, needs_active: bool
) -> None:
    """
    Condition:
    - A status change is retried with the same key after its response was lost.

    Expected:
    - The stored response is replayed instead of a stale-version failure, the version moves once, one audit event
      exists, and the operation reports the request as its committed result.
    """
    created = (await _create(rani)).json()
    version = created["version"]
    if needs_active:
        version = (await _move(rani, created, "activate", version, "setup")).json()["version"]

    first = await _move(rani, created, action, version, "retry")
    retry = await _move(rani, created, action, version, "retry")

    operation = (await rani.get(f"/api/v1/operations/{first.json()['operation_id']}")).json()
    final = (await rani.get(f"/api/v1/support-requests/{created['id']}")).json()
    async with get_session_factory()() as session:
        audited = await session.scalar(
            select(func.count())
            .select_from(AuditEventRecord)
            .where(AuditEventRecord.action == f"support_request.{action}", AuditEventRecord.subject_id == created["id"])
        )
    assert first.status_code == 200, first.text
    assert "Idempotent-Replayed" not in first.headers
    assert retry.status_code == 200
    assert retry.headers["Idempotent-Replayed"] == "true"
    assert retry.json() == first.json()
    assert final["version"] == version + 1
    assert audited == 1
    assert operation["status"] == "COMMITTED"
    assert operation["result"] == {"type": "support_request", "id": created["id"]}


@pytest.mark.parametrize("action", ["activate", "pause", "close"])
async def test_status_change_without_a_key_is_refused(
    rani: AsyncClient, caplog: pytest.LogCaptureFixture, action: str
) -> None:
    """
    Condition:
    - A status change arrives with no ``Idempotency-Key``.

    Expected:
    - ``BAD_REQUEST`` names the header, is not retryable, is recorded under its request ID, and changes nothing.
    """
    created = (await _create(rani)).json()

    with caplog.at_level(logging.WARNING):
        response = await rani.post(
            f"/api/v1/support-requests/{created['id']}/{action}",
            json={"acting_party_id": rani.headers["X-Acting-Party"], "expected_version": created["version"]},
        )

    error = response.json()["error"]
    final = (await rani.get(f"/api/v1/support-requests/{created['id']}")).json()
    assert response.status_code == 400
    assert error["code"] == "BAD_REQUEST"
    assert error["message"] == "Permintaan ini memerlukan kunci Idempotency-Key. Kirim ulang dengan kunci tersebut."
    assert error["details"][0]["loc"] == ["header", "Idempotency-Key"]
    assert error["recovery"] == {"retryable": False}
    assert error["request_id"] in caplog.text
    assert (final["status"], final["version"]) == ("DRAFT", created["version"])


async def test_status_change_key_reused_for_another_version_is_a_conflict(
    rani: AsyncClient, caplog: pytest.LogCaptureFixture
) -> None:
    """
    Condition:
    - A key that activated version 1 is reused to activate the request again at a later version.

    Expected:
    - ``IDEMPOTENCY_CONFLICT``, not retryable, recorded under its request ID, and the request stays paused.
    """
    created = (await _create(rani)).json()
    await _move(rani, created, "activate", 1, "reused")
    paused = (await _move(rani, created, "pause", 2, "pause")).json()

    with caplog.at_level(logging.WARNING):
        response = await _move(rani, created, "activate", paused["version"], "reused")

    error = response.json()["error"]
    final = (await rani.get(f"/api/v1/support-requests/{created['id']}")).json()
    assert response.status_code == 409
    assert error["code"] == "IDEMPOTENCY_CONFLICT"
    assert (
        error["message"]
        == "Kunci permintaan ini sudah dipakai untuk isi berbeda. Gunakan kunci baru untuk permintaan baru."
    )
    assert error["recovery"] == {"retryable": False}
    assert error["request_id"] in caplog.text
    assert (final["status"], final["version"]) == ("PAUSED", paused["version"])


async def test_one_key_on_two_actions_is_never_replayed(rani: AsyncClient) -> None:
    """
    Condition:
    - The key that activated a request is reused to close it, first with the same body and then with the current
      version. The two bodies of the first pair are identical, so only the operation name tells them apart.

    Expected:
    - The first close is judged on its own and is stale rather than a replay of the activation; the second runs.
    """
    created = (await _create(rani)).json()
    activated = await _move(rani, created, "activate", 1, "shared")

    stale = await _move(rani, created, "close", 1, "shared")
    between = (await rani.get(f"/api/v1/support-requests/{created['id']}")).json()
    closed = await _move(rani, created, "close", activated.json()["version"], "shared")

    assert "Idempotent-Replayed" not in stale.headers
    assert (stale.status_code, stale.json()["error"]["code"]) == (409, "STALE_VERSION")
    assert between["status"] == "ACTIVE"
    assert closed.status_code == 200, closed.text
    assert closed.json()["status"] == "CLOSED"


async def test_one_key_on_two_requests_never_answers_for_the_wrong_one(rani: AsyncClient) -> None:
    """
    Condition:
    - The key that activated one request is sent to activate another, with an identical body.

    Expected:
    - ``IDEMPOTENCY_CONFLICT`` instead of a success carrying the first request, and the second stays a draft.
    """
    first = (await _create(rani, "first")).json()
    second = (await _create(rani, "second")).json()
    await _move(rani, first, "activate", 1, "shared")

    response = await _move(rani, second, "activate", 1, "shared")

    final = (await rani.get(f"/api/v1/support-requests/{second['id']}")).json()
    assert (response.status_code, response.json()["error"]["code"]) == (409, "IDEMPOTENCY_CONFLICT")
    assert "Idempotent-Replayed" not in response.headers
    assert (final["status"], final["version"]) == ("DRAFT", 1)


async def test_editing_makes_a_new_version_and_the_old_one_stays(rani: AsyncClient) -> None:
    """
    Condition:
    - An active request's outcome is changed.

    Expected:
    - A new version; version 1 still reads the old outcome and budget; a change event is written per version.
    """
    created = (await _create(rani, budget=F01_BUDGET)).json()
    changed = (await _update(rani, created, 1, "v2", outcome="Validasi prototipe sembilan bulan")).json()
    old = (await rani.get(f"/api/v1/support-requests/{created['id']}/versions/1")).json()

    assert (changed["version"], changed["outcome"], changed["budget"]["max"]) == (
        2,
        "Validasi prototipe sembilan bulan",
        "30000.0000",
    )
    assert (old["outcome"], old["budget"]["max"]) == ("Validasi prototipe enam bulan", "30000.0000")
    async with get_session_factory()() as session:
        topics = list(
            await session.scalars(
                select(OutboxEventRecord.topic).where(OutboxEventRecord.topic.like("support_request%"))
            )
        )
    assert topics == ["support_request.changed", "support_request.changed"]


async def test_stale_version_does_not_overwrite(rani: AsyncClient) -> None:
    """
    Condition:
    - Two tabs change version 1.

    Expected:
    - The second gets ``STALE_VERSION``.
    """
    created = (await _create(rani)).json()
    await _update(rani, created, 1, "first", outcome="Satu")

    stale = await _update(rani, created, 1, "second", outcome="Dua")

    assert stale.status_code == 409 and stale.json()["error"]["current_version"] == 2


async def test_another_partys_or_unpublished_invention_is_refused(
    rani: AsyncClient, new_client: Callable[[], AsyncClient], sign_up
) -> None:
    """
    Condition:
    - Bima tries to attach a request to Rani's invention; Rani tries an unpublished one.

    Expected:
    - ``NOT_FOUND`` for Bima; ``CONFLICT`` for the unpublished invention.
    """
    async with new_client() as bima:
        me = await sign_up(bima, "bima@example.com", persona="mitra", name="Bima")
        foreign = await bima.post(
            "/api/v1/support-requests",
            json={
                "invention_id": rani.headers["X-Invention"],
                "acting_party_id": me["active_party_id"],
                "outcome": "x",
            },
            headers={"Idempotency-Key": "b"},
        )
    draft = (
        await rani.post(
            "/api/v1/inventions",
            json={"acting_party_id": rani.headers["X-Acting-Party"]},
            headers={"Idempotency-Key": "d"},
        )
    ).json()
    unpublished = await rani.post(
        "/api/v1/support-requests",
        json={"invention_id": draft["id"], "acting_party_id": rani.headers["X-Acting-Party"], "outcome": "x"},
        headers={"Idempotency-Key": "u"},
    )

    assert foreign.status_code == 404
    assert unpublished.status_code == 409
