# Feature Specification: Data rights

**Feature Branch**: `038-data-rights`
**Created**: 2026-10-30
**Status**: Seeded, not started
**Milestone**: M9 Saved service
**Depends on**: 026, 036, 037
**Size**: M
**Covers**: FR-16, AT-43, AT-44
**Flips**: none (with `akun`)

## User Scenarios & Testing

### User Story 1 - Take your data out (Priority: P1)

**Why this priority**: FR-16.

**Independent Test**: Export and reparse.

**Acceptance Scenarios**:

1. **Given** an export, **When** requested, **Then** an owner-only expiring file holds accepted measurements with units, intervals, UTC times, original timezone, provenance and scope.
2. **Given** an asset named `=HYPERLINK("x")`, **When** exported, **Then** the cell cannot execute as a formula (AT-44).

### User Story 2 - Delete deliberately (Priority: P1)

**Why this priority**: AT-43: reset, archive, unlink and delete stay distinct.

**Independent Test**: Delete a site.

**Acceptance Scenarios**:

1. **Given** deletion, **When** requested, **Then** the confirmation names the scope, user access ends at once, and purge status is visible.
2. **Given** retention, **When** read, **Then** configured periods are stated.
3. **Given** an export link issued before deletion, **When** the owner requests it after deletion is confirmed, **Then** no new download is authorized. The owner can still read the deletion status without reopening the site.

### Edge Cases

- Exports exclude tokens and credentials.
- Export size is bounded and rate limited.
- Configure and publish active-data and residual-backup windows. The proposed defaults are 30 days for active purge and a further 30 days for backup expiry.

## Requirements

### Functional Requirements

- **FR-001**: Routes MUST support PRD §16 exports and deletion, plus an owner-only status lookup for an accepted deletion.
- **FR-002**: Formula-leading cells MUST be neutralized.
- **FR-003**: Deletion MUST revoke site and export access in the same commit and record owner-only purge status independently of the site.

### Key Entities

- **Export**, **DeletionRequest**.

## Success Criteria

### Measurable Outcomes

- **SC-001**: An exported file reimports with zero new rows.
- **SC-002**: A foreign user cannot read an export link.
- **SC-003**: After deletion, a prior link fails, the owner can read purge status, and a foreign owner cannot infer whether the deleted site existed.
