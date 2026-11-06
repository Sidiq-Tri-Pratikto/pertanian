"""Accounts and sessions through the real application and Postgres (spec 006)."""

import logging
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select

from app.core import clock
from app.core.database import get_session_factory
from app.core.settings import get_settings
from app.identity.model.schema import CodeRequest
from app.identity.repository.sqlalchemy.models import AccountRecord, EmailCodeRecord, SessionRecord
from app.identity.service.mailbox_service import SECRET_DELIVERY
from app.identity.service.service import IdentityService
from app.platform.repository.sqlalchemy.models import JobRecord
from app.worker.loop import run_jobs
from app.worker.registry import registry
from tests.integration.mail_relay import LocalRelay

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("clean_tables")]

EMAIL = "rani@example.com"
START = datetime(2026, 11, 5, 9, tzinfo=UTC)


async def _request(client: AsyncClient, email: str = EMAIL, purpose: str = "sign_up", **profile: str):
    body = {"email": email, "purpose": purpose, "display_name": "Rani", "time_zone": "Asia/Jakarta", **profile}
    return await client.post("/api/v1/auth/code", json=body)


async def _code_rows() -> list[EmailCodeRecord]:
    async with get_session_factory()() as session:
        return list(await session.scalars(select(EmailCodeRecord)))


async def test_inventor_signs_up_without_any_organization(client: AsyncClient, latest_code) -> None:
    """
    Condition:
    - A new email signs up as an inventor with locale ``id`` and ``Asia/Jakarta`` (AC01).

    Expected:
    - A code is mailed and stored hashed; verifying it sets an http-only session cookie and ``/me`` shows a verified
      account with a personal party and no organizations.
    """
    sent = await _request(client, "  Rani@Example.COM ", persona="inovator")
    code = await latest_code(client, EMAIL)
    verified = await client.post("/api/v1/auth/verify", json={"email": EMAIL, "code": code})
    me = await client.get("/api/v1/me")

    assert sent.status_code == 202
    assert sent.json() == {"sent": True}
    assert all(code not in (row.code_sha256, row.salt) for row in await _code_rows())
    assert verified.status_code == 200
    cookie = verified.headers["set-cookie"]
    assert "tr_session=" in cookie and "HttpOnly" in cookie and "SameSite=lax" in cookie
    body = me.json()
    assert body["account"] | {"id": None} == {
        "id": None,
        "display_name": "Rani",
        "email": EMAIL,
        "email_verified": True,
        "locale": "id",
        "time_zone": "Asia/Jakarta",
        "persona": "inovator",
        "kind": "user",
        "email_notifications": False,
        "version": 1,
    }
    assert body["active_party_id"] == body["personal_party_id"]
    assert body["organizations"] == []


async def test_partner_needs_no_organization_either(client: AsyncClient, sign_up) -> None:
    """
    Condition:
    - An individual investor signs up as ``mitra`` (AC02).

    Expected:
    - The account exists with its own personal party and no organization.
    """
    me = await sign_up(client, "investor@example.com", persona="mitra", name="Bima")

    assert me["account"]["persona"] == "mitra"
    assert me["organizations"] == []
    assert me["personal_party_id"]


async def test_code_request_never_reveals_whether_an_account_exists(
    client: AsyncClient, new_client: Callable[[], AsyncClient], sign_up
) -> None:
    """
    Condition:
    - Code requests for an existing email (sign-up and sign-in) and for an unknown one (sign-in).

    Expected:
    - Each answer is the same 202 body; the unknown email receives a note instead of a code.
    """
    await sign_up(client, EMAIL)
    async with new_client() as visitor:
        answers = [
            await _request(visitor, EMAIL, "sign_up"),
            await _request(visitor, EMAIL, "sign_in"),
            await _request(visitor, "nobody@example.com", "sign_in"),
        ]
        note = (await visitor.get("/api/v1/dev/mailbox", params={"email": "nobody@example.com"})).json()

    assert {(answer.status_code, answer.text) for answer in answers} == {(202, '{"sent":true}')}
    assert "Belum ada akun" in note[0]["body"]


