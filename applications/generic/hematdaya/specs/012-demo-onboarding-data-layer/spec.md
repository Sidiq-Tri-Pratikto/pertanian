# Feature Specification: Demo onboarding and data layer

**Feature Branch**: `012-demo-onboarding-data-layer`
**Created**: 2026-10-30
**Status**: Seeded, not started
**Milestone**: M2 Read journey on phone
**Depends on**: 002, 008
**Size**: M
**Covers**: FR-18, UX-02, UX-05, UX-11, AT-40, S01, S02, P01
**Flips**: registry `demo` → `available`

## User Scenarios & Testing

### User Story 1 - Open the demo in two taps (Priority: P1)

**Why this priority**: PRD journey P01: useful data with no AC, schedule, production, tariff or credentials.

**Independent Test**: Coba demo → Rumah tangga → Buka demo reaches a populated session.

**Acceptance Scenarios**:

1. **Given** the welcome screen, **When** the user chooses Coba demo and Rumah tangga, **Then** the app shows "Menyiapkan data demo…", then Beranda with the "Demo · Data simulasi" tag.
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
2. **Given** an expired session, **When** a request fails with `SESSION_EXPIRED`, **Then** the app explains and offers to start again, with no raw code shown.

### User Story 4 - Failure is never a dead end (Priority: P1)

**Why this priority**: FR-18 and UX-11: every primary action has pending, failure and retry.

**Independent Test**: Stop the API during session creation.

**Acceptance Scenarios**:

1. **Given** the API is down, **When** the demo loads, **Then** the sheet stays open with the failure and Coba lagi, and retry uses the same request.
2. **Given** a retry after a timeout, **When** it succeeds, **Then** only one session exists.

### Edge Cases

- `max_attempts` from `recovery` stops automatic retries.
- Web stores the token in `sessionStorage`, because `expo-secure-store` has no web build. This is demo-only; 036 decides real sessions.

## Requirements

### Functional Requirements

- **FR-001**: All server state MUST go through one TanStack Query client.
- **FR-002**: The token MUST be stored in secure storage on native.
- **FR-003**: Period, scope and site MUST live in one navigation context provider.
- **FR-004**: The provenance tag MUST appear on every screen with demo data.
- **FR-005**: Mutations MUST expose pending, success, failure and unknown states.

### Key Entities

- **Workspace**: token, site ID, scenario, kind, expiry, held on the device.

## Success Criteria

### Measurable Outcomes

- **SC-001**: From welcome, a populated demo needs at most three taps and no text entry.
- **SC-002**: A demo journey test passes on web and Android (003).
