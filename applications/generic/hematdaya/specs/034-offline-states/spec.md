# Feature Specification: Offline and combined states

**Feature Branch**: `034-offline-states`
**Created**: 2026-10-30
**Status**: Seeded, not started
**Milestone**: M8 Recovery
**Depends on**: 022, 027
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
3. **Given** confirmed data and a non-secret draft, **When** the app restarts into the same confirmed workspace, **Then** supported local storage restores them with the fetch time. A different workspace cannot read them.

### User Story 2 - States stay independent (Priority: P1)

**Why this priority**: PRD §13: one generic "error" cannot erase distinctions.

**Independent Test**: Each combination scenario.

**Acceptance Scenarios**:

1. **Given** offline plus stale source, **When** shown, **Then** cache age and last source capture appear separately, and retry cannot fabricate a reading.
2. **Given** historical CSV plus offline, **When** shown, **Then** historical provenance stays, with no live-disconnection claim.
3. **Given** learning plus partial data in a core-only deployment, **When** shown, **Then** recorded kWh, gaps, and insufficient comparison all show. No estimated cost value is fabricated.
4. **Given** valid zero energy in a core-only deployment, **When** shown, **Then** numeric zero energy remains distinct from unavailable cost.
5. **Given** scope conflict with known values, **When** shown, **Then** only the combined total is refused.

### User Story 3 - Stale means stale (Priority: P1)

**Why this priority**: PRD §13: "Data belum diperbarui" never means equipment off.

**Independent Test**: Stale scenario.

**Acceptance Scenarios**:

1. **Given** a recurring source with known cadence past two expected intervals, **When** shown, **Then** last capture, cadence and Periksa sumber appear.
2. **Given** historical CSV or a source with no known cadence, **When** shown, **Then** elapsed time alone does not mark the source stale.

### Edge Cases

- Refresh failure keeps confirmed content with a timestamp.
- When 019 is available, also verify learning plus partial plus missing tariff and valid zero plus missing tariff. Record these as integration checks separately from core-only acceptance.
- Non-secret drafts survive navigation and restart where the platform allows.
- Saved-account session expiry and sign-in recovery are acceptance cases for 037. In 034, offline or expired demo state must not expose a different workspace's data.

## Requirements

### Functional Requirements

- **FR-001**: The app MUST persist the last confirmed summary per period and scope, with its fetch time.
- **FR-002**: Client offline MUST be separate from source staleness.
- **FR-003**: Writes MUST need an online confirmed save; no offline merge.
- **FR-004**: The service MUST compute staleness for recurring sources with known cadence and default to more than two intervals. Historical imports and unknown cadence MUST NOT imply a stale live source.
- **FR-005**: The app MUST scope persisted reads and non-secret drafts to the confirmed principal and workspace, and clear them on logout, workspace change, or demo reset.

### Key Entities

- **CachedSummary**, **Draft**.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Every offline, freshness, and quality combination in scope has a passing test. Saved-account recovery remains in 037.
- **SC-002**: No scenario shows a fake OFF or zero.
