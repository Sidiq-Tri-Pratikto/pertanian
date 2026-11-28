# Implementation Plan: TKT on screens

**Branch**: `f/056-tkt-screens` | **Spec**: [spec.md](spec.md) | **Track**: B | **Needs**: 055 merged

## Files

```text
applications/temuriset-web/src/
├── features/portfolio/TktSteps.tsx          # picker: 9 rows in 3 groups, bar, note, evidence chooser/upload
├── components/tr/TktBadge.tsx               # "TKT 6 · Prototipe" + Toggletip + provenance/evidence line
├── views/portfolio/EditorView.tsx           # step 2 section at #tkt; preview shows TktBadge; save sends readiness
├── views/portfolio/InventionViews.tsx       # owner and public detail: TktBadge
├── views/discovery/DiscoverView.tsx         # row facts + detail card badge; "TKT minimum" filter (inventions)   ← coordinate with Track A, see below
├── views/subscriptions/TeaserView.tsx       # badge on the public page
├── views/pitches/WorkspaceView.tsx          # badge in the frozen submission summary (read only)
├── views/pitches/PreflightView.tsx          # pre-tick TKT evidence
├── features/intake/MandateForm.tsx + views/intake/MandateCard.tsx  # min TKT select and line
├── features/i18n/app-en/tkt.ts              # English
└── tests/tkt-screens.test.tsx
applications/temuriset-api/
├── app/discovery/... (filter min_tkt), app/briefs/service/service.py (shareable file kind "tkt")
├── app/demo/service/scenario.py, app/demo/service/fixtures.py (seed readiness + evidence illustration)
└── tests/integration/discovery/test_min_tkt_filter.py, tests/integration/demo/test_scenario.py (TKT values)
docs/demo/scenario.md
```

**Shared file with Track A**: `DiscoverView.tsx`. Keep 056's change there to two small additions (badge in `rowFacts`/`ResultCard`, one filter select) and land 056 before 059 starts its rewrite; 059 then keeps them. If 059 lands first, 056 adds the same pieces to 059's new components instead.

## Contracts

- Editor sends `readiness: { tkt_level, note, evidence: { document_id, version } | null } | null` in the draft body (055).
- `GET /api/v1/discovery?type=inventions&min_tkt=5` → only cards with `tkt_level >= 5`. Applied filters echo `min_tkt`; relaxation label "Hapus filter TKT".
- Preflight `ShareableFile` gains `kind: "document" | "tkt"`; `tkt` files are `selected: true` by default.

## UI details

- **TktSteps**: a `fieldset` with legend "Tingkat Kesiapterapan Teknologi (TKT)" + Toggletip; native radio inputs (keyboard and screen-reader friendly), each label "TKT {n} · {name}" and a support line with the meaning; Toggletip per row with "Contoh bukti: …". Bar: nine `span` segments, `aria-hidden`, with a text equivalent "TKT 6 dari 9".
- **Evidence chooser**: `Select` listing AVAILABLE files of the owner (reuse `photoChoices` logic from `PublicPageForm` generalized to any type), plus "Unggah berkas baru" using `features/documents/upload.ts`; after upload, wait for AVAILABLE before allowing selection (show "Sedang diperiksa keamanannya").
- **Stage mismatch note**: lookup table in `tkt.ts`: expected TKT range per stage — IDEA 1–3, PROTOTYPE 3–6, PILOT 5–7, WORKING 6–8, MARKET 8–9. Outside the range ± 1 → note.
- **TktBadge**: tag style of `.tr-tag`; colours never carry meaning alone; the Toggletip text is the level's meaning plus the group.

## Tasks

1. `tkt.ts` helpers: `expectedRange(stage)`, `mismatch(stage, level)`. Unit tests.
2. `TktBadge` + tests (renders nothing without level; tooltip text; evidence line).
3. `TktSteps` + tests (default "Belum mengisi TKT", choose 6 → note and evidence fields, mismatch note, Escape closes tooltip, axe).
4. Editor step 2 wiring + preview; extend existing editor tests (save body includes readiness; `null` when cleared).
5. Read screens: invention detail, teaser, discovery row/detail, pitch workspace summary.
6. Discovery `min_tkt` filter: API (+ integration test, isolation unchanged since the route exists), web select and chip.
7. Mandate `min_tkt`: form select, card line, test.
8. Preflight pre-tick: API kind, web label; extend preflight test.
9. Demo seed and `docs/demo/scenario.md` (new step "Tunjukkan TKT"); update `tests/integration/demo/test_scenario.py`.
10. English in `app-en/tkt.ts`; guard test passes.
11. `e2e/routes.ts`: nothing new; add to `e2e/portfolio.spec.ts` one step that sets TKT 6 and sees the badge on the public page.

## Done when

```bash
cd applications/temuriset-api && DEMO_MODE=false make check
cd ../temuriset-web && make check && cd .. && make e2e
```

Browser: editor step 2 at 320 and 1280 px in ID and EN; Toggletips by keyboard; investor sees the badge in Jelajahi and on `/en/inventions/{id}`.

## Do not

- Do not show the evidence file to anyone outside a pitch grant.
- Do not make TKT required or block publishing on a mismatch.
- Do not invent TKT names outside `tkt.ts`.