async def test_sign_in_starts_a_new_session_and_keeps_the_old_one(
    client: AsyncClient, new_client: Callable[[], AsyncClient], sign_up, latest_code
) -> None:
    """
    Condition:
    - An existing account signs in again from another browser.

    Expected:
    - Both sessions work until they expire or are revoked; signing up again does not create a second account.
    """
    first = await sign_up(client, EMAIL)
    async with new_client() as other:
        await _request(other, EMAIL, "sign_up")
        await other.post("/api/v1/auth/verify", json={"email": EMAIL, "code": await latest_code(other, EMAIL)})
        again = (await other.get("/api/v1/me")).json()

    assert (await client.get("/api/v1/me")).status_code == 200
    assert again["account"]["id"] == first["account"]["id"]
    async with get_session_factory()() as session:
        assert await session.scalar(select(func.count()).select_from(AccountRecord)) == 1
        assert await session.scalar(select(func.count()).select_from(SessionRecord)) == 2


async def test_wrong_code_counts_and_says_how_many_attempts_remain(
    client: AsyncClient, latest_code, caplog: pytest.LogCaptureFixture
) -> None:
    """
    Condition:
    - A wrong code is submitted.

    Expected:
    - ``CODE_INVALID`` (422) with ``attempts_left: 4``, not retryable, recorded without the email or code.
    """
    await _request(client)
    code = await latest_code(client, EMAIL)
    wrong = f"{(int(code) + 1) % 1_000_000:06d}"

    with caplog.at_level(logging.DEBUG):
        response = await client.post("/api/v1/auth/verify", json={"email": EMAIL, "code": wrong})

    assert response.status_code == 422
    error = response.json()["error"]
    assert (error["code"], error["attempts_left"], error["recovery"]) == ("CODE_INVALID", 4, {"retryable": False})
    assert error["message"] == "Kode verifikasi tidak cocok. Periksa kode di email Anda lalu coba lagi."
    assert error["request_id"] in caplog.text
    assert EMAIL not in caplog.text and wrong not in caplog.text and code not in caplog.text
    assert (await _code_rows())[0].attempts == 1


async def test_five_wrong_codes_use_the_code_up(client: AsyncClient, latest_code) -> None:
    """
    Condition:
    - Five wrong guesses, then the right code.

    Expected:
    - Attempts left fall to 0, then the right code is refused with ``CODE_EXPIRED``.
    """
    await _request(client)
    code = await latest_code(client, EMAIL)
    wrong = f"{(int(code) + 1) % 1_000_000:06d}"
    left = [
        (await client.post("/api/v1/auth/verify", json={"email": EMAIL, "code": wrong})).json()["error"][
            "attempts_left"
        ]
        for _ in range(5)
    ]
    right = await client.post("/api/v1/auth/verify", json={"email": EMAIL, "code": code})

    assert left == [4, 3, 2, 1, 0]
    assert right.status_code == 422
    assert right.json()["error"]["code"] == "CODE_EXPIRED"
    assert (
        right.json()["error"]["message"]
        == "Kode verifikasi sudah tidak berlaku. Minta kode baru lalu masukkan kode tersebut."
    )


async def test_code_expires_after_ten_minutes(client: AsyncClient, latest_code) -> None:
    """
    Condition:
    - The right code arrives 10 minutes after it was sent.

    Expected:
    - ``CODE_EXPIRED``.
    """
    with clock.frozen(START):
        await _request(client)
    code = await latest_code(client, EMAIL)
    with clock.frozen(START + timedelta(minutes=10)):
        response = await client.post("/api/v1/auth/verify", json={"email": EMAIL, "code": code})

    assert response.json()["error"]["code"] == "CODE_EXPIRED"


