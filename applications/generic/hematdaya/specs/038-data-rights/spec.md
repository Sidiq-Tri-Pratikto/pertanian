# Feature Specification: Data rights

**Feature Branch**: `038-data-rights`
**Created**: 2026-10-30
**Status**: Seeded, not started
**Milestone**: M9 Saved service
**Depends on**: 036
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

### Edge Cases

- Exports exclude tokens and credentials.
- Export size is bounded and rate limited.
- Purge within a proposed 30 days; backups expire within a further 30.

## Requirements

### Functional Requirements

- **FR-001**: Routes MUST match PRD §16 exports and deletion.
- **FR-002**: Formula-leading cells MUST be neutralized.
- **FR-003**: Deletion MUST revoke access immediately and record purge status.

### Key Entities

- **Export**, **DeletionRequest**.

## Success Criteria

### Measurable Outcomes

- **SC-001**: An exported file reimports with zero new rows.
- **SC-002**: A foreign user cannot read an export link.
