# Feature Specification: CSV parser

**Feature Branch**: `m5/csv-parser`
**Created**: 2026-10-30
**Status**: Built, awaiting review
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

1. **Given** `power_w` or any other average-power alias, **When** parsed, **Then** it stays unresolved until the user confirms interval average; instantaneous power is blocked.
2. **Given** competing value columns, **When** parsed, **Then** the user must choose one.
3. **Given** naive timestamps, **When** parsed, **Then** the site timezone applies only after confirmation.
4. **Given** a timestamp-only interval-energy or average-power stream with one row or no reliable cadence, **When** parsed, **Then** it needs a confirmed interval duration or explicit start/end columns.
5. **Given** two mapped sources with different regular cadences and a long gap in one, **When** parsed, **Then** each stream keeps its own cadence. Every timestamp is the start of one interval, including the final row, and the long gap remains uncovered.
6. **Given** timestamp-only counter readings, **When** parsed, **Then** they remain point readings. The parser does not infer interval duration or energy from cadence.

### User Story 3 - Say exactly what is wrong (Priority: P1)

**Why this priority**: UX-20 needs a row and field message with the correction.

**Independent Test**: Bad input table.

**Acceptance Scenarios**:

1. **Given** a negative value, **When** parsed, **Then** the error reads `Baris data 7, energy_wh: gunakan angka 0 atau lebih.`
2. **Given** blank lines or multi-line quoted fields, **When** parsed, **Then** data row and file line stay correct and distinct. The message names the file line only when it differs from data row plus header line: `Baris data 7 (baris file 9), energy_wh: gunakan angka 0 atau lebih.`
3. **Given** `2026-02-30` or `2026-02-30 00:00`, **When** parsed, **Then** it is rejected, never rolled into March.
4. **Given** an unquoted `12,5` in a comma file, **When** parsed, **Then** the column count mismatch is reported, not silently read as 12.

### Edge Cases

- Limits: 10 MiB, 150,000 nonblank data rows, asset and source names up to 60 characters with no silent truncation.
- A formula-looking asset name stays plain text.
- Ambiguous delimiter or number format is rejected with an example. In a semicolon file that includes `12.5`, `0.250` and `1.250`. In a comma file it includes quoted `"1,250"`.
- Offset timestamps keep their explicit instant.
- A nonexistent or ambiguous local time in the confirmed timezone needs an offset or a correction.
- A naive `interval_end` beside an offset `interval_start` still asks for timezone confirmation.
- A timestamp column beside interval columns is rejected, never silently dropped.
- A file that is not UTF-8, holds a NUL character or has an unterminated or malformed quote is rejected with what to do next.

## Requirements

### Functional Requirements

- **FR-001**: Header aliases MUST match PRD §10.2, case-insensitively, plus `interval_start`, `interval_end`, `cumulative_wh` and the source aliases `source`, `sumber` and `source_id`. There is no kWh alias.
- **FR-002**: The parser MUST be pure: no database, network, clock, logging, process-wide state or production import from another feature module. It MUST stream: it never holds the whole file or a list of rows, and it yields row results one at a time. File-level answers may keep per-source timestamps, because cadence needs them.
- **FR-003**: For timestamp-only interval energy and average power, cadence inference MUST use sorted positive gaps per mapped source. At least 90% of those gaps MUST be within one second of their median. Every timestamp starts one confirmed or inferred interval, including the final row. A declared duration applies to one source only. Counter points bypass cadence inference.
- **FR-004**: Decimal parsing MUST be exact to three places, without binary floats. More than three places is rejected, never rounded.
- **FR-005**: Output MUST separate structural errors, meaning questions and row errors. Failures are returned as data with stable reasons, and 025 maps them to public errors.

### Key Entities

- **ParsedFile**, **RowResult**, **MeaningQuestion**.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Every parser assertion in prototype tests AT-27a, AT-27b, AT-28, AT-29, AT-31 and AT-32, plus AT-30's first error message, passes in Python with the same messages, as listed in `tasks.md`. `domain.test.js` has no AT-26 test, so AT-26 is a new test from PRD §10.2. AT-27a's 50 Wh and AT-27b's 30 Wh pass by feeding parser rows into 006's normalization.
- **SC-002**: A 150,000-row file within 10 MiB is parsed and its rows read within the 60-second target on the dev machine, with time, peak memory and machine recorded in `plan.md`. PRD §18's full validation and commit target is measured by 041.
