# Feature Specification: TKT foundation (data, contract, Toggletip, split dictionary)

**Feature Branch**: `055-tkt-foundation`
**Created**: 2026-11-28
**Status**: Built, awaiting review
**Milestone**: Revamp 2, demo feedback ([plan](../../docs/roadmap/revamp-2-demo-feedback.md)); Track B, day 1
**Depends on**: 009, 016, 054
**Size**: S
**Covers**: FR03, FR09, FR25, AC73, AC74
**Flips**: nothing (screens arrive in 056)

## Context

Demo feedback asked for TKT (Tingkat Kesiapterapan Teknologi), Indonesia's nine-level technology readiness scale (Permenristekdikti No. 42/2016). This spec lays everything both tracks build on, so it merges first and fast:

- where an invention's TKT, note and evidence live, and how they reach the public projection and the matching engine;
- an optional minimum TKT on a mandate;
- a shared, accessible **Toggletip** that explains a term in place (TKT, each level, each match dimension);
- a dictionary split so two branches never edit the same English file;
- stable element ids that other screens deep-link to.

It changes no visible screen except adding the empty ids. Screens come in 056.

## User Scenarios & Testing

### User Story 1 - TKT travels with the invention version (Priority: P1)

**Acceptance Scenarios**:

1. **Given** a draft, **When** the owner saves `readiness: { tkt_level: 6, note: "Diuji di dua koperasi", evidence: { document_id, version } }`, **Then** the draft returns it, and publishing freezes it with the version (AC73).
2. **Given** a published version with TKT 6, **When** the owner starts a new draft, **Then** the draft starts with the same TKT, note and evidence.
3. **Given** `tkt_level` 0 or 10, a note over 500 characters, or evidence that is not the managing party's own AVAILABLE file, **When** saved, **Then** `VALIDATION_FAILED` or `FILE_NOT_AVAILABLE` naming the field; nothing is saved.
4. **Given** no readiness, **When** saved or read, **Then** `readiness` is `null`; TKT is optional everywhere.
5. **Given** any signed-in reader or the public summary, **When** a version with TKT is read, **Then** they see `tkt_level`, the note, `provenance: "SELF_DECLARED"` and `has_evidence: true|false`, but never the evidence file itself; the file stays private and is shared only through a pitch grant (AC74).

### User Story 2 - Mandates may ask for a minimum TKT (Priority: P2)

1. **Given** a mandate draft, **When** `min_tkt: 5` is saved, **Then** the version stores it and every reader of the mandate sees it; `null` means no preference.
2. **Given** `min_tkt` outside 1–9, **When** saved, **Then** `VALIDATION_FAILED` on `min_tkt`.

### User Story 3 - The engine can read TKT (Priority: P1)

**Given** a need whose invention version has TKT 6 and a mandate with `min_tkt` 5, **When** the engine's source and target are built, **Then** `Source.tkt == 6` and `Target.min_tkt == 5`. Scores do not change in this spec; 057 uses them.

### Edge Cases

- Evidence file erased later: the evidence reference becomes `null`, TKT and note stay.
- A funding request links several inventions: `Source.tkt` is the lowest stated TKT among them, or `null` if none states one.
- Old API instances keep working: the new table and the nullable column are additive (expand-only migration rule).

## Requirements

- **FR-001**: New table `invention_readiness`, one row per invention version, with `tkt_level` 1–9, `note` (≤ 500), `evidence_version_id` (document version, `ON DELETE SET NULL`). No new constraint on an existing table.
- **FR-002**: New nullable column `opportunity_versions.min_tkt` (validated 1–9 in the API).
- **FR-003**: `DraftRequest.readiness`, `InventionVersionResponse.readiness`, `PublicInventionResponse.readiness`, the discovery invention card (`tkt_level`), the teaser (`tkt_level`), `OpportunityContent.min_tkt`, `Source.tkt`, `Target.min_tkt`.
- **FR-004**: `src/features/portfolio/tkt.ts`: the nine levels with Indonesian and English names, one-sentence meaning, example evidence and group (basic research 1–3, applied research 4–6, development 7–9) — the single source for every screen.
- **FR-005**: `Toggletip` component in the design system and the web port: a 24 px info button that opens a short explanation on click or Enter, closes on Escape or outside click, and is announced to screen readers. Not hover-only.
- **FR-006**: `src/features/i18n/app-en.ts` becomes a merge of `app-en/{core,tkt,matching,finder,mail}.ts`; the guard test reads all of them.
- **FR-007**: Stable ids for deep links: `#tkt`, `#fakta`, `#dokumen` in editor step 2; `#kata-kunci`, `#sektor`, `#tahap` in step 1; `#kisaran`, `#bentuk` on a need; `#baru` on the needs list.

## Success Criteria

- Migration round trip is clean; `alembic check` shows no drift; the migration compatibility check passes (no change to existing columns or constraints).
- Contract and web types regenerated; Track A can read `Source.tkt` and `Target.min_tkt` the same day.
