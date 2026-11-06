# Feature Specification: Metric screen

**Feature Branch**: `033-metric-s12`
**Created**: 2026-10-30
**Status**: Seeded, not started
**Milestone**: M7 Optional analysis
**Depends on**: 014, 017, 032
**Size**: M
**Covers**: FR-11, UX-15, S12, P06
**Flips**: registry `metrik-keluaran` → `available`

## User Scenarios & Testing

### User Story 1 - Set up a metric deliberately (Priority: P1)

**Why this priority**: P06: valid intensity appears, and missing input never becomes zero.

**Independent Test**: Enter 2.880 units.

**Acceptance Scenarios**:

1. **Given** S12, **When** valid inputs are previewed, **Then** numerator, denominator, method, units, period and coverage show.
2. **Given** a valid preview, **When** saved, **Then** Beranda shows the metric.
3. **Given** no valid preview or a draft edited after preview, **When** Simpan metrik is reached, **Then** it is disabled with the reason.
4. **Given** a stale preview or rejected save, **When** confirmation fails, **Then** the confirmed metric is unchanged and the draft stays available for correction or a new preview.
5. **Given** Nonaktifkan metrik, **When** acknowledged, **Then** the display goes and readings stay.

### User Story 2 - Correct mistakes in place (Priority: P1)

**Why this priority**: Invalid values remain fields with messages.

**Independent Test**: Enter 0.

**Acceptance Scenarios**:

1. **Given** zero output, **When** previewed, **Then** the error summary focuses and the field says "Tidak dapat dihitung: keluaran nol".
2. **Given** back, **When** pressed, **Then** the draft stays and the prior metric is unchanged.

### Edge Cases

- Households never meet this screen unless they open it.
- A lower ratio is stated as an observation, not proof of savings.

## Requirements

### Functional Requirements

- **FR-001**: Entry MUST be secondary, from S09 or S06.
- **FR-002**: The screen MUST NOT compute intensity.
- **FR-003**: Simpan metrik MUST send the reviewed draft and preview fingerprint to the aggregate save from 032. The screen MUST invalidate the preview after any draft edit.

### Key Entities

OutputMetric from 032.

## Success Criteria

### Measurable Outcomes

- **SC-001**: P06 passes on web and Android.
