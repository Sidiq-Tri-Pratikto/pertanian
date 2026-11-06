"""Freeze the synthetic retrieval judgments and audit the comparison denominators."""

import json
from copy import deepcopy
from dataclasses import replace
from math import log2
from pathlib import Path

import httpx
import pytest

from app.matching.engine.evaluate import evaluate
from benchmarks.retrieval import (
    FIXTURE,
    Fixture,
    FixtureError,
    Observation,
    _double_response,
    evaluate_modes,
    load_fixture,
    summarize,
    validate_fixture,
)


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ("linked", "Related records"),
        ("group", "group or duplicate text"),
        ("duplicate", "group or duplicate text"),
        ("manager", "manager crosses"),
        ("pool", "target in another split"),
        ("missing_label", "one judgment"),
        ("ungrounded", "explicit source grounding"),
        ("stale_selector", "source selector differs"),
    ],
)
def test_frozen_fixture_rejects_leakage_and_incomplete_judgments(change: str, message: str) -> None:
    """
    Condition:
    - A split, pool, grounding or live projection contract is changed in one otherwise valid fixture.

    Expected:
    - Validation refuses the fixture before evaluating any mode.
    """
    data = json.loads(FIXTURE.read_bytes())
    development = data["sources"]["d-main"]
    held = data["sources"]["h-main"]
    if change == "linked":
        development["links"].append("h-main")
    elif change == "group":
        held["group"] = development["group"]
    elif change == "duplicate":
        held["text"] = development["text"].upper()
    elif change == "manager":
        data["targets"]["h-new"]["projection"]["partner_party_id"] = data["targets"]["d-new"]["projection"][
            "partner_party_id"
        ]
    elif change == "pool":
        held["targets"].append("d-noise")
        held["judgments"]["d-noise"] = development["judgments"]["d-noise"]
    elif change == "missing_label":
        del held["judgments"]["h-new"]
    elif change == "ungrounded":
        del held["judgments"]["h-exact"]["requirements"]["h-exact-r1"]["source_fact"]
    else:
        held["selector"]["version"] += 1
    with pytest.raises(FixtureError, match=message):
        validate_fixture(Fixture.model_validate(data))


@pytest.mark.parametrize("invalid", [True, 1.5, -1, 4, "2"])
def test_fixture_refuses_noninteger_or_out_of_range_grades(invalid: object, tmp_path: Path) -> None:
    """
    Condition:
    - One graded judgment is coerced, fractional or outside the frozen relevance scale.

    Expected:
    - The comparison refuses the fixture with a safe diagnostic.
    """
    data = json.loads(FIXTURE.read_bytes())
    data["sources"]["h-main"]["judgments"]["h-new"]["grade"] = invalid
    candidate = tmp_path / "malformed.json"
    candidate.write_text(json.dumps(data))
    with pytest.raises(FixtureError, match="unreadable or malformed"):
        load_fixture(candidate)


def _observations(fixture: Fixture) -> list[Observation]:
    observations = []
    for key, query in sorted(fixture.sources.items()):
        if query.split != "held_out":
            continue
        candidates = ("h-exact", "h-verify", "h-conflict") if key == "h-main" else ()
        returned = candidates[:2]
        observations.append(
            Observation(
                key,
                candidates,
                returned,
                tuple(target for target in query.targets if target not in returned),
                {target: evaluate(query.projection, fixture.targets[target].projection) for target in query.targets},
                float(len(observations) + 1),
            )
        )
    return observations


def test_synthetic_metrics_publish_denominators_and_full_ideal() -> None:
    """
    Condition:
    - Four held-out observations include an abstention with no relevant ideal, incomplete candidate recall and two
      shown matches from different manager cohorts.

    Expected:
    - Candidate and display metrics have separate auditable denominators. nDCG uses all judged targets, and safety,
      timing, count and exposure diagnostics report their own units.
    """
    fixture = load_fixture()
    report = summarize(fixture, "held_out", _observations(fixture))
    metrics = report["metrics"]
    assert metrics["candidate_recall"] == {
        "value": 0.3,
        "numerator": 3,
        "denominator": 10,
        "undefined_queries": 1,
    }
    assert metrics["returned_precision"] == {
        "value": 1.0,
        "numerator": 2,
        "denominator": 2,
        "undefined_queries": 3,
    }
    assert metrics["precision_at_5"]["denominator"] == 20
    assert metrics["precision_at_5"]["value"] == 0.1
    ideal = sum(gain / log2(index + 2) for index, gain in enumerate((7, 7, 3, 3, 3)))
    assert metrics["ndcg_at_5"]["numerator"] == pytest.approx((7 + 3 / log2(3)) / ideal)
    assert metrics["ndcg_at_5"]["denominator"] == 3
    assert metrics["ndcg_at_5"]["undefined_queries"] == 1
    assert metrics["unknown_correctness"]["denominator"] == metrics["unknown_correctness"]["numerator"] == 4
    assert metrics["factual_source_support"]["denominator"] == metrics["factual_source_support"]["numerator"] == 1
    assert metrics["hard_rule_violations"]["numerator"] == 0
    assert metrics["coverage"]["value"] == 0.25 and metrics["abstention"]["value"] == 0.75
    assert report["result_counts"] == {
        "judged_targets": 24,
        "candidates": 3,
        "returned": 2,
        "excluded": 22,
        "undisplayed": 0,
        "known_hard_fail_pairs": 4,
    }
    assert report["manager_exposure"]["new"] == {
        "positions": 1,
        "total_positions": 2,
        "share": 0.5,
        "distinct_managers_exposed": 1,
        "distinct_managers_available": 2,
    }
    assert report["manager_exposure"]["established"]["distinct_managers_available"] == 4
    assert report["latency_ms"]["samples"] == 4 and report["latency_ms"]["p95_nearest_rank"] == 4.0
    assert report["cost"]["real_provider"] == "unmeasured"
    assert report["safety_passed"]


