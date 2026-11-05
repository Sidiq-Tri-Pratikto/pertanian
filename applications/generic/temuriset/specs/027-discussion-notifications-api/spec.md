# Feature Specification: Discussion, tasks, notifications and whose turn

**Feature Branch**: `027-discussion-notifications-api`
**Created**: 2026-11-05
**Status**: Seeded, not started
**Milestone**: M8 Discussion and scheduling
**Depends on**: 025
**Size**: M
**Covers**: FR16, AC46, AC48
**Flips**: none

## User Scenarios & Testing

### User Story 1 - A shared room that says who acts next (Priority: P1)

Pitch-scoped messages and tasks, in-app notifications from outbox consumers, and a whose-turn projection with one next action per party.

**Acceptance Scenarios**:

1. **Given** a submitted pitch, **When** each party reads `next_action`, **Then** the recipient gets "Putuskan pitching ini" as `you` and the requester gets the same pitch as `other`.
2. **Given** an approved pitch, **When** a clarification is needed, **Then** a task with owner party, due date and reference is created and approval history stays.
3. **Given** a decision commits and the email adapter (042) fails, **When** delivery retries, **Then** the decision exists once and notifications are deduplicated per event, recipient and channel (AC46).
4. **Given** an unrelated user, **When** it requests messages, files or the room, **Then** every route answers `NOT_FOUND` with no metadata (AC48).

### User Story 2 - Notifications in the app (Priority: P2)

**Acceptance Scenarios**:

1. **Given** a submission, decision, revision, schedule or confirmation event, **When** consumed, **Then** each party that must act gets one in-app notification linking to the room.
2. **Given** notifications, **When** marked read, **Then** only that party's read state changes.

### Edge Cases

- Polling every 30 seconds is enough in R1; no realtime transport.
- Message text is never logged and never sent to analytics.
- An empty message is refused with a field message.

## Requirements

### Functional Requirements

- **FR-001**: The whose-turn projection MUST be computed on the server from pitch, proposal, meeting and partnership state, covering every state in the prototype's `pitchTurn`.
- **FR-002**: Notifications MUST be outbox consumers, idempotent per event and recipient.
- **FR-003**: Lists MUST paginate and support `since` for polling.

### Key Entities

- **Message**, **Task**, **Notification**, **NextAction**.

## Success Criteria

### Measurable Outcomes

- **SC-001**: AC46 and AC48 pass; a whose-turn table test covers every state for both parties.
