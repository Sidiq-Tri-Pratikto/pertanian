# Feature Specification: CSV parser

**Feature Branch**: `024-csv-parser`
**Created**: 2026-10-30
**Status**: Seeded, not started
**Milestone**: M5 CSV
**Depends on**: 006
**Size**: L
**Covers**: FR-05, FR-06, AT-26, AT-27, AT-28, AT-29, AT-31, AT-32
**Flips**: none

## User Scenarios & Testing

### User Story 1 - Read real files (Priority: P1)

**Why this priority**: CSV is the complete first data path (PRD §4.1).

**Independent Test**: Parser tests on every accepted format.

**Acceptance Scenarios**:

1. **Given** `timestamp,perangkat,energi_wh`, **When** parsed, **Then** aliases resolve and values mean interval Wh.
2. **Given** `interval_start,interval_end,asset,energy_wh`, **When** parsed, **Then** explicit intervals are used.
3. **Given** UTF-8 BOM, semicolons, quoted names and decimal commas, **When** parsed, **Then** values and names are unchanged.
4. **Given** `cumulative_wh`, **When** parsed, **Then** the counter path is used, never interval energy.

### User Story 2 - Preserve meaning (Priority: P1)

**Why this priority**: Silent unit or time guesses corrupt everything downstream.

**Independent Test**: Meaning tests.

**Acceptance Scenarios**:

1. **Given** `power_w`, **When** parsed, **Then** it stays unresolved until the user confirms interval average; instantaneous power is blocked.
2. **Given** competing value columns, **When** parsed, **Then** the user must choose one.
3. **Given** naive timestamps, **When** parsed, **Then** the site timezone applies only after confirmation.
4. **Given** one row or irregular gaps, **When** parsed, **Then** cadence is not inferred and an explicit interval is required.
5. **Given** a long gap, **When** parsed, **Then** the earlier row is never stretched across it.

### User Story 3 - Say exactly what is wrong (Priority: P1)

**Why this priority**: UX-20 needs a row and field message with the correction.

**Independent Test**: Bad input table.

**Acceptance Scenarios**:

1. **Given** a negative value, **When** parsed, **Then** the error reads `Baris data 7, energy_wh: gunakan angka 0 atau lebih.`
2. **Given** blank lines or multi-line quoted fields, **When** parsed, **Then** data row and file line stay correct and distinct.
3. **Given** `2026-02-30`, **When** parsed, **Then** it is rejected, never rolled into March.
4. **Given** an unquoted `12,5` in a comma file, **When** parsed, **Then** the column count mismatch is reported, not silently read as 12.

### Edge Cases

- Limits: 10 MiB, 150,000 nonblank data rows, names up to 60 characters with no silent truncation.
- A formula-looking asset name stays plain text.
- Ambiguous delimiter or number format is rejected with an example.
- Offset timestamps keep their explicit instant.

## Requirements

### Functional Requirements

- **FR-001**: Header aliases MUST match PRD §10.2, case-insensitively.
- **FR-002**: The parser MUST be pure and stream rows.
- **FR-003**: Cadence inference MUST run per source and need 90% of gaps within one second of the median.
- **FR-004**: Decimal parsing MUST be exact to three places.
- **FR-005**: Output MUST separate structural errors, meaning questions and row errors.

### Key Entities

- **ParsedFile**, **RowResult**.

## Success Criteria

### Measurable Outcomes

- **SC-001**: All prototype parser tests pass in Python, with the same messages.
- **SC-002**: A 150,000-row file parses within the 60-second target on the dev machine, measured and recorded.
