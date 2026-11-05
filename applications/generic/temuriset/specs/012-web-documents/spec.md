# Feature Specification: Documents in the editor and pitch room

**Feature Branch**: `012-web-documents`
**Created**: 2026-11-05
**Status**: Seeded, not started
**Milestone**: M2 Portfolio and evidence
**Depends on**: 010, 011
**Size**: M
**Covers**: FR05, UX-10, AC12
**Flips**: web registry `dokumen` → `available`

## User Scenarios & Testing

### User Story 1 - Upload and watch three independent states (Priority: P1)

In editor step 2, the owner uploads a file and sees file security, text reading and evidence review as separate axes (`TR.DocumentItem`), each moving on its own.

**Why this priority**: UX-10 and FR05's separation of availability from review.

**Independent Test**: Playwright uploads a PDF, a scan and a mismatched file.

**Acceptance Scenarios**:

1. **Given** a PDF, **When** uploaded, **Then** the item shows "Sedang diunggah", then "Sedang diperiksa keamanannya", then "Aman dan tersedia", and review stays "Disediakan, belum diperiksa".
2. **Given** a scan, **When** checks pass, **Then** text reading shows "Perlu diisi manual" while the file is available (UX-10).
3. **Given** a rejected file, **When** shown, **Then** "Ditolak saat pemeriksaan keamanan" appears and the rest of the draft is unchanged.
4. **Given** a file over the limit, **When** chosen, **Then** the field error states the limit and nothing uploads.

### User Story 2 - See every grant and revoke one (Priority: P2)

**Acceptance Scenarios**:

1. **Given** a granted version, **When** the owner views it, **Then** it reads "Dibagikan hanya kepada Mitra A, hanya versi 1".
2. **Given** "Cabut akses" is confirmed in `TR.Dialog`, **When** it succeeds, **Then** the item says new downloads are blocked and copies already downloaded cannot be recalled.

### Edge Cases

- Uploading continues if the user moves to another step; leaving the page asks before abandoning an active transfer.
- Status changes are announced with a live region without moving focus.

## Requirements

### Functional Requirements

- **FR-001**: Upload MUST stream to the same-origin intent URL with progress and a cancel action.
- **FR-002**: The list MUST poll document state until every item is final.
- **FR-003**: Revocation MUST use `TR.Dialog` with focus return.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Playwright covers PDF, scan, rejection, size limit and revocation; axe and keyboard checks pass on the dialog.
