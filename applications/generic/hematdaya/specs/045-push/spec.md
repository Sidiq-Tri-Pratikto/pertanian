# Feature Specification: Push notifications

**Feature Branch**: `045-push`
**Created**: 2026-10-30
**Status**: Seeded, gated
**Milestone**: M11 Gated
**Depends on**: 021, 023, 042
**Size**: M
**Covers**: FR-14
**Flips**: registry `notifikasi` → `available`

**Entry condition**: native builds exist (042), and the owner confirms users want push. In-app Saran stays the required channel.

## User Scenarios & Testing

### User Story 1 - Consent first (Priority: P1)

**Why this priority**: Push is off until consent, and the core never depends on it.

**Independent Test**: Fresh install; no prompt appears.

**Acceptance Scenarios**:

1. **Given** a fresh install, **When** used, **Then** no permission prompt appears.
2. **Given** the user opts in, **When** a new observation revision appears, **Then** one notification is sent.
3. **Given** the same revision, **When** recomputed, **Then** no repeat is sent.
4. **Given** a notification is queued, **When** consent or registration is withdrawn before dispatch, **Then** it is discarded without contacting the gateway.

### Edge Cases

- Gateway acceptance is not delivery proof, so the UI never says "delivered".
- If gateway acceptance is unknown after a timeout, retry only when the gateway supports the same idempotency key. Otherwise keep the attempt unresolved and do not send it again.
- Copy carries no urgency or guilt.

## Requirements

### Functional Requirements

- **FR-001**: Routes MUST match PRD §16 notification preferences and push registrations.
- **FR-002**: Notifications MUST NOT be able to trigger an actuator.
- **FR-003**: Dispatch MUST be deduplicated by owner, observation revision and registration. The sender MUST check current consent, registration and feedback visibility before dispatch.

### Key Entities

- **NotificationPreference**, **PushRegistration**.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Opt-out stops all sends within one evaluation cycle.
