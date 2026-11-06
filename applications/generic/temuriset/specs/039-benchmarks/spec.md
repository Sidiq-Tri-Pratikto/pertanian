# Feature Specification: Performance benchmarks

**Feature Branch**: `039-benchmarks`
**Created**: 2026-11-05
**Status**: Local baseline measured. Standard-read misses tracked in [follow-up](standard-read-follow-up.md). Synthetic staging blocked pending an approved target.
**Milestone**: M11 Portability and operations
**Depends on**: 021, 037
**Size**: M
**Covers**: PRD section 18 targets (no FR or AC of its own)
**Flips**: none

## User Scenarios & Testing

### User Story 1 - Measure before optimizing (Priority: P1)

**Acceptance Scenarios**:

1. **Given** 1,000 published inventions, 100 active opportunities and 20 concurrent users on recorded hardware, **When** standard API reads run, **Then** p95 is measured against the 500 ms target and recorded with cache state.
2. **Given** the same dataset, **When** the authorized first discovery page loads, **Then** p95 is measured against 2 seconds.
3. **Given** a match run over the full catalog, **When** timed, **Then** candidate count and elapsed time are reported, and a job is used if it exceeds a request budget.

### Edge Cases

- Targets are hypotheses; a miss is reported, not hidden, and becomes a follow-up spec.

## Requirements

### Functional Requirements

- **FR-001**: A synthetic data generator MUST build the benchmark dataset through services, labelled as synthetic.
- **FR-002**: Results MUST record hardware, data size, concurrency and cache state.

## Success Criteria

### Measurable Outcomes

- **SC-001**: A benchmark report is committed to `docs/roadmap/benchmarks.md`.
