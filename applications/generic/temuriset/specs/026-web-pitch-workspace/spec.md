# Feature Specification: Pitch lists and workspace

**Feature Branch**: `026-web-pitch-workspace`
**Created**: 2026-11-05
**Status**: Seeded, not started
**Milestone**: M7 Review and revisions
**Depends on**: 024, 025
**Size**: L
**Covers**: S12, S13, UX-11, UX-12, J03
**Flips**: web registry `keputusan-revisi` → `available`

## User Scenarios & Testing

### User Story 1 - Lists say whose turn it is (Priority: P1)

S12 lists outgoing and incoming pitches with subject, purpose, status, whose turn, updated time and one open action; filters survive opening a case (UX-12).

**Acceptance Scenarios**:

1. **Given** Mitra A, **When** Pitching Masuk opens, **Then** F01 shows "Menunggu Anda"; for Rani the same pitch shows "Menunggu pihak lain".
2. **Given** filters, **When** a pitch is opened and Back pressed, **Then** filters return.

### User Story 2 - One room for summary, revisions, documents and history (Priority: P1)

S13 uses `TR.Tabs` with Ringkasan, Revisi, Dokumen, Diskusi (027), Jadwal (028) and Riwayat, and `TR.NextStep` above.

**Acceptance Scenarios**:

1. **Given** a recipient, **When** "Setujui untuk diskusi" opens its `TR.Dialog`, **Then** it says "Persetujuan ini membuka diskusi; belum merupakan pendanaan atau kerja sama", shows the acting party, traps focus and returns it.
2. **Given** a revision request, **When** Rani answers with `TR.RevisionItem`, **Then** save state shows, a failed upload keeps answers, missing required answers focus the error summary, and resubmission keeps round 1 visible (UX-11).
3. **Given** a member without `decide_pitch`, **When** the room opens, **Then** decision buttons are replaced by "Akun Anda hanya dapat melihat".
4. **Given** an unrelated account opens the room URL, **When** it loads, **Then** `TR.EmptyState` "Anda belum memiliki akses" shows with no title.

### User Story 3 - J03 end to end (Priority: P1)

**Acceptance Scenarios**:

1. **Given** the J03 path, **When** Playwright runs it as both parties, **Then** request revision → answer with "Belum dapat dipenuhi" → new file version → resubmit → accept item → approve completes.

### Edge Cases

- Tabs are in the URL (`?tab=`) so Back and sharing work.
- Riwayat lists every submission as a Disclosure with its frozen brief.

## Requirements

### Functional Requirements

- **FR-001**: Routes MUST be `/pitches`, `/pitches?box=masuk|diskusi`, `/pitches/[id]?tab=`.
- **FR-002**: Whose-turn MUST come from the API projection, not client logic (027 provides it; until then from status).

## Success Criteria

### Measurable Outcomes

- **SC-001**: J03 Playwright passes; dialog keyboard test passes; axe and overflow pass.
