# Feature Specification: Race-safe meeting scheduling

**Feature Branch**: `028-scheduling-api`
**Created**: 2026-11-05
**Status**: Seeded, not started
**Milestone**: M8 Discussion and scheduling
**Depends on**: 025
**Size**: L
**Covers**: FR17, AC47, AC49, AC50, AC51, AC68
**Flips**: manifest adapter `ics-export` → `available`

## User Scenarios & Testing

### User Story 1 - Propose, choose, confirm (Priority: P1)

After approval, either coordinator proposes 2–5 slots of 30 or 60 minutes with an IANA zone, agenda and optional HTTPS link. The other party chooses one and confirms, or counters with 2–5 alternatives. Choosing is not booking.

**Acceptance Scenarios**:

1. **Given** slots on 4 November at 09:00, 11:00 and 13:00 UTC, **When** read by an account in Asia/Jakarta and one in Asia/Makassar, **Then** 09:00 UTC shows as 16.00 WIB and 17.00 WITA for the same instant (AC49).
2. **Given** Peserta P is booked 09:00–10:00, **When** Rani accepts 09:00, **Then** `BOOKING_CONFLICT` keeps the proposal, agenda and other slots.
3. **Given** a counter with 09:30 and 10:00, **When** Mitra A accepts 09:30, **Then** conflict; **When** 10:00 is accepted, **Then** it succeeds under half-open intervals and exactly one confirmed meeting exists.
4. **Given** two overlapping acceptances race, **When** both commit, **Then** one booking commits and the other gets a recoverable conflict (AC50).
5. **Given** a confirmed meeting and a replacement proposal, **When** the replacement is not yet accepted, **Then** the old meeting and bookings stay; on acceptance they are replaced in one transaction (AC51).

### User Story 2 - Time passes honestly (Priority: P1)

**Acceptance Scenarios**:

1. **Given** a proposal created 2 November 08:00 UTC with slots on 6 November, **When** the clock reaches 5 November 08:00, **Then** it expires by age at exactly 72 hours.
2. **Given** all slots have passed before 72 hours, **When** read, **Then** it is expired with reason "all slots past", and the pitch stays approved for discussion.
3. **Given** a meeting time has passed, **When** no outcome is recorded, **Then** the meeting stays `CONFIRMED`; nothing marks it completed (AC47).
4. **Given** both parties record "completed", **When** read, **Then** it is `COMPLETED`; different outcomes stay visible as a disagreement.

### User Story 3 - Calendar file without a calendar connection (Priority: P2)

**Acceptance Scenarios**:

1. **Given** a confirmed meeting and no calendar adapter, **When** ICS is downloaded, **Then** it contains `DTSTART:20261104T100000Z` and `DTEND:20261104T110000Z`, and the UI says external availability is unknown (AC68).

### Edge Cases

- The proposer cannot accept its own proposal.
- Slots in the past are refused at proposal time.
- Cancelling a proposal never cancels a meeting; cancelling a meeting is a separate action.

## Requirements

### Functional Requirements

- **FR-001**: Bookings MUST use `tstzrange` with a GiST exclusion constraint per party.
- **FR-002**: Accept and replace MUST be single transactions with idempotency keys.
- **FR-003**: Expiry MUST be evaluated on read and by a worker job; policy `proposal-expiry` v1 holds 72 hours.
- **FR-004**: ICS MUST be generated from stored UTC instants.

### Key Entities

- **ScheduleProposal**, **ScheduleSlot**, **Meeting**, **Booking**, **MeetingOutcome**.

## Success Criteria

### Measurable Outcomes

- **SC-001**: AC47 and AC49–AC51 pass; a 50-way concurrent acceptance test yields one booking per party and interval.
