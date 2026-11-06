"""Offline synthetic model transport and immutable startup snapshot for Spec 045."""

import asyncio
import hashlib
import json
import math
import os
import re
import stat
from collections.abc import Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from types import MappingProxyType
from typing import Literal

from httpx import AsyncClient, HTTPError
from pydantic import BaseModel, ConfigDict, Field

from app.core.logging import suppress_http_diagnostics
from app.core.settings import Settings
from app.matching.engine.inputs import Source, Target
from app.matching.engine.retrieval import RERANK_LIMIT, RetrievalMode, retrieve

PINS = {
    "model_id": "synthetic-retrieval-double",
    "revision": "1",
    "tokenizer": "unicode-word-v1",
    "truncation": "512-chars-v1",
    "template": "fixture-text-v1",
    "calibration": "admission-v1",
}
PROFILE = "synthetic-retrieval-v1"
FIXTURE_PATH = Path(__file__).resolve().parents[3] / "benchmarks" / "fixtures" / "retrieval.json"
TIMEOUT_SECONDS = 3.0
_MAX_FIXTURE_BYTES = 512 * 1024
_MAX_OUTPUT_BYTES = 256 * 1024
_MAX_REQUEST_BYTES = 128 * 1024
_MAX_SOURCES = 32
_MAX_TARGETS = 100
_DIMENSIONS = 8
_FORMAT_VERSION = 1
_KEY = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}")
_LOOPBACK_URL = re.compile(r"http://(?:127\.0\.0\.1|\[::1\]):([1-9][0-9]{0,4})(?:/[A-Za-z0-9/._~-]*)?")
ArtifactFailure = Literal["artifact_missing", "artifact_invalid", "unsupported_input"]
ProducerFailure = Literal["relay_endpoint", "relay_unavailable", "relay_invalid"]


class RetrievalArtifactError(ValueError):
    """A safe local artifact or producer failure. Its text contains only a closed reason."""

    def __init__(self, reason: ArtifactFailure | ProducerFailure) -> None:
        """Keep the closed reason and omit upstream inputs."""
        self.reason = reason
        super().__init__(reason)


class _Selector(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    version: int = Field(ge=1)
    title: str = Field(min_length=1, max_length=200)
    keywords: tuple[str, ...] = Field(max_length=50)


class SourceSelector(_Selector):
    """The exact safe source projection admitted to the local experiment."""

    type: Literal["SUPPORT_REQUEST", "FUNDING_REQUEST"]
    sector: str
    stage: str | None
    relationship: str | None


class TargetSelector(_Selector):
    """The exact public catalog projection admitted to the local experiment."""

    partner: str = Field(min_length=1, max_length=200)


class FixtureSource(BaseModel):
    """Canonical synthetic query and its permitted catalog."""

    model_config = ConfigDict(frozen=True)

    text: str = Field(min_length=1, max_length=512)
    targets: tuple[str, ...] = Field(min_length=1, max_length=_MAX_TARGETS)
    selector: SourceSelector | None = None


class FixtureTarget(BaseModel):
    """Canonical synthetic target text and its optional runtime selector."""

    model_config = ConfigDict(frozen=True)

    text: str = Field(min_length=1, max_length=512)
    selector: TargetSelector | None = None


class _FixtureDocument(BaseModel):
    version: str
    sources: dict[str, FixtureSource] = Field(min_length=1, max_length=_MAX_SOURCES)
    targets: dict[str, FixtureTarget] = Field(min_length=1, max_length=_MAX_TARGETS)


class _EmbeddingOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)

    pins: dict[str, str]
    source_vectors: list[list[float]]
    target_vectors: list[list[float]]


class _RerankOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)

    pins: dict[str, str]
    rerank_scores: list[list[float]]


class _WireOutput(_EmbeddingOutput):
    rerank_scores: list[list[float]]


