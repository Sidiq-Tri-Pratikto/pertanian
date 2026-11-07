"""Demo sessions over real Postgres: seeding, isolation, replay, reset, capacity and expiry."""

import asyncio
import logging
import time
from unittest.mock import patch

import pytest
from httpx import AsyncClient

from app.core.settings import get_settings
from tests.integration.conftest import demo_headers, execute, start_demo

pytestmark = pytest.mark.integration


async def _rows(site_id: str) -> int:
    query = "SELECT count(*) FROM measurements m JOIN sources s ON s.id = m.source_id WHERE s.site_id = :site"
    return (await execute(query, site=site_id))[0][0]


async def _sessions_for_site(site_id: str) -> int:
    return (await execute("SELECT count(*) FROM demo_sessions WHERE site_id = :site", site=site_id))[0][0]


async def test_scenarios_are_public(client: AsyncClient) -> None:
    """
    Condition:
    - A client without credentials lists scenarios.

    Expected:
    - Every scenario with its Indonesian name, description and segment.
    """
    response = await client.get("/api/v1/demo/scenarios")

    assert response.status_code == 200
    assert {"id": "h-base", "segment": "household", "name": "Rumah tangga · dasar"}.items() <= response.json()[
        0
    ].items()
    assert len(response.json()) == 14


async def test_create_seeds_an_isolated_workspace(client: AsyncClient) -> None:
    """
    Condition:
    - Two clients create h-base sessions without credentials.

    Expected:
    - Each gets a token and a demo site with 2,688 seeded rows, quickly; neither reads the other's site.
    """
    started = time.perf_counter()
    first = await start_demo(client)
    took = time.perf_counter() - started
    second = await start_demo(client)

    own = await client.get(f"/api/v1/sites/{first['site_id']}", headers=first["auth"])
    foreign = await client.get(f"/api/v1/sites/{second['site_id']}", headers=first["auth"])

    print(f"h-base session created in {took:.2f}s")
    assert took < 2
    assert first["token"].startswith("hdd_v1_")
    assert first["initial_period"] == {"preset": "last_7_days", "start_date": "2026-10-19", "end_date": "2026-10-25"}
    assert await _rows(first["site_id"]) == 2688
    assert own.status_code == 200
    assert (own.json()["kind"], own.json()["now"]) == ("demo", "2026-10-25T17:00:00Z")
    assert foreign.status_code == 404


async def test_empty_scenario_has_no_readings(client: AsyncClient) -> None:
    """
    Condition:
    - A session for the empty scenario, the Mulai path before accounts.

    Expected:
    - A labelled demo site with no assets and no readings.
    """
    session = await start_demo(client, "empty")

    assets = await client.get(f"/api/v1/sites/{session['site_id']}/assets", headers=session["auth"])

    assert assets.json()["items"] == []
    assert await _rows(session["site_id"]) == 0


async def test_lost_response_is_recovered_without_reseeding(client: AsyncClient) -> None:
    """
    Condition:
    - A create committed but its response was lost; the client repeats the same key, proof and payload,
      twice at once.

    Expected:
    - Both receive the original token and site, and nothing is seeded again.
    """
    headers = demo_headers()
    first = await client.post("/api/v1/demo/sessions", json={"scenario_id": "h-base"}, headers=headers)

    replays = await asyncio.gather(
        *(client.post("/api/v1/demo/sessions", json={"scenario_id": "h-base"}, headers=headers) for _ in range(2))
    )

    assert first.status_code == 201
    assert {replay.status_code for replay in replays} == {200}
    assert {replay.json()["token"] for replay in replays} == {first.json()["token"]}
    assert await _sessions_for_site(first.json()["site_id"]) == 1
    assert await _rows(first.json()["site_id"]) == 2688


async def test_same_operation_twice_at_once_seeds_once(client: AsyncClient) -> None:
    """
    Condition:
    - Two copies of one new operation arrive together.

    Expected:
    - One seeds and one replays the same credential.
    """
    headers = demo_headers()

    responses = await asyncio.gather(
        *(client.post("/api/v1/demo/sessions", json={"scenario_id": "i-base"}, headers=headers) for _ in range(2))
    )

    assert sorted(response.status_code for response in responses) == [200, 201]
    assert len({response.json()["token"] for response in responses}) == 1


