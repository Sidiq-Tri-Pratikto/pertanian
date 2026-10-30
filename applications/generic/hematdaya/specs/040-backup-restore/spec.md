# Feature Specification: Backup and restore

**Feature Branch**: `040-backup-restore`
**Created**: 2026-10-30
**Status**: Seeded, not started
**Milestone**: M9 Saved service
**Depends on**: 039
**Size**: M
**Covers**: AT-50
**Flips**: none

## User Scenarios & Testing

### User Story 1 - A restore that was actually tested (Priority: P1)

**Why this priority**: PRD §17: a backup job's success message is not a restore test.

**Independent Test**: Restore to a clean database and compare.

**Acceptance Scenarios**:

1. **Given** a backup, **When** restored to a clean database, **Then** totals reconcile against raw readings for H, I and an imported file.
2. **Given** a replay of the same import, **When** run, **Then** totals do not change.

### Edge Cases

- Backups never contain plaintext secrets beyond what the database holds; tokens are hashed.
- A deleted site stays gone after retention expiry, per the stated window.

## Requirements

### Functional Requirements

- **FR-001**: Backups MUST run on a schedule and be stored off the host.
- **FR-002**: Restore MUST be a documented, rehearsed procedure.
- **FR-003**: A reconciliation script MUST compare summaries against raw rows.

### Key Entities

None.

## Success Criteria

### Measurable Outcomes

- **SC-001**: A rehearsal is recorded with date, size and duration.
