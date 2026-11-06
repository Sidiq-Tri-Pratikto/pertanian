"""Matching through HTTP against Postgres, with F01–F06 and Recipients A–E loaded through the API (spec 019)."""

import json
import os
import re
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

import pytest
from httpx import AsyncClient
from pydantic import SecretStr
from sqlalchemy import text

from app.core.database import get_session_factory
from app.core.settings import get_settings
from app.main import app
from app.matching.service import retrieval_adapter
from tests.factories.inventors import INVENTIONS, SUPPORT_REQUESTS
from tests.factories.recipients import OPPORTUNITIES, PROFILES
from tests.integration.matching.conftest import World, result_for, row

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("clean_tables")]

GOLDEN = Path(__file__).resolve().parents[5] / "contracts" / "golden"
_UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")


def _golden_text(result: dict[str, Any]) -> str:
    """A result with every generated id replaced, so the file holds only what the engine decided."""
    return _UUID.sub("<id>", json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True)) + "\n"


@pytest.mark.parametrize(
    ("name", "source", "target"),
    [
        ("match-f01-a1", "F01", "A1"),
        ("match-f02-a2", "F02", "A2"),
        ("match-f03-d1", "F03", "D1"),
        ("match-f06-a3", "F06", "A3"),
        ("match-fraise01-b1", "FRaise01", "B1"),
    ],
)
async def test_golden_results_hold_byte_for_byte(world: World, name: str, source: str, target: str) -> None:
    """
    Condition:
    - A fixture source matched against a fixture target over HTTP (FR-006).

    Expected:
    - The result equals ``contracts/golden/<name>.json`` byte for byte; ``UPDATE_GOLDEN=1`` rewrites it.
    """
    run = await (world.funding() if source == "FRaise01" else world.support(source))
    text = _golden_text(result_for(run, world.opportunity(target)))
    path = GOLDEN / f"{name}.json"
    if os.environ.get("UPDATE_GOLDEN") == "1":
        path.write_text(text)

    assert text == path.read_text()


async def test_f01_gap_golden_then_completing_restores_readiness(make_world: Callable[..., Awaitable[World]]) -> None:
    """
    Condition:
    - F01-GAP matched against A1, then the range filled in and matched again (J01).

    Expected:
    - First "Perlu konfirmasi" with the range gap (golden ``match-f01gap-a1``), then "Kecocokan kuat" and ready.
    """
    world = await make_world(gap=True)
    try:
        before = result_for(await world.support("F01", "before"), world.opportunity("A1"))
        path = GOLDEN / "match-f01gap-a1.json"
        if os.environ.get("UPDATE_GOLDEN") == "1":
            path.write_text(_golden_text(before))
        assert _golden_text(before) == path.read_text()
        assert before["gap"]["reason"] == "Kisaran biaya pilot untuk kebutuhan ini belum diisi."

        rani, request_id = world.inventors.clients["rani"], world.inventors.support_requests["F01"]
        current = (await rani.get(f"/api/v1/support-requests/{request_id}")).json()
        from tests.factories.inventors import F01_BUDGET  # noqa: PLC0415

        saved = await rani.put(
            f"/api/v1/support-requests/{request_id}",
            json={
                "acting_party_id": world.inventors.parties["rani"],
                "expected_version": current["version"],
                **SUPPORT_REQUESTS["F01"],
                "budget": F01_BUDGET,
            },
            headers={"Idempotency-Key": "fill-range"},
        )
        assert saved.status_code == 200, saved.text
        after = result_for(await world.support("F01", "after"), world.opportunity("A1"))
    finally:
        await world.recipients.close()
        await world.inventors.close()

    assert (after["label"], after["readiness"]) == ("Kecocokan kuat", "READY_TO_SUBMIT")


async def test_incompatible_and_abstaining_targets_are_excluded(world: World) -> None:
    """
    Condition:
    - F01 and F03 matched against every active target.

    Expected:
    - F01's only recommendation is A1, with A3 excluded for no relevance; F03's D1 is excluded with the SSO reason.
    """
    f01 = await world.support("F01")
    f03 = await world.support("F03")

    assert [item["opportunity_id"] for item in f01["results"]] == [world.opportunity("A1")]
    assert result_for(f01, world.opportunity("A3")) in f01["excluded"]
    d1 = result_for(f03, world.opportunity("D1"))
    assert d1 in f03["excluded"]
    assert row(d1, "SSO yang sudah berjalan")["reason"].startswith("Fitur baru direncanakan")


