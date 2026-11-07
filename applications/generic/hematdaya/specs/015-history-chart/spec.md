# Feature Specification: History chart

**Feature Branch**: `015-history-chart`
**Created**: 2026-10-30
**Status**: Implemented and verified in automated tests and Chrome. Spoken web screen-reader check pending.
**Milestone**: M2 Read journey on phone
**Depends on**: 010, 014
**Merged implementation prerequisite**: 022 supplies the shared chart used by S08.
**Size**: M
**Covers**: UX-13, UX-18, AT-56, S06
**Flips**: none. 016 owns the combined `detail-perangkat` availability flip.

## User Scenarios & Testing

### User Story 1 - Read history without relying on the picture (Priority: P1)

**Why this priority**: AT-56: text and data alternatives must answer the task by touch, keyboard and screen reader.

**Independent Test**: Answer "which day was highest?" from the summary text alone.

**Acceptance Scenarios**:

1. **Given** a week, **When** Lihat riwayat is pressed, **Then** seven daily buckets show on a zero baseline with unit, period and timezone. The text summary identifies the highest eligible bucket returned by the service, or explains that there is no eligible bucket.
2. **Given** Lihat data, **When** opened, **Then** a table shows the same values and quality with associated headers. Rows stack on narrow screens. Both disclosures work by touch and keyboard, and the values are readable with a web screen reader.
3. **Given** an open History view, **When** a new selection is pending or a read fails, **Then** the last confirmed History may stay visible for that workspace and asset with its original period, timezone and elapsed cutoff. The status identifies it as retained, and only the response for the current confirmed selection can replace it.

### User Story 2 - Missing never looks like zero (Priority: P1)

**Why this priority**: Presentation of missing data changes interpretation (PRD §14.1).

**Independent Test**: Read the 19–25 October household learning-partial history. Pompa Air has a missing day on 24 October. Kulkas reports `1,100 kWh` and `91,6%` coverage on 22 October.

**Acceptance Scenarios**:

1. **Given** a gap, **When** drawn, **Then** it is hatched and labelled "Tidak ada data", with a text note naming the period.
2. **Given** a measured bucket with reported energy of zero, **When** drawn, **Then** it is a baseline tick and the table says `0,000 kWh`. A partial bucket with the same reported value retains its partial marker, coverage and explanation.
3. **Given** a future bucket, **When** drawn, **Then** it is empty and the table says it has not happened.
4. **Given** a bucket blocked by source conflict or insufficient resolution, **When** drawn, **Then** it has no numeric bar and the table explains its unavailable reason separately from missing or future data.
5. **Given** partial energy, **When** shown, **Then** the recorded energy and returned coverage appear together and the plot distinguishes partial energy from complete measured energy.
6. **Given** a current bucket that crosses the service's elapsed cutoff, **When** the bucket or its coverage is shown, **Then** it is qualified through that cutoff, including a measured bucket with 100% coverage. If the service selects that bucket as highest, the summary names it with the same elapsed qualification.

### Edge Cases

- A single resolved local date uses hourly buckets, including a Monday Minggu ini. The axis is sparse and omits per-bar values. The display uses the returned UTC bounds and offsets so a 23-hour day shows only its returned hours and a 25-hour day distinguishes both occurrences of a repeated hour.
- No smoothing, interpolation or hover-only value.
- Asset history shows the full recorded energy series. The existing S08 evidence chart keeps its frozen current and reference series, which differ by more than colour.
- A confirmed all-missing, all-future, or all-unavailable series replaces any retained view and shows its returned buckets and their reasons.

## Requirements

### Functional Requirements

- **FR-001**: The chart MUST render from history buckets and limit energy arithmetic to layout scale.
- **FR-002**: Every chart MUST have a visible summary and data alternative.
- **FR-003**: The plot MUST expose one accessible label, not one per bar.
- **FR-004**: The chart, table and text summary MUST use the same validated response for the selected asset and resolved period. Use 010's `highest_bucket` and its eligibility/tie rules without inferring a maximum from chart layout or display rounding. Use the response's `window.effective_end` to qualify recorded values and coverage for an elapsed portion.
- **FR-005**: The History read MUST respect the service's retryability, wait and total attempt limit, including the first request and any automatic, manual or lifecycle trigger for the same operation. At terminal failure, surface safe recovery guidance and the service reference when available. Keep eligible confirmed content visible with its own context.

### Key Entities

HistoryBucket from 010.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Chart, table and summary agree in tests for every bucket state, service-selected highest and current or retained elapsed cutoff.
- **SC-002**: A web screen reader and keyboard can answer the highest-bucket question and read the exact values. Table headers remain associated above and below 768 CSS px. Record 320 CSS px reflow and 200% text resizing as separate checks. Native assistive technology is verified at 043.
- **SC-003**: A failing read with a total limit of one or three makes at most that many attempts. Tests exercise wait timing, disclosure reopening, remount, focus, reconnect and any exposed retry action, and verify the retained context and terminal status.
