# Feature Specification: Insight feedback

**Feature Branch**: `023-feedback`
**Created**: 2026-10-30
**Status**: Seeded, not started
**Milestone**: M4 Evidence
**Depends on**: 022
**Size**: M
**Covers**: FR-14, AT-39, S08, P10
**Flips**: registry `bukti-saran` → `available`

## User Scenarios & Testing

### User Story 1 - Respond without consequence (Priority: P1)

**Why this priority**: Feedback must never touch data or equipment (PRD §9 FR-14).

**Independent Test**: Give feedback, compare readings.

**Acceptance Scenarios**:

1. **Given** evidence, **When** Berguna is chosen, **Then** it shows pending, then confirmed after acknowledgment.
2. **Given** a failed save, **When** it fails, **Then** retry is offered and nothing changed.
3. **Given** a timeout with unknown result, **When** retried, **Then** the same idempotency key avoids a duplicate.
4. **Given** a key was used for one action, **When** reused by the owner for a different insight, revision or action, **Then** the request is rejected without applying another change.

### User Story 2 - Hide, snooze, restore (Priority: P1)

**Why this priority**: P10.

**Independent Test**: Hide from S08, restore from the hidden list.

**Acceptance Scenarios**:

1. **Given** Sembunyikan, **When** acknowledged, **Then** the app returns to its invoker with a restore link.
2. **Given** Tunda hingga besok on a demo site, **When** acknowledged, **Then** the item returns at the next local midnight of the site clock, and the time is shown.
3. **Given** Saran tersembunyi, **When** Pulihkan is pressed, **Then** the item returns.

### User Story 3 - Feedback follows its evidence (Priority: P2)

**Why this priority**: FR-19.

**Independent Test**: Change data, reopen.

**Acceptance Scenarios**:

1. **Given** feedback on revision 1, **When** revision 2 appears, **Then** the old feedback stays with revision 1 and the screen says the evidence was updated.

### Edge Cases

- Feedback is scoped to the insight and the owner.
- Equivalent recomputation preserves feedback.
- A frozen virtual clock means a snooze persists until the scenario resets; the screen shows the return time either way.

## Requirements

### Functional Requirements

- **FR-001**: `POST /insights/{id}/feedback` MUST accept useful, not relevant, snooze, hide and restore.
- **FR-002**: The route MUST scope `Idempotency-Key` by owner and operation, replay the original result for the same insight, revision and action, and reject conflicting reuse. The idempotency record and effect MUST commit together.
- **FR-003**: Feedback MUST reference a revision of the addressed insight, and the owner MUST be authorized for both. Preserve existing feedback when an equivalent evaluation reuses its revision.
- **FR-004**: No feedback action MAY affect measurements.

### Key Entities

- **InsightFeedback**: insight, revision, principal, action, until.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Measurement identities, values and derived totals are unchanged by any feedback action or retry.
- **SC-002**: AT-39 ported test passes through the API.