class _ArtifactDocument(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    format: Literal[1]
    fixture_version: str
    fixture_sha256: str
    output: _WireOutput


@dataclass(frozen=True, slots=True)
class Corpus:
    """Curated, immutable inputs used by both offline production and startup validation."""

    version: str
    digest: str
    sources: Mapping[str, FixtureSource]
    targets: Mapping[str, FixtureTarget]


@dataclass(frozen=True, slots=True)
class ModelArtifact:
    """Validated, normalized model outputs keyed only by curated fixture IDs."""

    source_vectors: Mapping[str, tuple[float, ...]]
    target_vectors: Mapping[str, tuple[float, ...]]
    rerank_scores: Mapping[str, Mapping[str, float]]
    digest: str = ""


@dataclass(frozen=True, slots=True)
class RetrievalExperiment:
    """The startup snapshot used by the normal route, with no request-time file or network I/O."""

    mode: RetrievalMode
    corpus: Corpus | None = None
    artifact: ModelArtifact | None = None
    fallback: ArtifactFailure | None = None

    def select(self, source: Source, title: str, targets: list[Target]) -> tuple[str, ...] | None:
        """Return admitted version IDs, or None when the source or whole catalog is unsupported."""
        if self.corpus is None or self.artifact is None:
            return None
        source_fields = (
            source.type,
            source.version,
            title,
            source.sector,
            source.stage,
            source.relationship,
            source.keywords,
        )
        matches = [
            (key, fixture)
            for key, fixture in self.corpus.sources.items()
            if fixture.selector is not None
            and source_fields
            == (
                fixture.selector.type,
                fixture.selector.version,
                fixture.selector.title,
                fixture.selector.sector,
                fixture.selector.stage,
                fixture.selector.relationship,
                fixture.selector.keywords,
            )
        ]
        if len(matches) != 1:
            return None
        source_key, fixture = matches[0]
        actual = {
            (target.number, target.title, target.partner_name, target.keywords): target.version_id for target in targets
        }
        selected: dict[str, str] = {}
        for key in fixture.targets:
            selector = self.corpus.targets[key].selector
            if selector is None:
                return None
            version_id = actual.get((selector.version, selector.title, selector.partner, selector.keywords))
            if version_id is None:
                return None
            selected[key] = version_id
        if len(set(selected.values())) != len(targets) or len(selected) != len(targets):
            return None

        result = retrieve(
            self.mode,
            fixture.text,
            {key: self.corpus.targets[key].text for key in selected},
            self.artifact.source_vectors[source_key],
            self.artifact.target_vectors,
            self.artifact.rerank_scores[source_key],
        )
        return tuple(selected[key] for key in result.admitted)


def _unique_fields(pairs: list[tuple[str, object]]) -> dict[str, object]:
    fields = dict(pairs)
    if len(fields) != len(pairs):
        raise ValueError("Duplicate JSON field")
    return fields


def _decode(data: bytes) -> object:
    return json.loads(data.decode(), object_pairs_hook=_unique_fields)


def _read(path: Path, limit: int) -> bytes:
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
        with os.fdopen(descriptor, "rb") as file:
            # The opened descriptor, rather than an earlier stat, decides what can be read.
            if not stat.S_ISREG(os.fstat(file.fileno()).st_mode):
                raise RetrievalArtifactError("artifact_invalid")
            content = file.read(limit + 1)
    except FileNotFoundError:
        raise RetrievalArtifactError("artifact_missing") from None
    except RetrievalArtifactError:
        raise
    except (OSError, ValueError):
        raise RetrievalArtifactError("artifact_invalid") from None
    if len(content) > limit:
        raise RetrievalArtifactError("artifact_invalid")
    return content


def load_corpus(path: Path) -> Corpus:
    """Validate the committed fixture's identity, bounds and closed target references."""
    data = _read(path, _MAX_FIXTURE_BYTES)
    try:
        fixture = _FixtureDocument.model_validate(_decode(data))
        if not all(_KEY.fullmatch(key) for key in (fixture.version, *fixture.sources, *fixture.targets)):
            raise ValueError("Invalid key")
        for source in fixture.sources.values():
            if len(set(source.targets)) != len(source.targets) or not set(source.targets) <= fixture.targets.keys():
                raise ValueError("Invalid target pool")
    except (ValueError, RecursionError):
        raise RetrievalArtifactError("artifact_invalid") from None
    return Corpus(
        fixture.version,
        hashlib.sha256(data).hexdigest(),
        MappingProxyType(fixture.sources),
        MappingProxyType(fixture.targets),
    )


def _normalize(vector: list[float]) -> tuple[float, ...]:
    if len(vector) != _DIMENSIONS or not all(math.isfinite(value) for value in vector):
        raise ValueError("Invalid vector")
    scale = max(map(abs, vector))
    if scale == 0:
        raise ValueError("Invalid vector norm")
    scaled = tuple(value / scale for value in vector)
    length = math.hypot(*scaled)
    return tuple(value / length for value in scaled)


def _validated_vectors(
    output: _EmbeddingOutput, corpus: Corpus
) -> tuple[dict[str, tuple[float, ...]], dict[str, tuple[float, ...]]]:
    sources = sorted(corpus.sources)
    targets = sorted(corpus.targets)
    if output.pins != PINS or (len(output.source_vectors), len(output.target_vectors)) != (len(sources), len(targets)):
        raise ValueError("Unexpected model pins or vector count")
    source_vectors = {key: _normalize(vector) for key, vector in zip(sources, output.source_vectors, strict=True)}
    target_vectors = {key: _normalize(vector) for key, vector in zip(targets, output.target_vectors, strict=True)}
    return source_vectors, target_vectors


def _rerank_heads(
    corpus: Corpus, source_vectors: Mapping[str, tuple[float, ...]], target_vectors: Mapping[str, tuple[float, ...]]
) -> dict[str, tuple[str, ...]]:
    return {
        key: retrieve(
            "hybrid",
            source.text,
            {target: corpus.targets[target].text for target in source.targets},
            source_vectors[key],
            target_vectors,
            {},
        ).candidates[:RERANK_LIMIT]
        for key, source in sorted(corpus.sources.items())
    }


def _validate_output(output: _WireOutput, corpus: Corpus) -> ModelArtifact:
    source_vectors, target_vectors = _validated_vectors(output, corpus)
    heads = _rerank_heads(corpus, source_vectors, target_vectors)
    if len(output.rerank_scores) != len(heads):
        raise ValueError("Unexpected rerank row count")
    rerank_scores: dict[str, Mapping[str, float]] = {}
    for (key, head), row in zip(heads.items(), output.rerank_scores, strict=True):
        if len(row) != len(head) or not all(0 <= score <= 1 for score in row):
            raise ValueError("Invalid rerank scores")
        rerank_scores[key] = MappingProxyType(dict(zip(head, row, strict=True)))
    return ModelArtifact(
        MappingProxyType(source_vectors), MappingProxyType(target_vectors), MappingProxyType(rerank_scores)
    )


def load_artifact(path: Path, corpus: Corpus) -> ModelArtifact:
    """Load a bounded local artifact only for the exact fixture bytes and pinned profile."""
    raw = _read(path, _MAX_OUTPUT_BYTES)
    try:
        stored = _ArtifactDocument.model_validate(_decode(raw))
        if (stored.fixture_version, stored.fixture_sha256) != (corpus.version, corpus.digest):
            raise ValueError("Fixture identity mismatch")
        return replace(_validate_output(stored.output, corpus), digest=hashlib.sha256(raw).hexdigest())
    except (ValueError, RecursionError):
        raise RetrievalArtifactError("artifact_invalid") from None


async def _exchange(client: AsyncClient, endpoint: str, payload: dict[str, object]) -> object:
    content = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
    if len(content) > _MAX_REQUEST_BYTES:
        raise RetrievalArtifactError("relay_invalid")
    headers = {"Content-Type": "application/json", "Accept": "application/json", "Accept-Encoding": "identity"}
    data = bytearray()
    async with client.stream("POST", endpoint, content=content, headers=headers) as response:
        response.raise_for_status()
        content_type = response.headers.get("content-type", "").partition(";")[0].strip().lower()
        if content_type != "application/json" or response.headers.get("content-encoding", "identity") != "identity":
            raise RetrievalArtifactError("relay_invalid")
        async for chunk in response.aiter_bytes():
            if len(data) + len(chunk) > _MAX_OUTPUT_BYTES:
                raise RetrievalArtifactError("relay_invalid")
            data.extend(chunk)
    return _decode(bytes(data))


async def produce_artifact(endpoint: str, corpus: Corpus) -> bytes:
    """Fetch embeddings then rerank only the bounded fused head for each synthetic query."""
    address = _LOOPBACK_URL.fullmatch(endpoint)
    if not address or int(address[1]) > 65535:
        raise RetrievalArtifactError("relay_endpoint")
    suppress_http_diagnostics()
    try:
        async with (
            asyncio.timeout(TIMEOUT_SECONDS),
            AsyncClient(timeout=TIMEOUT_SECONDS, follow_redirects=False, trust_env=False) as client,
        ):
            embedding_payload = {
                "pins": PINS,
                "queries": [corpus.sources[key].text for key in sorted(corpus.sources)],
                "targets": [corpus.targets[key].text for key in sorted(corpus.targets)],
            }
            embeddings = _EmbeddingOutput.model_validate(await _exchange(client, endpoint, embedding_payload))
            source_vectors, target_vectors = _validated_vectors(embeddings, corpus)
            heads = _rerank_heads(corpus, source_vectors, target_vectors)
            rerank_payload = {
                "pins": PINS,
                "rerank": [
                    {"query": corpus.sources[key].text, "targets": [corpus.targets[target].text for target in head]}
                    for key, head in heads.items()
                ],
            }
            rerank = _RerankOutput.model_validate(await _exchange(client, endpoint, rerank_payload))
            if rerank.pins != PINS:
                raise ValueError("Unexpected rerank pins")
        output = _WireOutput(**embeddings.model_dump(), rerank_scores=rerank.rerank_scores)
        _validate_output(output, corpus)
        encoded = (
            _ArtifactDocument(
                format=_FORMAT_VERSION, fixture_version=corpus.version, fixture_sha256=corpus.digest, output=output
            )
            .model_dump_json()
            .encode()
        )
        if len(encoded) > _MAX_OUTPUT_BYTES:
            raise ValueError("Artifact too large")
    except (TimeoutError, HTTPError):
        raise RetrievalArtifactError("relay_unavailable") from None
    except RetrievalArtifactError:
        raise
    except (ValueError, RecursionError):
        raise RetrievalArtifactError("relay_invalid") from None
    return encoded


def load_experiment(settings: Settings, corpus_path: Path | None = None) -> RetrievalExperiment | None:
    """Read once before serving. A missing or invalid snapshot leaves lexical matching available."""
    mode = settings.match_retrieval_mode
    if mode == "off":
        return None
    try:
        corpus = load_corpus(corpus_path or FIXTURE_PATH)
        artifact_path = settings.match_retrieval_artifact
        if artifact_path is None or not artifact_path.get_secret_value():
            raise RetrievalArtifactError("artifact_missing")
        artifact = load_artifact(Path(artifact_path.get_secret_value()), corpus)
    except RetrievalArtifactError as error:
        reason: ArtifactFailure = "artifact_missing" if error.reason == "artifact_missing" else "artifact_invalid"
        return RetrievalExperiment(mode, fallback=reason)
    return RetrievalExperiment(mode, corpus=corpus, artifact=artifact)
