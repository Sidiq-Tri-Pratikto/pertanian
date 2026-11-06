# Feature Specification: Hybrid retrieval and reranking (gated)

**Feature Branch**: `045-hybrid-retrieval`
**Created**: 2026-11-05
**Status**: Local synthetic implementation planned, deployment gated
**Milestone**: M12 Gated adapters
**Depends on**: 019, 039
**Size**: L
**Covers**: FR11
**Flips**: Manifest adapters `dense-retrieval` and `reranker` become available for deployment after their individual quality and activation gates.

**Entry conditions**. The local implementation uses a committed synthetic judged corpus. Product-quality evaluation requires a permissioned labelled set with grouped splits, independent review and adjudication from PRD §20, plus a lexical quality baseline on that set. Spec 039 supplies a timing baseline.

## User Scenarios & Testing

### User Story 1 - Better candidates without weaker rules (Priority: P1)

An inventor can find useful targets through an experimental retrieval mode while retaining the same eligibility, readiness and factual evidence as the existing matcher.

**Acceptance Scenarios**.

1. **Given** a frozen grouped evaluation set, **when** lexical+rules, dense+rules, hybrid+rules and hybrid+rerank+rules are compared, **then** each mode reports candidate recall, returned precision, precision@5, nDCG@5, hard-rule violations, UNKNOWN correctness, factual source support, coverage and abstention, result counts, latency, cost status and manager exposure.
2. **Given** any mode, **when** a mandatory submission requirement fails, **then** the target is never returned as a positive match. UNKNOWN keeps its verification status, reason and action.
3. **Given** a configured synthetic run whose model outputs are missing, unavailable, invalid or incompatible with its inputs, **when** matching runs, **then** it returns the original lexical result and records the effective mode and safe fallback reason for the owner.
4. **Given** the default deployment or a source or catalog outside the synthetic fixture, **when** matching runs, **then** the original authorization and lexical behavior apply. The local model relay receives only curated synthetic fixture content.

## Requirements

- **FR-001**. Use actual BM25 for the hybrid lexical channel and normalized dense scores for the dense channel. Use one-based reciprocal rank fusion with k = 60, zero contribution from an absent channel, up to 50 candidates per channel and at most 30 reranked candidates. Apply versioned mode-specific admission thresholds and show up to five experimental results with deterministic ties.
- **FR-002**. Pin the profile, model identity and revision, tokenizer, truncation, input template and calibration per run. Record safe requested/effective mode and provenance on the owner-visible run. Keep requirement facts outside model input and score interpretation.
- **FR-003**. Keep the existing deterministic engine authoritative for requirement rows, eligibility, readiness, fit and factual explanation. Preserve the existing lexical baseline and its order. Apply the original access and visibility policies, including on replay and read.
- **FR-004**. Default to the lexical baseline. Explicitly fall back to it for unavailable or rejected experimental outputs and unsupported inputs. Validate the local model boundary and keep it outside matching's write transaction. Keep relay traffic limited to synthetic data.
- **FR-005**. Compare the four modes on the same versioned queries, judgments and target pool for each split. Keep related sources and opportunities together and freeze the thresholds before evaluating the held-out set. Report metric denominators and the provenance of labels and timing.
- **FR-006**. Require permissioned real cases, two independent human labels, preserved disagreements and adjudication, and reviewed evidence of gains and safety before selecting a production model or promoting its capability.

## Success Criteria

- **SC-001**. Promote a mode only after recording the reviewed, mode-specific gain over the labelled lexical baseline and satisfying the safety, privacy and staging gates in `docs/roadmap/benchmarks.md`.
- **SC-002**. The local benchmark reproduces results and reports zero known mandatory-rule violations. The local matching route exercises a successful synthetic experiment, transparent lexical fallback, authorization and exact replay while default configurations retain lexical behavior.
