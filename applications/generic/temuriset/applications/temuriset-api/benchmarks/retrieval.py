"""Produce and measure the frozen Spec 045 synthetic experiment offline."""

import argparse
import asyncio
import json
import os
import re
from collections import Counter
from dataclasses import dataclass
from hashlib import sha256
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from math import ceil, log2
from pathlib import Path
from statistics import median
from tempfile import NamedTemporaryFile
from time import perf_counter
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

from app.matching.engine.evaluate import evaluate, rank
from app.matching.engine.inputs import Source, Target

FIXTURE = Path(__file__).parent / "fixtures" / "retrieval.json"
SPLITS = ("development", "held_out")
MODES = ("lexical", "dense", "hybrid", "reranked")
_DISPLAY_LIMIT = 5
_RELEVANCE_MINIMUM = 2
_MAX_FIXTURE_BYTES = 131_072
_MAX_DOUBLE_REQUEST = 8_192

Mode = Literal["lexical", "dense", "hybrid", "reranked"]
Split = Literal["development", "held_out"]
Cohort = Literal["new", "established"]
Result = dict[str, Any]


class FixtureError(ValueError):
    """The curated comparison input cannot support a trustworthy report."""


class _FixtureRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    text: str = Field(min_length=1, max_length=512)
    selector: dict[str, object] | None
    split: Split
    group: str = Field(min_length=1)
    links: tuple[str, ...]


class RequirementJudgment(BaseModel):
    """An independently specified rule outcome and its grounding, when applicable."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    result: Literal["PASS", "FAIL", "UNKNOWN"]
    reason: str = Field(min_length=1)
    action: str | None
    verification_mode: Literal["DECLARATION", "DOCUMENT_PRESENT", "REVIEWER_CONFIRMED"]
    source_fact: Literal["stage", "relationship", "authority", "entity", "budget", "contribution"] | None = None


class Judgment(BaseModel):
    """Topical usefulness and separate rule expectations for one judged pair."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    grade: int = Field(strict=True, ge=0, le=3)
    eligibility: Literal["ELIGIBLE", "NEEDS_VERIFICATION", "INCOMPATIBLE"]
    readiness: Literal["READY_TO_SUBMIT", "NEEDS_INFORMATION", "BLOCKED_FOR_THIS_TARGET"]
    requirements: dict[str, RequirementJudgment]


class QueryCase(_FixtureRecord):
    """One versioned applicant input and its complete allowed catalog and judgments."""

    targets: tuple[str, ...] = Field(min_length=1)
    projection: Source
    judgments: dict[str, Judgment]


class TargetCase(_FixtureRecord):
    """One versioned target and its manager cohort."""

    cohort: Cohort
    projection: Target


