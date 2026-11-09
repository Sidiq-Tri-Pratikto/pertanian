# Feature Specification: Accounts on mobile

**Feature Branch**: `037-auth-mobile`
**Created**: 2026-10-30
**Status**: Seeded, not started
**Milestone**: M9 Saved service
**Depends on**: 012, 027, 029, 034, 036
**Size**: M
**Covers**: FR-01, AT-40
**Flips**: registry `akun` → `available`

## Pilot account scope

Ship sign-in, session recovery and owner-isolated draft handling for the core app. Verify available core saves before the pilot release. Optional tariff, schedule, output and push work can proceed separately. Any later save flow must pass the same expiry, ownership and replay checks before its own release.

## User Scenarios & Testing

### User Story 1 - Sign in without losing the demo path (Priority: P1)

**Why this priority**: The demo stays credential-free; saved data needs an account.

**Independent Test**: Register, sign out, demo still works.

**Acceptance Scenarios**:

1. **Given** the saved-data entry, **When** the user chooses to sign in, **Then** register and login screens appear, and the separate demo entry remains available.
2. **Given** a signed-in user, **When** the app restarts, **Then** the session resumes.
3. **Given** logout, **When** confirmed, **Then** tokens and cached data for that user are cleared.

### User Story 2 - Session expiry keeps work (Priority: P1)

**Why this priority**: AT-40.

**Independent Test**: Expire during a save.

**Acceptance Scenarios**:

1. **Given** an expired session during a save, **When** it fails, **Then** the non-secret draft stays, the login boundary shows, and retry after login is explicit.
2. **Given** retry after login, **When** run, **Then** no duplicate commit occurs.
3. **Given** a different owner logs in, **When** the previous session expired during a save, **Then** the previous owner's draft and confirmed data are unavailable to that owner.

### Edge Cases

- Passwords never persist in a draft.
- Two tabs using the same web refresh cookie share one refresh operation. Terminal failure is propagated to both tabs.

## Requirements

### Functional Requirements

- **FR-001**: Tokens MUST be stored per the decision in 036.
- **FR-002**: Refresh MUST be single-flight within a native client and across web tabs that share the refresh cookie.
- **FR-003**: Forms MUST support password managers and platform autofill.

### Key Entities

Session on device.

## Success Criteria

### Measurable Outcomes

- **SC-001**: AT-40 passes for the core import and scope saves. Apply the same checks to optional saves when they ship and meter enrollment before user-facing release.
