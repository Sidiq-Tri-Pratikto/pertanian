# Implementation Plan: Race-safe meeting scheduling

**Branch**: `028-scheduling-api` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
app/scheduling/
├── router.py                     # /pitches/{id}/schedule-proposals, /schedule-proposals/{id}/accept|counter|cancel,
│                                 #   /meetings/{id}, /reschedule, /cancel, /outcome, /calendar.ics
├── service/proposals.py          # validate 2–5 slots, 30/60, future, zone, https link
├── service/booking.py            # transaction: lock proposal, insert bookings, rely on EXCLUDE, map IntegrityError to BOOKING_CONFLICT
├── service/expiry.py             # lazy check and worker job
├── service/ics.py
└── repository/sqlalchemy/        # schedule_proposals, schedule_slots, meetings, bookings, meeting_outcomes
migrations/versions/0015_scheduling.py   # CREATE EXTENSION btree_gist; EXCLUDE constraint
```

## Prototype Reference

`proposeSlots`, `acceptSlot`, `expireIfDue`, `recordOutcome`, `ics` in `domain.js`; oracles J04, SCHED-72H, all-slots-past, AC47, AC51.

## Test Plan

AC47, AC49–AC51; both expiry kinds with a frozen clock; proposer cannot accept; past slots refused; concurrency test against Postgres; ICS contents; isolation.

## Out of Scope

External calendars (043), web (029).

## Task Outline

1. Migration with exclusion constraint; failing AC tests.
2. Proposals and counters.
3. Accept with conflict mapping; concurrency test.
4. Replacement and cancellation.
5. Expiry, outcomes, ICS; manifest flip.