async def test_brute_force_is_stopped_by_attempts_and_rate_limits(client: AsyncClient, latest_code) -> None:
    """
    Condition:
    - An attacker tries 1,000 guesses, requesting a new code whenever one is used up (SC-002).

    Expected:
    - Each code accepts at most five guesses, and after five codes in an hour the email is rate limited, so at most
      25 guesses are ever evaluated.
    """
    evaluated = 0
    rate_limited = False
    with clock.frozen(START):
        for guess in range(1000):
            response = await client.post("/api/v1/auth/verify", json={"email": EMAIL, "code": f"{guess:06d}"})
            error = response.json().get("error", {})
            if error.get("code") == "CODE_INVALID":
                evaluated += 1
                continue
            requested = await _request(client)
            if requested.status_code == 429:
                rate_limited = True
                break

    assert evaluated <= 25
    assert rate_limited


async def test_rate_limit_says_when_to_retry(client: AsyncClient) -> None:
    """
    Condition:
    - A sixth code request for one email within an hour.

    Expected:
    - 429 ``RATE_LIMITED``, retryable, with ``retry_after_seconds`` and a ``Retry-After`` header for when the
      oldest request leaves the window.
    """
    with clock.frozen(START):
        for _ in range(5):
            await _request(client)
    with clock.frozen(START + timedelta(minutes=20)):
        response = await _request(client)

    assert response.status_code == 429
    error = response.json()["error"]
    assert error["code"] == "RATE_LIMITED"
    assert error["recovery"]["retryable"] is True
    assert error["recovery"]["retry_after_seconds"] == 40 * 60
    assert response.headers["Retry-After"] == str(40 * 60)


async def test_per_address_limit_covers_many_emails(client: AsyncClient) -> None:
    """
    Condition:
    - One client address asks for codes for 21 different emails within an hour.

    Expected:
    - The 21st is refused.
    """
    with clock.frozen(START):
        statuses = [(await _request(client, f"user{index}@example.com")).status_code for index in range(21)]

    assert statuses == [202] * 20 + [429]


async def test_me_needs_a_session(client: AsyncClient) -> None:
    """
    Condition:
    - No session cookie.

    Expected:
    - ``UNAUTHENTICATED`` 401.
    """
    response = await client.get("/api/v1/me")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"


async def test_sign_out_revokes_the_session_and_clears_the_cookie(client: AsyncClient, sign_up) -> None:
    """
    Condition:
    - A signed-in account signs out.

    Expected:
    - 204, the cookie is cleared, and the old token no longer works.
    """
    await sign_up(client, EMAIL)
    token = client.cookies["tr_session"]

    response = await client.post("/api/v1/auth/sign-out")
    client.cookies.set("tr_session", token)

    assert response.status_code == 204
    assert 'tr_session=""' in response.headers["set-cookie"]
    assert (await client.get("/api/v1/me")).status_code == 401


@pytest.mark.parametrize("origin", ["https://evil.example", None])
async def test_cookie_bearing_post_from_another_origin_is_refused(
    client: AsyncClient, sign_up, origin: str | None, caplog: pytest.LogCaptureFixture
) -> None:
    """
    Condition:
    - A POST carries the session cookie but comes from another origin, or none.

    Expected:
    - ``FORBIDDEN`` before any handler runs: the session stays valid.
    """
    await sign_up(client, EMAIL)
    headers = {"Origin": origin} if origin else {}
    del client.headers["Origin"]

    with caplog.at_level(logging.WARNING):
        response = await client.post("/api/v1/auth/sign-out", headers=headers)

    assert response.status_code == 403
    error = response.json()["error"]
    assert error["code"] == "FORBIDDEN"
    assert error["request_id"] in caplog.text
    assert (await client.get("/api/v1/me")).status_code == 200