def test_synthetic_safety_fails_for_hard_rule_unknown_and_unsupported_reason() -> None:
    """
    Condition:
    - A simulated mode returns a known hard fail, changes a provisional explanation and invents a factual reason.

    Expected:
    - All three issues register independently, and the report emits counts without the untrusted reason.
    """
    fixture = load_fixture()
    observations = _observations(fixture)
    index = next(index for index, item in enumerate(observations) if item.query == "h-main")
    original = observations[index]
    evaluated = deepcopy(original.evaluated)
    evaluated["h-exact"]["reasons"].append("synthetic injected ungrounded value")
    evaluated["h-verify"]["rows"][0]["reason"] = "changed provisional reason"
    observations[index] = replace(
        original,
        returned=original.returned + ("h-conflict",),
        excluded=tuple(key for key in original.excluded if key != "h-conflict"),
        evaluated=evaluated,
    )
    report = summarize(fixture, "held_out", observations)
    assert not report["safety_passed"]
    assert report["metrics"]["hard_rule_violations"]["numerator"] == 1
    assert report["metrics"]["unknown_correctness"]["numerator"] == 3
    assert report["metrics"]["factual_source_support"]["value"] == 0.5
    assert "synthetic injected ungrounded value" not in json.dumps(report)


def test_report_rejects_a_mode_that_changes_its_allowed_pool() -> None:
    """
    Condition:
    - One mode silently removes an authorized judged target or admits one outside its pool.

    Expected:
    - The report rejects the comparison instead of shrinking the denominator.
    """
    fixture = load_fixture()
    observations = _observations(fixture)
    observation = observations[0]
    observations[0] = replace(observation, candidates=observation.candidates + ("d-new",))
    with pytest.raises(FixtureError, match="changed the judged pool"):
        summarize(fixture, "held_out", observations)


async def test_four_modes_return_expected_no_overlap_candidate_with_the_shared_artifact(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """
    Condition:
    - The same exact model artifact and frozen per-query catalogs are passed to all four modes.

    Expected:
    - The original lexical path misses a useful no-overlap target. All three experimental modes surface it with
      clean safety diagnostics. The relay only reranks a bounded slice of each query's own catalog.
    """
    from app.matching.service import retrieval_adapter

    fixture = load_fixture()
    pins = dict(retrieval_adapter.PINS)
    rerank_sizes: list[int] = []
    requests = 0

    def relay(request: httpx.Request) -> httpx.Response:
        nonlocal requests
        requests += 1
        body = json.loads(request.content)
        if "rerank" in body:
            rerank_sizes.extend(len(case["targets"]) for case in body["rerank"])
        response = _double_response(body, fixture, pins)
        assert response is not None
        return httpx.Response(200, json=response)

    def client(**options: object) -> httpx.AsyncClient:
        return httpx.AsyncClient(transport=httpx.MockTransport(relay), **options)

    monkeypatch.setattr(retrieval_adapter, "AsyncClient", client)
    corpus = retrieval_adapter.load_corpus(FIXTURE)
    artifact = tmp_path / "retrieval.json"
    artifact.write_bytes(await retrieval_adapter.produce_artifact("http://127.0.0.1:58045/retrieval", corpus))
    report = evaluate_modes(artifact, fixture)
    assert report["safety_passed"] and report["fixture_sha256"] == fixture.digest
    held = report["splits"]["held_out"]
    assert set(held) == {"lexical", "dense", "hybrid", "reranked"}
    key = "h-new"
    assert fixture.sources["h-main"].judgments[key].grade == 3
    assert set(fixture.sources["h-main"].projection.keywords).isdisjoint(fixture.targets[key].projection.keywords)
    for mode, measured in held.items():
        main = next(query for query in measured["per_query"] if query["query"] == "h-main")
        assert (key in main["returned_keys"]) == (mode != "lexical"), (mode, main)
        assert measured["result_counts"]["judged_targets"] == 24
        assert measured["result_counts"]["returned"] > 0
    assert requests == 2 and len(rerank_sizes) == len(fixture.sources)
    assert all(
        size <= len(fixture.sources[key].targets)
        for key, size in zip(sorted(fixture.sources), rerank_sizes, strict=True)
    )
    assert max(rerank_sizes) <= 30
