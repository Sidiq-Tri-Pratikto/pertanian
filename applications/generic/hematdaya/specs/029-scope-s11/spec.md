# Feature Specification: Scope screen

**Feature Branch**: `029-scope-s11`
**Created**: 2026-10-30
**Status**: Seeded, not started
**Milestone**: M6 Scope
**Depends on**: 013, 028
**Size**: M
**Covers**: UX-19, AT-57, S11, P09
**Flips**: registry `cakupan-sumber` → `available`

## User Scenarios & Testing

### User Story 1 - Resolve an overlap (Priority: P1)

**Why this priority**: AT-57: selected equipment scope stays distinct from time completeness.

**Independent Test**: Scope scenario end to end.

**Acceptance Scenarios**:

1. **Given** the scope scenario, **When** S11 opens, **Then** sources, physical inclusion, current selection and why the total is blocked are visible.
2. **Given** a parent and children, **When** a view is chosen, **Then** options read "Meter utama · 10 kWh" or the child view, never a sum.
3. **Given** two sources, **When** one is chosen, **Then** child values appear only after that choice.
4. **Given** a valid selection, **When** Konfirmasi cakupan is pressed, **Then** the summary updates after acknowledgment.

### User Story 2 - Failure changes nothing (Priority: P1)

**Why this priority**: S11 contract.

**Independent Test**: Reject the save.

**Acceptance Scenarios**:

1. **Given** a rejected save, **When** it fails, **Then** the proposal stays for retry and the previous confirmed summary is still used.
2. **Given** Batal, **When** pressed, **Then** nothing changes.

### Edge Cases

- A conflicted child is never shown as 0.
- Scope and completeness keep separate labels.
- The primary action is disabled with a stated reason until valid.

## Requirements

### Functional Requirements

- **FR-001**: S11 MUST show included and excluded assets with reasons before confirmation.
- **FR-002**: Beranda and Perangkat MUST link here from any scope issue.

### Key Entities

Selection from 028.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The screen never displays a combined value for an invalid selection.
