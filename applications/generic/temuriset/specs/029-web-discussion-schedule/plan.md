# Implementation Plan: Discussion, schedule and Beranda queue

**Branch**: `029-web-discussion-schedule` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
applications/temuriset-web/src/
├── app/home/page.tsx             # queue and notifications replace the base empty state
├── components/tr/ScheduleSlotList.tsx
├── features/scheduling/{time.ts, propose.ts, confirm.ts}
├── features/discussion/{use-messages.ts, use-notifications.ts}
└── views/pitches/{DiscussionTab, ScheduleTab}.tsx, views/HomeView.tsx
e2e/j04-schedule.spec.ts
```

## Prototype Reference

`vm.schedule`, `vm.home`, `Schedule.dc.html`, `Home.dc.html`; walker `j04`, `more2` replacement path; the "completed panel" defect fixed in the prototype.

## Test Plan

Time formatting in WIB, WITA and WIT; schedule tab states; conflict copy; queue ordering; J04 Playwright; axe; keyboard.

## Out of Scope

External calendars (043).

## Task Outline

1. Time formatting with tests.
2. Discussion tab with polling.
3. Schedule tab: propose, choose, confirm, conflict, expiry, replacement, outcome.
4. Beranda queue and notifications.
5. J04 journey, registry flips.
