# Feature Specification: Scope API

**Feature Branch**: `028-scope-api`
**Created**: 2026-10-30
**Status**: Implemented and verified locally
**Milestone**: M6 Scope
**Depends on**: 009
**Size**: M
**Covers**: FR-09, AT-35, AT-36, AT-36b
**Flips**: none

## User Scenarios & Testing

### User Story 1 - Save a valid selection (Priority: P1)

**Why this priority**: P09: a conflict is visible and no double-counted total shows.

**Independent Test**: Selection endpoints with the scope scenario.

**Acceptance Scenarios**:

1. **Given** Meter utama and its children, **When** a selection holds both, **Then** the save is refused, naming the overlap.
2. **Given** Meter utama alone, **When** saved, **Then** summaries use 10 kWh for 25 Oktober.
3. **Given** the children alone, **When** saved, **Then** summaries sum them and the unmeasured remainder stays unnamed.
4. **Given** a draft selection with proposed authority or disjoint confirmations, **When** previewed, **Then** the service returns the proposed result and its validity with its resolved period and both revisions, without changing any selection, binding, relation, or audit record.
5. **Given** two selected assets use the same source over an overlapping interval, **When** scope is evaluated, **Then** the service names the affected pair and refuses their combined total even if the loads have a disjoint relation. Adjacent authority intervals are allowed when the other validity rules pass.

### User Story 2 - Choose the source of truth (Priority: P1)

**Why this priority**: AT-35: 2 kWh never becomes 4.

**Independent Test**: Resolve a two-source asset.

**Acceptance Scenarios**:

1. **Given** two sources for Kulkas, **When** one is chosen with an effective time, **Then** bindings update only within the affected interval, earlier attribution and readings stay, and the value is 2 kWh for 24–25 Oktober, never 4.
2. **Given** skipping the new source, **When** saved, **Then** the old source stays authoritative.

### User Story 3 - Unknown overlap needs a person (Priority: P1)

**Why this priority**: PRD §5.2 rule 3.

**Independent Test**: Confirm disjoint.

**Acceptance Scenarios**:

1. **Given** unknown overlap, **When** the user confirms the loads are separate, **Then** the unknown-overlap relation is replaced with positive disjoint evidence and the sum is allowed when the remaining validity checks pass.
2. **Given** a main meter goes stale, **When** read, **Then** the selection does not switch silently to children.

### Edge Cases

- Child percentages use the parent only when intervals and coverage are comparable.
- A failed save leaves the confirmed selection, bindings, relations, revisions, and audit in force. A changed selection revision, binding revision, or resolved local period requires a new preview.
- A saved asset stays in the membership when archived and is excluded from totals with its reason. Saving a selection cannot add an already archived asset or silently substitute another asset.

## Requirements

### Functional Requirements

- **FR-001**: The API MUST expose `GET` and `PUT /sites/{id}/aggregation-selection` and a read-only preview of the complete proposal. The confirmed reads MUST expose raw membership and independent selection and binding revisions. Preview MUST expose the resolved summary, candidate bindings, and the revisions it used. The site summary MUST carry the scope revisions from the state that produced its totals.
- **FR-002**: `PUT` MUST verify both expected revisions and the preview's resolved timezone and local dates. It MUST revalidate the proposal and apply selection, authority, disjoint confirmations, and audit in one transaction. GET, preview, PUT, and site summary MUST refuse an overlapping use of one source across selected assets, even with positive disjointness.
- **FR-003**: Every committed selection, authority, or disjoint confirmation change MUST be versioned and audited. Authority events MUST record the effective time and affected interval. Selection and disjoint changes apply site-wide and MUST distinguish the reviewed period from their effect.

### Key Entities

- **AggregationSelection**: site, assets, revision.

## Success Criteria

### Measurable Outcomes

- **SC-001**: No test path produces 11 or 4 in the overlap fixtures. Shared-source overlap is refused with the pair identified, while adjacent intervals with proven disjointness can be summed.
- **SC-002**: Preview leaves persisted state intact. A failed, stale, or concurrently superseded confirmation leaves every pending change rolled back, including audit and revision increments.

## Verification

- PostgreSQL 16.11 UTF8 passed the populated upgrade from Alembic 0009 to 0010, the downgrade and re-upgrade, and the single-head check at 0010.
- API `make check` passed 1,078 tests with 99.12% coverage. Eight opt-in integration performance cases were skipped. The focused `core-only` run passed 198 tests.
- Mobile lint, type checking, and 545 tests passed with 92.79% line coverage. Android, iOS, and web exports passed. Repeat generation produced byte-identical OpenAPI and TypeScript contracts.
- The PostgreSQL 17 GitHub CI result is pending release approval.
