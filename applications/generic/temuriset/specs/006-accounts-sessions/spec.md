# Feature Specification: Accounts and sessions

**Feature Branch**: `006-accounts-sessions`
**Created**: 2026-11-05
**Status**: Built, awaiting review
**Milestone**: M1 Identity and access
**Depends on**: 005
**Size**: L
**Covers**: FR01, AC01, AC02
**Flips**: none (the web registry entry `akun` flips at 008)

## User Scenarios & Testing

### User Story 1 - Sign up with a verified email and no institution (Priority: P1)

An independent inventor or an individual investor creates an account with display name, email, locale, time zone and persona. A personal party exists immediately. No organization or affiliation is asked for.

**Why this priority**: FR01 and AC01–AC02; everything after this needs an account.

**Independent Test**: Request a code, read it from the development mailbox, verify, and read `/me`.

**Acceptance Scenarios**:

1. **Given** a new email, **When** `POST /auth/code` is sent with purpose `sign_up`, display name, locale `id`, time zone `Asia/Jakarta` and persona `inovator`, **Then** a six-digit code is mailed and the response reveals nothing about whether the email already exists.
2. **Given** the right code within 10 minutes, **When** `POST /auth/verify` is sent, **Then** the account is verified, a personal party is created, the `tr_session` cookie is set, and `GET /me` returns the account with `organizations: []` (AC01).
3. **Given** persona `mitra`, **When** the account is created, **Then** no organization is required and partner intake fields become available later on the personal party (AC02).
4. **Given** an existing account, **When** it signs in with a new code, **Then** a new session starts and earlier sessions stay valid until they expire or are revoked.

### User Story 2 - Failures keep the form and explain the fix (Priority: P1)

**Acceptance Scenarios**:

1. **Given** a wrong code, **When** it is verified, **Then** `CODE_INVALID` states the attempts left, and the display name and email typed earlier are not lost on the client.
2. **Given** five wrong codes or an expired code, **When** verification is tried, **Then** `CODE_EXPIRED` asks for a new code.
3. **Given** more than five code requests per email per hour or 20 per address, **When** another is sent, **Then** `RATE_LIMITED` with `retry_after_seconds` is returned.
4. **Given** no session, **When** `/me` is called, **Then** `UNAUTHENTICATED` is returned.

### User Story 3 - Sign out and session safety (Priority: P2)

**Acceptance Scenarios**:

1. **Given** a session, **When** `POST /auth/sign-out` is sent, **Then** the session is revoked and the cookie cleared.
2. **Given** a POST from another origin, **When** it carries the session cookie, **Then** it is refused with `FORBIDDEN` before any handler runs.

### Edge Cases

- A verified email proves control of the address only; nothing implies verified funds, identity, expertise or ownership. The account has no badge beyond "Email terverifikasi".
- Emails are case-insensitive and trimmed; codes are compared in constant time and stored hashed.
- Changing persona or time zone later goes through `PATCH /me`.

## Requirements

### Functional Requirements

- **FR-001**: Accounts MUST store display name, email, verification time, locale, IANA time zone, persona and kind (`user`, `demo`).
- **FR-002**: Sign-in MUST use emailed one-time codes; no password is stored.
- **FR-003**: Sessions MUST be opaque, stored hashed, sent as an http-only `SameSite=Lax` cookie, `Secure` outside development, 30-day sliding expiry.
- **FR-004**: Every unsafe request MUST pass an `Origin` check against `WEB_ORIGIN`.
- **FR-005**: The mailbox adapter MUST be readable only in development and tests; production refuses to start with it.
- **FR-006**: Every account MUST get exactly one personal party at verification (the `parties` table arrives here with only the personal kind; 007 adds organizations).

### Key Entities

- **Account**, **EmailCode**, **Session**, **Party** (personal), **MailboxMessage**.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Each failure path asserts code, Indonesian message, recovery, request ID, record, and that the code and email never appear in logs.
- **SC-002**: A brute-force test of 1,000 guesses is stopped after five per code and by the rate limit.
