# Feature Specification: Scope API

**Feature Branch**: `028-scope-api`
**Created**: 2026-10-30
**Status**: Seeded, not started
**Milestone**: M6 Scope
**Depends on**: 009
**Size**: M
**Covers**: FR-09, AT-35, AT-36
**Flips**: none

## User Scenarios & Testing

### User Story 1 - Save a valid selection (Priority: P1)

**Why this priority**: P09: a conflict is visible and no double-counted total shows.

**Independent Test**: Selection endpoints with the scope scenario.

**Acceptance Scenarios**:

1. **Given** Meter utama and its children, **When** a selection holds both, **Then** the save is refused, naming the overlap.
2. **Given** Meter utama alone, **When** saved, **Then** summaries use 10 kWh for 25 Oktober.
3. **Given** the children alone, **When** saved, **Then** summaries sum them and the unmeasured remainder stays unnamed.

### User Story 2 - Choose the source of truth (Priority: P1)

**Why this priority**: AT-35: 2 kWh never becomes 4.

**Independent Test**: Resolve a two-source asset.

**Acceptance Scenarios**:

1. **Given** two sources for Kulkas, **When** one is chosen with an effective time, **Then** bindings update, history stays, and the value is 2 kWh for 24–25 Oktober, never 4.
2. **Given** skipping the new source, **When** saved, **Then** the old source stays authoritative.

### User Story 3 - Unknown overlap needs a person (Priority: P1)

**Why this priority**: PRD §5.2 rule 3.

**Independent Test**: Confirm disjoint.

**Acceptance Scenarios**:

1. **Given** unknown overlap, **When** the user confirms the loads are separate, **Then** the relation is removed and the sum is allowed.
2. **Given** a main meter goes stale, **When** read, **Then** the selection does not switch silently to children.

### Edge Cases

- Child percentages use the parent only when intervals and coverage are comparable.
- A failed save leaves the confirmed selection in force.

## Requirements

### Functional Requirements

- **FR-001**: The API MUST expose `GET` and `PUT /sites/{id}/aggregation-selection`.
- **FR-002**: `PUT` MUST validate relations and source conflicts at the service.
- **FR-003**: Every selection change MUST be versioned and audited.

### Key Entities

- **AggregationSelection**: site, assets, revision.

## Success Criteria

### Measurable Outcomes

- **SC-001**: No test path produces 11 or 4 in the overlap fixtures.
