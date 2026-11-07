# Tasks — History chart

**Inputs** [spec.md](spec.md), [plan.md](plan.md), [010 history contract](../010-history/plan.md), [S06 handoff](../../docs/product/design-handoff-EN.md), and [binding architecture](../../docs/roadmap/architecture.md).

All paths are relative to the HematDaya root. `[P]` marks tasks that can run in parallel once their listed prerequisites are met. Establish a red test or concrete failing check before each implementation increment.

## Implementation decisions

- Keep History inline in the existing S06 detail before **Sumber data**. **Lihat riwayat** opens it for the selected asset and period. Use the same route from Beranda, Perangkat, and direct entry so the tab and back behavior stay consistent.
- Use the active asset summary's confirmed `window.start_date` and `window.end_date` as the explicit local dates for History. Equal dates use `hour`, including a Monday **Minggu ini**. Other ranges use `day`. Date bounds and timezone come from the service. A retained summary for an earlier selection cannot authorize a read for the new selection.
- Build chart marks, table rows, and the visible summary from one History response. Preserve server order, start/end identity, state, coverage, provenance, and decimal strings. Limit energy conversion to plot geometry. Resolve `highest_bucket.start` to its UTC instant and use the selected bucket's value. The service alone applies unrounded ranking, eligibility, and the earliest-UTC tie rule.
- Use History's own `window.effective_end` for the elapsed cutoff. A measured bucket can be fully covered through that instant and can be the highest bucket while its nominal interval is still underway. Qualify the number and coverage through the cutoff wherever they appear.
- A previously confirmed chart may stay visible during an in-place period change or failed refresh with its own original period, timezone and cutoff, and a clear status while the selected period is pending or has failed. Scope retained data to the workspace and asset. Discard late results from the active view when their request is no longer selected. A valid all-missing, all-future, or all-unavailable series replaces retained data.
- One History retry sequence owns the total attempt budget for its active or cached request identity. Automatic retry consumes the available attempts after the specified wait. Toggle, remount, focus, reconnect and invalidation preserve terminal failure. Terminal status includes safe recovery guidance and the available reference, and has no retry action.
- 020 already returns comparison fields on the endpoint. S06 uses the full selected `energy_kwh` series. S08 continues using its separate frozen comparison series, reference style, and evidence revision. The `detail-perangkat` registry entry still describes edit and archive, which ship in 016. 016 owns the final availability flip.

## Phase 1 — Setup

- [X] T001 Check merged 014 and 022 with `git merge-base --is-ancestor 42aeebc HEAD` and `git merge-base --is-ancestor fd50a7a HEAD`. Run `.specify/scripts/bash/check-prerequisites.sh --json` on `015-history-chart` and record the starting commit and feature directory in `specs/015-history-chart/tasks.md`.
- [X] T002 Select Node 24 as specified by `applications/hematdaya-mobile/.nvmrc`, reuse an installed lockfile-matched dependency tree or run `make install`, and run the baseline `make check` in `applications/hematdaya-mobile/`. Record commands, suites, tests, coverage and any environment blockers in `specs/015-history-chart/tasks.md`.

**Checkpoint** 014 and 022 are merged, the prerequisites script locates the feature, and the baseline is recorded.

## Phase 2 — Foundational history read

- [X] T003 Add failing client tests in `applications/hematdaya-mobile/tests/data-layer.test.tsx` for the encoded asset path, bearer, local date pair and bucket query. Cover day/hour success with optional comparison fields, an unfamiliar unavailable reason, wrong echoed date/granularity/timezone, an invalid cutoff or bucket bound, inconsistent state/value/coverage, a dangling or non-measured highest pointer, and unexpected 204. Verify failure code, reference and recovery with a fake secret that stays out of the normalized error.
- [X] T004 Add the generated `HistoryResponse` and granularity types and a `getAssetHistory` adapter in `applications/hematdaya-mobile/src/api/client.ts`. Reuse `apiRequest` and enforce the echoed selection, time bounds, fields and state/value invariants in the plan. Resolve the non-null highest pointer to a unique measured bucket by UTC instant. Accept an unfamiliar unavailable reason for safe display fallback. Map invalid responses and unexpected 204 to `UNEXPECTED_RESPONSE`. Run T003.
- [X] T005 Add failing QueryClient tests with fake HTTP responses and timers in `applications/hematdaya-mobile/tests/history-query.test.tsx`. Cover a closed disclosure, absent workspace or current confirmed period, isolation by site/asset/dates/timezone/granularity, Monday week and explicit single-day ranges. For retryable failures, assert exact total attempt counts at limits one and three and no early request during the service wait. At terminal failure, attempt close/reopen, remount, focus, reconnect and invalidation and verify no extra request. Cover a nonretryable error and a later success within the budget.
- [X] T006 Add `applications/hematdaya-mobile/src/features/assets/useHistory.ts`. Enable the read only when open with the current workspace, asset ID and matching confirmed window. Key by site, asset, resolved local dates, timezone and granularity. Use the existing cache and normalized error handling. Own one automatic retry sequence for this read with the normalized wait and total limits, counting the initial request. Gate retry, refetch and lifecycle triggers after the operation becomes terminal while it remains active or cached. Keep successful reads refreshable. Run T005 and record the existing shared-policy off-by-one separately.

