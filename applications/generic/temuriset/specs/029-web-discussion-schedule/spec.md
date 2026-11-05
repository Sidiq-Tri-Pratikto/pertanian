# Feature Specification: Discussion, schedule and Beranda queue

**Feature Branch**: `029-web-discussion-schedule`
**Created**: 2026-11-05
**Status**: Seeded, not started
**Milestone**: M8 Discussion and scheduling
**Depends on**: 026, 027, 028
**Size**: L
**Covers**: S02, S14, UX-13, UX-14, J04
**Flips**: web registry `diskusi` and `jadwal` → `available`

## User Scenarios & Testing

### User Story 1 - Beranda shows what waits (Priority: P1)

S02 shows the queue from `/me/queue`: the first item as `TR.NextStep`, the rest as rows with "Menunggu Anda" or "Menunggu pihak lain", and in-app notifications.

**Acceptance Scenarios**:

1. **Given** a pending revision and a proposal waiting for the other party, **When** Beranda opens, **Then** "Jawab permintaan revisi" leads, and the proposal row says "Menunggu pihak lain".

### User Story 2 - Choose a time without confusion (Priority: P1)

S14 inside the room: propose with slot selects in the viewer's zone, choose with `TR.ScheduleSlotList` showing both zones, confirm explicitly (UX-13).

**Acceptance Scenarios**:

1. **Given** a chosen slot, **When** not yet confirmed, **Then** it reads "Dipilih, belum dikonfirmasi" and no meeting exists.
2. **Given** a conflict, **When** confirming, **Then** a live alert explains it, the agenda and other slots stay, and "Usulkan waktu lain" pre-fills alternatives (UX-14).
3. **Given** an expired proposal, **When** the tab opens, **Then** the reason is stated and the pitch remains approved.
4. **Given** a confirmed meeting with a pending replacement, **When** viewed, **Then** both are shown, and the old meeting stays until the replacement is confirmed.
5. **Given** a confirmed meeting, **When** "Unduh ICS" is pressed, **Then** the file downloads and the ICS text is readable in a Disclosure.

### User Story 3 - J04 end to end (Priority: P1)

**Acceptance Scenarios**:

1. **Given** the J04 path, **When** Playwright runs it as both parties, **Then** propose → conflict → counter → conflict → confirm 10:00 → replacement → record outcomes completes.

### Edge Cases

- Discussion tab: messages and tasks with polling; failed send keeps the text.
- A completed meeting shows a completed panel instead of the proposal form.

## Requirements

### Functional Requirements

- **FR-001**: TanStack Query MAY be introduced here for polling; no other client store.
- **FR-002**: Times MUST be formatted with `Intl.DateTimeFormat('id-ID', {timeZone})` and the zone label "WIB (Asia/Jakarta)".

## Success Criteria

### Measurable Outcomes

- **SC-001**: J04 Playwright passes; axe, keyboard and overflow pass on the room.
