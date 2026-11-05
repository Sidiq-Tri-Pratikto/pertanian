# Feature Specification: Partner profile and mandate editor

**Feature Branch**: `017-web-partner-mandate`
**Created**: 2026-11-05
**Status**: Seeded, not started
**Milestone**: M4 Partner intake
**Depends on**: 008, 016
**Size**: M
**Covers**: FR08, FR09, S08, S09
**Flips**: web registry `profil-mitra` and `mandat` → `available`

## User Scenarios & Testing

### User Story 1 - Partner profile reads clearly to both sides (Priority: P1)

S08 shows subtype, thesis, sectors, accepted stages, regions, support forms, check range, intake status and source labels, and the contact route.

**Acceptance Scenarios**:

1. **Given** Mitra A's own profile, **When** opened from Kebutuhan/Mandat, **Then** each mandate shows status, version, outcome, support and `TR.FinancialScope`, with "Ubah mandat" and "Tutup penerimaan".
2. **Given** Recipient E viewed by an inventor, **When** opened, **Then** "Dilaporkan sumber" and "Ketersediaan belum dikonfirmasi" are visible, and the external link says it opens another site and is not a sent pitch.

### User Story 2 - Edit, review, then activate a mandate (Priority: P1)

**Acceptance Scenarios**:

1. **Given** S09, **When** a requirement is added, **Then** its stage and verification mode are chosen, and narrative ones are labelled as manual review.
2. **Given** "Tinjau mandat", **When** pressed, **Then** a `TR.SummaryList` review shows before "Aktifkan versi N".
3. **Given** a stale version, **When** activating, **Then** `TR.VersionConflict` keeps the edits.

### Edge Cases

- A partner with no profile sees an empty state offering to create one.
- Requirement rows use `TR.RequirementRow` with result "Tidak berlaku" in edit mode, so no pass or fail is implied.

## Requirements

### Functional Requirements

- **FR-001**: Routes MUST be `/partners/[partyId]`, `/opportunities`, `/opportunities/[id]/edit`.
- **FR-002**: Kebutuhan/Mandat MUST list the acting party's mandates with status and version.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Playwright edits, reviews and activates A1 version 2; axe and overflow pass.
