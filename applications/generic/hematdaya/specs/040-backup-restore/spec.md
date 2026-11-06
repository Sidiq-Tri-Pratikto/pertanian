# Feature Specification: Backup and restore

**Feature Branch**: `040-backup-restore`
**Created**: 2026-10-30
**Status**: Seeded, not started
**Milestone**: M9 Saved service
**Depends on**: 026, 038, 039
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
3. **Given** a retained snapshot predating a site deletion, **When** restored, **Then** the deletion is reconciled before traffic opens, and neither the site nor its exports become readable again.

### Edge Cases

- Encrypt backups in transit and at rest, keep credentials out of the archive and record expiry according to 038's configured retention.
- If the deletion ledger is unavailable or cannot be reconciled, keep the restore isolated.

## Requirements

### Functional Requirements

- **FR-001**: Backups MUST run on a schedule and be stored off the host.
- **FR-002**: Restore MUST be a documented, rehearsed procedure.
- **FR-003**: A reconciliation script MUST compare summaries against raw rows.
- **FR-004**: Restore MUST apply deletion markers from outside the restored database before the recovered API serves traffic.

### Key Entities

None.

## Success Criteria

### Measurable Outcomes

- **SC-001**: A rehearsal is recorded with date, size and duration.
- **SC-002**: A snapshot taken before deletion restores with reconciled totals for retained sites and no restored access to the deleted site or its exports.
