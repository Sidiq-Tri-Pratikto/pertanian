# Feature Specification: Email delivery adapter (gated)

**Feature Branch**: `042-email-adapter`
**Created**: 2026-11-05
**Status**: Seeded, not started; gated
**Milestone**: M12 Gated adapters
**Depends on**: 027, 037
**Size**: M
**Covers**: FR16, AC46
**Flips**: manifest adapter `email` → `available`; web registry `pemberitahuan-email` → `available`

**Entry condition**: an approved provider, sender domain with SPF, DKIM and DMARC, and accepted processing terms.

## User Scenarios & Testing

### User Story 1 - Codes and notifications by email, never duplicated decisions (Priority: P1)

**Acceptance Scenarios**:

1. **Given** sign-in, **When** a code is requested, **Then** the provider sends it and the development mailbox is off.
2. **Given** a notification with email enabled in preferences, **When** delivery fails, **Then** it retries with backoff and the decision stays single (AC46).
3. **Given** preferences off, **When** an event occurs, **Then** only in-app notification is created.

## Requirements

### Functional Requirements

- **FR-001**: The adapter MUST be a `MailboxAdapter` implementation behind configuration validation.
- **FR-002**: Templates MUST be Indonesian and contain no private document content.

## Success Criteria

### Measurable Outcomes

- **SC-001**: A provider sandbox test and a failure-retry test pass.
