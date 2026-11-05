# Feature Specification: Web sign-in, onboarding and context

**Feature Branch**: `008-web-auth-context`
**Created**: 2026-11-05
**Status**: Built, awaiting review
**Milestone**: M1 Identity and access
**Depends on**: 002, 007
**Size**: L
**Covers**: FR01, FR02, S01, S18, UX-01, UX-02, UX-09
**Flips**: web registry `akun` → `available`

## User Scenarios & Testing

### User Story 1 - Start, verify and land in the right place (Priority: P1)

S01 becomes real: choose a persona, enter display name, email, language and time zone, receive a code, verify, and land on the persona's first destination. Organization and affiliation are not asked.

**Why this priority**: UX-01; every later screen needs a signed-in party.

**Independent Test**: Playwright signs up an inventor and a partner using the development mailbox.

**Acceptance Scenarios**:

1. **Given** a new visitor, **When** they complete S01 and enter the code, **Then** Beranda (inventor) or Jelajahi (partner) opens and no organization field was shown (UX-01).
2. **Given** a wrong code, **When** it is submitted, **Then** an error summary receives focus, links to the code field, states attempts left, and every typed value stays (UX-09).
3. **Given** an expired session, **When** any page loads, **Then** it redirects to sign-in and returns to the page after sign-in.

### User Story 2 - See and change who you act as (Priority: P1)

**Acceptance Scenarios**:

1. **Given** an account with a personal party and one organization, **When** any page renders, **Then** the bar shows `TR.ContextSwitcher` with "Bertindak sebagai" and both options (UX-02).
2. **Given** a switch to the organization, **When** it succeeds, **Then** the page reloads in that context and a status announces the change without moving focus.
3. **Given** a consequential action screen, **When** it renders, **Then** the read-only switcher shows the acting party beside the primary action.

### User Story 3 - Members and invitations (Priority: P2)

**Acceptance Scenarios**:

1. **Given** an organization manager, **When** they invite a member with chosen capabilities, **Then** the invitation shows its expiry and can be revoked.
2. **Given** an invitation link, **When** a signed-in account opens it, **Then** it shows the organization, capabilities and expiry before "Terima undangan".

### Edge Cases

- The persona cookie from 002 seeds the persona field once, then is removed.
- Context switch failure keeps the old context and explains why.
- Sign-out ends the session everywhere in this browser.

## Requirements

### Functional Requirements

- **FR-001**: S01 MUST collect display name, email, locale and time zone, and never an organization.
- **FR-002**: The code screen MUST show where the code went and allow resending after the rate-limit wait.
- **FR-003**: Server Components MUST read `/me` with forwarded cookies; unauthenticated pages redirect to `/start`.
- **FR-004**: The context switcher MUST appear in the bar on every signed-in screen; read-only beside consequential actions.
- **FR-005**: S18 MUST show account fields, persona, time zone and organization memberships.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Playwright covers sign-up for both personas, wrong code, context switch and sign-out; the 003 suite covers the new routes.
