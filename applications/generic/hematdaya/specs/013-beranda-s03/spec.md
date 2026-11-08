# Feature Specification: Populated Beranda

**Feature Branch**: `013-beranda-s03`
**Created**: 2026-10-30
**Status**: Implemented on `f/012-013-onboarding-beranda`; Jest tests use the H and scope golden responses, and the web build showed H at 14,700 kWh against a live API, including 320 px
**Milestone**: M2 Read journey on phone
**Depends on**: 009, 012
**Size**: M
**Covers**: UX-04, UX-06, UX-17, UX-18, UX-19, AT-10, AT-55, S03, P03
**Flips**: registry `ringkasan-energi`, `kontributor` → `available`

## User Scenarios & Testing

### User Story 1 - Answer "how much energy was monitored?" first (Priority: P1)

**Why this priority**: UX-17 fixes the reading order: period and scope, recorded kWh, qualified cost, completeness and freshness, contributors, one observation.

**Independent Test**: Open `h-base` and read the screen top to bottom.

**Acceptance Scenarios**:

1. **Given** `h-base`, **When** Beranda opens with the demo's initial period, **Then** it shows 19–25 Oktober 2026, "Cakupan pengukuran: 4 perangkat", 14,700 kWh, "Kelengkapan data: 100% periode", and the ranking with Kulkas first at 57,14%.
2. **Given** the virtual Monday, **When** Hari ini is chosen, **Then** no number appears, the screen explains why, and it offers Lihat periode data.
3. **Given** `h-current`, **When** Hari ini is chosen, **Then** 0,870 kWh shows with "sampai 12.00 (berjalan)".

### User Story 2 - Reach the largest contributor quickly (Priority: P1)

**Why this priority**: UX-04 and the 30-second research target.

**Independent Test**: Read the ranking and its table. After 014, count taps from Beranda to the asset.

**Acceptance Scenarios**:

1. **Given** the ranking, **When** Lihat data is opened, **Then** a table shows the same values.
2. **Given** 014 has shipped, **When** the user presses Lihat perangkat terbesar or a ranking row, **Then** the matching asset opens in one tap with the same period. Until then, show the ranking and its data alternative without an asset-detail action.

### User Story 3 - Refuse honestly (Priority: P1)

**Why this priority**: Scope and quality limits sit next to the number they change.

**Independent Test**: Scope and learning-partial scenarios.

**Acceptance Scenarios**:

1. **Given** a scope conflict, **When** Beranda opens, **Then** no total shows, the conflict reason appears, and the screen does not say "Belum ada data energi". Add the Pilih cakupan action when 029 ships.
2. **Given** partial data, **When** Beranda opens, **Then** the qualifier and first gaps are visible without expanding anything.
3. **Given** valid zero, **When** Beranda opens, **Then** 0,000 kWh shows with "Nol terukur" and no percentages.

### Edge Cases

- `HD.EnergyMetric` has no scope-conflict state on web; the native version adds it (recorded as a system change).
- Period change updates all values together, never one at a time.
- Measurement scope and time completeness stay separate labels; never "akurat".
- No schedule or output card appears when those are absent (AT-10).

## Requirements

### Functional Requirements

- **FR-001**: The screen MUST render only service values, formatted from strings.
- **FR-002**: `HDPeriodSelector` MUST offer Hari ini, Minggu ini and a range with explicit local boundaries.
- **FR-003**: Ranking MUST use a shared zero baseline, direct labels and a data alternative.
- **FR-004**: Refresh MUST keep confirmed content on screen with an update status.
- **FR-005**: Cost shows as "Segera hadir" until 019.

### Key Entities

Summary from 009.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The ranking and data table identify the largest contributor. Verify one-tap access to its detail in 014 and to featured evidence in 022.
- **SC-002**: Displayed values equal golden JSON for H and I, including Indonesian formatting.

## Onboarding refresh

[Spec 047](../047-explore-first-onboarding/spec.md) supersedes the original Welcome and first import entry behavior. Its verification is tracked separately.
