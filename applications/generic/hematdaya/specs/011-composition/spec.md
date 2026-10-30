# Feature Specification: Composition enforcement

**Feature Branch**: `011-composition`
**Created**: 2026-10-30
**Status**: Seeded, not started
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

1. **Given** `core-only`, **When** an optional capability is used through the API or a service call, **Then** it fails with `CAPABILITY_DISABLED` and a reason naming the capability.
2. **Given** `core-plus-optional`, **When** the same call runs, **Then** it proceeds.

### User Story 2 - Core-only is a complete product (Priority: P1)

**Why this priority**: AT-47: CSV and demo work with no broker, meter, AI or push.

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
- **FR-003**: Summaries MUST report `capability_disabled` for an unavailable optional value.
- **FR-004**: CI MUST run the core energy tests under both compositions.

### Key Entities

- **Composition**: ID, version, capabilities, adapters, policy versions.

## Success Criteria

### Measurable Outcomes

- **SC-001**: A test bypassing the router still gets `CAPABILITY_DISABLED`.
- **SC-002**: Golden energy files pass under both compositions.
