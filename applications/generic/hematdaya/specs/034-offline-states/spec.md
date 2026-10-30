# Feature Specification: Offline and combined states

**Feature Branch**: `034-offline-states`
**Created**: 2026-10-30
**Status**: Seeded, not started
**Milestone**: M8 Recovery
**Depends on**: 022
**Size**: M
**Covers**: FR-15, FR-18, UX-05, UX-11, AT-38, AT-40, AT-57, P08
**Flips**: registry `data-tersimpan` → `available`

## User Scenarios & Testing

### User Story 1 - Keep reading offline (Priority: P1)

**Why this priority**: FR-15: cached data with timestamp, scope and quality.

**Independent Test**: Go offline after loading.

**Acceptance Scenarios**:

1. **Given** cached data, **When** the device is offline, **Then** values stay with "Offline · menampilkan data tersimpan" and the cache time.
2. **Given** offline, **When** the user tries to save, **Then** the draft stays and the app says nothing was sent. It never claims a queued save.

### User Story 2 - States stay independent (Priority: P1)

**Why this priority**: PRD §13: one generic "error" cannot erase distinctions.

**Independent Test**: Each combination scenario.

**Acceptance Scenarios**:

1. **Given** offline plus stale source, **When** shown, **Then** cache age and last source capture appear separately, and retry cannot fabricate a reading.
2. **Given** historical CSV plus offline, **When** shown, **Then** historical provenance stays, with no live-disconnection claim.
3. **Given** learning plus no tariff plus partial, **When** shown, **Then** recorded kWh, gaps, absent cost and insufficient comparison all show.
4. **Given** valid zero plus no tariff, **When** shown, **Then** numeric zero energy and unavailable cost show.
5. **Given** scope conflict with known values, **When** shown, **Then** only the combined total is refused.

### User Story 3 - Stale means stale (Priority: P1)

**Why this priority**: PRD §13: "Data belum diperbarui" never means equipment off.

**Independent Test**: Stale scenario.

**Acceptance Scenarios**:

1. **Given** a source past two expected intervals, **When** shown, **Then** last capture, cadence and Periksa sumber appear.

### Edge Cases

- Refresh failure keeps confirmed content with a timestamp.
- Non-secret drafts survive navigation and restart where the platform allows.
- A session expiry keeps the draft and needs an explicit retry (AT-40, completed in 037).

## Requirements

### Functional Requirements

- **FR-001**: The app MUST persist the last confirmed summary per period and scope, with its fetch time.
- **FR-002**: Client offline MUST be separate from source staleness.
- **FR-003**: Writes MUST need an online confirmed save; no offline merge.
- **FR-004**: The service MUST compute staleness from cadence with the policy default of two intervals.

### Key Entities

- **CachedSummary**, **Draft**.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Every combination in handoff §10 has a passing test.
- **SC-002**: No scenario shows a fake OFF or zero.