async def test_proposed_entity_fails_b1_and_b2_stays_open(make_world: Callable[..., Awaitable[World]]) -> None:
    """
    Condition:
    - FRaise01 for a company not founded yet (AC21).

    Expected:
    - B1's entity requirement fails; B2 is ready.
    """
    world = await make_world(proposed_entity=True)
    try:
        run = await world.funding()
    finally:
        await world.recipients.close()
        await world.inventors.close()

    assert row(result_for(run, world.opportunity("B1")), "Badan usaha yang sudah berdiri")["result"] == "FAIL"
    assert result_for(run, world.opportunity("B2"))["readiness"] == "READY_TO_SUBMIT"


async def test_a_run_is_stored_and_reproducible(world: World) -> None:
    """
    Condition:
    - F01 matched, then the run read back by its owner and by another party (FR-005).

    Expected:
    - The owner reads the same results with engine and policy versions; another party gets NOT_FOUND.
    """
    run = await world.support("F01")
    rani, galih = world.inventors.clients["rani"], world.inventors.clients["galih"]
    read = await rani.get(f"/api/v1/match-runs/{run['run_id']}")
    stranger = await galih.get(f"/api/v1/match-runs/{run['run_id']}")

    assert read.status_code == 200
    stored = read.json()
    assert (stored["results"], stored["excluded"]) == (run["results"], run["excluded"])
    assert (stored["engine"], stored["policy_versions"]) == (
        "lexical-rules@1",
        {"matching-weights": 1, "fit-thresholds": 1},
    )
    assert stored["source"] == {**run["source"]}
    assert stranger.status_code == 404


