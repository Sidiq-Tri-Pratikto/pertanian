# Feature Specification: History chart

**Feature Branch**: `015-history-chart`
**Created**: 2026-10-30
**Status**: Seeded, not started
**Milestone**: M2 Read journey on phone
**Depends on**: 014
**Size**: M
**Covers**: UX-13, UX-18, AT-56, S06
**Flips**: registry `detail-perangkat` → `available` (with 016)

## User Scenarios & Testing

### User Story 1 - Read history without relying on the picture (Priority: P1)

**Why this priority**: AT-56: text and data alternatives must answer the task by touch, keyboard and screen reader.

**Independent Test**: Answer "which day was highest?" from the summary text alone.

**Acceptance Scenarios**:

1. **Given** a week, **When** Lihat riwayat is pressed, **Then** seven daily bars show on a zero baseline with unit, period, timezone and a text summary.
2. **Given** Lihat data, **When** opened, **Then** a table shows the same values, and rows stack on narrow screens.

### User Story 2 - Missing never looks like zero (Priority: P1)

**Why this priority**: Presentation of missing data changes interpretation (PRD §14.1).

**Independent Test**: Learning-partial scenario.

**Acceptance Scenarios**:

1. **Given** a gap, **When** drawn, **Then** it is hatched and labelled "Tidak ada data", with a text note naming the period.
2. **Given** measured zero, **When** drawn, **Then** it is a baseline tick and the table says `0,000 kWh`.
3. **Given** a future bucket, **When** drawn, **Then** it is empty and the table says it has not happened.

### Edge Cases

- A one-day period uses 24 dense bars with sparse labels and no per-bar values.
- No smoothing, interpolation or hover-only value.
- Selected and reference series differ by more than colour once 020 adds the reference.

## Requirements

### Functional Requirements

- **FR-001**: The chart MUST render from history buckets without arithmetic beyond layout scale.
- **FR-002**: Every chart MUST have a visible summary and data alternative.
- **FR-003**: The plot MUST expose one accessible label, not one per bar.

### Key Entities

HistoryBucket from 010.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Chart, table and summary agree in tests for every bucket state.
- **SC-002**: The task is completable with a screen reader on web, and on Android at 043.