async def test_replay_needs_its_proof_payload_window_and_session(client: AsyncClient) -> None:
    """
    Condition:
    - A known operation is repeated with a wrong proof, a changed scenario, after its window, and after the
      session ended.

    Expected:
    - Wrong proof is NOT_FOUND; the others are CONFLICT; none returns the credential or a new session.
    """
    headers = demo_headers()
    created = (await client.post("/api/v1/demo/sessions", json={"scenario_id": "h-base"}, headers=headers)).json()

    wrong_proof = await client.post(
        "/api/v1/demo/sessions", json={"scenario_id": "h-base"}, headers=demo_headers(key=headers["Idempotency-Key"])
    )
    changed = await client.post("/api/v1/demo/sessions", json={"scenario_id": "i-base"}, headers=headers)
    await execute(
        "UPDATE demo_create_operations SET replay_expires_at = now() - interval '1 second' WHERE operation_id = :id",
        id=headers["Idempotency-Key"],
    )
    elapsed = await client.post("/api/v1/demo/sessions", json={"scenario_id": "h-base"}, headers=headers)

    other_headers = demo_headers()
    other = (await client.post("/api/v1/demo/sessions", json={"scenario_id": "h-base"}, headers=other_headers)).json()
    ended = await client.delete("/api/v1/demo/sessions/current", headers={"Authorization": f"Bearer {other['token']}"})
    after_end = await client.post("/api/v1/demo/sessions", json={"scenario_id": "h-base"}, headers=other_headers)

    assert wrong_proof.status_code == 404
    assert (changed.status_code, elapsed.status_code) == (409, 409)
    assert ended.status_code == 204
    assert after_end.status_code == 409
    for response in (wrong_proof, changed, elapsed, after_end):
        assert created["token"] not in response.text and "token" not in response.json()
    assert await _sessions_for_site(other["site_id"]) == 0


async def test_short_keys_are_refused(client: AsyncClient) -> None:
    """
    Condition:
    - A key and proof too short to carry the required randomness.

    Expected:
    - BAD_REQUEST before anything is admitted.
    """
    response = await client.post(
        "/api/v1/demo/sessions", json={"scenario_id": "h-base"}, headers=demo_headers(key="abc", proof="def")
    )

    assert response.status_code == 400


async def test_unknown_scenario_is_not_found(client: AsyncClient) -> None:
    """
    Condition:
    - A scenario outside the catalog.

    Expected:
    - NOT_FOUND with the scenario message.
    """
    response = await client.post("/api/v1/demo/sessions", json={"scenario_id": "h-ac"}, headers=demo_headers())

    assert response.status_code == 404
    assert "Skenario" in response.json()["error"]["message"]


async def test_reset_returns_only_this_workspace_to_its_start(client: AsyncClient) -> None:
    """
    Condition:
    - Two sessions; the first renames an asset and its site, then resets.

    Expected:
    - The first is back at the scenario start with the same token, site and 2,688 rows; the second is unchanged.
    """
    first, second = await start_demo(client), await start_demo(client)
    asset = (await client.get(f"/api/v1/sites/{first['site_id']}/assets", headers=first["auth"])).json()["items"][0]
    await client.patch(f"/api/v1/assets/{asset['id']}", json={"name": "Diubah"}, headers=first["auth"])
    await client.patch(f"/api/v1/sites/{first['site_id']}", json={"name": "Diubah"}, headers=first["auth"])
    second_assets = (await client.get(f"/api/v1/sites/{second['site_id']}/assets", headers=second["auth"])).json()

    reset = await client.post("/api/v1/demo/sessions/current/reset", headers=first["auth"])
    names = [
        item["name"]
        for item in (await client.get(f"/api/v1/sites/{first['site_id']}/assets", headers=first["auth"])).json()[
            "items"
        ]
    ]
    site = (await client.get(f"/api/v1/sites/{first['site_id']}", headers=first["auth"])).json()

    assert reset.status_code == 200
    assert reset.json()["site_id"] == first["site_id"]
    assert reset.json()["expires_at"] == first["expires_at"]
    assert "token" not in reset.json()
    assert site["kind"] == "demo"
    assert names == ["Kulkas", "Pompa Air", "Router", "TV"]
    assert site["name"] == "Rumah Bandung (demo)"
    assert await _rows(first["site_id"]) == 2688
    assert (
        await client.get(f"/api/v1/sites/{second['site_id']}/assets", headers=second["auth"])
    ).json() == second_assets


async def test_failed_reset_keeps_the_prior_workspace(client: AsyncClient) -> None:
    """
    Condition:
    - Reset fails while seeding.

    Expected:
    - The transaction rolls back: assets, readings and the token all still work.
    """
    session = await start_demo(client)

    with patch("app.demo.service.service.seed", side_effect=RuntimeError("seed failed")):
        failed = await client.post("/api/v1/demo/sessions/current/reset", headers=session["auth"])
    assets = await client.get(f"/api/v1/sites/{session['site_id']}/assets", headers=session["auth"])

    assert failed.status_code == 500
    assert len(assets.json()["items"]) == 4
    assert await _rows(session["site_id"]) == 2688