async def test_only_the_owner_may_match_a_source(world: World) -> None:
    """
    Condition:
    - Galih asks to match Rani's support request, and Rani matches with a stale acting party.

    Expected:
    - NOT_FOUND for Galih, with nothing about F01 in the answer; STALE_CONTEXT for the stale party.
    """
    request_id = world.inventors.support_requests["F01"]
    response = await world.inventors.clients["galih"].post(
        "/api/v1/matches",
        json={
            "acting_party_id": world.inventors.parties["galih"],
            "source_type": "SUPPORT_REQUEST",
            "source_id": request_id,
        },
        headers={"Idempotency-Key": "steal"},
    )
    stale = await world.inventors.clients["rani"].post(
        "/api/v1/matches",
        json={
            "acting_party_id": world.inventors.parties["galih"],
            "source_type": "SUPPORT_REQUEST",
            "source_id": request_id,
        },
        headers={"Idempotency-Key": "stale"},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"
    assert "ClearSpring" not in response.text
    assert stale.json()["error"]["code"] == "STALE_CONTEXT"


async def test_another_partys_file_proves_nothing(world: World, client: AsyncClient) -> None:
    """
    Condition:
    - Galih publishes an invention whose function fact links Rani's uploaded test report, then needs support.

    Expected:
    - A1's file requirement is UNKNOWN for Galih: a file the party does not own counts as absent.
    """
    from tests.factories.inventors import INVENTIONS  # noqa: PLC0415

    galih, party = world.inventors.clients["galih"], world.inventors.parties["galih"]
    rani_view = (
        await world.inventors.clients["rani"].get(f"/api/v1/inventions/{world.inventors.inventions['F01']}")
    ).json()
    borrowed = next(fact for fact in rani_view["published"]["facts"] if fact["key"] == "function")
    content = {**INVENTIONS["F01"]["content"], "title": "Saringan pinjaman", "facts": [borrowed]}
    created = (
        await galih.post("/api/v1/inventions", json={"acting_party_id": party}, headers={"Idempotency-Key": "b"})
    ).json()
    saved = (
        await galih.put(
            f"/api/v1/inventions/{created['id']}/draft",
            json={"acting_party_id": party, "expected_version": created["version"], **content},
            headers={"Idempotency-Key": "b-draft"},
        )
    ).json()
    await galih.post(
        f"/api/v1/inventions/{created['id']}/publish",
        json={"acting_party_id": party, "expected_version": saved["version"]},
        headers={"Idempotency-Key": "b-publish"},
    )
    need = (
        await galih.post(
            "/api/v1/support-requests",
            json={"acting_party_id": party, "invention_id": created["id"], "outcome": "Uji"},
            headers={"Idempotency-Key": "b-need"},
        )
    ).json()
    run = (await world.match("galih", "SUPPORT_REQUEST", need["id"])).json()

    assert row(result_for(run, world.opportunity("A1")), "Berkas uji fungsi")["result"] == "UNKNOWN"


async def test_funding_matching_needs_company_funding(world: World, monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Condition:
    - The ``project-support-only`` composition, and Bima matches FRaise01, then F01 is matched by Rani.

    Expected:
    - ``CAPABILITY_UNAVAILABLE`` for the raise, not retryable; project support still matches.
    """
    settings = get_settings()
    monkeypatch.setattr(settings, "composition", "project-support-only")
    refused = await world.match("bima", "FUNDING_REQUEST", world.inventors.funding)
    allowed = await world.support("F01")

    assert refused.status_code == 403
    body = refused.json()["error"]
    assert body["code"] == "CAPABILITY_UNAVAILABLE"
    assert body["recovery"]["retryable"] is False
    assert body["request_id"]
    assert body["message"].startswith("Fitur ini tidak tersedia")
    assert allowed["results"]


def _synthetic_snapshot(tmp_path: Path, case: str) -> retrieval_adapter.RetrievalExperiment:
    queries = {}
    targets = {
        key: {
            "text": f"kandidat {key}",
            "selector": {
                "version": 1,
                "title": opportunity["content"]["title"],
                "partner": PROFILES[opportunity["partner"]]["party"]["name"],
                "keywords": opportunity["content"]["keywords"],
            },
        }
        for key, opportunity in OPPORTUNITIES.items()
    }
    for key in ("F01", "F02", "F03"):
        invention = INVENTIONS[key]["content"]
        queries[key] = {
            "text": "pompa tiruan",
            "targets": list(targets),
            "selector": {
                "type": "SUPPORT_REQUEST",
                "version": 2,
                "title": invention["title"],
                "sector": invention["sector"],
                "stage": invention["stage"],
                "keywords": invention["keywords"],
                "relationship": SUPPORT_REQUESTS[key]["relationship_form"],
            },
        }
    if case == "stale":
        targets["A1"]["selector"]["version"] = 2
    fixture = tmp_path / "fixture.json"
    fixture.write_text(json.dumps({"version": "test-v1", "sources": queries, "targets": targets}))
    corpus = retrieval_adapter.load_corpus(fixture)
    artifact = tmp_path / "artifact.json"
    axis = [1] + [0] * 7
    if case != "missing":
        artifact.write_text(
            json.dumps(
                {
                    "format": 1,
                    "fixture_version": corpus.version,
                    "fixture_sha256": "mismatch" if case == "invalid" else corpus.digest,
                    "output": {
                        "pins": retrieval_adapter.PINS,
                        "source_vectors": [axis] * len(queries),
                        "target_vectors": ([[0, 1] + [0] * 6] if case == "abstain" else [axis]) * len(targets),
                        "rerank_scores": [([] if case == "abstain" else [0.9] * len(targets)) for _ in queries],
                    },
                }
            )
        )
    settings = get_settings().model_copy(
        update={
            "match_retrieval_mode": "dense",
            "match_retrieval_artifact": SecretStr(str(artifact)),
        }
    )
    experiment = retrieval_adapter.load_experiment(settings, fixture)
    assert experiment is not None
    fixture.unlink()
    artifact.unlink(missing_ok=True)
    return experiment


async def _label_demo(*party_ids: str) -> None:
    async with get_session_factory()() as session, session.begin():
        for party_id in party_ids:
            await session.execute(
                text("UPDATE accounts SET kind = 'demo' WHERE id = (SELECT account_id FROM parties WHERE id = :party)"),
                {"party": party_id},
            )


async def test_synthetic_matching_pins_an_owned_replay_and_preserves_fail_and_unknown(
    world: World, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    Condition:
    - Seeded authorized demo projections match the exact fixture and the validated startup files are then removed.

    Expected:
    - The normal route uses only the snapshot, protects owned reads/replays and preserves all rule outcomes.
    """
    baseline = await world.support("F01", "legacy")
    assert "retrieval" not in baseline and baseline["engine"] == "lexical-rules@1"
    monkeypatch.setattr(app.state, "match_retrieval", _synthetic_snapshot(tmp_path, "valid"), raising=False)

    def no_relay(**_kwargs: object) -> None:
        pytest.fail("The request path must never call a relay.")

    monkeypatch.setattr(retrieval_adapter, "AsyncClient", no_relay)
    real_lookalike = await world.support("F01", "real")
    assert real_lookalike["retrieval"]["fallback_reason"] == "unsupported_input"
    assert real_lookalike["results"] == baseline["results"]

    await _label_demo(*(world.inventors.parties[key] for key in ("rani", "dewi", "galih")))
    experimental = await world.support("F01", "synthetic")
    assert experimental["engine"] == "dense-rules@1"
    provenance = experimental["retrieval"]
    assert provenance["effective_mode"] == provenance["requested_mode"] == "dense"
    assert provenance["fallback_reason"] is None
    assert provenance["model"] == retrieval_adapter.PINS
    assert len(provenance["fixture_sha256"]) == len(provenance["artifact_sha256"]) == 64
    assert len(experimental["results"]) <= 5
    assert (
        result_for(experimental, world.opportunity("A1"))["fit"] == result_for(baseline, world.opportunity("A1"))["fit"]
    )

    fail = await world.support("F03", "fail")
    excluded = result_for(fail, world.opportunity("D1"))
    assert excluded in fail["excluded"] and excluded["eligibility"] == "INCOMPATIBLE"
    unknown = await world.support("F02", "unknown")
    provisional = result_for(unknown, world.opportunity("A2"))
    assert provisional["eligibility"] == "NEEDS_VERIFICATION"
    assert provisional["gap"]["result"] == "UNKNOWN"
    assert provisional["gap"]["reason"] and provisional["gap"]["action"]

    run_path = f"/api/v1/match-runs/{experimental['run_id']}"
    rani, galih = (world.inventors.clients[key] for key in ("rani", "galih"))
    assert (await rani.get(run_path)).json()["retrieval"] == provenance
    assert (await galih.get(run_path)).status_code == 404
    assert (await world.support("F01", "synthetic")) == experimental
    assert (await world.support("F01", "legacy")) == baseline


@pytest.mark.parametrize(
    ("case", "reason"),
    [
        ("missing", "artifact_missing"),
        ("invalid", "artifact_invalid"),
        ("stale", "unsupported_input"),
        ("abstain", None),
    ],
)
async def test_synthetic_artifact_fallback_is_exact_and_valid_empty_output_abstains(
    world: World, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, case: str, reason: str | None
) -> None:
    """
    Condition:
    - The profile has missing, rejected or stale input, or a valid model artifact with no admitted evidence.

    Expected:
    - Failed experiments preserve the original lexical results; a valid empty result stays experimental.
    """
    baseline = await world.support("F01", "baseline")
    await _label_demo(world.inventors.parties["rani"])
    monkeypatch.setattr(app.state, "match_retrieval", _synthetic_snapshot(tmp_path, case), raising=False)
    tested = await world.support("F01", "synthetic")
    assert tested["retrieval"]["fallback_reason"] == reason
    if reason:
        assert tested["retrieval"]["effective_mode"] == "lexical"
        assert "artifact_sha256" not in tested["retrieval"]
        assert tested["engine"] == baseline["engine"]
        assert tested["results"] == baseline["results"]
        assert tested["excluded"] == baseline["excluded"]
    else:
        assert tested["retrieval"]["effective_mode"] == "dense"
        assert tested["results"] == []
