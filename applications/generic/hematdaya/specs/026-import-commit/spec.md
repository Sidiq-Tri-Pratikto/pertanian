# Feature Specification: Import commit

**Feature Branch**: `026-import-commit`
**Created**: 2026-10-30
**Status**: Seeded, not started
**Milestone**: M5 CSV
**Depends on**: 025
**Size**: M
**Covers**: FR-06, FR-19, AT-33, AT-34, AT-37
**Flips**: manifest adapter `csv` → `available`

## User Scenarios & Testing

### User Story 1 - All or nothing (Priority: P1)

**Why this priority**: FR-06: no bad upload can erase earlier data.

**Independent Test**: Fail mid-commit; nothing changed.

**Acceptance Scenarios**:

1. **Given** a valid preview, **When** committed, **Then** all accepted rows, new assets, sources and bindings appear in one transaction.
2. **Given** a failure during commit, **When** it rolls back, **Then** no row or asset remains, and the preview stays usable.

### User Story 2 - Retry is safe (Priority: P1)

**Why this priority**: AT-34.

**Independent Test**: Commit twice with one key.

**Acceptance Scenarios**:

1. **Given** a committed import, **When** commit is repeated, **Then** the first result returns and no reading is added.
2. **Given** a connection lost after commit, **When** the client reads status, **Then** it finds the committed result.
3. **Given** a blocked preview, **When** commit is called anyway, **Then** the service refuses.

### User Story 3 - The result is exact (Priority: P1)

**Why this priority**: Users must see what actually happened.

**Independent Test**: Compare counts with database rows.

**Acceptance Scenarios**:

1. **Given** a commit, **When** it succeeds, **Then** the result lists rows added, skipped, duplicated, assets mapped and created, and periods affected.
2. **Given** a late import over an existing period, **When** committed, **Then** affected insights get new revisions and an audit event names the range.

### Edge Cases

- A preview gone stale because stored data changed is refused with a re-preview message.
- Counter imports store deltas, and a reset interval has no energy.
- Imported data is `Data historis · Impor CSV`, never a disconnected live meter.

## Requirements

### Functional Requirements

- **FR-001**: Commit MUST be one transaction through `IngestService`.
- **FR-002**: Commit MUST be idempotent through `imports.status` and unique measurement identity.
- **FR-003**: `GET /imports/{id}` MUST report status beyond any client timeout.
- **FR-004**: Commit MUST write one audit event.

### Key Entities

Import from 025.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Concurrent double commit produces one result, proven by an integration test.
- **SC-002**: A 150,000-row commit finishes within target or reports recoverable status; result recorded.
