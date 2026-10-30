# Feature Specification: Perangkat and asset detail

**Feature Branch**: `014-perangkat-s04-s06`
**Created**: 2026-10-30
**Status**: Seeded, not started
**Milestone**: M2 Read journey on phone
**Depends on**: 010, 013
**Size**: M
**Covers**: UX-13, UX-14, S04, S06, P03
**Flips**: registry `daftar-perangkat` → `available`

## User Scenarios & Testing

### User Story 1 - See every measured thing (Priority: P1)

**Why this priority**: S04 lists devices, groups, circuits and site-total meters with visible scope labels.

**Independent Test**: Open Perangkat in `h-base` and in the scope scenario.

**Acceptance Scenarios**:

1. **Given** `h-base`, **When** Perangkat opens, **Then** four rows show name, location, scope kind and kWh for the shared period, largest first with a stable tie-break.
2. **Given** the scope scenario, **When** Perangkat opens, **Then** Meter utama shows as a site meter, individual values remain, and a scope notice links to scope resolution.
3. **Given** any row, **When** inspected, **Then** no switch, power icon or "paling boros" label appears.

### User Story 2 - Open one asset in context (Priority: P1)

**Why this priority**: Period and scroll must survive the round trip (UX-05, UX-14).

**Independent Test**: Scroll, open, go back.

**Acceptance Scenarios**:

1. **Given** a row, **When** opened, **Then** the detail shows the same period, name, scope type, kWh, coverage, gaps and source provenance.
2. **Given** detail, **When** Kembali is pressed, **Then** the list returns at the same scroll position and tab.
3. **Given** an empty period, **When** detail opens, **Then** it offers Lihat periode data and shows no zero.

### Edge Cases

- Full names wrap and are never truncated.
- A stale simulated source says "Data belum diperbarui", never "mati".
- Loading or failure never replaces a known list with zeros.
- An asset with two unresolved sources shows each value and links to resolution.

## Requirements

### Functional Requirements

- **FR-001**: Rows MUST show recorded kWh and quality, or an explicit unavailable state.
- **FR-002**: The list MUST use the shared period and scope.
- **FR-003**: Detail routes MUST live in the shared tab folder.
- **FR-004**: Primary **Tambah sumber** and **Impor data** MUST stay reachable.

### Key Entities

Asset and summary rows from 005 and 009.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Values on list, detail and Beranda are identical for one period.
- **SC-002**: Scroll position is restored on back on web and Android.
