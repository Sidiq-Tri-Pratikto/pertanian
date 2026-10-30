# Feature Specification: Matched baseline

**Feature Branch**: `020-baseline`
**Created**: 2026-10-30
**Status**: Seeded, not started
**Milestone**: M4 Evidence
**Depends on**: 010
**Size**: M
**Covers**: FR-12, AT-16, AT-19, AT-20, AT-21
**Flips**: none

## User Scenarios & Testing

### User Story 1 - Compare only what is comparable (Priority: P1)

**Why this priority**: A partial total against a full total is a false finding (PRD §11.6).

**Independent Test**: Port the comparison tests.

**Acceptance Scenarios**:

1. **Given** a complete week and three complete prior weeks, **When** compared, **Then** the result holds each window's energy on the common mask, the median, MAD, resolution and coverage.
2. **Given** a current period still running, **When** compared, **Then** prior windows use the same elapsed duration.
3. **Given** only one eligible prior window, **When** compared, **Then** the state is `learning` with the reason, and measured totals stay.
4. **Given** coverage under 90% in the current window, **When** compared, **Then** the state is `not_comparable`.
5. **Given** a common mask under 90%, **When** compared, **Then** the comparison is suppressed.

### User Story 2 - Never call silence "normal" (Priority: P1)

**Why this priority**: FR-12: no verdict from a missing baseline.

**Independent Test**: Learning scenario.

**Acceptance Scenarios**:

1. **Given** no comparison, **When** the state is read, **Then** it says comparison unavailable, distinct from "no eligible change".
2. **Given** unknown resolution, **When** compared, **Then** a descriptive comparison returns and automatic alerts stay off.
3. **Given** a zero baseline, **When** compared, **Then** absolute change returns and percent is `null`.

### Edge Cases

- Periods longer than seven days are not compared.
- An asset with an unresolved source conflict is not compared.
- Full recorded totals stay separate from common-mask totals.

## Requirements

### Functional Requirements

- **FR-001**: The baseline MUST use the same local weekday and time in the previous three weeks, at least two eligible.
- **FR-002**: Each window MUST have at least 90% coverage, and the common mask at least 90%.
- **FR-003**: `B` MUST be the median of eligible windows on the common mask.
- **FR-004**: States MUST be `comparable`, `learning`, `not_comparable`, `descriptive`, `unavailable`.
- **FR-005**: History MUST gain a reference series when two or more windows are eligible.

### Key Entities

- **Comparison**: state, reason, current, historical windows, median, MAD, resolution, mask coverage.

## Success Criteria

### Measurable Outcomes

- **SC-001**: AT-16, AT-19, AT-20 and AT-21 ported tests pass.
- **SC-002**: Common-mask arithmetic is integer mWh, with no float in any comparison path.
