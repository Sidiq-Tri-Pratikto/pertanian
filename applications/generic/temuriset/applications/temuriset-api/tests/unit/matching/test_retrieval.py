"""Deterministic candidate ranking for Spec 045."""

from dataclasses import replace

import pytest

from app.matching.engine.evaluate import evaluate, rank_experiment
from app.matching.engine.retrieval import bm25, reciprocal_rank_fusion, retrieve
from tests.unit.matching.builders import support, target


def test_bm25_counts_unicode_terms_with_length_and_inverse_document_frequency() -> None:
    """
    Condition:
    - Two documents contain the same Unicode term at different frequencies and lengths.

    Expected:
    - The case-folded term retrieves both; the compact repeated term ranks first.
    """
    scores = bm25("PÖMPA", {"short": "pömpa pömpa", "long": "pömpa " + "air " * 15, "other": "komunitas"})
    assert scores["short"] > scores["long"] > 0
    assert "other" not in scores


def test_rrf_uses_one_based_positions_and_deterministic_ties() -> None:
    """
    Condition:
    - Two channels disagree and one candidate occurs in both.

    Expected:
    - The shared candidate wins; equal single-channel ranks break by key.
    """
    assert reciprocal_rank_fusion(("b", "shared"), ("a", "shared")) == ("shared", "a", "b")


def test_separate_relevance_thresholds_and_rerank_tail_are_bounded() -> None:
    """
    Condition:
    - Sixty identical dense candidates and one lexical-only candidate share one query.

    Expected:
    - Dense and BM25 channels are capped independently; reranking changes only the first thirty.
    """
    documents = {f"k{position:02}": "nomatch" for position in range(60)} | {"lexical": "air"}
    vectors = {key: (1.0, 0.0) for key in documents} | {"lexical": (0.0, 1.0)}
    scores = dict.fromkeys(documents, 0.0)
    dense = retrieve("dense", "air", documents, (1.0, 0.0), vectors, scores)
    hybrid = retrieve("hybrid", "air", documents, (1.0, 0.0), vectors, scores)
    reranked = retrieve("reranked", "air", documents, (1.0, 0.0), vectors, scores)
    assert len(dense.candidates) == len(dense.admitted) == 50
    assert len(hybrid.candidates) == len(hybrid.admitted) == 51
    assert "lexical" in hybrid.admitted
    assert reranked.candidates[30:] == hybrid.candidates[30:]
    assert reranked.admitted == hybrid.admitted[30:]


def test_retrieval_admission_keeps_exact_fit_and_hard_rules() -> None:
    """
    Condition:
    - An experimental candidate has no lexical overlap and fails a mandatory submission requirement.

    Expected:
    - Retrieval may clear the relevance abstention but cannot affect fit, requirement evidence or positive placement.
    """
    source = support("F03", keywords=())
    mandate = target("D1")
    baseline = evaluate(source, mandate)
    experimental = evaluate(source, mandate, retrieval_evidence=True)
    assert baseline["relevant"] is False and experimental["relevant"] is True
    for key in ("fit", "rows", "reasons", "readiness", "eligibility"):
        assert experimental[key] == baseline[key]
    assert rank_experiment([experimental], (mandate.version_id,)) == ([], [experimental])


@pytest.mark.parametrize("mode", ["dense", "hybrid", "reranked"])
def test_an_empty_evidence_pool_abstains(mode: str) -> None:
    """
    Condition:
    - The candidate is orthogonal and the query has no matching word.

    Expected:
    - No score admits the candidate.
    """
    assert retrieve(mode, "air", {"d": "surya"}, (1.0, 0.0), {"d": (0.0, 1.0)}, {"d": 1.0}).admitted == ()


def test_experimental_display_cap_does_not_label_valid_tail_as_incompatible() -> None:
    """
    Condition:
    - Seven equally eligible and relevant targets arrive in the experimental ranking.

    Expected:
    - Five results are shown in experiment order and the valid tail is not listed as an exclusion.
    """
    keys = tuple(str(index) for index in reversed(range(7)))
    results = [
        evaluate(support("F01"), replace(target("A1"), version_id=key, opportunity_id=key), retrieval_evidence=True)
        for key in keys
    ]
    shown, excluded = rank_experiment(results, keys)
    assert [result["opportunity_version_id"] for result in shown] == list(keys[:5])
    assert excluded == []
