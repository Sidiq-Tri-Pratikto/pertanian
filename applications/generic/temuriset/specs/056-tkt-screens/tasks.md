# Tasks: TKT on screens (inventor form, investor view, tooltips)

**Input**: Design documents from `applications/generic/temuriset/specs/056-tkt-screens/` (`spec.md`, `plan.md`), `docs/roadmap/revamp-2-demo-feedback.md`, `docs/roadmap/architecture.md`, and `.specify/memory/constitution.md`.
**Branch**: `f/056-tkt-screens` | **Track**: B | **Needs**: 055

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: User story label (`US1`, `US2`, `US3`, `US4`)

---

## Phase 1: Backend Support (Discovery Filter, Preflight Pre-tick, Pitch Snapshot, Demo Seed)

- [X] T001 [US2] Add `tkt_level` to `filters` JSONB in `refresh_invention` (`applications/generic/temuriset/applications/temuriset-api/app/discovery/service/projection.py`), accept `min_tkt: int | None = Query(default=None, ge=1, le=9)` on `GET /api/v1/discovery` (`app/discovery/router.py`), filter `tkt_level >= min_tkt` for `INVENTION` in `app/discovery/repository/sqlalchemy/repository.py`, and add `"min_tkt": "Hapus filter TKT"` relaxation in `app/discovery/service/service.py`
- [X] T002 [P] [US2] Add `kind: Literal["document", "tkt"] = "document"` and `selected: bool = False` to `ShareableFile` in `applications/generic/temuriset/applications/temuriset-api/app/briefs/model/schema.py` and include each linked invention version's TKT evidence (`kind="tkt"`, `selected=True`) in `BriefService.preflight` (`app/briefs/service/service.py`)
- [X] T003 [P] [US2] Include sanitized `readiness` (with `evidence=None`) per invention in `SubmissionService.snapshot` (`applications/generic/temuriset/applications/temuriset-api/app/pitches/service/submission.py`) so received pitches freeze TKT
- [X] T004 [US4] Add demo TKT data (`PRODUCT_A` TKT 4 + generated illustration evidence, `INVESTOR_A` `min_tkt=6`, `INVESTOR_B` `min_tkt=3`, `PRODUCT_B` TKT 5) in `app/demo/service/scenario.py`, `app/demo/service/fixtures.py`, `docs/demo/scenario.md`, and assert TKT values in `tests/integration/demo/test_scenario.py`
- [X] T005 [P] [US2] Write integration test `applications/generic/temuriset/applications/temuriset-api/tests/integration/discovery/test_min_tkt_filter.py` covering `min_tkt` filtering, excluding inventions without TKT, and `"Hapus filter TKT"` relaxation; verify preflight TKT pre-tick
- [X] T006 Regenerate `applications/generic/temuriset/contracts/openapi.json` and `applications/generic/temuriset/applications/temuriset-web/src/api/schema.generated.ts`

---

## Phase 2: Shared TKT UI Components & Helpers (US1, US2)

- [X] T007 [P] [US1] Add `expectedRange(stage)` and `mismatch(stage, level)` helpers (IDEA 1–3, PROTOTYPE 3–6, PILOT 5–7, WORKING 6–8, MARKET 8–9; note outside range ± 1) to `applications/generic/temuriset/applications/temuriset-web/src/features/portfolio/tkt.ts`
- [X] T008 [P] [US2] Create `applications/generic/temuriset/applications/temuriset-web/src/components/tr/TktBadge.tsx` rendering `.tr-tag` badge `"TKT {n} · {stage/name}"` + `Toggletip` (level meaning + group), optional 9-segment progress bar (`aria-hidden` + `"TKT {n} dari 9"`), provenance `"Dinyatakan inovator"`, optional note, and evidence status line; renders nothing when level is null/undefined
- [X] T009 [US1] Create `applications/generic/temuriset/applications/temuriset-web/src/features/portfolio/TktSteps.tsx` (`fieldset` with `"Tingkat Kesiapterapan Teknologi (TKT) — opsional"` + `Toggletip`, default `"Belum mengisi TKT"` + 9 grouped radios with meaning & example-evidence `Toggletip`, 9-segment bar, mismatch note, `"Catatan TKT"` ≤ 500, `"Dokumentasi TKT"` file select + inline upload via `uploadFile`)

---

## Phase 3: Screen Integrations (US1, US2, US3)

- [X] T010 [US1] Wire `readiness` in `src/features/portfolio/editor-state.ts`, `src/app/inventions/[id]/edit/page.tsx`, and `src/views/portfolio/EditorView.tsx` (render `TktSteps` at `#tkt`, show `TktBadge` in `PreviewStep`, send `readiness` in `draftRequest`)
- [X] T011 [P] [US2] Display `TktBadge` on owner/public invention detail (`src/views/portfolio/InventionViews.tsx`), signed-out public page (`src/views/subscriptions/TeaserView.tsx`), discovery row & detail card + `min_tkt` filter/chip/empty-state (`src/features/discovery/model.ts`, `src/views/discovery/DiscoverView.tsx`), and frozen pitch submission summary (`src/views/pitches/WorkspaceView.tsx`)
- [X] T012 [P] [US2] Pre-tick `kind === 'tkt'` files with `"Dokumentasi TKT"` label (still untickable) in `src/views/pitches/PreflightView.tsx`
- [X] T013 [P] [US3] Add optional `"TKT minimum"` select + `Toggletip` in `src/features/intake/MandateForm.tsx` and display `"Mencari TKT {n} ke atas"` + `Toggletip` in `src/views/intake/MandateCard.tsx`
- [X] T014 [US1] Add all new Indonesian strings and English translations to `src/features/i18n/app-en/tkt.ts` (and `src/features/i18n/id.ts` / `en.ts` if needed for signed-out `TeaserView`)

---

## Phase 4: Tests, Verification & Spec Status

- [X] T015 Write targeted web tests in `applications/generic/temuriset/applications/temuriset-web/tests/tkt-screens.test.tsx` covering `expectedRange`/`mismatch`, `TktBadge`, `TktSteps` (default, choose 6, mismatch note, Escape closes tooltip, axe clean), editor save body, mandate `min_tkt` form & card, and preflight TKT pre-tick
- [X] T016 Run targeted API tests (`test_min_tkt_filter.py`, `test_scenario.py`, `test_readiness.py`, `test_preflight.py`), `ruff check/format`, Web `make check` (`eslint`, `tsc`, `vitest`, `app-i18n.test.tsx`) & `make build`
- [X] T017 Update `**Status**` in `applications/generic/temuriset/specs/056-tkt-screens/spec.md` to `Built, awaiting review` and mark all tasks `[X]`
