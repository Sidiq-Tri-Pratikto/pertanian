"""Reject malformed synthetic benchmark inputs and missing or miscounted measurements."""

import argparse
import sys
from pathlib import Path
from types import ModuleType
from typing import NoReturn
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import httpx
import pytest
from pydantic import SecretStr

from app.core.settings import Settings
from app.identity.service.codes import new_token
from app.matching.model.schema import MatchResultResponse, MatchRunResponse, MatchSource
from benchmarks import generate, run
from benchmarks.generate import Actor, BenchmarkError, Dataset, verify_dataset, write_handoff
from benchmarks.run import ME, Request, Samples, load_dataset, sample, verify_match

ORIGIN = "http://127.0.0.1:8040"
DATABASE = "temuriset_benchmark"


@pytest.fixture
def dataset() -> Dataset:
    """Use two separate synthetic actors and two opportunities owned by one partner."""
    actors = [
        Actor(
            token=SecretStr(new_token()),
            account_id=uuid4(),
            party_id=uuid4(),
            inventions=[uuid4()],
        )
        for _ in range(2)
    ]
    return Dataset(
        origin=ORIGIN,
        database=DATABASE,
        actors=actors,
        opportunity_ids={uuid4(), uuid4()},
        partner_ids={actors[1].party_id},
        source_id=uuid4(),
    )


def test_target_rejects_another_origin_or_database(monkeypatch):
    """The command cannot target a different origin or an ordinary database."""
    monkeypatch.setenv("BENCHMARK_ORIGIN", ORIGIN)
    settings = Settings(database_url=f"postgresql+asyncpg://postgres@127.0.0.1:55419/{DATABASE}", web_origin=ORIGIN)
    monkeypatch.setattr(generate, "get_settings", lambda: settings)
    assert generate.target(ORIGIN, staging=False) == DATABASE
    with pytest.raises(BenchmarkError, match="isolated benchmark origin"):
        generate.target("http://127.0.0.1:8041", staging=False)
    settings.database_url = SecretStr("postgresql+asyncpg://postgres@127.0.0.1:55419/temuriset")
    with pytest.raises(BenchmarkError, match="benchmark-only database"):
        generate.target(ORIGIN, staging=False)


@pytest.mark.parametrize("token", ["", "a" * 42 + ";", "a" * 42 + "é", "a" * 43 + "\r\nCookie: injected"])
def test_handoff_requires_safe_sessions(tmp_path: Path, dataset: Dataset, token: str) -> None:
    """
    Condition:
    - A private handoff has a missing or malformed session cookie.

    Expected:
    - The runner refuses it before building a request.
    """
    dataset.actors[0].token = SecretStr(token)
    tmp_path.chmod(0o700)
    path = tmp_path / "handoff.json"
    with path.open("w") as file:
        write_handoff(file, dataset)
    path.chmod(0o600)
    with pytest.raises(BenchmarkError, match="invalid synthetic session token"):
        load_dataset(path, ORIGIN, DATABASE)


@pytest.mark.parametrize(("command", "entrypoint"), [(generate, "generate"), (run, "run_with_cleanup")])
def test_cli_sanitizes_http_errors(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    command: ModuleType,
    entrypoint: str,
) -> None:
    """
    Condition:
    - The HTTP exception for a benchmark request includes a fake private cookie.

    Expected:
    - The command exits with a safe failure message and omits the cookie.
    """
    token = "benchmark-fake-private-cookie"
    request = httpx.Request("GET", ORIGIN, headers={"Cookie": f"tr_session={token}"})

    def request_failure(args: argparse.Namespace) -> NoReturn:
        raise httpx.ConnectError(f"request with {request.headers['Cookie']} failed", request=request)

    monkeypatch.setattr(sys, "argv", ["benchmark", "--origin", ORIGIN, "--handoff", "sessions.json"])
    monkeypatch.setattr(command, entrypoint, request_failure)
    with pytest.raises(SystemExit) as error:
        command.main()
    assert error.value.code == 1
    captured = capsys.readouterr()
    assert "selected API request failed" in captured.err
    assert token not in captured.out + captured.err


