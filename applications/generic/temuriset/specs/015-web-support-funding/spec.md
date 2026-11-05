# Feature Specification: Support and funding screens

**Feature Branch**: `015-web-support-funding`
**Created**: 2026-11-05
**Status**: Built, awaiting review
**Milestone**: M3 Needs and funding
**Depends on**: 011, 013, 014
**Size**: M
**Covers**: FR06, FR07, S06, S07, UX-05, UX-06
**Flips**: web registry `dukungan-proyek` and `pendanaan-perusahaan` → `available`

## User Scenarios & Testing

### User Story 1 - State a project need with labelled money (Priority: P1)

S06 lists and edits support requests. Every amount shows subject, currency, period and scope through `TR.FinancialScope` (UX-05).

**Acceptance Scenarios**:

1. **Given** F01, **When** the request opens, **Then** the budget reads "Dukungan Proyek · USD 20.000–30.000 selama 6 bulan · Cakupan: biaya pilot enam bulan".
2. **Given** a null range, **When** shown, **Then** it reads "Belum ditentukan", and Beranda's queue offers "Lengkapi kisaran biaya pilot untuk kebutuhan ini".
3. **Given** max below min, **When** saved, **Then** the error summary takes focus and both values stay.
4. **Given** the request was opened from a match with `?return=`, **When** saved, **Then** the user returns to that match with filters intact.

### User Story 2 - One raise card for several inventions (Priority: P1)

**Acceptance Scenarios**:

1. **Given** FRaise01, **When** S07 renders, **Then** one `TR.FundingRequestCard` shows Target Pendanaan USD 500.000 and Kisaran kontribusi per investor USD 50.000–100.000 as separate amounts, and two linked inventions (UX-06).
2. **Given** a linked invention, **When** opened and Back is pressed, **Then** the same funding request returns.
3. **Given** `project-support-only`, **When** S07 opens, **Then** a notice says company funding is not available here and nothing is editable.

### Edge Cases

- Company stage and invention maturity always have distinct labels.
- Amounts are formatted from strings with Indonesian grouping; nothing parses them into floats.

## Requirements

### Functional Requirements

- **FR-001**: Routes MUST be `/support-requests`, `/support-requests/[id]`, `/funding-requests/[id]`, `/funding-requests/[id]/edit`.
- **FR-002**: Editor step 3 MUST link to both forms.
- **FR-003**: A string-only money formatter MUST be shared and unit-tested.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Playwright covers J02 up to opening FRaise01 from either invention; axe and overflow pass.
