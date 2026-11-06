# Feature Specification: Preflight screen and submission

**Feature Branch**: `024-web-preflight-submit`
**Created**: 2026-11-05
**Status**: Built, awaiting review
**Milestone**: M6 Pitch submission
**Depends on**: 012, 020, 023
**Size**: L
**Covers**: S11, UX-02, UX-08, UX-17, J01, J02, AC34
**Flips**: web registry `pemeriksaan-pitching` and `pitching` → `available`; manifest capability `core` → `available`

## User Scenarios & Testing

### User Story 1 - Check everything, then send on purpose (Priority: P1)

S11 shows recipient, versions, purpose, requirement rows, each file to share by checkbox with its axes, money scope, the editable brief, the acting party and the exact effect of sending (UX-08).

**Acceptance Scenarios**:

1. **Given** F01 → A1, **When** S11 opens, **Then** "Siap dikirim" shows, the function file is unchecked, and "Kirim pitching" names Mitra A as recipient and Rani as sender (UX-02).
2. **Given** no file chosen, **When** "Kirim pitching" is pressed, **Then** the error summary links to the file list and nothing is sent.
3. **Given** the mandate changes, **When** sending, **Then** `TR.VersionConflict` says what changed, keeps the edited brief, and "Periksa ulang" refreshes (AC34, UX-17).
4. **Given** the response is lost, **When** shown, **Then** "Status pengiriman belum diketahui" explains that retrying is safe, and "Coba kirim lagi" reuses the key and opens the existing pitch (UX-17).
5. **Given** a duplicate, **When** shown, **Then** "Buka pitching yang ada" opens it.

### User Story 2 - Two journeys reach "submitted" (Priority: P1)

**Acceptance Scenarios**:

1. **Given** the J01 path, **When** Playwright runs it, **Then** Rani goes from Beranda through the F01-GAP repair and match to a submitted pitch, and Mitra A sees it in Pitching Masuk.
2. **Given** the J02 path, **When** Playwright runs it, **Then** Bima submits FRaise01 to B1 and the second link points to the same pitch.

### Edge Cases

- `NEEDS_INFORMATION` and `BLOCKED_FOR_THIS_TARGET` show the button disabled with its reason linked.
- The brief is "Brief pitching" in a `TR.TextArea`; the summarizer button appears only when the manifest lists it.
- Print uses a print stylesheet of the brief.

## Requirements

### Functional Requirements

- **FR-001**: Route MUST be `/pitches/new?source=&target=`.
- **FR-002**: The idempotency key MUST be created when the page renders and kept across retries until a final result.

## Success Criteria

### Measurable Outcomes

- **SC-001**: J01 and J02 Playwright journeys pass to submission; axe and overflow pass; `core` flips because the first complete inventor journey works end to end.
