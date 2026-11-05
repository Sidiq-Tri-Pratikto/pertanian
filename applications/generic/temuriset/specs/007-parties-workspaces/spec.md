# Feature Specification: Parties, organizations and memberships

**Feature Branch**: `007-parties-workspaces`
**Created**: 2026-11-05
**Status**: Seeded, not started
**Milestone**: M1 Identity and access
**Depends on**: 006
**Size**: L
**Covers**: FR02, AC04, AC05, AC06
**Flips**: none

## User Scenarios & Testing

### User Story 1 - Act for an organization only with the right capability (Priority: P1)

An account can create an organization, invite members with explicit capabilities, and switch its active context. Each request is authorized against the active party's membership and the object's permission.

**Why this priority**: FR02; every later data route uses this policy and its isolation test.

**Independent Test**: Two organizations and three accounts exercised through the policy and a test route.

**Acceptance Scenarios**:

1. **Given** Bima creates "Demo Circular Materials Ltd", **When** it is created, **Then** an organization party exists and Bima is a member with every capability.
2. **Given** an invitation with capability `edit_portfolio` only, **When** it is accepted within seven days, **Then** the member can edit but a `decide_pitch` action is refused with `FORBIDDEN` (AC04).
3. **Given** an account, **When** it sets its active party to an organization it has not joined, **Then** the change is refused with `NOT_FOUND` and no metadata about that organization is returned (AC05).
4. **Given** an expired or revoked invitation, **When** it is accepted, **Then** `INVITATION_EXPIRED` is returned.
5. **Given** a member is removed while a job they started is pending, **When** the job runs or its result is fetched, **Then** access is rechecked and denied (AC06).

### User Story 2 - Two tabs cannot cross contexts (Priority: P1)

**Acceptance Scenarios**:

1. **Given** a session whose active party changed in another tab, **When** a consequential mutation sends the old `acting_party_id`, **Then** it is refused with `STALE_CONTEXT` and nothing changes.

### User Story 3 - Isolation is tested from the first data route (Priority: P1)

**Acceptance Scenarios**:

1. **Given** the two-party isolation harness, **When** it walks every registered data route as an unrelated party, **Then** each returns `NOT_FOUND` or an empty list and never another party's data.

### Edge Cases

- An individual investor or inventor never needs an organization; the personal party is always available.
- Removing the last member with `manage_members` is refused.
- Historical authorship stays after a member is removed.

## Requirements

### Functional Requirements

- **FR-001**: A PartyReference MUST be exactly one personal or organization party.
- **FR-002**: Capabilities MUST be `edit_portfolio`, `submit_pitch`, `review_publication`, `decide_pitch`, `confirm_relationship`, `schedule`, `manage_members`.
- **FR-003**: Invitations MUST expire after seven days, be revocable, and store only a token hash.
- **FR-004**: `PUT /me/context` MUST check membership; every request MUST recheck it.
- **FR-005**: One policy module MUST answer `NOT_FOUND` for invisible objects and `FORBIDDEN` for visible objects with a missing capability.
- **FR-006**: The isolation harness MUST run in CI and each data PR MUST register its routes.

### Key Entities

- **Party**, **Organization**, **Membership**, **Invitation**, **Principal** (account, active party, capabilities).

## Success Criteria

### Measurable Outcomes

- **SC-001**: The isolation harness covers every route in the contract except health, capabilities and auth.