async def test_preferences_change_against_the_version_read(client: AsyncClient, sign_up) -> None:
    """
    Condition:
    - ``PATCH /me`` with the current version, then again with the old one.

    Expected:
    - The first changes persona and time zone; the second is ``STALE_VERSION`` with the current version.
    """
    await sign_up(client, EMAIL)

    changed = await client.patch(
        "/api/v1/me", json={"persona": "mitra", "time_zone": "Asia/Makassar", "expected_version": 1}
    )
    stale = await client.patch("/api/v1/me", json={"display_name": "Rani S.", "expected_version": 1})

    account = changed.json()["account"]
    assert (account["persona"], account["time_zone"], account["version"]) == ("mitra", "Asia/Makassar", 2)
    assert stale.status_code == 409
    assert stale.json()["error"] | {"request_id": None, "message": None} == {
        "code": "STALE_VERSION",
        "message": None,
        "request_id": None,
        "recovery": {"retryable": False},
        "current_version": 2,
    }


@pytest.mark.parametrize(
    "body",
    [
        {"email": "not-an-email", "purpose": "sign_in"},
        {"email": EMAIL, "purpose": "sign_up", "display_name": "Rani", "time_zone": "Mars/Olympus"},
        {"email": EMAIL, "purpose": "sign_up", "display_name": "Rani", "persona": "operator"},
    ],
)
async def test_invalid_requests_are_field_errors(client: AsyncClient, body: dict) -> None:
    """
    Condition:
    - A malformed email, an unknown time zone or persona.

    Expected:
    - ``VALIDATION_FAILED`` with field details; no code is stored.
    """
    response = await client.post("/api/v1/auth/code", json=body)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_FAILED"
    assert await _code_rows() == []


