# Tasks — Bilingual MVP

## Setup

- [x] T019 Verify merged 048 and 049, inventory routes and run Spec Kit analysis across `specs/050-bilingual-mvp/`.

## US1 — Localize the MVP

Independent check: open every route from the inventory in either locale and check the visible and accessible copy for its fixture and recovery states.

- [x] T020 [US1] Migrate shared controls, state and route copy in `applications/hematdaya-mobile/src/components/`, `src/app/` and `src/features/`.
- [x] T021 [US1] Mirror both languages in `docs/generic/hematdaya/prototype/project/`, update binding notes, and sync `docs/reference/prototype/hematdaya-app.js`.

## US2 — Persist the language and preserve state

Independent check: switch language with an existing workspace and recover the same locale and state after restart.

- [x] T022 [US2] Add Welcome and Settings language controls in both builds, set document and supported accessibility language, and verify stable state after switching.

## Acceptance

- [x] T023 Record both bilingual fixture journeys, responsive checks, build results and separate native and spoken accessibility evidence in `specs/050-bilingual-mvp/tasks.md`.

## Dependencies

T019 precedes implementation. T020 and T021 each start with shared controls and are independent across runtimes. T022 follows complete copy in both runtimes. T023 verifies the combined slice.

## Analysis

FR-001 and FR-002 map to T020 and T021. T022 delivers FR-003. T020 through T023 cover the preservation and recovery checks in FR-004. T021 owns the prototype defaults and binding notes in FR-005. T023 verifies all three success criteria. Language stays outside route identity and mutation keys. Translated presentation derives from structured state, including while offline. No blocking contradictions were found.

## Acceptance evidence

- Expo web and the standalone prototype completed both demo journeys in Indonesian and English. Both displayed 14.700 kWh for the household week and 144.000 kWh for the industrial week. The live Expo and API checks verified the measured industrial Sunday zero, chart data, household and industrial scope refusal, evidence, explicit feedback recovery, and original saved timestamps offline.
- The live CSV checks in each locale covered a lost response, explicit status confirmation, same-key replay and a fresh preview of the same file. The fresh preview found two duplicates and added zero readings. The imported meter retained 0.500 kWh of independent history. The prototype covered offline reads, scope refusal, interrupted import recovery and repeated import in both locales.
- Chromium passed Welcome, Home, Devices, Insights, scope and import at 320, 390, 768 and 1280 px in both languages and both builds at standard and 200% text. It verified readable tab labels, 48 px entry and tab targets, keyboard activation and chart alternatives. Both builds preserved the active route and pasted draft across a locale change, preserved the user-entered name in the CSV, and restored English after reload.
- API `make check` passed with 1,084 tests, eight skips and 98.91% coverage. Mobile lint, type checking and all 582 tests passed. The prototype passed all 36 domain checks. Both prototype reference files and the bundle binding fingerprint matched.

| Evidence | Result |
| --- | --- |
| JavaScript bundles | Android, iOS and web exported locally. |
| Android runtime | The Android Smoke workflow exercises the English selector offline and after restart. The Android Offline workflow runs the live recovery matrix on an embedded bundle. Track both on the release PR. |
| iOS runtime | Not run. The simulator runtime is available locally and no native build was installed. |
| Spoken accessibility | Not run. Browser keyboard, accessible names and document language were checked separately. |
