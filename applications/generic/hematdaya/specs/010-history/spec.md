# Feature Specification: History buckets

**Feature Branch**: `010-history`
**Created**: 2026-10-30
**Status**: Seeded, not started
**Milestone**: M1 Energy core
**Depends on**: 009
**Size**: M
**Covers**: FR-07
**Flips**: none

## User Scenarios & Testing

### User Story 1 - History that matches the summary (Priority: P1)

**Why this priority**: Charts and totals must reconcile (UX-14). Same intervals, same selection, same timezone.

**Independent Test**: Sum daily buckets and compare with the summary.

**Acceptance Scenarios**:

1. **Given** 19–25 Oktober, **When** daily buckets are read for Kulkas, **Then** seven buckets of `1.200` kWh sum to the summary's `8.400` kWh.
2. **Given** one day, **When** hourly buckets are read, **Then** 24 buckets return.

### User Story 2 - Gaps stay gaps (Priority: P1)

**Why this priority**: A missing bucket must never look like zero (PRD §11, UX-13).

**Independent Test**: Learning-partial scenario.

**Acceptance Scenarios**:

1. **Given** no readings for a bucket, **When** read, **Then** its value is `null` with `state: "missing"`.
2. **Given** a measured zero, **When** read, **Then** the value is `"0.000"` with `state: "measured"`.
3. **Given** a partly covered bucket, **When** read, **Then** it reports its recorded value, coverage and `state: "partial"`.
4. **Given** a bucket after now, **When** read, **Then** `state: "future"`.

### Edge Cases

- A request above 1,000 buckets is refused with a field message.
- Hourly data never appears as minute data.

## Requirements

### Functional Requirements

- **FR-001**: The API MUST return day or hour buckets in local time with UTC bounds.
- **FR-002**: Responses MUST be limited to 1,000 buckets per series.
- **FR-003**: Each bucket MUST carry state and coverage.
- **FR-004**: Provenance MUST be returned with the series.

### Key Entities

- **HistoryBucket**: start, end, label date or hour, `energy_kwh`, state, coverage.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Bucket sums equal the summary in every fixture test.
- **SC-002**: No code path fills or interpolates a missing bucket.