class Fixture(BaseModel):
    """The versioned, author-judged synthetic evaluation set."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    version: Literal["synthetic-retrieval-v1"]
    label_provenance: str = Field(min_length=1)
    sources: dict[str, QueryCase]
    targets: dict[str, TargetCase]
    _digest: str = PrivateAttr(default="")

    @property
    def digest(self) -> str:
        """SHA-256 of the exact fixture bytes read from disk."""
        return self._digest


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = dict(pairs)
    if len(result) != len(pairs):
        raise ValueError("Duplicate JSON fields")
    return result


def load_fixture(path: Path = FIXTURE) -> Fixture:
    """Read the bounded fixture and reject invalid projections, incomplete labels and split leakage."""
    try:
        with path.open("rb") as stream:
            raw = stream.read(_MAX_FIXTURE_BYTES + 1)
        if len(raw) > _MAX_FIXTURE_BYTES:
            raise FixtureError("The synthetic fixture exceeds its byte budget.")
        fixture = Fixture.model_validate(json.loads(raw, object_pairs_hook=_unique_object))
    except FixtureError:
        raise
    except (OSError, ValueError, RecursionError) as error:
        raise FixtureError("The synthetic fixture is unreadable or malformed.") from error
    validate_fixture(fixture)
    fixture._digest = sha256(raw).hexdigest()
    return fixture


def validate_fixture(fixture: Fixture) -> None:
    """Require complete judgments and keep related and duplicated records within one split."""
    if set(fixture.sources) & set(fixture.targets) or {case.split for case in fixture.sources.values()} != set(SPLITS):
        raise FixtureError("Source and target keys must be distinct and both splits must have queries.")
    records = fixture.sources | fixture.targets
    groups: dict[str, Split] = {}
    texts: dict[str, Split] = {}
    for key, case in records.items():
        canonical_text = " ".join(case.text.casefold().split())
        if (
            groups.setdefault(case.group, case.split) != case.split
            or texts.setdefault(canonical_text, case.split) != case.split
        ):
            raise FixtureError("A declared group or duplicate text crosses splits.")
        if len(case.links) != len(set(case.links)) or any(link not in records or link == key for link in case.links):
            raise FixtureError("A declared relationship has an invalid endpoint.")
        if any((records[link].group, records[link].split) != (case.group, case.split) for link in case.links):
            raise FixtureError("Related records must stay in one group and split.")

    managers: dict[str, tuple[Split, str, Cohort]] = {}
    for key, target in fixture.targets.items():
        projection = target.projection
        manager = projection.partner_party_id
        grouping = (target.split, target.group, target.cohort)
        if managers.setdefault(manager, grouping) != grouping:
            raise FixtureError("A manager crosses groups, splits or exposure cohorts.")
        if projection.opportunity_id != key or projection.number < 1 or not projection.active:
            raise FixtureError("The catalog contains an unpinned or inactive target projection.")
        if target.selector is not None and target.selector != {
            "version": projection.number,
            "title": projection.title,
            "partner": projection.partner_name,
            "keywords": list(projection.keywords),
        }:
            raise FixtureError("A target selector differs from its judged projection.")

    judged_targets: set[str] = set()
    for key, query in fixture.sources.items():
        source = query.projection
        if source.id != key or source.version < 1:
            raise FixtureError("A query does not pin its source projection.")
        if query.selector is not None and (
            not isinstance(query.selector.get("title"), str)
            or query.selector
            != {
                "title": query.selector["title"],
                "type": source.type,
                "version": source.version,
                "sector": source.sector,
                "stage": source.stage,
                "relationship": source.relationship,
                "keywords": list(source.keywords),
            }
        ):
            raise FixtureError("A source selector differs from its judged projection.")
        pool = set(query.targets)
        if pool != set(query.judgments) or len(pool) != len(query.targets):
            raise FixtureError("Every allowed target needs exactly one judgment per query.")
        if not pool <= fixture.targets.keys() or any(fixture.targets[item].split != query.split for item in pool):
            raise FixtureError("A query references an unknown target or a target in another split.")
        judged_targets.update(pool)
        for target_key, judgment in query.judgments.items():
            _validate_judgment(query.projection, fixture.targets[target_key].projection, judgment)
    if judged_targets != set(fixture.targets):
        raise FixtureError("The frozen catalog contains an unjudged target.")


def _validate_judgment(source: Source, target: Target, judgment: Judgment) -> None:
    if any(
        not {"id", "field", "operator", "value", "label", "applies_at", "mandatory", "verification_mode"} <= rule.keys()
        or not isinstance(rule["id"], str)
        for rule in target.requirements
    ):
        raise FixtureError("A target requirement is missing its pinned fields.")
    rules = {rule["id"]: rule for rule in target.requirements}
    if len(rules) != len(target.requirements) or set(judgment.requirements) != rules.keys():
        raise FixtureError("Every declared target requirement needs one expected outcome.")
    for key, label in judgment.requirements.items():
        if label.verification_mode != rules[key]["verification_mode"]:
            raise FixtureError("A judgment changes the declared verification mode.")
        if label.source_fact is not None and (label.result != "PASS" or not getattr(source, label.source_fact)):
            raise FixtureError("A supported explanation needs a present source fact and a passing row.")
        if label.result == "PASS" and rules[key]["applies_at"] == "SUBMISSION" and label.source_fact is None:
            raise FixtureError("Every expected submission explanation needs explicit source grounding.")


@dataclass(frozen=True)
class Observation:
    """Candidate and display results over one authorized synthetic pool."""

    query: str
    candidates: tuple[str, ...]
    returned: tuple[str, ...]
    excluded: tuple[str, ...]
    evaluated: dict[str, Result]
    elapsed_ms: float


@dataclass
class Ratio:
    """An auditable aggregate with per-query undefined counts."""

    numerator: int | float = 0
    denominator: int | float = 0
    undefined_queries: int = 0

    def add(self, numerator: int | float, denominator: int | float) -> None:
        """Accumulate the raw numerator and denominator."""
        self.numerator += numerator
        self.denominator += denominator
        self.undefined_queries += denominator == 0

    def report(self) -> dict[str, int | float | None]:
        """Publish the ratio, raw totals and undefined query count."""
        return {
            "value": self.numerator / self.denominator if self.denominator else None,
            "numerator": self.numerator,
            "denominator": self.denominator,
            "undefined_queries": self.undefined_queries,
        }


def _gain(grades: list[int]) -> float:
    return sum((2**grade - 1) / log2(position + 2) for position, grade in enumerate(grades[:_DISPLAY_LIMIT]))


def _check_observation(query: QueryCase, observation: Observation) -> None:
    pool = set(query.targets)
    sets = tuple(set(items) for items in (observation.candidates, observation.returned, observation.excluded))
    candidates, returned, excluded = sets
    if (
        set(observation.evaluated) != pool
        or any(not keys <= pool for keys in sets)
        or any(
            len(keys) != len(items)
            for keys, items in zip(
                sets, (observation.candidates, observation.returned, observation.excluded), strict=True
            )
        )
        or not returned <= candidates
        or returned & excluded
    ):
        raise FixtureError("A mode changed the judged pool or returned an invalid result partition.")


def _safety(
    query: QueryCase,
    observation: Observation,
    ratios: dict[str, Ratio],
) -> None:
    unknown_rows = correct_unknown = correct_rules = 0
    for target_key, judgment in query.judgments.items():
        result = observation.evaluated[target_key]
        rows = {row["requirement_id"]: row for row in result["rows"]}
        rows_match = set(rows) == judgment.requirements.keys() and len(rows) == len(result["rows"])
        for key, label in judgment.requirements.items():
            row = rows.get(key, {})
            correct = all(
                row.get(field) == getattr(label, field) for field in ("result", "reason", "action", "verification_mode")
            )
            rows_match &= correct
            if label.result == "UNKNOWN":
                unknown_rows += 1
                correct_unknown += (
                    correct
                    and result["eligibility"] == judgment.eligibility
                    and result["readiness"] == judgment.readiness
                )
        correct_rules += (
            rows_match and result["eligibility"] == judgment.eligibility and result["readiness"] == judgment.readiness
        )

    hard_violations = supported = explanations = 0
    for key in observation.returned:
        judgment = query.judgments[key]
        hard_violations += judgment.eligibility == "INCOMPATIBLE"
        allowed = {row.reason for row in judgment.requirements.values() if row.source_fact is not None}
        reasons = observation.evaluated[key]["reasons"]
        explanations += len(reasons)
        supported += sum(reason in allowed for reason in reasons)
    ratios["hard_rule_violations"].add(hard_violations, len(observation.returned))
    ratios["rule_outcome_correctness"].add(correct_rules, len(query.judgments))
    ratios["unknown_correctness"].add(correct_unknown, unknown_rows)
    ratios["factual_source_support"].add(supported, explanations)


def summarize(fixture: Fixture, split: Split, observations: list[Observation]) -> dict[str, Any]:
    """Calculate comparison and safety metrics against the identical frozen pool for one split."""
    expected = {key for key, query in fixture.sources.items() if query.split == split}
    if len(observations) != len(expected) or {item.query for item in observations} != expected:
        raise FixtureError("Every mode needs exactly one observation for every query in its split.")
    ratios = {
        key: Ratio()
        for key in (
            "candidate_recall",
            "returned_precision",
            "precision_at_5",
            "ndcg_at_5",
            "hard_rule_violations",
            "rule_outcome_correctness",
            "unknown_correctness",
            "factual_source_support",
            "coverage",
            "abstention",
        )
    }
    exposure: Counter[str] = Counter()
    visible_managers: dict[str, set[str]] = {cohort: set() for cohort in ("new", "established")}
    available_managers: dict[str, set[str]] = {cohort: set() for cohort in ("new", "established")}
    counts: Counter[str] = Counter()
    per_query = []
    for observed in observations:
        query = fixture.sources[observed.query]
        _check_observation(query, observed)
        useful = {key for key, judgment in query.judgments.items() if judgment.grade >= _RELEVANCE_MINIMUM}
        shown = observed.returned
        ratios["candidate_recall"].add(sum(key in useful for key in observed.candidates), len(useful))
        ratios["returned_precision"].add(sum(key in useful for key in shown), len(shown))
        ratios["precision_at_5"].add(sum(key in useful for key in shown[:_DISPLAY_LIMIT]), _DISPLAY_LIMIT)
        ideal = _gain(sorted((item.grade for item in query.judgments.values()), reverse=True))
        actual = _gain([query.judgments[key].grade for key in shown])
        ratios["ndcg_at_5"].add(actual / ideal if ideal else 0, int(ideal > 0))
        ratios["coverage"].add(int(bool(shown)), 1)
        ratios["abstention"].add(int(not shown), 1)
        _safety(query, observed, ratios)
        for key in query.targets:
            target = fixture.targets[key]
            available_managers[target.cohort].add(target.projection.partner_party_id)
        for key in shown:
            target = fixture.targets[key]
            exposure[target.cohort] += 1
            visible_managers[target.cohort].add(target.projection.partner_party_id)
        query_counts = {
            "judged_targets": len(query.targets),
            "candidates": len(observed.candidates),
            "returned": len(shown),
            "excluded": len(observed.excluded),
            "undisplayed": len(query.targets) - len(shown) - len(observed.excluded),
            "known_hard_fail_pairs": sum(item.eligibility == "INCOMPATIBLE" for item in query.judgments.values()),
        }
        counts.update(query_counts)
        per_query.append(
            {
                "query": observed.query,
                **query_counts,
                "returned_keys": list(shown),
                "candidate_keys": list(observed.candidates),
            }
        )

    timings = sorted(item.elapsed_ms for item in observations)
    returned = counts["returned"]
    metrics = {key: value.report() for key, value in ratios.items()}
    safe = ratios["hard_rule_violations"].numerator == 0 and all(
        ratios[name].numerator == ratios[name].denominator
        for name in ("rule_outcome_correctness", "unknown_correctness", "factual_source_support")
    )
    return {
        "query_count": len(observations),
        "metrics": metrics,
        "result_counts": dict(counts),
        "per_query": per_query,
        "safety_passed": safe,
        "manager_exposure": {
            cohort: {
                "positions": exposure[cohort],
                "total_positions": returned,
                "share": exposure[cohort] / returned if returned else None,
                "distinct_managers_exposed": len(visible_managers[cohort]),
                "distinct_managers_available": len(available_managers[cohort]),
            }
            for cohort in visible_managers
        },
        "latency_ms": {
            "samples": len(timings),
            "median": median(timings),
            "p95_nearest_rank": timings[ceil(0.95 * len(timings)) - 1],
            "scope": "Local in-process retrieval, rule evaluation and display ranking per query.",
        },
        "cost": {"real_provider": "unmeasured", "synthetic_double": "local_fixture_no_provider_billing"},
    }


def evaluate_modes(artifact_path: Path, fixture: Fixture) -> dict[str, Any]:
    """Load the runtime artifact and reuse the actual rules and rankers for every compared mode."""
    from app.matching.engine.retrieval import (  # noqa: PLC0415
        CHANNEL_LIMIT,
        DENSE_MIN,
        HYBRID_MIN,
        RERANK_LIMIT,
        RERANK_MIN,
        RRF_K,
        retrieve,
    )
    from app.matching.service.retrieval_adapter import PINS, load_artifact, load_corpus  # noqa: PLC0415

    from app.matching.engine.evaluate import ENGINE, rank_experiment  # noqa: PLC0415

    corpus = load_corpus(FIXTURE)
    if corpus.digest != fixture.digest:
        raise FixtureError("The judged fixture changed during this comparison.")
    artifact = load_artifact(artifact_path, corpus)
    splits: dict[str, dict[str, Any]] = {}
    for split in SPLITS:
        modes: dict[str, Any] = {}
        for mode in MODES:
            observations = []
            for key, query in sorted(fixture.sources.items()):
                if query.split != split:
                    continue
                targets = {item: fixture.targets[item] for item in query.targets}
                start = perf_counter()
                if mode == "lexical":
                    evaluated = {
                        item: evaluate(query.projection, target.projection) for item, target in targets.items()
                    }
                    candidates = tuple(item for item, result in evaluated.items() if result["relevant"])
                    shown, excluded = rank(list(evaluated.values()))
                else:
                    selection = retrieve(
                        mode,
                        query.text,
                        {item: target.text for item, target in targets.items()},
                        artifact.source_vectors[key],
                        {item: artifact.target_vectors[item] for item in targets},
                        artifact.rerank_scores[key],
                    )
                    candidates = selection.candidates
                    admitted = set(selection.admitted)
                    evaluated = {
                        item: evaluate(query.projection, target.projection, retrieval_evidence=item in admitted)
                        for item, target in targets.items()
                    }
                    admitted_versions = tuple(targets[item].projection.version_id for item in selection.admitted)
                    shown, excluded = rank_experiment(list(evaluated.values()), admitted_versions)
                elapsed = (perf_counter() - start) * 1000
                observations.append(
                    Observation(
                        key,
                        candidates,
                        tuple(row["opportunity_id"] for row in shown),
                        tuple(row["opportunity_id"] for row in excluded),
                        evaluated,
                        elapsed,
                    )
                )
            modes[mode] = summarize(fixture, split, observations)
        splits[split] = modes
    return {
        "fixture_version": fixture.version,
        "fixture_sha256": corpus.digest,
        "artifact_sha256": artifact.digest,
        "label_provenance": fixture.label_provenance,
        "calibration": {
            "id": PINS["calibration"],
            "dense_minimum_cosine": DENSE_MIN,
            "hybrid_minimum_cosine_or_positive_bm25": HYBRID_MIN,
            "reranked_head_minimum": RERANK_MIN,
            "reciprocal_rank_fusion_k": RRF_K,
            "channel_candidate_limit": CHANNEL_LIMIT,
            "provider_rerank_limit": RERANK_LIMIT,
            "policy": "Frozen implementation thresholds. The command fits no thresholds on either split.",
        },
        "baseline": ENGINE,
        "pins": dict(PINS),
        "binary_relevance_minimum_grade": _RELEVANCE_MINIMUM,
        "evidence": "Author-judged synthetic text and local elapsed time.",
        "splits": splits,
        "safety_passed": all(mode["safety_passed"] for split in splits.values() for mode in split.values()),
    }


_TOPIC_WORDS = tuple(
    frozenset(words.split())
    for words in (
        "air pesisir laut payau membran desalinasi saringan penyaring sumur",
        "irigasi surya panel matahari fotovoltaik sawah pertanian lahan",
        "limbah sanitasi",
        "klinik kesehatan pasien diagnosis",
        "literasi pembelajaran modul kelas baca",
        "gudang penyimpanan panen",
        "mobilitas angkutan perjalanan lintas",
        "daur ulang sampah kemasan kompos",
    )
)


def _topics(text: str) -> frozenset[int]:
    words = set(re.findall(r"\w+", text.casefold()))
    return frozenset(index for index, vocabulary in enumerate(_TOPIC_WORDS) if words & vocabulary)


def _double_response(payload: object, fixture: Fixture, pins: dict[str, str]) -> dict[str, Any] | None:
    source_keys = sorted(fixture.sources)
    queries = [fixture.sources[key].text for key in source_keys]
    targets = [fixture.targets[key].text for key in sorted(fixture.targets)]
    if payload == {"pins": pins, "queries": queries, "targets": targets}:
        return {
            "pins": pins,
            "source_vectors": [_vector(_topics(text)) for text in queries],
            "target_vectors": [_vector(_topics(text)) for text in targets],
        }
    if not isinstance(payload, dict) or set(payload) != {"pins", "rerank"} or payload["pins"] != pins:
        return None
    requests = payload["rerank"]
    if not isinstance(requests, list) or len(requests) != len(source_keys):
        return None
    scores = []
    for key, request in zip(source_keys, requests, strict=True):
        query = fixture.sources[key]
        allowed = {fixture.targets[target_key].text for target_key in query.targets}
        if (
            not isinstance(request, dict)
            or set(request) != {"query", "targets"}
            or request["query"] != query.text
            or not isinstance(request["targets"], list)
            or len(request["targets"]) > 30
            or any(not isinstance(text, str) or text not in allowed for text in request["targets"])
            or len(set(request["targets"])) != len(request["targets"])
        ):
            return None
        source_topics = _topics(query.text)
        scores.append([_rerank_score(source_topics, _topics(text)) for text in request["targets"]])
    return {"pins": pins, "rerank_scores": scores}


def _vector(topics: frozenset[int]) -> list[float]:
    return [float(index in topics) for index in range(len(_TOPIC_WORDS))]


def _rerank_score(left: frozenset[int], right: frozenset[int]) -> float:
    return len(left & right) / len(left | right) if left | right else 0.0


def _serve_double(port: int, fixture: Fixture, pins: dict[str, str]) -> None:
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802 - stdlib HTTP handler method
            self.connection.settimeout(2)
            try:
                length = int(self.headers.get("Content-Length", 0))
                if (
                    self.path != "/retrieval"
                    or not 1 <= length <= _MAX_DOUBLE_REQUEST
                    or self.headers.get_content_type() != "application/json"
                ):
                    self.send_error(HTTPStatus.BAD_REQUEST)
                    return
                payload = json.loads(self.rfile.read(length), object_pairs_hook=_unique_object)
            except (ValueError, TimeoutError, RecursionError):
                self.send_error(HTTPStatus.BAD_REQUEST)
                return
            response = _double_response(payload, fixture, pins)
            if response is None:
                self.send_error(HTTPStatus.BAD_REQUEST)
                return
            if "rerank_scores" in response:
                counts = [len(scores) for scores in response["rerank_scores"]]
                print(json.dumps({"synthetic_rerank_candidates_per_query": counts}), flush=True)
            body = json.dumps(response, allow_nan=False).encode()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, _format: str, *_args: object) -> None:
            # Request paths and input text belong outside the local double's diagnostic surface.
            return

    with ThreadingHTTPServer(("127.0.0.1", port), Handler) as server:
        print(f"Synthetic model double listening on http://127.0.0.1:{server.server_port}/retrieval", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            return


def _write_artifact(path: Path, content: bytes) -> None:
    with NamedTemporaryFile(dir=path.parent, delete=False) as temporary:
        try:
            temporary.write(content)
            temporary.flush()
            os.replace(temporary.name, path)
        finally:
            Path(temporary.name).unlink(missing_ok=True)


def main() -> int:
    """Run the opt-in double, artifact producer or frozen comparison."""
    from app.matching.service.retrieval_adapter import (  # noqa: PLC0415
        PINS,
        RetrievalArtifactError,
        load_corpus,
        produce_artifact,
    )

    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    double = commands.add_parser("serve-double", help="Bind a synthetic-only model double to IPv4 loopback.")
    double.add_argument("--port", default=58045, type=int)
    producer = commands.add_parser("produce", help="Publish a local artifact from the committed fixture.")
    producer.add_argument("--endpoint", required=True)
    producer.add_argument("--artifact", required=True, type=Path)
    comparison = commands.add_parser("evaluate", help="Report all four modes on both frozen splits.")
    comparison.add_argument("--artifact", required=True, type=Path)
    args = parser.parse_args()
    try:
        fixture = load_fixture()
        if args.command == "serve-double":
            _serve_double(args.port, fixture, dict(PINS))
            return 0
        if args.command == "produce":
            corpus = load_corpus(FIXTURE)
            if corpus.digest != fixture.digest:
                raise FixtureError("The judged fixture changed before the producer request.")
            _write_artifact(args.artifact, asyncio.run(produce_artifact(args.endpoint, corpus)))
            print(
                json.dumps({"artifact": "written", "fixture_version": corpus.version, "fixture_sha256": corpus.digest})
            )
            return 0
        report = evaluate_modes(args.artifact, fixture)
        print(json.dumps(report, ensure_ascii=False, allow_nan=False, indent=2))
        return int(not report["safety_passed"])
    except FixtureError as error:
        parser.exit(2, f"{error}\n")
    except RetrievalArtifactError:
        parser.exit(
            2, "The synthetic artifact could not be produced or validated. Check the local fixture and relay.\n"
        )
    except (OSError, OverflowError):
        parser.exit(2, "The local benchmark resource could not be opened. Check the port or output directory.\n")


if __name__ == "__main__":
    raise SystemExit(main())
