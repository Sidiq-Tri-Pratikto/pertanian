# Feature Specification: Accounts API

**Feature Branch**: `036-auth-api`
**Created**: 2026-10-30
**Status**: Seeded, not started
**Milestone**: M9 Saved service
**Depends on**: 004, 008, 025
**Size**: L
**Covers**: FR-01, AT-41
**Flips**: registry `akun` stays `coming_soon` until 037

## User Scenarios & Testing

### User Story 1 - Own saved data (Priority: P1)

**Why this priority**: G3 requires verified ownership before any saved data is offered.

**Independent Test**: Register, log in, reach an owned site.

**Acceptance Scenarios**:

1. **Given** registration, **When** it succeeds, **Then** a user principal and one owned standard site exist.
2. **Given** login, **When** valid, **Then** a short-lived access token and a rotating refresh session are issued.
3. **Given** logout, **When** called, **Then** the session is revoked.

### User Story 2 - Isolation holds everywhere (Priority: P1)

**Why this priority**: AT-41: denied on all reads, mutations and exports without leakage.

**Independent Test**: Walk every route with a second user.

**Acceptance Scenarios**:

1. **Given** a second user, **When** any data route is called with the first user's ID, **Then** the response is `NOT_FOUND`.
2. **Given** a demo token, **When** it calls a shared data route, **Then** it reaches only its own demo site. Account-only routes reject it.

### User Story 3 - Resist abuse (Priority: P1)

**Why this priority**: PRD §17 requires rate limits on authentication, imports and exports.

**Independent Test**: Exceed the login limit.

**Acceptance Scenarios**:

1. **Given** repeated failed logins, **When** the limit is hit, **Then** the retryable `RATE_LIMITED` envelope returns with `Retry-After`.
2. **Given** a reused refresh token, **When** presented, **Then** the whole session family is revoked.
3. **Given** two concurrent refreshes with the same valid token, **When** both arrive, **Then** at most one rotation succeeds. Confirmed reuse revokes the family, including the new refresh token and all of its access tokens.

### Edge Cases

- Passwords and tokens never reach logs, traces or `debug_info`.
- Login errors do not reveal whether an account exists.
- Web session handling must be decided here, because `expo-secure-store` has no web build.

## Requirements

### Functional Requirements

- **FR-001**: Routes MUST match PRD §16: register, login, refresh, logout, `/me`.
- **FR-002**: Passwords MUST be hashed with Argon2id.
- **FR-003**: Refresh tokens MUST rotate atomically with reuse detection. Once logout or reuse revocation is committed, all access and refresh tokens in that family MUST fail authorization.
- **FR-004**: The resolver MUST add user principals without touching site ownership.
- **FR-005**: Rate limits MUST work across instances on auth, anonymous demo admission per client and import preview per principal.

### Key Entities

- **User**, **RefreshSession**.

## Success Criteria

### Measurable Outcomes

- **SC-001**: An automated route walk proves AT-41 for every data route.
- **SC-002**: A sanitizer test with fake secrets finds them nowhere.
