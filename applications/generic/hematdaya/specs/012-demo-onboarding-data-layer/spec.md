# Feature Specification: Demo onboarding and data layer

**Feature Branch**: `012-demo-onboarding-data-layer`
**Created**: 2026-10-30
**Status**: Implemented on `f/012-013-onboarding-beranda`; Jest journey tests pass and the web build was walked against a live API. Android journey evidence via 003 is not recorded yet
**Milestone**: M2 Read journey on phone
**Depends on**: 002, 003, 008
**Size**: M
**Covers**: FR-18, UX-02, UX-05, UX-11, AT-40, S01, S02, P01
**Flips**: registry `demo` → `available`

## User Scenarios & Testing

### User Story 1 - Open the demo without text entry (Priority: P1)

**Why this priority**: PRD journey P01: useful data with no AC, schedule, production, tariff or credentials.

**Independent Test**: Coba demo → Rumah tangga → Buka demo reaches a populated session.

**Acceptance Scenarios**:

1. **Given** the welcome screen, **When** the user chooses Coba demo, Rumah tangga and Buka demo, **Then** the app shows "Menyiapkan data demo…", then Beranda with the "Demo · Data simulasi" tag and the initial period returned by the service.
2. **Given** context Industri was chosen, **When** the demo sheet opens, **Then** Industri is preselected.
3. **Given** the sheet is open, **When** the user cancels or presses Escape, **Then** focus returns to Coba demo and nothing was created.

### User Story 2 - Start empty (Priority: P1)

**Why this priority**: S01 says Mulai enters S02 for an empty workspace.

**Independent Test**: Mulai creates an `empty` session.

**Acceptance Scenarios**:

1. **Given** Mulai, **When** pressed, **Then** an empty session starts, and the screen says the workspace is temporary before accounts exist.
2. **Given** an empty workspace, **When** Coba demo is chosen on S02, **Then** the scenario choice opens.

### User Story 3 - Sessions survive a restart and expire honestly (Priority: P1)

**Why this priority**: The token is the user's only key to their demo.

**Independent Test**: Restart the app; the session resumes. Expire the token; the app explains.

**Acceptance Scenarios**:

1. **Given** a valid token, **When** the app restarts, **Then** it opens Beranda directly.
2. **Given** a stored demo token, **When** the service reports `SESSION_EXPIRED` or rejects the token with `UNAUTHORIZED` after purge, **Then** the app clears that workspace and its cached server state, explains the session is no longer usable, and offers to start again without showing a raw code.

### User Story 4 - Failure is never a dead end (Priority: P1)

**Why this priority**: FR-18 and UX-11: every primary action has pending, failure and retry.

**Independent Test**: Stop the API during session creation.

**Acceptance Scenarios**:

1. **Given** the API is down, **When** the demo loads, **Then** the sheet stays open with the failure and Coba lagi, and retry uses the same request.
2. **Given** the service committed creation but the response was lost, **When** the user retries within 008's replay window, **Then** the unchanged request, operation ID and replay proof recover the same workspace and token, with one seeded session.
3. **Given** the replay window elapsed without a confirmed workspace, **When** the retry is refused, **Then** the app explains the unknown outcome and offers an explicit new start. It never silently starts a new session.

### Edge Cases

- `retryable`, `retry_after_seconds` and `max_attempts` from `recovery` govern retries, including the first attempt in the limit.
- Web stores the token in `sessionStorage`, because `expo-secure-store` has no web build. This is demo-only; 036 decides real sessions.

## Requirements

### Functional Requirements

- **FR-001**: All server state MUST go through one TanStack Query client.
- **FR-002**: The token MUST be stored in secure storage on native.
- **FR-003**: Period, scope and site MUST live in one navigation context provider.
- **FR-004**: The provenance tag MUST appear on every screen with demo data.
- **FR-005**: Mutations MUST expose pending, success, failure and unknown states.
- **FR-006**: Each intentional session creation MUST generate and reuse the same `Idempotency-Key` and separate secret `X-Demo-Replay-Proof` for retries of the unchanged request, as defined by 008. The replay proof MUST stay out of logs, diagnostics and ordinary drafts.

### Key Entities

- **Workspace**: token, site ID, scenario, kind, expiry, held on the device.

## Success Criteria

### Measurable Outcomes

- **SC-001**: From welcome, a populated demo needs at most three taps and no text entry.
- **SC-002**: A demo journey test passes on web and Android (003).
