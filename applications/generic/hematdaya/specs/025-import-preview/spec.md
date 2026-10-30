# Feature Specification: Import preview

**Feature Branch**: `025-import-preview`
**Created**: 2026-10-30
**Status**: Seeded, not started
**Milestone**: M5 CSV
**Depends on**: 024
**Size**: M
**Covers**: FR-06, AT-30, AT-32, AT-33
**Flips**: none

## User Scenarios & Testing

### User Story 1 - See the result before anything is saved (Priority: P1)

**Why this priority**: PRD §10.2: parse, map, validate and preview before commit.

**Independent Test**: Preview leaves `measurements` unchanged.

**Acceptance Scenarios**:

1. **Given** a parsed file and mapping, **When** previewed, **Then** counts reconcile: accepted unique + invalid + exact duplicate + conflicting = all nonblank data rows.
2. **Given** 2 of 10 rows invalid, **When** previewed, **Then** eight rows can import only after explicit acknowledgment.
3. **Given** 3 of 10 invalid, **When** previewed, **Then** commit is blocked with `Impor diblokir: 3 dari 10 baris tidak valid.`

### User Story 2 - Conflicts and duplicates (Priority: P1)

**Why this priority**: The same interval with different values must never be picked silently.

**Independent Test**: Duplicate and conflict rows.

**Acceptance Scenarios**:

1. **Given** identical repeated rows, **When** previewed, **Then** one is accepted and the rest count as duplicates.
2. **Given** different values for one source and interval, **When** previewed, **Then** they are conflicts and block commit even if the invalid share is low.
3. **Given** a reimport of a committed file, **When** previewed, **Then** rows are exact duplicates and none are new.

### User Story 3 - Map by identity, not name (Priority: P1)

**Why this priority**: Two assets may share a name (PRD §5.1).

**Independent Test**: Two "Kulkas" assets.

**Acceptance Scenarios**:

1. **Given** two assets with one name, **When** mapped, **Then** the user must pick with location, type and ID context.
2. **Given** a target asset with another source, **When** mapped, **Then** preview requires an explicit choice and never adds them.
3. **Given** unknown overlap with existing loads, **When** confirmed as unknown, **Then** the import proceeds and totals are refused until scope is resolved.

### Edge Cases

- A preview survives a restart: it lives in Postgres.
- Skipped invalid rows cannot waive structural, meaning or scope conflicts.
- Stale previews are rejected at commit if stored data changed.

## Requirements

### Functional Requirements

- **FR-001**: Previews MUST be stored with mapping, counts, assumptions and row results.
- **FR-002**: The invalid share MUST use all nonblank data rows as denominator; up to and including 20% may proceed.
- **FR-003**: Limits MUST be enforced server-side.
- **FR-004**: Preview MUST NOT change measurements.
- **FR-005**: Assumptions MUST be listed before confirmation.

### Key Entities

- **Import**, **ImportRow**.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Counts reconcile in every test.
- **SC-002**: AT-30 and AT-33 thresholds pass exactly.