**Checkpoint** The lazy query calls the existing contract for the intended period and stays isolated across workspaces and assets.

## Phase 3 — User Story 1, read history without relying on the picture (P1)

**Independent test** Open Kulkas for 19–25 October in the household demo. The visible text identifies 19 October as the service-selected highest day at `1,200 kWh`. Open **Lihat data** and read seven matching rows, each with its period and value. Repeat with a one-day range to read the exact hours from the table.

### Tests first

- [X] T007 [P] [US1] Extend `applications/hematdaya-mobile/tests/perangkat.test.tsx` with typed history responses based on `contracts/openapi.json` and `applications/hematdaya-api/tests/integration/test_history.py`. Cover the lazy disclosure from Beranda and Perangkat, back/tab context, data parity and first load. Defer a previous summary and History response across a period change and verify neither can start or replace the new active History. Cover a failed refresh and period change with retained period/timezone/cutoff, a retry wait announced without a competing action, terminal copy/reference without **Coba lagi** or an injected fake secret, and disclosure reopening without another attempt. Keep the assertions for 016 actions and the Beranda table.
- [X] T008 [P] [US1] Add failing tests in `applications/hematdaya-mobile/tests/history-model.test.ts` for a weekly tie, equal displayed energy where the service chooses a later UTC start, measured zero as a valid highest, and a measured highest bucket crossing `effective_end` with coverage `1.000`. Assert exact values, elapsed wording, the 23/25 server-ordered hours, and offset-distinct repeated hours in the sparse axis, table and highest summary. Use the returned response bounds.
- [X] T009 [P] [US1] Strengthen the frozen comparison regression in `applications/hematdaya-mobile/tests/saran.test.tsx`. Use a frozen revision containing a null gap and exact non-null current/reference data. Check the single image label, legend entries, dotted-gap copy, aligned marks, exact data values, and unchanged evidence revision. Assert no asset measurements request.

### Implementation

- [X] T010 [P] [US1] Add `applications/hematdaya-mobile/src/features/assets/history-model.ts` after T008. Produce one display model with exact Indonesian energy labels, response context and cutoff, supplied provenance/resolution, plot labels and table rows. Use the returned UTC bounds and local date/time/offset. Keep every table row, sparsify dense axes and distinguish both repeated hours. Use the service's highest pointer or no-eligible-bucket copy. Qualify current coverage, current highest and period context using the same cutoff. Run T008.
- [X] T011 [P] [US1] Port `applications/hematdaya-mobile/src/components/hd/HDHistoryChart.tsx` to the installed `react-native-svg` after T009. Draw from a common zero baseline with chart tokens and 20% headroom. Preserve S08's filled current and dashed reference on one scale and the dotted mark for a frozen null. Render one accessible image label for the whole plot with no per-bar targets. Keep title, scope, period, unit, legend, scale and summary readable at larger text sizes. Dense axes show sparse labels and omit per-bar values. Verify T009.
- [X] T012 [P] [US1] Preserve the disclosure API in `applications/hematdaya-mobile/src/components/hd/HDChartDataAlternative.tsx` and supply semantic web markup with a caption, column headers and row headers in `applications/hematdaya-mobile/src/components/hd/HDChartDataTable.web.tsx` and responsive styles in `applications/hematdaya-mobile/src/components/hd/HDChartDataTable.css`. Keep the native stacked label/value rendition in `applications/hematdaya-mobile/src/components/hd/HDChartDataTable.tsx`. Stack the web rows below 768 CSS px and preserve the header relationships when stacked. Verify the keyboard-accessible disclosure and preserve the existing S03/S08 behavior.
- [X] T013 [US1] Wire the inline disclosure and statuses in `applications/hematdaya-mobile/src/features/assets/AssetHistorySection.tsx` and `applications/hematdaya-mobile/src/features/assets/AssetDetailScreen.tsx` after T006 and T010–T012. Pass only the current confirmed summary window to the query. Retain History during pending and failure within the same site and asset, with its own labels and cutoff. Announce pending, retry wait and terminal failure. Surface safe service copy, reference and terminal next step. Reuse the shared progress/error UI where it can honor the History budget. Keep current workspace/session handling, maintain the S06 back stack, show a truthful empty array state and expose the data alternative by button.
- [X] T014 [US1] Run the story tests with `npm test -- --runInBand tests/perangkat.test.tsx tests/history-model.test.ts tests/saran.test.tsx` in `applications/hematdaya-mobile/`. Record the complete-week and hourly checkpoints in `specs/015-history-chart/tasks.md`.

