# Feature Specification: Inovasi Saya, detail and four-step editor

**Feature Branch**: `011-web-portfolio-editor`
**Created**: 2026-11-05
**Status**: Seeded, not started
**Milestone**: M2 Portfolio and evidence
**Depends on**: 008, 009
**Size**: L
**Covers**: FR03, FR04, S04, S05, UX-03, UX-04, AC12
**Flips**: web registry `inovasi` → `available`

## User Scenarios & Testing

### User Story 1 - Build a profile in four steps without losing work (Priority: P1)

S05: basics; what exists and evidence; support and financial scope; public preview. Values survive Back, step changes, failed saves and stale versions.

**Why this priority**: UX-03; the inventor's first real task.

**Independent Test**: Playwright creates an invention, fails a save, retries, publishes.

**Acceptance Scenarios**:

1. **Given** step 1, **When** "Simpan dan lanjutkan" is pressed, **Then** the draft saves, `TR.SaveState` says "Tersimpan", and step 2 opens with focus on its heading.
2. **Given** a failed save, **When** it shows, **Then** `TR.SaveState` says "Gagal menyimpan", every value stays on screen, and "Coba lagi" retries with the same key.
3. **Given** a draft changed in another tab, **When** saving, **Then** `TR.VersionConflict` shows the current revision and the local text, with a refresh path (UX-03).
4. **Given** publication errors, **When** "Terbitkan" is pressed, **Then** the editor opens the first step with an error, and the error summary links to each field.
5. **Given** step 4, **When** it renders, **Then** the public card, what stays private, and the effect of publishing are shown before "Terbitkan versi N" (AC12).

### User Story 2 - Read an invention honestly (Priority: P1)

**Acceptance Scenarios**:

1. **Given** S04 as owner, **When** it renders, **Then** problem, current solution, stage, Saat ini and Direncanakan facts with provenance labels, support requests, documents and people and rights claims appear, with one primary action (UX-04).
2. **Given** S04 as a partner, **When** it renders, **Then** only the public projection appears, documents say they are shared per pitch, and the primary action is "Simpan inovasi".
3. **Given** a claim "not yet established", **When** shown, **Then** it reads "Belum ditetapkan", never empty.

### User Story 3 - Inovasi Saya list (Priority: P2)

**Acceptance Scenarios**:

1. **Given** no inventions, **When** the list opens, **Then** `TR.EmptyState` explains publication and offers "Tambah inovasi".
2. **Given** a published invention with a draft, **When** listed, **Then** its card shows "Ada draf perubahan".

### Edge Cases

- Step 3 links to support requests and funding (015) and shows "Segera hadir" until then.
- Step 2's document area links to 012 and shows "Segera hadir" until then.
- 200% text and 320 px keep the step navigation usable.

## Requirements

### Functional Requirements

- **FR-001**: The editor MUST use `TR.Steps`, `TR.SaveState`, `TR.ErrorSummary`, `TR.VersionConflict`, `TR.FactSource`.
- **FR-002**: Every save MUST send `expected_version` and an idempotency key; a retry reuses the key.
- **FR-003**: Optional fields MUST never block a save; publication rules come from the API.
- **FR-004**: Routes MUST be `/inventions`, `/inventions/[id]`, `/inventions/[id]/edit?step=1..4`.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Playwright covers create, failed save, stale draft, publish and partner view; axe and overflow pass on all routes.
