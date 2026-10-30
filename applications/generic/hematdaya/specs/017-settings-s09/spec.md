# Feature Specification: Site settings

**Feature Branch**: `017-settings-s09`
**Created**: 2026-10-30
**Status**: Seeded, not started
**Milestone**: M3 Settings and cost
**Depends on**: 013
**Size**: M
**Covers**: FR-02, UX-05, AT-04, AT-51, S09, P11
**Flips**: registry `pengaturan-lokasi` → `available`

## User Scenarios & Testing

### User Story 1 - Change context without changing data (Priority: P1)

**Why this priority**: P11 and AT-04: readings, source identity, tariff and optional inputs stay unchanged.

**Independent Test**: Switch Rumah tangga to Industri; compare summaries.

**Acceptance Scenarios**:

1. **Given** a populated site, **When** context changes, **Then** a preview says examples change, and after saving every number is identical.

### User Story 2 - Change timezone with understanding (Priority: P1)

**Why this priority**: AT-51: UTC data is preserved and local boundaries are explicit.

**Independent Test**: Change to Asia/Makassar and compare window bounds.

**Acceptance Scenarios**:

1. **Given** a timezone change, **When** selected, **Then** the screen explains that local days recalculate and stored measurements stay.
2. **Given** it is saved, **When** Beranda reloads, **Then** the resolved window shows the new timezone, and stored readings are unchanged.

### User Story 3 - Drafts behave (Priority: P1)

**Why this priority**: UX-05 and §5: save, cancel and failure keep confirmed values apart from drafts.

**Independent Test**: Reject a save, leave, return.

**Acceptance Scenarios**:

1. **Given** a rejected save, **When** it fails, **Then** the draft stays and confirmed values are still used.
2. **Given** Batal, **When** pressed, **Then** the invoker returns with confirmed values.

### Edge Cases

- Unknown timezone is refused by the service, not only by the picker.
- Notification preference stays off and no permission prompt appears (045).

## Requirements

### Functional Requirements

- **FR-001**: The screen MUST edit site name, context and timezone.
- **FR-002**: Timezone change MUST require explicit confirmation.
- **FR-003**: Pengaturan MUST keep listing unshipped features.
- **FR-004**: A save MUST write one audit event.

### Key Entities

Site from 004.

## Success Criteria

### Measurable Outcomes

- **SC-001**: A context switch leaves golden numbers unchanged.
- **SC-002**: A timezone change leaves `measurements` rows untouched.