**Checkpoint** The complete-week question is answerable from visible text and the table alone, and the 23/25-hour cases render the service's actual buckets.

## Phase 4 — User Story 2, missing never looks like zero (P1)

**Independent test** Open the 19–25 October household learning-partial history. Pompa Air shows a gap on 24 October and Kulkas shows `1,100 kWh` with `91,6%` coverage on 22 October. Inspect the mixed fixture for measured and partial zero, future and both unavailable reasons, and the separate fixture with no eligible highest.

### Tests first

- [X] T015 [P] [US2] Extend `applications/hematdaya-mobile/tests/perangkat.test.tsx` with a mixed response covering measured positive/zero, partial positive/near-zero/reported zero, missing, future and unavailable reasons. Include a valid measured highest, a larger partial value, and comparison energy different from the recorded value. Assert exact energy/coverage parity, elapsed coverage for a current measured bucket, missing-period text and distinct reasons including a safe unfamiliar-reason fallback. In separate all-missing, all-future and all-unavailable responses assert null highest, appropriate rows, and replacement of a previous numeric chart. In `applications/hematdaya-mobile/tests/history-model.test.ts` assert the missing-period note for a repeated-hour gap uses the distinct returned UTC bounds and offsets.
- [X] T016 [P] [US2] Add failing plot tests in `applications/hematdaya-mobile/tests/history-chart.test.tsx` for numeric bars, a measured-zero baseline tick, distinct marks for partial positive/near-zero/reported zero, gap hatching, empty future slots and nonnumeric unavailable markers. Assert a single image role for all plot states. Check the distinct S08 current/reference marks and its dotted frozen-null marker in the shared renderer.

### Implementation

- [X] T017 [P] [US2] Extend `applications/hematdaya-mobile/src/features/assets/history-model.ts` after T015. Preserve the state and reason for plot, notes and table. Label missing **Tidak ada data** with an affected interval using the returned bounds and offsets. Label measured energy reported as zero **0,000 kWh** and mark it as measured. Keep recorded partial energy and coverage, even when the reported energy is zero. Label future **Belum terjadi**. Explain `source_conflict` and `insufficient_resolution` separately in safe Indonesian and show generic copy for an unfamiliar reason. Apply the same cutoff qualification to current state labels and retained context.
- [X] T018 [P] [US2] Extend `applications/hematdaya-mobile/src/components/hd/HDHistoryChart.tsx` after T016. Use an SVG `Pattern` with the missing-marker token and a matching legend label for S06 gaps. Use a measured-zero baseline tick and a distinct partial mark at any reported value. Leave future slots empty and use a nonnumeric treatment for unavailable data. Match plot text and notes to the state details in the display model. Verify the S08 frozen comparison and dotted gap from T009.
- [X] T019 [US2] Run `npm test -- --runInBand tests/perangkat.test.tsx tests/history-model.test.ts tests/history-chart.test.tsx tests/saran.test.tsx` in `applications/hematdaya-mobile/` and record the state-parity checkpoint in `specs/015-history-chart/tasks.md`.

**Checkpoint** Each service state is distinguishable across the plot and data alternative. Partial energy retains its coverage, future has no plotted measurement, and zero has a numeric value and a baseline tick.

## Phase 5 — Verification and handoff

