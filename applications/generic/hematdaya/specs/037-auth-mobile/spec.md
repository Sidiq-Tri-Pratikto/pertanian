# Feature Specification: Accounts on mobile

**Feature Branch**: `037-auth-mobile`
**Created**: 2026-10-30
**Status**: Seeded, not started
**Milestone**: M9 Saved service
**Depends on**: 012, 036
**Size**: M
**Covers**: FR-01, AT-40
**Flips**: registry `akun` → `available`

## User Scenarios & Testing

### User Story 1 - Sign in without losing the demo path (Priority: P1)

**Why this priority**: The demo stays credential-free; saved data needs an account.

**Independent Test**: Register, sign out, demo still works.

**Acceptance Scenarios**:

1. **Given** Mulai, **When** the user chooses to save data, **Then** register and login screens appear, and demo stays one tap away.
2. **Given** a signed-in user, **When** the app restarts, **Then** the session resumes.
3. **Given** logout, **When** confirmed, **Then** tokens and cached data for that user are cleared.

### User Story 2 - Session expiry keeps work (Priority: P1)

**Why this priority**: AT-40.

**Independent Test**: Expire during a save.

**Acceptance Scenarios**:

1. **Given** an expired session during a save, **When** it fails, **Then** the non-secret draft stays, the login boundary shows, and retry after login is explicit.
2. **Given** retry after login, **When** run, **Then** no duplicate commit occurs.

### Edge Cases

- Passwords never persist in a draft.
- Refresh failure on two tabs on web does not sign out twice.

## Requirements

### Functional Requirements

- **FR-001**: Tokens MUST be stored per the decision in 036.
- **FR-002**: Refresh MUST be single-flight.
- **FR-003**: Forms MUST support password managers and platform autofill.

### Key Entities

Session on device.

## Success Criteria

### Measurable Outcomes

- **SC-001**: AT-40 passes for tariff, schedule, import and scope saves.