async def test_disabled_mail_rejects_code_without_persisting_it(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from sqlalchemy import func, select

    from app.core.database import get_session_factory
    from app.core.settings import get_settings
    from app.identity.repository.sqlalchemy.models import EmailCodeRecord, MailboxMessageRecord

    monkeypatch.setattr(get_settings(), "mailbox_adapter", "disabled")
    response = await client.post(
        "/api/v1/auth/code",
        json={"email": "undelivered@example.com", "purpose": "sign_up", "display_name": "Fixture"},
    )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "MAIL_UNAVAILABLE"
    async with get_session_factory()() as session:
        assert await session.scalar(select(func.count()).select_from(EmailCodeRecord)) == 0
        assert await session.scalar(select(func.count()).select_from(MailboxMessageRecord)) == 0


async def test_loopback_delivers_a_real_code_only_after_commit(client: AsyncClient, local_relay: LocalRelay) -> None:
    """
    Condition:
    - A synthetic signup queues an encrypted message and one originating transaction rolls back.

    Expected:
    - An independent worker cannot deliver uncommitted work. A committed request sends once and its code verifies.
    """
    local_relay.enable()
    address = "loopback-signup@example.test"
    factory = get_session_factory()
    async with factory() as session:
        service = IdentityService(session, get_settings())
        await service.request_code(CodeRequest(email=address, purpose="sign_up", display_name="Rani"), "127.0.0.1")
        assert await run_jobs(factory, registry) == 0
        await session.rollback()

    assert await _code_rows() == []
    assert not local_relay.requests
    requested = await _request(client, address)
    assert (requested.status_code, requested.json()) == (202, {"sent": True})
    assert not local_relay.requests
    assert (await client.get("/api/v1/dev/mailbox", params={"email": address})).json() == []

    async with factory() as session:
        job = await session.scalar(select(JobRecord).where(JobRecord.kind == SECRET_DELIVERY))
        assert job is not None
        assert set(job.input) == {"key", "envelope"}
        assert address not in str(job.input)
        assert job.input_expires_at == (await _code_rows())[0].expires_at

    assert await run_jobs(factory, registry) == 1
    [message] = local_relay.accepted.values()
    assert message["to"] == address and message["from"] == "relay@example.test"
    assert message["subject"] == "Kode verifikasi TemuRiset"
    code = message["body"].splitlines()[0].rsplit(" ", 1)[1]
    async with factory() as session:
        job = await session.scalar(select(JobRecord).where(JobRecord.kind == SECRET_DELIVERY))
        assert job is not None and (job.status, job.input) == ("SUCCEEDED", {})
    assert (await client.post("/api/v1/auth/verify", json={"email": address, "code": code})).status_code == 200
    replay = await client.post("/api/v1/auth/verify", json={"email": address, "code": code})
    assert replay.json()["error"]["code"] == "CODE_EXPIRED"


async def test_loopback_terminal_failure_scrubs_its_message(
    client: AsyncClient, local_relay: LocalRelay, caplog: pytest.LogCaptureFixture
) -> None:
    """
    Condition:
    - The relay redirects a signup message and echoes the submission in its response.

    Expected:
    - The redirect stays terminal and private. The job input is scrubbed and the worker records one safe failure.
    """
    local_relay.enable()
    local_relay.outcomes.append(302)
    address = "terminal-recipient@example.test"
    assert (await _request(client, address)).status_code == 202
    assert await run_jobs(get_session_factory(), registry) == 1
    assert await run_jobs(get_session_factory(), registry) == 0
    [(_, attempted)] = local_relay.requests
    assert local_relay.accepted == {}
    async with get_session_factory()() as session:
        job = await session.scalar(select(JobRecord).where(JobRecord.kind == SECRET_DELIVERY))
        assert job is not None
        assert (job.status, job.attempts, job.input, job.last_error_code) == (
            "FAILED",
            1,
            {},
            "APP-MAIL-RELAY-REJECTED",
        )
    assert caplog.text.count("APP-MAIL-RELAY-REJECTED") == 2  # One record contains both code and original_code.
    assert "ref_" in caplog.text
    assert "fixture-private-relay-response" not in caplog.text
    assert attempted["body"] not in caplog.text
    assert address not in caplog.text


async def test_retry_discards_a_replaced_code(
    client: AsyncClient, local_relay: LocalRelay, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    Condition:
    - A code's delivery fails, then the same address requests a replacement before the retry.

    Expected:
    - Only the replacement arrives and verifies. The stale job is scrubbed without resending the first code.
    """
    local_relay.enable()
    local_relay.outcomes.append(503)
    codes = iter(["111111", "222222"])
    monkeypatch.setattr("app.identity.service.service.new_code", lambda: next(codes))
    email = "replace-code@example.test"
    factory = get_session_factory()

    with clock.frozen(START):
        assert (await _request(client, email)).status_code == 202
        assert await run_jobs(factory, registry) == 1
    with clock.frozen(START + timedelta(seconds=1)):
        assert (await _request(client, email)).status_code == 202
    with clock.frozen(START + timedelta(seconds=5)):
        assert await run_jobs(factory, registry) == 2
        assert (await client.post("/api/v1/auth/verify", json={"email": email, "code": "222222"})).status_code == 200

    assert len(local_relay.requests) == 2
    [message] = local_relay.accepted.values()
    assert "222222" in message["body"] and "111111" not in message["body"]
    async with factory() as session:
        jobs = list(await session.scalars(select(JobRecord).where(JobRecord.kind == SECRET_DELIVERY)))
        assert len(jobs) == 2 and all(job.status == "SUCCEEDED" and not job.input for job in jobs)


async def test_loopback_does_not_queue_mail_for_an_unknown_sign_in(
    client: AsyncClient, local_relay: LocalRelay
) -> None:
    """
    Condition:
    - An unknown address requests sign-in without creating a challenge.

    Expected:
    - The public response remains the same and no unthrottled notification can be sent to that address.
    """
    local_relay.enable()
    response = await _request(client, "unknown@example.test", purpose="sign_in")
    assert (response.status_code, response.json()) == (202, {"sent": True})
    assert await run_jobs(get_session_factory(), registry) == 0
    assert not local_relay.requests