- [X] T020 Run `make check` and `make export` in `applications/hematdaya-mobile/`. Run the mobile CI contract/token drift check with `make generate-api tokens && git diff --exit-code -- src/api/schema.generated.ts src/design/tokens.generated.ts`. Compare `contracts/openapi.json` against the T001 starting commit. Verify in `applications/hematdaya-mobile/tests/registry.test.ts` that 016's combined feature has not been advertised early. Record outputs and blockers in `specs/015-history-chart/tasks.md`.
- [X] T021 Run the web journey from `local-start.sh` or point `applications/hematdaya-mobile/Makefile`'s `web` target at a ready local API. In the household and industrial demos check Kulkas's seven `1,200 kWh` rows and Oven's highest date against the real 010 response. Select 19–25 October in the learning-partial scenario and check the Pompa Air gap on 24 October and Kulkas's `1,100 kWh` and `91,6%` on 22 October. Record the fixtures, browser and observed results or blockers in `specs/015-history-chart/tasks.md`.
- [ ] T022 Run the real web accessibility checks from `docs/product/design-handoff-EN.md` for the changed chart and disclosures. Check 320 CSS px reflow and 200% text separately. At widths below and above 768 CSS px, verify real table/header associations and row values in S03, S06 and S08. Use Tab, Enter and Space, verify logical visible focus, expanded state, announced loading/failure and no trap, and use a web screen reader to answer the highest-day question and read exact values. Measure affected touch targets at least 48×48 CSS px on mobile web and actual contrast at least 4.5:1 for normal text and 3:1 for necessary graphic/control information. Record measured results, runtime, viewport, assistive technology and blockers in `specs/015-history-chart/tasks.md`. Track native assistive technology as the separate 043 gate.
- [X] T023 Run `python3 docs/roadmap/check_traceability.py`. Update `specs/015-history-chart/spec.md` with the status supported by the executed checks. In `specs/015-history-chart/tasks.md`, record the final evidence and blockers, 016's combined registry flip, and the S07 **Tentang riwayat perangkat** link that still opens the generic feature-information placeholder for 016 to account for.

## Dependencies and execution order

```text
T001–T002 → T003 → T004 → T005 → T006
T006 → T007 / T008 / T009
T008 → T010    T009 → T011    T007 / T009 → T012
T006 / T007 / T010 / T011 / T012 → T013 → T014
T014 → T015 / T016    T015 → T017    T016 → T018
T017 / T018 → T019 → T020 / T021
T021 → T022    T020 / T022 → T023
```

- **US1 parallel example** Author the S06 flow, display model and S08 regression tests in their separate files. After the relevant tests are in place, implement the display model, SVG component and semantic table independently. Integrate once their display fields agree.
- **US2 parallel example** Author the S06 parity and SVG mark tests separately. Implement state copy in the history model and mark rendering in the shared chart in parallel after agreeing on the state fields.
- **MVP checkpoint** Verify the complete-week US1 path first with the normal chart and table, then complete US2 before opening the feature for release. Both stories share the plot and disclosure infrastructure.

## Coverage map

| Requirement | Evidence tasks |
|---|---|
| FR-001 and UX-13, service buckets and truthful states | T007–T011, T015–T019 |
| FR-002 and UX-18, visible summary and exact data alternative | T007, T012–T014, T021–T022 |
| FR-003 and AT-56, single plot label and operable alternatives | T009, T011–T012, T016, T022 |
| FR-004 and SC-001, validated response, elapsed cutoff and service-selected highest | T003–T008, T010, T013–T019 |
| FR-005, SC-003 and EH-09, bounded retries and truthful retained context | T003–T007, T013–T014 |
| SC-002, web screen reader and native handoff | T022–T023 and spec 043 |
| S06 and 016, integration and availability handoff | T007, T013, T020–T023 |

## Verification log

### Setup and automated checkpoints