def test_generator_releases_failed_handoff_reservation(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """
    Condition:
    - API readiness or seeding fails after the generator reserves the handoff.

    Expected:
    - The original failure is raised and the reserved file is removed.
    """
    tmp_path.chmod(0o700)
    handoff = tmp_path / "handoff.json"
    args = argparse.Namespace(origin=ORIGIN, staging=False, handoff=handoff, users=4, inventions=12, opportunities=4)
    monkeypatch.setattr(generate, "target", lambda origin, *, staging: DATABASE)
    monkeypatch.setattr(generate, "seed_ready_target", AsyncMock(side_effect=BenchmarkError("not ready")))
    with pytest.raises(BenchmarkError, match="not ready"):
        generate.generate(args)
    assert not handoff.exists()


def test_warmup_reports_slow_requests_without_applying_the_latency_target() -> None:
    """
    Condition:
    - An endpoint exceeds its latency budget with no failed requests.

    Expected:
    - The measurement fails the target and the diagnostic warmup passes while still reporting latency.
    """
    samples = Samples(latency=[700])
    assert samples.report(ME)["passed"] is False
    outcome = samples.report(ME, enforce_target=False)
    assert (outcome["p95_ms"], outcome["target_ms"], outcome["passed"]) == (700, None, True)


def test_warmup_reports_request_failures_without_successful_samples() -> None:
    """
    Condition:
    - The diagnostic warmup times out before completing a successful request.

    Expected:
    - The warmup reports the timeout and fails without attempting to calculate p95.
    """
    outcome = Samples(timeouts=1).report(ME, enforce_target=False)
    assert (outcome["attempted"], outcome["timeouts"], outcome["p95_ms"], outcome["passed"]) == (1, 1, None, False)


async def test_readiness_rejects_incomplete_seed(dataset):
    """Live sessions and an active catalog cannot mask missing published inventions."""
    accounts = [actor.account_id for actor in dataset.actors]
    partner = next(iter(dataset.partner_ids))
    session = AsyncMock()
    session.scalar.return_value = DATABASE
    session.scalars.side_effect = [accounts, accounts, dataset.actors[0].inventions]
    session.execute.return_value = MagicMock()
    session.execute.return_value.all.return_value = [(opportunity, partner) for opportunity in dataset.opportunity_ids]
    with pytest.raises(BenchmarkError, match="counts differ"):
        await verify_dataset(session, dataset)


async def test_invalid_http_payload_is_excluded_and_empty_samples_fail():
    """Count failed responses but calculate p95 only from successful requests."""
    response = httpx.MockTransport(lambda _: httpx.Response(200, json={"unexpected": True}))
    samples = Samples()
    async with httpx.AsyncClient(base_url=ORIGIN, transport=response) as client:
        await sample(client, Request(ME, ME, lambda content: False), samples)
    assert samples.invalid_payloads == 1
    with pytest.raises(BenchmarkError, match="No successful samples"):
        samples.report(ME)
    samples.latency.extend(range(1, 21))
    outcome = samples.report(ME)
    assert (outcome["attempted"], outcome["successful"], outcome["p95_ms"], outcome["passed"]) == (21, 20, 19, False)


def test_match_requires_every_distinct_candidate(dataset):
    """The correct row count still fails if a candidate is duplicated across the two lists."""
    partner = next(iter(dataset.partner_ids))
    first, second = [
        MatchResultResponse.model_construct(opportunity_id=opportunity_id, partner_party_id=partner)
        for opportunity_id in dataset.opportunity_ids
    ]
    payload = MatchRunResponse.model_construct(
        source=MatchSource.model_construct(id=dataset.source_id, type="SUPPORT_REQUEST"),
        operation_id=uuid4(),
        results=[first],
        excluded=[second],
    )
    verify_match(payload, dataset)
    payload.excluded = [first]
    with pytest.raises(BenchmarkError, match="expected opportunities"):
        verify_match(payload, dataset)
