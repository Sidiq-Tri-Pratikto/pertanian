"""Synthetic OAuth through the owner routes and a real loopback transport."""

import asyncio
import json
import logging
from base64 import urlsafe_b64encode
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from socket import AF_INET, SOCK_STREAM, socket
from urllib.parse import parse_qs, urlsplit

import pytest
import uvicorn
from httpx import AsyncClient
from sqlalchemy import text

from app.core.database import get_session_factory
from app.core.logging import logger
from app.core.settings import get_settings
from app.main import app
from tests.integration.conftest import LatestCode, SignUp
from tests.integration.scheduling.conftest import (
    TEST_ACCESS_TOKEN,
    CalendarRelay,
    connect_calendar,
    consent,
    disconnect_calendar,
)

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("clean_tables")]
ROOT = "/api/v1/me/calendar"
FAKE_CODE = "private-synthetic-authorization-code"


def _query(location: str) -> dict[str, list[str]]:
    return parse_qs(urlsplit(location).query)


@pytest.fixture
def calendar_records(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> pytest.LogCaptureFixture:
    """Capture the centralized record in addition to the response."""
    monkeypatch.setattr(logger, "propagate", True)
    caplog.set_level(logging.WARNING, logger="app")
    return caplog


def _record(caplog: pytest.LogCaptureFixture, reference: str) -> dict:
    records = [
        json.loads(entry.getMessage().split("Application failure ", 1)[1])
        for entry in caplog.records
        if entry.name == "app" and reference in entry.getMessage()
    ]
    assert len(records) == 1
    return records[0]


async def test_adapter_off_refuses_mutation_and_reports_planned(client: AsyncClient, sign_up: SignUp) -> None:
    """
    Condition:
    - The default deployment and a signed-in account.

    Expected:
    - The manifest and status remain off, and a write and callback cannot activate the adapter.
    """
    await sign_up(client, "calendar-owner@example.com")
    status = await client.get(ROOT)
    manifest = await client.get("/api/v1/capabilities")
    assert status.json() == {"state": "off", "version": 0}
    assert {"id": "calendar", "status": "planned", "implementation": None} in manifest.json()["adapters"]
    failed = await client.post(ROOT + "/connect", json={"expected_version": 0, "consent": True})
    assert failed.status_code == 404
    assert failed.json()["error"]["code"] == "NOT_FOUND"
    callback = await client.get(ROOT + "/callback", params={"code": FAKE_CODE})
    assert callback.status_code == 404
    assert FAKE_CODE not in callback.text
    assert callback.headers["referrer-policy"] == "no-referrer"
    assert "no-store" in callback.headers["cache-control"]


async def test_oauth_consent_state_is_single_use_bound_to_owner_and_session(
    client: AsyncClient,
    new_client: Callable[[], AsyncClient],
    sign_up: SignUp,
    latest_code: LatestCode,
    calendar_relay: CalendarRelay,
    calendar_records: pytest.LogCaptureFixture,
) -> None:
    """
    Condition:
    - The owner consents while another account and a second owner session try to use its state.

    Expected:
    - Only the initiating session exchanges the single-use state with S256 and the fixed scope.
    - The access token and verifier use ciphertext, and state/codes never enter platform operations or records.
    """
    email = "calendar-owner@example.com"
    await sign_up(client, email)
    enabled = (await client.get("/api/v1/capabilities")).json()["adapters"]
    assert {"id": "calendar", "status": "available", "implementation": "loopback-oauth"} in enabled
    for consent_value in (False, 1):
        denied = await client.post(ROOT + "/connect", json={"expected_version": 0, "consent": consent_value})
        assert (denied.status_code, denied.json()["error"]["code"]) == (422, "VALIDATION_FAILED")
    forged = await client.post(
        ROOT + "/connect",
        json={"expected_version": 0, "consent": True},
        headers={"Origin": "http://foreign.test", "Idempotency-Key": "forged"},
    )
    assert (forged.status_code, forged.json()["error"]["code"]) == (403, "FORBIDDEN")
    authorized, params = await consent(client)
    replayed = await client.post(
        ROOT + "/connect",
        json={"expected_version": 0, "consent": True},
        headers={"Idempotency-Key": "consent"},
    )
    assert replayed.headers["idempotent-replayed"] == "true"
    assert "no-store" in replayed.headers["cache-control"]
    assert params["state"] not in replayed.text
    assert params["response_type"] == "code"
    assert params["scope"] == "freebusy.read"
    assert params["code_challenge_method"] == "S256"
    assert params["redirect_uri"] == "http://localhost:8020" + ROOT + "/callback"
    assert authorized.headers["referrer-policy"] == "no-referrer"

    callback_params = {"state": params["state"], "code": FAKE_CODE}
    async with new_client() as unrelated, new_client() as other_session:
        await sign_up(unrelated, "unrelated-calendar@example.com")
        assert (await unrelated.get(ROOT)).json() == {"state": "disconnected", "version": 0}
        sent = await other_session.post("/api/v1/auth/code", json={"email": email, "purpose": "sign_in"})
        assert sent.status_code == 202
        signed = await other_session.post(
            "/api/v1/auth/verify", json={"email": email, "code": await latest_code(client, email)}
        )
        assert signed.status_code == 200, signed.text
        for stranger in (unrelated, other_session):
            wrong = await stranger.get(ROOT + "/callback", params=callback_params)
            assert wrong.status_code == 303
            assert _query(wrong.headers["location"])["kalender"] == ["gagal"]
            reference = _query(wrong.headers["location"])["ref"][0]
            assert _record(calendar_records, reference)["code"] == "APP-CALENDAR-CALLBACK-INVALID"
        assert not calendar_relay.requests

    async with get_session_factory()() as session:
        row = (await session.execute(text("SELECT state_sha256, encrypted_verifier FROM calendar_connections"))).one()
        assert row.state_sha256 == sha256(params["state"].encode()).hexdigest()
        assert params["state"].encode() not in row.encrypted_verifier
    succeeded = await client.get(ROOT + "/callback", params=callback_params)
    assert _query(succeeded.headers["location"]) == {"kalender": ["terhubung"]}
    assert succeeded.headers["referrer-policy"] == "no-referrer"
    rejected = await client.get(ROOT + "/callback", params=callback_params)
    assert _query(rejected.headers["location"])["kalender"] == ["gagal"]
    assert [request.path for request in calendar_relay.requests] == ["/token"]
    exchanged = parse_qs(calendar_relay.requests[0].body.decode())
    verifier = exchanged["code_verifier"][0]
    assert urlsafe_b64encode(sha256(verifier.encode()).digest()).decode().rstrip("=") == params["code_challenge"]
    assert exchanged == {
        "code": [FAKE_CODE],
        "code_verifier": [verifier],
        "grant_type": ["authorization_code"],
        "redirect_uri": [params["redirect_uri"]],
        "client_id": ["local-fixture"],
    }
    assert (await client.get(ROOT)).json() == {"state": "connected", "version": 2}
    async with get_session_factory()() as session:
        row = (await session.execute(text("SELECT * FROM calendar_connections"))).one()
        assert TEST_ACCESS_TOKEN.encode() not in row.encrypted_token
        assert row.state_sha256 is None and row.encrypted_verifier is None
        stored = (await session.execute(text("SELECT response_body::text FROM idempotency_records"))).scalars().all()
    for value in (FAKE_CODE, params["state"], verifier, TEST_ACCESS_TOKEN):
        assert value not in calendar_records.text + succeeded.headers["location"] + rejected.headers["location"]
        assert all(value not in item for item in stored if item)


@pytest.mark.parametrize("bad_token", ["wide_scope", "missing_expiry", "refresh_token", "expired"])
async def test_malformed_or_overprivileged_token_redirects_safely(
    bad_token: str,
    client: AsyncClient,
    sign_up: SignUp,
    calendar_relay: CalendarRelay,
    calendar_records: pytest.LogCaptureFixture,
) -> None:
    """
    Condition:
    - The provider returns a secret-bearing response with an invalid scope, expiry or refresh grant.

    Expected:
    - The consumed attempt cannot be replayed. The safe failure redirect correlates with one sanitized record.
    """
    await sign_up(client, "calendar-owner@example.com")
    _, params = await consent(client)
    if bad_token == "wide_scope":
        calendar_relay.token["scope"] = "freebusy.read full-calendar.read"
    elif bad_token == "missing_expiry":
        del calendar_relay.token["expires_in"]
    elif bad_token == "refresh_token":
        calendar_relay.token["refresh_token"] = "private-synthetic-refresh-token"
    else:
        calendar_relay.token["expires_in"] = 0
    response = await client.get(ROOT + "/callback", params={"state": params["state"], "code": FAKE_CODE})
    assert response.status_code == 303
    redirect = response.headers["location"]
    assert redirect.startswith("http://localhost:3020/settings?")
    result = _query(redirect)
    assert result["kalender"] == ["gagal"]
    record = _record(calendar_records, result["ref"][0])
    assert (record["code"], record["http_status"], record["operation"]) == (
        "APP-CALENDAR-UNAVAILABLE",
        503,
        ROOT + "/callback",
    )
    assert record["debug_info"]["original_message"] == "invalid calendar token response"
    for value in (FAKE_CODE, TEST_ACCESS_TOKEN, params["state"], "private-synthetic-refresh-token"):
        assert value not in response.text + redirect + calendar_records.text
    assert (await client.get(ROOT)).json()["state"] == "disconnected"


async def test_expired_state_and_credential_require_new_consent(
    client: AsyncClient,
    sign_up: SignUp,
    calendar_relay: CalendarRelay,
) -> None:
    """
    Condition:
    - The OAuth attempt has expired, then an independent reconnected credential expires.

    Expected:
    - No exchange runs for expired state and another consent can replace expired credentials.
    """
    await sign_up(client, "calendar-owner@example.com")
    _, pending = await consent(client)
    past = datetime.now(UTC) - timedelta(seconds=1)
    async with get_session_factory()() as session, session.begin():
        await session.execute(text("UPDATE calendar_connections SET state_expires_at = :past"), {"past": past})
    expired = await client.get(ROOT + "/callback", params={"state": pending["state"], "code": FAKE_CODE})
    assert _query(expired.headers["location"])["kalender"] == ["gagal"]
    assert not calendar_relay.requests
    _, current = await consent(client, version=1, key="new-consent")
    callback = await client.get(ROOT + "/callback", params={"state": current["state"], "code": FAKE_CODE})
    assert _query(callback.headers["location"])["kalender"] == ["terhubung"]
    async with get_session_factory()() as session, session.begin():
        await session.execute(text("UPDATE calendar_connections SET token_expires_at = :past"), {"past": past})
    status = (await client.get(ROOT)).json()
    assert status == {"state": "expired", "version": 3}
    _, next_attempt = await consent(client, version=status["version"], key="after-expiry")
    assert next_attempt["state"] != current["state"]


async def test_disconnect_during_exchange_cannot_resurrect_credentials(
    client: AsyncClient,
    sign_up: SignUp,
    calendar_relay: CalendarRelay,
) -> None:
    """
    Condition:
    - A callback consumed state and is waiting on the synthetic provider when the owner disconnects.

    Expected:
    - The local generation changes first. The finished exchange is discarded and its token is revoked.
    """
    await sign_up(client, "calendar-owner@example.com")
    _, params = await consent(client)
    calendar_relay.block_token = True
    callback = asyncio.create_task(client.get(ROOT + "/callback", params={"state": params["state"], "code": FAKE_CODE}))
    await asyncio.wait_for(calendar_relay.token_started.wait(), 1)
    disconnected = await disconnect_calendar(client)
    assert disconnected.json()["revocation"] == "not_required"
    calendar_relay.release_token.set()
    response = await callback
    assert _query(response.headers["location"])["kalender"] == ["gagal"]
    assert (await client.get(ROOT)).json() == {"state": "disconnected", "version": 2}
    assert [request.path for request in calendar_relay.requests] == ["/token", "/revoke"]


@pytest.mark.parametrize(("relay_status", "result"), [(200, "confirmed"), (503, "unconfirmed")])
async def test_disconnect_commits_locally_and_retries_never_revoke_twice(
    client: AsyncClient,
    sign_up: SignUp,
    calendar_relay: CalendarRelay,
    relay_status: int,
    result: str,
) -> None:
    """
    Condition:
    - The provider accepts or fails revocation and the browser retries its original mutation.

    Expected:
    - Both responses report a committed local disconnect and a truthful provider result.
    - The stored credential is deleted and the same idempotent intent performs one remote revoke.
    """
    await sign_up(client, "calendar-owner@example.com")
    await connect_calendar(client)
    calendar_relay.revoke_status = relay_status
    disconnected = await disconnect_calendar(client)
    replayed = await client.post(
        ROOT + "/disconnect",
        json={"expected_version": 2},
        headers={"Idempotency-Key": "disconnect"},
    )
    assert disconnected.status_code == 200 and disconnected.json() == replayed.json()
    assert disconnected.json()["revocation"] == "unconfirmed"
    assert (await client.get(ROOT)).json()["revocation"] == result
    assert replayed.headers["idempotent-replayed"] == "true"
    assert [request.path for request in calendar_relay.requests] == ["/token", "/revoke"]
    async with get_session_factory()() as session:
        row = (await session.execute(text("SELECT encrypted_token, token_expires_at FROM calendar_connections"))).one()
        assert row.encrypted_token is None and row.token_expires_at is None


async def test_disabled_profile_still_lets_only_the_owner_erase_local_credentials(
    client: AsyncClient,
    new_client: Callable[[], AsyncClient],
    sign_up: SignUp,
    calendar_relay: CalendarRelay,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Condition:
    - The owner connected locally and the deployment switches the profile off and removes its key.

    Expected:
    - Only the owner sees its remaining connection and can remove it. No provider request is sent.
    """
    await sign_up(client, "calendar-owner@example.com")
    await connect_calendar(client)
    settings = get_settings()
    monkeypatch.setattr(settings, "calendar_adapter", "off")
    monkeypatch.setattr(settings, "calendar_envelope_key", None)
    async with new_client() as other:
        await sign_up(other, "calendar-other@example.com")
        assert (await other.get(ROOT)).json() == {"state": "off", "version": 0}
        assert (await disconnect_calendar(other)).status_code == 404
    assert (await client.get(ROOT)).json() == {"state": "off_with_connection", "version": 2}
    result = await disconnect_calendar(client)
    assert result.status_code == 200 and result.json()["revocation"] == "unconfirmed"
    assert (await client.get(ROOT)).json() == {"state": "off", "version": 3, "revocation": "unconfirmed"}
    assert [request.path for request in calendar_relay.requests] == ["/token"]
    async with get_session_factory()() as session:
        assert await session.scalar(text("SELECT encrypted_token IS NULL FROM calendar_connections")) is True


async def test_uvicorn_callback_access_logs_omit_credentials_and_preserve_other_queries(
    calendar_relay: CalendarRelay,
    calendar_records: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Condition:
    - A direct callback with sensitive values reaches Uvicorn's actual HTTP protocol.

    Expected:
    - The callback query is absent from access and application logs and from the response.
    - An ordinary request is still logged with its query.
    """
    access = logging.getLogger("uvicorn.access")
    monkeypatch.setattr(access, "propagate", True)
    calendar_records.set_level(logging.INFO, logger=access.name)
    config = uvicorn.Config(app, host="127.0.0.1", port=0, log_config=None, lifespan="off", access_log=True)
    server = uvicorn.Server(config)
    state = "abcd" * 16
    with socket(AF_INET, SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        task = asyncio.create_task(server.serve(sockets=[listener]))
        try:
            async with asyncio.timeout(2):
                while not server.started:
                    await asyncio.sleep(0.01)
            async with AsyncClient(base_url=f"http://127.0.0.1:{listener.getsockname()[1]}", trust_env=False) as api:
                response = await api.get(ROOT + "/callback", params={"state": state, "code": FAKE_CODE})
                health = await api.get("/health/live", params={"probe": "visible"})
            assert health.status_code == 200 and response.status_code == 303
            assert "GET /api/v1/me/calendar/callback HTTP/" in calendar_records.text
            assert "GET /health/live?probe=visible HTTP/" in calendar_records.text
            for private in (FAKE_CODE, state):
                assert private not in calendar_records.text + response.headers["location"] + response.text
        finally:
            server.should_exit = True
            await asyncio.wait_for(task, 3)


@pytest.mark.parametrize("connected", [False, True])
async def test_completed_account_profile_erasure_removes_calendar_state_and_ciphertext(
    client: AsyncClient,
    sign_up: SignUp,
    calendar_relay: CalendarRelay,
    connected: bool,
) -> None:
    """
    Condition:
    - The privacy worker fulfills account-profile erasure with a pending or connected calendar.

    Expected:
    - The retained anonymized account has no calendar row, and erasure sends no provider request.
    """
    from uuid import UUID

    from app.moderation.model.schema import CategoryToRemove, PrivacyAnswer
    from app.moderation.service.retention import complete_deletion, prepare_deletion

    me = await sign_up(client, "calendar-owner@example.com")
    if connected:
        await connect_calendar(client)
    else:
        await consent(client)
    account_id = UUID(me["account"]["id"])
    answer = PrivacyAnswer(
        to_remove=[CategoryToRemove(key="account_profile", label="Profil akun")],
        removed=[],
        retained=[],
        notice="",
    )
    async with get_session_factory()() as session, session.begin():
        await prepare_deletion(session, account_id, answer)
    async with get_session_factory()() as session, session.begin():
        await complete_deletion(session, account_id, answer)
    async with get_session_factory()() as session:
        assert await session.scalar(text("SELECT count(*) FROM calendar_connections")) == 0
        assert (await session.scalar(text("SELECT email FROM accounts"))).startswith("deleted-")
    assert [request.path for request in calendar_relay.requests] == (["/token"] if connected else [])
    assert (await client.get(ROOT)).status_code == 401
