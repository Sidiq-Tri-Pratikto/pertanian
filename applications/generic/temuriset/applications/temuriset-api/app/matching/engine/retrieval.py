"""Pure, bounded candidate ranking for the synthetic retrieval experiment."""

import math
import re
import unicodedata
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal

RetrievalMode = Literal["dense", "hybrid", "reranked"]
CHANNEL_LIMIT = 50
RERANK_LIMIT = 30
RRF_K = 60
DENSE_MIN = 0.65
HYBRID_MIN = 0.55
RERANK_MIN = 0.60
_BM25_K1 = 1.2
_BM25_B = 0.75
_WORDS = re.compile(r"[^\W_]+", re.UNICODE)


@dataclass(frozen=True, slots=True)
class RetrievalSelection:
    """Version keys in pre-admission and admitted order."""

    candidates: tuple[str, ...]
    admitted: tuple[str, ...]


def _tokens(text: str) -> list[str]:
    return _WORDS.findall(unicodedata.normalize("NFKC", text).casefold())


def bm25(query: str, documents: Mapping[str, str]) -> dict[str, float]:
    """Score documents with positive BM25 evidence on case-folded Unicode words."""
    query_terms = sorted(set(_tokens(query)))
    counts = {key: Counter(_tokens(text)) for key, text in documents.items()}
    lengths = {key: sum(terms.values()) for key, terms in counts.items()}
    average_length = sum(lengths.values()) / len(lengths) if lengths else 0.0
    if not query_terms or not average_length:
        return {}
    total = len(counts)
    scores = dict.fromkeys(counts, 0.0)
    for term in query_terms:
        document_frequency = sum(term in terms for terms in counts.values())
        idf = math.log1p((total - document_frequency + 0.5) / (document_frequency + 0.5))
        for key, terms in counts.items():
            frequency = terms[term]
            if frequency:
                length_penalty = 1 - _BM25_B + _BM25_B * lengths[key] / average_length
                scores[key] += idf * frequency * (_BM25_K1 + 1) / (frequency + _BM25_K1 * length_penalty)
    return {key: score for key, score in scores.items() if score > 0}


def _ordered(scores: Mapping[str, float]) -> tuple[str, ...]:
    return tuple(sorted(scores, key=lambda key: (-scores[key], key)))


def reciprocal_rank_fusion(lexical: tuple[str, ...], dense: tuple[str, ...]) -> tuple[str, ...]:
    """Fuse bounded one-based ranks. Missing keys contribute zero."""
    scores: dict[str, float] = {}
    for channel in (lexical, dense):
        for position, key in enumerate(channel[:CHANNEL_LIMIT], start=1):
            scores[key] = scores.get(key, 0) + 1 / (RRF_K + position)
    return _ordered(scores)


def retrieve(
    mode: RetrievalMode,
    query: str,
    documents: Mapping[str, str],
    source_vector: tuple[float, ...],
    target_vectors: Mapping[str, tuple[float, ...]],
    rerank_scores: Mapping[str, float],
) -> RetrievalSelection:
    """Use validated, normalized vectors and score only the supplied catalog."""
    dense_scores = {
        key: math.fsum(a * b for a, b in zip(source_vector, target_vectors[key], strict=True)) for key in documents
    }
    dense = _ordered({key: score for key, score in dense_scores.items() if score > 0})[:CHANNEL_LIMIT]
    if mode == "dense":
        return RetrievalSelection(dense, tuple(key for key in dense if dense_scores[key] >= DENSE_MIN))

    lexical = _ordered(bm25(query, documents))[:CHANNEL_LIMIT]
    fused = reciprocal_rank_fusion(lexical, dense)
    lexical_keys = set(lexical)
    admitted = {key for key in fused if key in lexical_keys or dense_scores[key] >= HYBRID_MIN}
    if mode == "hybrid":
        return RetrievalSelection(fused, tuple(key for key in fused if key in admitted))

    head = fused[:RERANK_LIMIT]
    # Python sort is stable. Equal reranker scores retain the previous fusion order.
    reranked = tuple(sorted(head, key=lambda key: -rerank_scores[key]))
    admitted.difference_update(key for key in head if rerank_scores[key] < RERANK_MIN)
    order = reranked + fused[RERANK_LIMIT:]
    return RetrievalSelection(order, tuple(key for key in order if key in admitted))
