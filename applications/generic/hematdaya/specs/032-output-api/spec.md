# Feature Specification: Output metric API

**Feature Branch**: `032-output-api`
**Created**: 2026-10-30
**Status**: Seeded, not started
**Milestone**: M7 Optional analysis
**Depends on**: 011, 021
**Size**: M
**Covers**: FR-11, AT-22, AT-23, AT-24, AT-25
**Flips**: manifest capability `output` → `available`

## User Scenarios & Testing

### User Story 1 - Valid intensity (Priority: P1)

**Why this priority**: Workshop owners ask "did energy per batch change?", but only on request.

**Independent Test**: `i-optional`.

**Acceptance Scenarios**:

1. **Given** 144 kWh and 2,880 units for one week, **When** computed, **Then** `0.050` kWh/unit with numerator, denominator, unit, period and method.
2. **Given** the metric is disabled, **When** summaries run, **Then** totals, rankings and advice are unchanged.

### User Story 2 - Never a fake number (Priority: P1)

**Why this priority**: AT-23.

**Independent Test**: Invalid denominators.

**Acceptance Scenarios**:

1. **Given** zero output with energy, **When** computed, **Then** no value and "Tidak dapat dihitung: keluaran nol".
2. **Given** missing, negative or non-finite output, **When** computed, **Then** no value and a correction message.
3. **Given** different units or product meaning, **When** compared, **Then** comparison is withheld (AT-25).

### User Story 3 - Honest estimates (Priority: P1)

**Why this priority**: AT-24: no calendar-time prorating of production.

**Independent Test**: `i-current`.

**Acceptance Scenarios**:

1. **Given** an average per output day during a running period, **When** computed without confirmation, **Then** only complete eligible days count, for both energy and output.
2. **Given** declared output windows and confirmed uniform output, **When** computed, **Then** the elapsed fraction applies and the result is labelled an estimate.
3. **Given** batch output, **When** computed, **Then** it is never assumed uniform.

### Edge Cases

- A partial numerator gives provisional recorded-energy-per-output, with no efficiency-change claim.
- Area metrics use kWh/m² and never mix with production output.
- A numerator with overlapping assets is refused.

## Requirements

### Functional Requirements

- **FR-001**: One metric per site in v1, enabled only on request.
- **FR-002**: Actual output MUST match the exact period.
- **FR-003**: Estimated results MUST be labelled "Estimasi energi per …".
- **FR-004**: An intensity insight MUST compare only compatible complete periods with one method.

### Key Entities

- **OutputMetric**, **OutputInput**.

## Success Criteria

### Measurable Outcomes

- **SC-001**: AT-22 to AT-25 pass with exact numbers.
- **SC-002**: No code path divides by zero or returns infinity.
