# Implementation Plan: Hybrid retrieval and reranking (gated)

**Branch**: `045-hybrid-retrieval` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

## Task Outline

1. Evaluation harness with grouped splits.
2. Dense index (pgvector) and multilingual embeddings behind an adapter.
3. RRF fusion and bounded reranking.
4. Comparison report; enable only on measured gain.