async def test_capacity_and_budget_are_shared_and_atomic(client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Condition:
    - One active slot remains and two distinct operations arrive together; then the minute budget is spent.

    Expected:
    - At most one seeds; the others get RATE_LIMITED with retry guidance and a matching Retry-After.
    """
    active = (await execute("SELECT count(*) FROM demo_sessions WHERE expires_at > now()"))[0][0]
    monkeypatch.setattr(get_settings(), "demo_max_active_sessions", active + 1)

    raced = await asyncio.gather(
        *(client.post("/api/v1/demo/sessions", json={"scenario_id": "empty"}, headers=demo_headers()) for _ in range(2))
    )
    monkeypatch.setattr(get_settings(), "demo_max_active_sessions", 10**9)
    recent = (
        await execute("SELECT count(*) FROM demo_create_operations WHERE created_at > now() - interval '1 minute'")
    )[0][0]
    monkeypatch.setattr(get_settings(), "demo_create_max_per_minute", recent)
    budget = await client.post("/api/v1/demo/sessions", json={"scenario_id": "empty"}, headers=demo_headers())

    assert sorted(response.status_code for response in raced) == [201, 429]
    limited = next(response for response in raced if response.status_code == 429)
    assert limited.json()["error"]["recovery"] == {"retryable": True, "retry_after_seconds": 60, "max_attempts": 3}
    assert limited.headers["retry-after"] == "60"
    assert budget.status_code == 429


async def test_expiry_then_purge(client: AsyncClient) -> None:
    """
    Condition:
    - A session expires, then a new creation purges it.

    Expected:
    - Before purge the token gets SESSION_EXPIRED; after it, generic UNAUTHORIZED, and the site and principal are gone.
    """
    session = await start_demo(client, "empty")
    principal = (await execute("SELECT principal_id FROM demo_sessions WHERE site_id = :s", s=session["site_id"]))[0][0]
    await execute(
        "UPDATE demo_sessions SET expires_at = now() - interval '1 second' WHERE site_id = :s", s=session["site_id"]
    )

    expired = await client.get(f"/api/v1/sites/{session['site_id']}", headers=session["auth"])
    await start_demo(client, "empty")
    purged = await client.get(f"/api/v1/sites/{session['site_id']}", headers=session["auth"])

    assert (expired.status_code, expired.json()["error"]["code"]) == (401, "SESSION_EXPIRED")
    assert (purged.status_code, purged.json()["error"]["code"]) == (401, "UNAUTHORIZED")
    assert (await execute("SELECT count(*) FROM sites WHERE id = :s", s=session["site_id"]))[0][0] == 0
    assert (await execute("SELECT count(*) FROM principals WHERE id = :p", p=principal))[0][0] == 0


async def test_malformed_and_unknown_tokens_are_unauthorized(client: AsyncClient) -> None:
    """
    Condition:
    - A malformed bearer value, and a well-formed demo token nobody issued.

    Expected:
    - Both are UNAUTHORIZED with no reason.
    """
    for header in ("Bearer", "Bearer hdd_v1_" + "0" * 64, "Token abc"):
        response = await client.get(
            "/api/v1/sites/00000000-0000-0000-0000-000000000000", headers={"Authorization": header}
        )
        assert (response.status_code, response.json()["error"]["code"]) == (401, "UNAUTHORIZED")


async def test_credentials_never_reach_logs_or_errors(client: AsyncClient, caplog: pytest.LogCaptureFixture) -> None:
    """
    Condition:
    - Failing requests carry a real token, a key and a proof.

    Expected:
    - Neither the token nor the proof appears in any log record or error body.
    """
    session = await start_demo(client)
    headers = demo_headers()
    caplog.set_level(logging.DEBUG)

    bodies = [
        (await client.post("/api/v1/demo/sessions", json={"scenario_id": "h-ac"}, headers=headers)).text,
        (await client.get("/api/v1/sites/not-a-uuid", headers=session["auth"])).text,
        (await client.post("/api/v1/demo/sessions", json={"scenario_id": 5}, headers=headers)).text,
    ]

    for secret in (session["token"], headers["X-Demo-Replay-Proof"]):
        assert all(secret not in body for body in bodies)
        assert secret not in caplog.text
