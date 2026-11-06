# Feature Specification: Schedule on mobile

**Feature Branch**: `031-schedule-mobile`
**Created**: 2026-10-30
**Status**: Seeded, not started
**Milestone**: M7 Optional analysis
**Depends on**: 014, 017, 030
**Size**: M
**Covers**: FR-10, UX-15, AT-14, S09, P05
**Flips**: registry `jadwal-pemakaian` → `available`

## User Scenarios & Testing

### User Story 1 - Set site hours (Priority: P1)

**Why this priority**: P05: overnight windows and continuous assets behave consistently.

**Independent Test**: Enter Senin 22.00 → 06.00 and read the preview.

**Acceptance Scenarios**:

1. **Given** the editor, **When** an overnight window is entered with Berakhir hari berikutnya, **Then** the preview says it is counted on the start day.
2. **Given** equal times, **When** saved, **Then** the error asks for a correction or 24 jam.
3. **Given** effective now, **When** previewed, **Then** past periods are stated as unchanged.
4. **Given** historical correction, **When** previewed, **Then** inside and outside energy from the service show before anything is saved.
5. **Given** a draft edited after preview, **When** Simpan is reached, **Then** a fresh preview is required.

### User Story 2 - Override per asset (Priority: P1)

**Why this priority**: AT-14.

**Independent Test**: Set each mode on an asset.

**Acceptance Scenarios**:

1. **Given** asset detail, **When** a mode is chosen, **Then** Ikuti jadwal lokasi, Tanpa jadwal, Diharapkan terus menyala and Jadwal khusus each save and show.

### User Story 3 - Failure keeps everything (Priority: P1)

**Why this priority**: The state combination "failed schedule save plus pending insight view" must hold.

**Independent Test**: Reject the save.

**Acceptance Scenarios**:

1. **Given** a rejected save, **When** it fails, **Then** draft and previous confirmed schedule and evidence remain.

### Edge Cases

- Schedule stays optional: skipping is always possible.
- Without a schedule, no outside value or warning appears.

## Requirements

### Functional Requirements

- **FR-001**: The editor MUST support weekdays, multiple windows, next-day end and 24 jam.
- **FR-002**: Previews MUST come from the read-only service endpoints in 030. Only confirmation sends a save, using the same draft and its expected versions.
- **FR-003**: Native time pickers MUST be used on phones. Web time fields MUST be labelled and operable by keyboard.

### Key Entities

Schedule from 030.

## Success Criteria

### Measurable Outcomes

- **SC-001**: P05 completes with no explanation of "start-day anchoring" outside the screen's own copy.
