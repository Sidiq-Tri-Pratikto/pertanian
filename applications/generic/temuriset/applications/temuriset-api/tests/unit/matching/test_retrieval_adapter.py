"""Exercise the synthetic model boundary without external traffic."""

import json
from pathlib import Path

import httpx
import pytest

from app.matching.service import retrieval_adapter as adapter


@pytest.fixture
def corpus(tmp_path: Path) -> adapter.Corpus:
    """A single query and one candidate with no live application selectors."""
    fixture = tmp_path / "fixture.json"
    fixture.write_text(
        json.dumps(
            {
                "version": "test-v1",
                "sources": {"query-key": {"text": "pompa sintetis", "targets": ["target-key"]}},
                "targets": {"target-key": {"text": "air sintetis"}},
            }
        )
    )
    return adapter.load_corpus(fixture)


async def test_loopback_producer_round_trip_pins_only_synthetic_text_and_normalizes(
    corpus: adapter.Corpus, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    Condition:
    - A loopback relay returns finite vectors and bounded scores for the pinned fixture.

    Expected:
    - Only curated text and pins cross the wire; the validated artifact round-trips without raw provider fields.
    """

    def relay(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        if "queries" in payload:
            assert payload == {"pins": adapter.PINS, "queries": ["pompa sintetis"], "targets": ["air sintetis"]}
            return httpx.Response(
                200,
                json={
                    "pins": adapter.PINS,
                    "source_vectors": [[2] + [0] * 7],
                    "target_vectors": [[3] + [0] * 7],
                },
            )
        assert payload == {"pins": adapter.PINS, "rerank": [{"query": "pompa sintetis", "targets": ["air sintetis"]}]}
        return httpx.Response(200, json={"pins": adapter.PINS, "rerank_scores": [[0.75]]})

    def client(**kwargs: object) -> httpx.AsyncClient:
        assert kwargs["trust_env"] is False and kwargs["follow_redirects"] is False
        return httpx.AsyncClient(transport=httpx.MockTransport(relay), trust_env=False)

    monkeypatch.setattr(adapter, "AsyncClient", client)
    artifact = tmp_path / "artifact.json"
    artifact.write_bytes(await adapter.produce_artifact("http://127.0.0.1:54500/model", corpus))
    loaded = adapter.load_artifact(artifact, corpus)
    assert loaded.source_vectors["query-key"] == (1.0,) + (0.0,) * 7
    assert loaded.rerank_scores["query-key"]["target-key"] == 0.75


@pytest.mark.parametrize("endpoint", ["http://localhost:1", "http://example.invalid:1", "http://127.0.0.1:1/?secret=x"])
async def test_relay_rejects_nonliteral_or_credential_bearing_endpoints(endpoint: str, corpus: adapter.Corpus) -> None:
    """
    Condition:
    - The endpoint can resolve externally or embed sensitive request metadata.

    Expected:
    - Validation fails before transport; diagnostics exclude the supplied endpoint.
    """
    with pytest.raises(adapter.RetrievalArtifactError, match="relay_endpoint") as failure:
        await adapter.produce_artifact(endpoint, corpus)
    assert endpoint not in str(failure.value)


async def test_relay_receives_only_the_fused_head_and_load_rejects_mismatched_positions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Condition:
    - Forty eligible candidates share equal fused positions and the model can score all of them.

    Expected:
    - The relay scores only the first thirty and startup rejects any extra positions.
    """
    fixture = tmp_path / "fixture.json"
    keys = [f"target-{i:02}" for i in range(40)]
    fixture.write_text(
        json.dumps(
            {
                "version": "test-v1",
                "sources": {"q": {"text": "air", "targets": keys}},
                "targets": {key: {"text": f"air {key}"} for key in keys},
            }
        )
    )
    corpus = adapter.load_corpus(fixture)
    requests = []

    def relay(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        requests.append(body)
        if "queries" in body:
            vector = [5e-324, 5e-324] + [0] * 6
            return httpx.Response(
                200, json={"pins": adapter.PINS, "source_vectors": [vector], "target_vectors": [vector] * 40}
            )
        assert body["rerank"] == [{"query": "air", "targets": [f"air {key}" for key in keys[:30]]}]
        return httpx.Response(200, json={"pins": adapter.PINS, "rerank_scores": [[0.75] * 30]})

    monkeypatch.setattr(
        adapter, "AsyncClient", lambda **_kwargs: httpx.AsyncClient(transport=httpx.MockTransport(relay))
    )
    artifact = tmp_path / "artifact.json"
    artifact.write_bytes(await adapter.produce_artifact("http://127.0.0.1:54500/model", corpus))
    loaded = adapter.load_artifact(artifact, corpus)
    assert len(requests) == 2
    assert set(loaded.rerank_scores["q"]) == set(keys[:30])
    assert sum(value * value for value in loaded.source_vectors["q"]) == pytest.approx(1)
    invalid = json.loads(artifact.read_bytes())
    invalid["output"]["rerank_scores"][0].append(1)
    artifact.write_text(json.dumps(invalid))
    with pytest.raises(adapter.RetrievalArtifactError, match="artifact_invalid"):
        adapter.load_artifact(artifact, corpus)


@pytest.mark.parametrize(
    ("case", "reason"),
    [
        ("pins", "relay_invalid"),
        ("nonfinite", "relay_invalid"),
        ("zero", "relay_invalid"),
        ("oversize", "relay_invalid"),
        ("timeout", "relay_unavailable"),
        ("http", "relay_unavailable"),
    ],
)
async def test_unsafe_or_unavailable_relay_output_is_rejected_without_diagnostics_leak(
    corpus: adapter.Corpus,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    case: str,
    reason: str,
) -> None:
    """
    Condition:
    - The relay is down or sends unsafe model output.

    Expected:
    - The producer refuses the artifact and diagnostics carry no upstream payload or status text.
    """
    import asyncio  # noqa: PLC0415
    import logging  # noqa: PLC0415

    marker = "private-synthetic-relay-marker-4381"
    caplog.set_level(logging.DEBUG)
    monkeypatch.setattr(adapter, "TIMEOUT_SECONDS", 0.05)

    async def relay(_request: httpx.Request) -> httpx.Response:
        if case == "timeout":
            await asyncio.Event().wait()
        if case == "http":
            return httpx.Response(503, content=marker, extensions={"reason_phrase": marker.encode()})
        if case == "oversize":
            return httpx.Response(200, headers={"Content-Type": "application/json"}, content=marker * 30000)
        vector = [0] * 8 if case == "zero" else [1] + [0] * 7
        payload = {
            "pins": {"model_id": marker} if case == "pins" else adapter.PINS,
            "source_vectors": [vector],
            "target_vectors": [vector],
        }
        if case == "nonfinite":
            payload["source_vectors"][0][0] = float("nan")
            return httpx.Response(200, headers={"Content-Type": "application/json"}, content=json.dumps(payload))
        return httpx.Response(200, json=payload)

    monkeypatch.setattr(
        adapter, "AsyncClient", lambda **_kwargs: httpx.AsyncClient(transport=httpx.MockTransport(relay))
    )
    with pytest.raises(adapter.RetrievalArtifactError, match=reason) as failure:
        await adapter.produce_artifact("http://127.0.0.1:54500/model", corpus)
    assert marker not in str(failure.value) + caplog.text