- **T001–T002**. Started on branch `015-history-chart` at `a3f7556`. Both `git merge-base --is-ancestor` checks passed for `42aeebc` (014) and `fd50a7a` (022). `check-prerequisites.sh --json --require-tasks --include-tasks` found `applications/generic/hematdaya/specs/015-history-chart` and `tasks.md`. The mobile baseline on Node 24.8.0 with the lockfile-matched dependency tree passed `make check` with 14 suites, 405 tests, and 94.71% line coverage.
- **T003–T006**. The adapter tests failed before the export existed. They then passed with encoded bearer reads and safe normalized errors, including a valid daily range with a midnight offset change. The query tests failed before the hook existed and then passed. Fake timers verified one and three total HTTP attempts, the full wait, lifecycle triggers after terminal failure, and recovery during a background refresh. The shared retry callback still receives TanStack's zero-based failure count, while its existing test calls it with a one-based count. History owns and tests its separate total-attempt budget.
- **T007–T014**. The route, display model, and frozen comparison regressions first failed on the missing feature. The initial story checkpoint passed with 3 suites and 82 tests. Kulkas has seven matching daily rows and a highest-day summary. The hourly fixtures retain all 23 or 25 service buckets and distinguish both repeated hours. The S08 fixture retains its requested revision, exact current and reference data, aligned marks, and dotted null. Late summary and History replies, retained cutoff during failure and retry, and tab/back context have route coverage.
- **T015–T019**. The new state and mark assertions first failed on missing state treatments. The state checkpoint passed with the distinct marks, exact decimal and coverage text, missing interval boundaries, and replacement by all-missing, all-future, or all-unavailable data. The final targeted adapter, query, route, model, plot, S08, and registry run passed 7 suites and 162 tests.

### Live web and release evidence

- **T020**. Final `make check` passed lint, TypeScript and Jest on Node 24.8.0 with 17 suites, 461 tests and 94.55% line coverage. `make export` emitted Android and iOS Hermes bundles and the web export. The first offline run used the cached 7.13.0 executable because the sandbox lacked npm registry metadata. A later default `make generate-api tokens` run also passed with no generated diff. `contracts/openapi.json` and the registry matched `a3f7556`. The registry suite passed and `detail-perangkat` remains `coming_soon`. `make doctor` passed 20 of 20 checks. The production dependency audit reported zero high or critical findings, 21 moderate and one low.
- **T021**. Chrome 156.0.8078.80 on macOS exercised the Expo web development build at `localhost:8105` with FastAPI at `localhost:8025` and a disposable PostgreSQL 17 database. For 19–25 October 2026, the `h-base` Kulkas chart and table show seven `1,200 kWh` rows and name 19 October as highest. The `i-base` Oven names the same highest date and shows six `12,000 kWh` rows followed by measured `0,000 kWh` and a 2 CSS px tick. The `h-learning-partial` Pompa Air has hatched gaps on 24 and 25 October and no numeric energy in either row. The same demo's Kulkas shows `1,100 kWh`, `91,6%`, and partial copy on 22 October, with a distinct diamond marker. The `h-current` Kulkas shows 24 hourly rows, a cutoff of 21 October at 12.00 WIB, 12 measured marks, and 12 future slots with no measurement mark.
- **T022, browser portion**. At 900 and 320 CSS px, checked S03 Beranda, S06 History, and S08 revision 1 for native HTML caption and headers, explicit cell-to-header IDs, Chromium accessibility-tree table and header roles, and exact row values. The 320 CSS px view stacked without horizontal overflow. A separate 200% font-size and line-height simulation showed no clipped table cells. S06 exposed a single named image. Keyboard checks exercised Tab and Shift+Tab, Enter and Space, visible expanded state, a 2 CSS px solid focus outline, and leaving and returning to the controls without a trap. Both **Lihat riwayat** and **Lihat data** measured 288 × 48 CSS px and had a visible 2 CSS px solid outline. A delayed real GET exposed polite loading, and an injected refusal exposed the polite terminal message and service reference with one GET after collapse and reopening. Against the actual canvas `#f6f7f3`, normal primary text measured 15.21:1, secondary text and the gap stroke 6.35:1, the action text and current mark 6.16:1, the focus outline 5.80:1, and the baseline 3.86:1. The dashed reference stroke measured 4.86:1 against its fill.
- **T022, assistive technology still open**. Chrome's accessibility tree exposed the highest-bucket name and exact cell values. The VoiceOver speech query against the isolated Chrome window timed out, and VoiceOver was returned to its prior off state. A spoken web screen-reader run remains pending. Android TalkBack and iOS VoiceOver are part of 043. Bundle exports are build evidence.
- **T023**. `python3 docs/roadmap/check_traceability.py` mapped 123 requirements across 46 specs. Spec 016 owns the combined `detail-perangkat` registry flip for the edit and archive work. The existing S07 **Tentang riwayat perangkat** link still opens the feature-information placeholder and belongs in that handoff.
