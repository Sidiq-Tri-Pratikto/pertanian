"""Failures end to end: message, code, reference, record, recovery, and no injected secret anywhere (rules 003, 008)."""

import logging
from copy import deepcopy

import pytest
from httpx import AsyncClient, Response

from tests.factories.recipients import (
    OPPORTUNITIES,
    PROFILES,
    create_opportunity,
    move_opportunity,
    save_profile,
)

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("clean_tables")]

CONTENT = deepcopy(OPPORTUNITIES["A1"]["content"])
SECRET = "sk-live-FAKESECRET-123"


def _party(client: AsyncClient) -> str:
    return client.headers["X-Acting-Party"]


def _assert_failure(
    response: Response, caplog: pytest.LogCaptureFixture, *, status: int, code: str, message: str
) -> None:
    error = response.json()["error"]
    assert response.status_code == status
    assert error["code"] == code
    assert error["message"] == message
    assert error["recovery"] == {"retryable": False}
    assert error["request_id"] in caplog.text
    assert SECRET not in response.text
    assert SECRET not in caplog.text


async def test_a_refused_requirement(partner: AsyncClient, caplog: pytest.LogCaptureFixture) -> None:
    """
    Condition:
    - A requirement's value does not fit its operator, and its text carries a fake secret.

    Expected:
    - ``VALIDATION_FAILED`` with a field message that does not echo the input, recorded under its request ID, with the
      secret nowhere.
    """
    requirement = {
        "label": f"Syarat {SECRET}",
        "field": "stage",
        "operator": "in_set",
        "value": SECRET,
        "reason": SECRET,
    }

    with caplog.at_level(logging.WARNING):
        response = await create_opportunity(partner, _party(partner), {**CONTENT, "requirements": [requirement]})

    _assert_failure(
        response,
        caplog,
        status=422,
        code="VALIDATION_FAILED",
        message="Ada isian yang belum valid. Perbaiki isian yang ditandai lalu simpan lagi.",
    )
    assert response.json()["error"]["details"] == [
        {
            "loc": ["body", "requirements", 0, "value"],
            "msg": "Isi daftar nilai untuk dibandingkan.",
            "type": "requirement",
        }
    ]


async def test_an_unnamed_field_with_a_secret(partner: AsyncClient, caplog: pytest.LogCaptureFixture) -> None:
    """
    Condition:
    - A profile save sends a field the profile does not hold, with a fake secret as its value.

    Expected:
    - ``VALIDATION_FAILED``, recorded under its request ID, with the secret nowhere.
    """
    with caplog.at_level(logging.WARNING):
        response = await save_profile(partner, _party(partner), {"credentials": SECRET})

    error = response.json()["error"]
    assert (response.status_code, error["code"]) == (422, "VALIDATION_FAILED")
    assert error["recovery"] == {"retryable": False}
    assert error["request_id"] in caplog.text
    assert SECRET not in response.text
    assert SECRET not in caplog.text


async def test_an_invalid_transition(partner: AsyncClient, caplog: pytest.LogCaptureFixture) -> None:
    """
    Condition:
    - A draft is paused, with a fake secret as the idempotency key.

    Expected:
    - ``INVALID_TRANSITION``, recorded under its request ID, with the secret nowhere, and the key free for a retry.
    """
    party = _party(partner)
    draft = (await create_opportunity(partner, party, CONTENT)).json()

    with caplog.at_level(logging.WARNING):
        response = await move_opportunity(partner, party, draft["id"], "pause", draft["version"], key=SECRET)
        retry = await move_opportunity(partner, party, draft["id"], "pause", draft["version"], key=SECRET)

    _assert_failure(
        response,
        caplog,
        status=409,
        code="INVALID_TRANSITION",
        message="Status ini tidak dapat diubah dengan cara itu. Muat ulang untuk melihat status terbaru.",
    )
    assert "Idempotent-Replayed" not in retry.headers
    assert retry.json()["error"]["code"] == "INVALID_TRANSITION"


async def test_a_handoff_conflict(
    partner: AsyncClient, stranger: AsyncClient, caplog: pytest.LogCaptureFixture
) -> None:
    """
    Condition:
    - A handoff is sent to a partner whose route is in-app, with a fake secret as the idempotency key.

    Expected:
    - ``CONFLICT`` with its two-clause message, recorded under its request ID, with the secret nowhere.
    """
    party = _party(partner)
    await save_profile(partner, party, PROFILES["A"]["content"])

    with caplog.at_level(logging.WARNING):
        response = await stranger.post(
            f"/api/v1/partners/{party}/handoffs",
            json={"acting_party_id": _party(stranger)},
            headers={"Idempotency-Key": SECRET},
        )

    _assert_failure(
        response,
        caplog,
        status=409,
        code="CONFLICT",
        message="Mitra ini tidak memakai jalur eksternal. Gunakan jalur yang tersedia pada profilnya.",
    )
