# Feature Specification: Schedule API

**Feature Branch**: `030-schedule-api`
**Created**: 2026-10-30
**Status**: Seeded, not started
**Milestone**: M7 Optional analysis
**Depends on**: 011, 021
**Size**: L
**Covers**: FR-10, AT-11, AT-12, AT-13, AT-14, AT-15, AT-18
**Flips**: manifest capability `schedule` → `available`

## User Scenarios & Testing

### User Story 1 - Weekly windows with overnight support (Priority: P1)

**Why this priority**: AT-13: Monday 22.00–Tuesday 06.00 anchored on Monday.

**Independent Test**: Oracles.

**Acceptance Scenarios**:

1. **Given** that window and 1 kWh per hour from Monday 21.00 to Tuesday 07.00, **When** split, **Then** 10 kWh total, 8 inside, 2 outside.
2. **Given** overlapping windows, **When** computed, **Then** shared minutes count once (AT-12).
3. **Given** a 60 Wh interval 16.30–17.30 and a window ending 17.00, **When** split, **Then** 30 inside and 30 outside, both labelled proportional estimates (AT-15).
4. **Given** equal start and end without the 24-hour choice, **When** saved, **Then** it is refused.
5. **Given** a proposed site schedule or asset override, **When** previewed, **Then** the service returns the effective definition, estimated split or reason, and impacted period without updating schedules, audit, or evidence.

### User Story 2 - Inheritance is explicit (Priority: P1)

**Why this priority**: AT-14: continuous, custom, disabled and inherited stay distinct.

**Independent Test**: One asset per mode.

**Acceptance Scenarios**:

1. **Given** a site schedule, **When** an asset inherits, **Then** it uses that schedule and evidence names it.
2. **Given** continuous expected, **When** evaluated, **Then** the site schedule is overridden and no outside finding exists (AT-11).
3. **Given** "no schedule for this asset", **When** evaluated, **Then** inheritance is off and the split is unavailable.
4. **Given** nothing configured, **When** read, **Then** outside energy is `null` with `no_schedule`, never zero.

### User Story 3 - Outside-window observation (Priority: P1)

**Why this priority**: AT-18.

**Independent Test**: `i-change`.

**Acceptance Scenarios**:

1. **Given** `i-change`, **When** evaluated, **Then** Kompresor outside energy is +3,000 kWh against 0,000, percent is unavailable, and copy says the use is not proven avoidable.
2. **Given** `i-optional`, **When** evaluated, **Then** outside energy is exactly 0.
3. **Given** a schedule changed inside the comparison weeks, **When** evaluated, **Then** the comparison is withheld.

### Edge Cases

- A change defaults to effective now; historical correction is explicit and versioned.
- Holiday calendars and shift rotation are out of scope.

## Requirements

### Functional Requirements

- **FR-001**: Schedules MUST be weekly, multi-window, with next-day end and a separate 24-hour option.
- **FR-002**: Effective expected use MUST distinguish all four override modes. `continuous` uses an all-day expectation, `none` stops inheritance and returns no split, `custom` uses the asset windows, and `inherit` uses the site schedule if present or returns no split.
- **FR-003**: Splits MUST conserve energy.
- **FR-004**: Routes and rules MUST use the capability guard.
- **FR-005**: The outside-window rule MUST reuse the scale-aware rule from 021.
- **FR-006**: The API MUST offer a read-only preview for site and asset drafts before a separate save. Save MUST check the expected schedule revisions and revalidate the proposed definition.

### Key Entities

- **Schedule**, **ScheduleWindow**, **AssetScheduleOverride**.

## Success Criteria

### Measurable Outcomes

- **SC-001**: All schedule oracles in PRD §19.4 and AT-18 pass exactly.
- **SC-002**: Saving a schedule is atomic: a failed save changes nothing.
