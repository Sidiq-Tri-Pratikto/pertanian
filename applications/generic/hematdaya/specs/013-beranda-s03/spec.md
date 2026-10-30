# Feature Specification: Populated Beranda

**Feature Branch**: `013-beranda-s03`
**Created**: 2026-10-30
**Status**: Seeded, not started
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

1. **Given** `h-base`, **When** Beranda opens, **Then** it shows 19–25 Oktober 2026, "Cakupan pengukuran: 4 perangkat", 14,700 kWh, "Kelengkapan data: 100% periode", and the ranking with Kulkas first at 57,14%.
2. **Given** the virtual Monday, **When** Hari ini is chosen, **Then** no number appears, the screen explains why, and it offers Lihat periode data.
3. **Given** `h-current`, **When** Hari ini is chosen, **Then** 0,870 kWh shows with "sampai 12.00 (berjalan)".

### User Story 2 - Reach the largest contributor quickly (Priority: P1)

**Why this priority**: UX-04 and the 30-second research target.

**Independent Test**: Count taps from Beranda to the asset.

**Acceptance Scenarios**:

1. **Given** the ranking, **When** the user presses Lihat perangkat terbesar, **Then** the asset opens in one tap with the same period.
2. **Given** a ranking row, **When** pressed, **Then** that asset opens.
3. **Given** the ranking, **When** Lihat data is opened, **Then** a table shows the same values.

### User Story 3 - Refuse honestly (Priority: P1)

**Why this priority**: Scope and quality limits sit next to the number they change.

**Independent Test**: Scope and learning-partial scenarios.

**Acceptance Scenarios**:

1. **Given** a scope conflict, **When** Beranda opens, **Then** no total shows, the reason and Pilih cakupan appear, and the screen does not say "Belum ada data energi".
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

- **SC-001**: Largest contributor is reachable in one tap, featured evidence (after 022) in one tap.
- **SC-002**: Displayed values equal golden JSON for H and I, including Indonesian formatting.
