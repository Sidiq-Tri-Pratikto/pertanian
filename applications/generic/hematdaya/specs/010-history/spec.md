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
2. **Given** one local day, **When** hourly buckets are read, **Then** the buckets cover the actual duration between the local date boundaries. Jakarta's ordinary day has 24 buckets. A day with a one-hour DST transition has 23 or 25, with unique UTC bounds and offsets for any repeated local hour.
3. **Given** complete measured buckets, **When** the series is read, **Then** the service identifies the highest one, with earliest UTC start breaking a tie. If there is no eligible bucket the result is null.

### User Story 2 - Gaps stay gaps (Priority: P1)

**Why this priority**: A missing bucket must never look like zero (PRD §11, UX-13).

**Independent Test**: Learning-partial scenario.

**Acceptance Scenarios**:

1. **Given** no readings for a bucket, **When** read, **Then** its value is `null` with `state: "missing"`.
2. **Given** a measured zero, **When** read, **Then** the value is `"0.000"` with `state: "measured"`.
3. **Given** a partly covered bucket, **When** read, **Then** it reports its recorded value, coverage and `state: "partial"`.
4. **Given** a bucket after now, **When** read, **Then** `state: "future"`.
5. **Given** unresolved source authority or a long counter delta that cannot be allocated to a bucket, **When** read, **Then** the affected value is null with the appropriate reason, and the series never manufactures measured detail.

### Edge Cases

- A request above 1,000 buckets is refused with a field message.
- Hourly data never appears as minute data.

## Requirements

### Functional Requirements

- **FR-001**: The API MUST return day or hour buckets in local time with UTC bounds.
- **FR-002**: Responses MUST be limited to 1,000 buckets per series.
- **FR-003**: Each bucket MUST carry state and coverage.
- **FR-004**: Provenance MUST be returned with the series.
- **FR-005**: Use the same scope, binding, interval and coverage rules as 009. Return `highest_bucket` from the service so clients can render the summary without calculating it.

### Key Entities

- **HistoryBucket**: start, end, label date or hour, `energy_kwh`, state, coverage.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Where intervals are eligible for the selected granularity, bucket sums equal the summary. When a coarser total contains unallocatable energy, report that limit and keep the affected bucket values unavailable.
- **SC-002**: No code path fills or interpolates a missing bucket.
