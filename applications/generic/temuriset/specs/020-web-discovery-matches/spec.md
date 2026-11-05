# Feature Specification: Discovery and match screens

**Feature Branch**: `020-web-discovery-matches`
**Created**: 2026-11-05
**Status**: Seeded, not started
**Milestone**: M5 Discovery and matching
**Depends on**: 017, 018, 019
**Size**: L
**Covers**: S03, S10, UX-07, AC24
**Flips**: web registry `jelajahi` and `kecocokan` → `available`

## User Scenarios & Testing

### User Story 1 - Partners browse, inventors find (Priority: P1)

S03 shows result types per persona with search, filters, saved items and "Kurang relevan". Funding requests show one card per raise.

**Acceptance Scenarios**:

1. **Given** a partner, **When** Jelajahi opens, **Then** Inovasi and Pendanaan Perusahaan are separate result types, and FRaise01 appears once.
2. **Given** no results, **When** filters exclude everything, **Then** `TR.EmptyState` explains the filters and offers "Hapus semua filter".
3. **Given** filters set, **When** a result is opened and Back pressed, **Then** filters and scroll position return.

### User Story 2 - Reasons first, details on request (Priority: P1)

S10 shows, per target, a label, up to three reasons, the blocking gap if any, and one action; requirement rows and the score note sit in `TR.Disclosure` (UX-07).

**Acceptance Scenarios**:

1. **Given** F01-GAP, **When** S10 opens, **Then** A1 shows "Perlu konfirmasi" and "Lengkapi kisaran biaya" as its action, which opens the request with a return path.
2. **Given** the gap is fixed, **When** returning, **Then** A1 shows "Kecocokan kuat" and "Siapkan pitching".
3. **Given** F03, **When** S10 opens, **Then** D1 sits in "mandat tidak direkomendasikan" with the SSO reason.
4. **Given** Recipient E, **When** shown, **Then** "Buka formulir mitra" opens another site and says it is not a sent pitch (AC24).
5. **Given** the score note, **When** expanded, **Then** it says the range reflects missing information, not a chance of funding.

### Edge Cases

- Matching runs show a loading status, then results; failure keeps the selected source and offers retry.
- Green is used only for real requirement results, never for computed match labels.

## Requirements

### Functional Requirements

- **FR-001**: Routes MUST be `/discover?type=` and `/matches?source=`.
- **FR-002**: Match results MUST keep eligibility, readiness and fit visually distinct.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Playwright covers J01 from Beranda to "Siapkan pitching", including the F01-GAP repair; axe and overflow pass.
