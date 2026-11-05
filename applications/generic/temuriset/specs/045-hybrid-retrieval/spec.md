# Feature Specification: Hybrid retrieval and reranking (gated)

**Feature Branch**: `045-hybrid-retrieval`
**Created**: 2026-11-05
**Status**: Seeded, not started; gated
**Milestone**: M12 Gated adapters
**Depends on**: 019, 039
**Size**: L
**Covers**: FR11
**Flips**: manifest adapters `dense-retrieval` and `reranker` → `available` only if the benchmark shows a gain

**Entry condition**: a labelled evaluation set from PRD section 20 with grouped splits, and a lexical baseline result to beat.

## User Scenarios & Testing

### User Story 1 - Better candidates without weaker rules (Priority: P1)

**Acceptance Scenarios**:

1. **Given** the evaluation set, **When** lexical+rules, dense+rules, hybrid+rules and reranked runs are compared, **Then** candidate recall, precision, nDCG@5, known hard-rule violations and abstention are reported per mode.
2. **Given** any mode, **When** a mandatory requirement fails, **Then** the target is never shown as a positive match.
3. **Given** a model outage, **When** matching runs, **Then** it falls back explicitly to lexical rules and says so in the run record.

## Requirements

### Functional Requirements

- **FR-001**: RRF with k = 60 MUST combine ranks, not raw scores; at most 50 + 50 candidates and 30 reranked.
- **FR-002**: Model identity, revision, tokenizer and truncation MUST be pinned per run.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The mode is enabled only when its measured gain over the baseline is recorded in `docs/roadmap/benchmarks.md`.
