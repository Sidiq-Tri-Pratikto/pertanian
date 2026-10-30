# Feature Specification: Benchmarks

**Feature Branch**: `041-benchmarks`
**Created**: 2026-10-30
**Status**: Seeded, not started
**Milestone**: M9 Saved service
**Depends on**: 039
**Size**: S
**Covers**: FR-07
**Flips**: none

## User Scenarios & Testing

### User Story 1 - Know the real limits (Priority: P1)

**Why this priority**: PRD §18 targets are proposals until measured, and compute-on-read depends on them.

**Independent Test**: Run the benchmark on the pilot host.

**Acceptance Scenarios**:

1. **Given** one site, 20 sources and 90 days at one minute, **When** summaries run, **Then** p95 is recorded against the 2-second target, naming hardware, concurrency and cold or warm state.
2. **Given** a 10 MiB, 150,000-row file, **When** imported, **Then** duration is recorded against the 60-second target.
3. **Given** a target is missed, **When** recorded, **Then** a follow-up spec is opened instead of adding rollups silently.

### Edge Cases

- Results never imply arbitrary industrial scale or an availability level.

## Requirements

### Functional Requirements

- **FR-001**: Benchmarks MUST be reproducible from the repository.
- **FR-002**: Results MUST be committed with environment details.

### Key Entities

None.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Each §18 target has a recorded measurement or a stated reason it was not run.
