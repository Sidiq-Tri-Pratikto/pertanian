# Feature Specification: TKT on screens (inventor form, investor view, tooltips)

**Feature Branch**: `056-tkt-screens`
**Created**: 2026-11-28
**Status**: Seeded, not started
**Milestone**: Revamp 2, demo feedback ([plan](../../docs/roadmap/revamp-2-demo-feedback.md)); Track B
**Depends on**: 055
**Size**: M
**Covers**: FR03, FR09, FR25, AC75, AC76, AC88, S04, S05, S09
**Flips**: nothing

## Context

With the data in place (055), inventors can state their TKT and attach documentation, and investors see it wherever they judge an invention. The inventor side is an optional section in editor step 2. The investor side stays simple: a badge "TKT 6 · Prototipe" with a tooltip, and an optional "TKT minimum" on a mandate. Inspiration: the UMS Innovation Hub catalogue, which filters by TKT and shows the level beside field and sector.

## User Scenarios & Testing

### User Story 1 - Inventor states TKT with documentation (Priority: P1)

In editor step 2 ("Yang sudah ada dan bukti") a section **Tingkat Kesiapterapan Teknologi (TKT) — opsional** sits above the facts, at `#tkt`.

**Acceptance Scenarios**:

1. **Given** the section, **When** opened, **Then** it shows a short definition with a Toggletip "Apa itu TKT?" and a choice of nine levels as a vertical step list: each row has the number, the name, one sentence of meaning, and its own Toggletip with the example evidence. Rows are grouped "Riset dasar (1–3)", "Riset terapan (4–6)", "Pengembangan dan komersialisasi (7–9)". "Belum mengisi TKT" is the first choice and the default.
2. **Given** a chosen level, **When** shown, **Then** a progress bar of nine segments fills up to that level, and two optional fields appear: **Catatan TKT** (≤ 500 characters, hint "Apa yang membuktikan tingkat ini? Misalnya: diuji di dua koperasi selama tiga bulan.") and **Dokumentasi TKT** (choose one of the owner's uploaded files, or upload a new image or PDF right there; hint "Foto, laporan uji, atau sertifikat. Berkas tetap privat dan hanya dibagikan saat pitching.").
3. **Given** the chosen level and the invention's stage disagree strongly (for example TKT 8 with stage "Ide"), **When** shown, **Then** a neutral note says "TKT 8 biasanya sudah melewati tahap Ide. Periksa lagi tahap atau TKT." It never blocks saving.
4. **Given** the draft is saved, **When** the preview step opens, **Then** the public card shows "TKT 6 · Prototipe" with the bar, and "Bukti TKT: tersedia (dibagikan saat pitching)" when a file is attached.
5. **Given** keyboard only or a phone at 320 px, **When** the section is used, **Then** every Toggletip opens and closes with Enter and Escape and nothing overflows (AC75).

### User Story 2 - Investors see TKT when it is given (Priority: P1)

1. **Given** an invention with TKT, **When** an investor sees it in Jelajahi (row and detail), on invention detail, on the public page `/temuan/{id}` and in a received pitch, **Then** a badge "TKT 6 · Prototipe" appears with a Toggletip explaining TKT 6, plus "Dinyatakan inovator" and, if attached, "Bukti terlampir saat pitching" (AC76).
2. **Given** no TKT, **Then** nothing about TKT is shown; never "TKT 0" or an empty bar.
3. **Given** Jelajahi for investors, **When** filtering, **Then** a "TKT minimum" select (Semua, 3 ke atas … 9) narrows inventions to those that state a TKT at or above it.
4. **Given** a pitch is prepared, **When** the invention has TKT evidence, **Then** preflight pre-ticks that file under "Berkas yang dibagikan", labelled "Dokumentasi TKT"; the inventor can untick it.

### User Story 3 - Mandates may set a minimum TKT (Priority: P2)

1. **Given** the mandate form, **When** the investor opens it, **Then** an optional select **TKT minimum** with a Toggletip appears after accepted stages; default "Tidak ada syarat TKT".
2. **Given** a mandate with a minimum, **When** an inventor reads it, **Then** it shows "Mencari TKT 5 ke atas" with the same Toggletip (AC88). It is a preference used by matching (057), not a hard requirement.

### User Story 4 - Demo data (Priority: P1)

`app/demo/service/scenario.py`: Produk A (ClearSpring) TKT 4 with a generated illustration as evidence; Investor A mandate `min_tkt` 6; `INVESTOR_B` script gets `min_tkt` 3 and `PRODUCT_B` TKT 5 so the demo shows a strong TKT fit for Investor B and a weak one for Investor A. Update `docs/demo/scenario.md`.

## Requirements

- **FR-001**: One component `TktBadge({ level, stage?, hasEvidence? })` and one `TktSteps` picker, both reading `features/portfolio/tkt.ts`; no level text written anywhere else.
- **FR-002**: Every tooltip uses `Toggletip` from 055; text in Indonesian with English in `app-en/tkt.ts`.
- **FR-003**: Discovery filter `min_tkt` added to `GET /api/v1/discovery` (inventions only); cards without TKT are excluded when the filter is set and the empty state explains that.
- **FR-004**: Preflight's shareable files mark the TKT evidence file (`kind: "tkt"`) and pre-select it.

## Success Criteria

- An inventor states TKT 6 with a photo in under a minute without leaving step 2.
- An investor understands TKT 6 from the tooltip alone (usability check in the demo script).
