# Feature Specification: Backup, restore and migration safety

**Feature Branch**: `038-backup-restore`
**Created**: 2026-11-05
**Status**: Final integrated local Compose recovery and stacked PR-base compatibility passed at Alembic 0015. The earlier M7-to-0014 comparison remains blocked by the old erasure worker. Actual staging and trusted previous-release evidence remain open.
**Milestone**: M11 Portability and operations
**Depends on**: 037
**Size**: M
**Covers**: FR24, AC71, AC72
**Flips**: none

## User Scenarios & Testing

### User Story 1 - Restore is a rehearsed procedure (Priority: P1)

**Acceptance Scenarios**:

1. **Given** a staging database and object store, **When** the restore drill runs, **Then** data and files return to a recorded point, and the measured recovery point and time are written to the runbook.
2. **Given** a schema change deployed while old code still runs, **When** checked, **Then** expand and migrate steps keep both versions working, and the contract step waits for retirement (AC71).
3. **Given** a migration that code rollback cannot undo, **When** documented, **Then** the forward-repair or restore procedure and data-loss window are tested (AC72).

## Requirements

### Functional Requirements

- **FR-001**: Backups MUST cover Postgres and the object store with retention and encryption at rest.
- **FR-002**: A CI check MUST run the newest migration against the previous release's code for expand-phase compatibility.

## Success Criteria

### Measurable Outcomes

- **SC-001**: One restore drill recorded with timings before any real pilot data.
