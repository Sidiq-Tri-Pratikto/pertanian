# Feature Specification: Relationship and public profile screens

**Feature Branch**: `032-web-relationship-profile`
**Created**: 2026-11-05
**Status**: Built, awaiting review
**Milestone**: M9 Relationships
**Depends on**: 029, 031
**Size**: L
**Covers**: S15, S16, UX-15, UX-16, J05
**Flips**: web registry `kerja-sama` and `profil-publik` → `available`

## User Scenarios & Testing

### User Story 1 - Confirm the same summary, see what becomes public (Priority: P1)

S15 proposes and confirms with `TR.PartnershipConsent`: version, values, per-party consent, effective public fields and restrictions.

**Acceptance Scenarios**:

1. **Given** one confirmation, **When** shown, **Then** "Menunggu konfirmasi" appears and no "Dikonfirmasi kedua pihak" status (UX-15).
2. **Given** "Minta perubahan", **When** confirmed in `TR.Dialog`, **Then** version N+1 opens and says old confirmations no longer apply.
3. **Given** a confirmed version, **When** "Sembunyikan" is pressed on a field, **Then** it disappears from the public view at once and copy says delivered copies cannot be recalled (UX-16).

### User Story 2 - Public profile (Priority: P1)

**Acceptance Scenarios**:

1. **Given** S16, **When** an unrelated or signed-out visitor opens it, **Then** only published inventions and effective relationship fields appear; amount stays hidden when not permitted by both.

### User Story 3 - J05 end to end (Priority: P1)

**Acceptance Scenarios**:

1. **Given** the J05 path, **When** Playwright runs it as both parties, **Then** propose → correction → both confirm version 2 → narrow → public view completes.

### Edge Cases

- EQUITY on a proposed company shows the entity rule before any field.
- Consent checkboxes lock after a party confirms.

## Requirements

### Functional Requirements

- **FR-001**: Routes MUST be `/partnerships/new?pitch=`, `/partnerships/[id]`, `/profiles/[partyId]`.

## Success Criteria

### Measurable Outcomes

- **SC-001**: J05 Playwright passes; axe and overflow pass on both routes, including signed-out S16.

## Validation

The production Chromium suite passed 437 cases with 423 expected skips. J05 passed at 320, 360, 768 and 1280 CSS px with axe and overflow checks. The project quality gate passed 832 API tests and 261 web tests.
