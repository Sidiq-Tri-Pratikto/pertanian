# Feature Specification: Composition enforcement

**Feature Branch**: `011-composition`
**Created**: 2026-10-30
**Status**: Implemented on `f/m1-energy-core`. Guard unit tests pass, and the energy unit, summary and history tests (goldens included) pass under both `core-plus-optional` and `core-only`. AT-47 and AT-53 are partial: CSV/demo core-only journeys arrive in 012 and 024–027, and real optional routes in 018, 030 and 032
**Milestone**: M1 Energy core
**Depends on**: 009
**Size**: M
**Covers**: FR-21, AT-47, AT-53
**Flips**: none

## User Scenarios & Testing

### User Story 1 - A disabled capability is refused at the service (Priority: P1)

**Why this priority**: PRD FR-21: hiding a screen is insufficient. This must exist before any optional module ships.

**Independent Test**: In `core-only`, a guarded call fails with the stable reason.

**Acceptance Scenarios**:

1. **Given** `core-only`, **When** a guarded test use case is called directly, **Then** it fails with `CAPABILITY_DISABLED` and a reason naming the capability. Optional routes and workers adopt this guard as they ship.
2. **Given** `core-plus-optional`, **When** the same test use case runs, **Then** the capability check passes while ownership and per-request prerequisites still apply.

### User Story 2 - Core energy behaves identically across compositions (Priority: P1)

**Why this priority**: This verifies the shared energy core without a broker, meter, AI or push. Full AT-47 evidence waits for the demo and CSV journeys, and full AT-53 evidence waits for actual optional paths.

**Independent Test**: Run the energy test suite in both compositions.

**Acceptance Scenarios**:

1. **Given** the H and I fixtures, **When** summaries run under each composition, **Then** energy numbers are identical.
2. **Given** an unsupported combination, **When** the service starts, **Then** startup fails.

### Edge Cases

- Composition never grants access: ownership still applies first.
- Config cannot disable an invariant such as no double counting.

## Requirements

### Functional Requirements

- **FR-001**: A single guard MUST live at the service layer, so an API call and a future worker share it.
- **FR-002**: Compositions MUST be versioned data, not client-specific branches.
- **FR-003**: Define the stable `capability_disabled` reason for optional summary values. Add the actual fields and their disabled-path behavior in 018, 030 and 032, as each module lands.
- **FR-004**: CI MUST run the core energy tests under both compositions.

### Key Entities

- **Composition**: ID, version, capabilities, adapters, policy versions.

## Success Criteria

### Measurable Outcomes

- **SC-001**: A test bypassing the router still gets `CAPABILITY_DISABLED`.
- **SC-002**: Golden energy files pass under both compositions.
- **SC-003**: Record partial AT-47 and AT-53 evidence for this spec. Verify CSV/demo core-only in 012 and 024–027 and actual optional API or service guard, owner checks and prerequisite behavior with each optional module.
