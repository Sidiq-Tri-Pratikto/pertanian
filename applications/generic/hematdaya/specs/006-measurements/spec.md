# Feature Specification: Measurements

**Feature Branch**: `006-measurements`
**Created**: 2026-10-30
**Status**: Seeded, not started
**Milestone**: M1 Energy core
**Depends on**: 005
**Size**: L
**Covers**: FR-05, AT-27, AT-37
**Flips**: none

## User Scenarios & Testing

### User Story 1 - One normalized reading, whatever the source (Priority: P1)

All sources enter one ingestion rule that stores interval energy with its meaning intact.

**Why this priority**: Every total in the product rests on this. Unit and interval mistakes cannot be fixed by the UI.

**Independent Test**: Ingest each measurement kind through the service with exact expected values.

**Acceptance Scenarios**:

1. **Given** interval energy 10 Wh, **When** ingested, **Then** 10,000 mWh is stored for that interval.
2. **Given** average power 100 W for 30 minutes, **When** ingested, **Then** 50 Wh is stored.
3. **Given** one instantaneous sample of 100 W, **When** ingested, **Then** it is stored as a point with no energy.
4. **Given** counter readings 100 → 130 → 5 Wh, **When** ingested, **Then** the first delta is 30 Wh, the reset starts a new segment, and the reset interval has no energy: never −125 or +125 Wh.

### User Story 2 - Repeats and corrections are safe (Priority: P1)

**Why this priority**: PRD §10.3 and §17 require idempotent ingestion.

**Independent Test**: Ingest the same batch twice; totals do not change.

**Acceptance Scenarios**:

1. **Given** an identical reading, **When** it arrives again, **Then** it is an idempotent repeat.
2. **Given** the same identity with a changed value, **When** it arrives, **Then** it is a new revision with provenance, not a second reading.
3. **Given** a late reading, **When** it arrives, **Then** the affected interval range is returned for recomputation.
4. **Given** a point sample or counter reading without a capture ID, **When** the same source, kind and measurement time are ingested again, **Then** it is an idempotent repeat. A different time remains a distinct point.
5. **Given** a late or corrected counter reading, **When** it changes the adjacent deltas, **Then** affected old deltas are replaced or withdrawn, never summed with the new deltas. Replaying the input leaves the same current measurements.

### Edge Cases

- Equal values in different intervals remain separate readings.
- Negative consumption, non-finite values and `end <= start` are rejected, never stored as zero.
- A valid zero is stored as zero; missing data has no row at all.
- A long counter gap keeps its total but is flagged as unusable for sub-period analysis.
- Phase total and phase components are never mixed: a source declares which it is.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST store energy as integer mWh with a half-open interval in UTC.
- **FR-002**: The system MUST keep origin, received time, quality, source record ID and revision on every reading.
- **FR-003**: Average power MUST convert as `W × seconds / 3600`.
- **FR-004**: Instantaneous power MUST never become energy.
- **FR-005**: Counter deltas MUST stay within one segment; a decrease MUST start a new segment.
- **FR-006**: Identity MUST prefer a stable source record ID, otherwise source and kind plus interval bounds for interval observations or capture time for points.
- **FR-007**: Decimal inputs MUST parse without binary floats, and the wire type MUST reject JSON numbers.
- **FR-008**: Keep raw values, units, source provenance and capture times. When conversion to integer mWh needs quantization, round once at normalization using nearest mWh, with exact ties to even. Do not round to display precision during aggregation.
- **FR-009**: Ingestion MUST use the shared site write lock and advance the measurement revision on a committed change. A replay or rollback leaves the revision unchanged.

### Key Entities

- **Measurement**: source, record ID, kind, interval or point, `energy_mwh`, received time, quality, revision.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The power and counter oracles in PRD §19.4 pass exactly.
- **SC-002**: Ingesting a batch twice changes no total and adds no row.
