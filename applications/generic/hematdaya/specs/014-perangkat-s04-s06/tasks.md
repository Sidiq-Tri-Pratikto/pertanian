# Tasks: Perangkat and asset detail

**Input**: `specs/014-perangkat-s04-s06/spec.md`, `plan.md`, generated against `origin/main` at `5ec2fba` and updated against `6563a2f`, the base now
**Branch**: `m2/perangkat`, fast-forwarded to `6563a2f`. `check-prerequisites.sh` refuses this name, so run it as `SPECIFY_FEATURE=014-perangkat-s04-s06 .specify/scripts/bash/check-prerequisites.sh --json`.
**Lane**: P2, roadmap round 5, internal MVP. P1 reviews every change listed under "For P1 review" in Notes.
**Prerequisites**: 010 and 013 are merged in `6563a2f`. `app/energy/router.py` serves `/assets/{asset_id}/measurements`, and `(tabs)/(beranda)/beranda.tsx` is the populated S03. The list also reads 021's notices, which are merged too (D3). 026 is merged as well, with Alembic head `0009`. 014 adds no migration and depends on neither 026 nor 027 (D25).
**Tests**: Required and first (constitution principle 2, roadmap step 4). Each phase writes its tests, then a checkpoint task runs them and records the failure, and only then writes the code. Tests follow rule 009: query by role and visible text, and cover loading, success, failure, empty and retry paths. Failure tests assert message, reference ID, recovery and that an injected fake secret appears nowhere (rule 008).

**Paths** start at `applications/generic/hematdaya/`. Commands run from `applications/hematdaya-mobile/`, on Node 24: `export PATH="$HOME/.nvm/versions/node/v24.8.0/bin:$PATH"`. The shell is zsh, so quote any path with parentheses. `app.js` means `docs/reference/prototype/hematdaya-app.js`. `Recorded` means `tests/fixtures/assets.json` from T002.

## Decisions resolved against the code

| ID | Decision | Why |
|---|---|---|
| D1 | The list joins two reads by asset ID. P1's `useSummary` gives name, `scope_kind`, kWh, reason, coverage, gaps, conflict sources, scope, window and origins. A new `useAssets` gives `location` and `category` from `GET /sites/{id}/assets`, following `next_cursor`. A summary row with no asset row still renders, with no location. | `AssetEnergyResponse` has no location or category, and `AssetResponse` has no energy. Two reads, no per-row request, and no API change. |
| D2 | Rows keep the service's order and the client never sorts: energy descending, unavailable last, then name, then asset ID. | `summary.py` L173. The seeded spec said "asset ID as a stable tie-break", which is not what the service does, and principle 8 keeps ordering with the service. |
| D3 | "Data belum diperbarui" comes from `useInsights().data.notices`, using entries with `kind === 'stale'` and an `asset_id`. The client never compares a timestamp with a cadence. Stale and partial show together. If the insights read fails, rows stay and one line says the check could not run. | `app/insights/service/notices.py` L70–85 computes staleness with the site clock, and nothing else exposes it. Rule 009 and principle 8 forbid recomputing it. The handoff treats stale and partial as independent facts, so the prototype's one-or-the-other label at `app.js` L312–313 is not copied. |
| D4 | Detail reads `GET /assets/{id}/summary` with the shared period and `GET /assets/{id}`. Its row is `summary.assets[0]`. It never renders `share_percent`, `scope.excluded` or the site-level "Total gabungan" copy. | Measured: a one-asset summary answers `share_percent: "100.00"` and lists every other asset in `excluded` as `not_selected`. Both are true for the request and misleading on screen. |
| D5 | Detail provenance comes from `asset.sources[].origin`. The list uses `summary.origins` through a shared `shownOrigins` helper taken from Beranda's inline rule. Detail falls back to the same helper when the asset read failed. | Measured: `origins` is `[]` on a no-data period and on a conflicted asset, so a tag driven by it would vanish exactly when the user most needs it. The Beranda line is at `beranda.tsx` L142. |
| D6 | Detail builds on `berandaModel` for period label, timezone, state, empty detail, latest reading and allocation, and overrides scope label and gaps. It reuses `HDEnergyMetric`, `HDDataQuality`, `HDPeriodSelector`, `HDProvenanceTag`, `HDNotice` and `HDProgressStatus`. A conflicted asset shows `HDNotice` and no `HDEnergyMetric`. | Principle 3 and rule 001. `HDEnergyMetric`'s conflict copy says "Total gabungan" and "Nilai masing-masing perangkat", which does not describe one asset with two sources, and P1's component needs no change. |
| D7 | Period comes from `useNavigationContext()`, with no new state. `HDPeriodSelector` appears on the populated list and on detail. A change on either screen moves every tab. | Architecture: navigation context lives in one provider. The handoff's period rule is the same one Beranda follows. |
| D8 | No client scope parameter. The list shows the scope of the service's response, and detail's scope is the asset itself. Query keys hold site, asset and period only. | `EnergyService.summarize` says "Until 028 the default selection is every active asset", and no route takes a scope. 029 adds selection and its invalidation. |
| D9 | One line fixes scroll: `HDScreen` calls `focus({ preventScroll: true })` on web. No offset is stored in the navigation context. | Measured in the browser on merged code: Beranda scrolled to 1200, opened Pengaturan and came back at 0, on the same DOM node, with focus on the heading. With `preventScroll` patched in at runtime, it came back at 1200, after a tab round trip too. The stack keeps the list mounted, so the scroll view keeps its own offset. A stored offset would add state that this fix makes unnecessary. |
| D10 | Rows render with `.map` inside `HDScreen`'s `ScrollView`, as `role="list"`. No `FlatList`. | `HDScreen` owns a vertical `ScrollView`, so a nested `FlatList` warns and stops virtualizing. Architecture bans FlashList until a measured need and does not ask for `FlatList`. The summary returns every row at once, PRD §18's working scale is 20 sources, and demo sites have 4 or 5 assets. Rule 006: measure first. |
| D11 | A failed read keeps the last confirmed content. New `useLastConfirmed(query)` holds the last non-placeholder success in state and returns `query.data ?? kept`. The list and detail bodies mount under `key={siteId}` so nothing crosses workspaces. | `keepPreviousData` only applies while a query is pending (`queryObserver.ts`), so a failed period change makes `data` undefined. Measured on Beranda: number gone, selector gone. The observer also remembers its last query across a `queryClient.clear()` (`#lastQueryWithDefinedData`, L666–667), which the `key` drops. |
| D12 | Failures use `ReadFailure`: label, service `message`, `ID referensi` when present, and **Coba lagi** only when `recovery.retryable === true`. A press is a new user-started attempt. | Rule 009. Query retries already spend `max_attempts` before an error surfaces (`shouldRetry`), so hiding the button at the limit would hide it always. Beranda and Saran always show the button and no reference. That gap is reported, not changed here. |
| D13 | Detail never waits on a disabled query. With no workspace, or a `NOT_FOUND` from either read, it shows "Perangkat tidak ditemukan" and Kembali. A foreign asset reads the same. | A disabled query stays pending, so "no data means loading" would spin forever after a session ends. Measured: an unknown ID and another principal's ID both return 404 `NOT_FOUND`, `retryable: false`. |
| D14 | One empty S04 for no workspace and for no assets: "Belum ada perangkat", existing body, **Tambah sumber** primary, **Impor data**, **Coba demo** through `DemoSheet`, `SessionEndedNotice` and Pengaturan. "Lihat rencana fitur ini" goes. It shows no date and no number, so it does not depend on the `empty` scenario's `virtual_now`. | Handoff S04: "Empty list links to import/demo". The removed link would announce "Segera hadir" for a shipped feature. The clock is an open owner question, and this state stays correct whatever the answer. |
| D15 | **Tambah sumber** and **Impor data** stay on `openFeature('sumber-meter')` and `openFeature('impor-data')` in both empty and populated states. | FR-004. 035 and 027 replace them. 026's commit route does not change this: `impor-data` is still `coming_soon` at `6563a2f`, and no client path can import until 027. |
| D16 | `useTabNavigation` gains `openAsset(id)`, pushing `inTab('asset/<encoded id>')`, so detail stays in the invoking tab. Routes only compose: `(perangkat)/perangkat.tsx` exports `PerangkatScreen` and `asset/[id].tsx` passes the param to `AssetDetailScreen`. | Rule 009 layout, FR-003 and the `saran/[id].tsx` pattern. |
| D17 | Beranda wiring changes P1's modules, all flagged for review: `berandaModel` ranking gains `assetId`; `HDContributionRanking` gains required `onOpen`, makes each row one link and keys by ID; `beranda.tsx` adds primary **Lihat perangkat terbesar**, shown only when `largest.share !== null`. | 013's plan left this for 014. A name is not an identity (`AssetModel` docstring), and today's `key={item.name}` collides on equal names. With no share there is no largest: zero total, scope conflict and insufficient resolution all hide the action. |
| D18 | Flip only `daftar-perangkat`. `detail-perangkat` stays `coming_soon` until 015 and 016. Pengaturan shows `FEATURES.filter((feature) => feature.status === 'coming_soon')`. | `.status` is read only by `tests/registry.test.ts`. `FeatureRow` hard-codes "segera hadir" and `segera-hadir/[feature].tsx` renders `HDComingSoon` whatever the status. Measured: all 17 rows say "segera hadir" with a workspace open. Without the filter, Settings would say "Daftar perangkat, segera hadir" beside the working tab. |
| D19 | `e2e/smoke.yaml` stays byte for byte. Its Perangkat step runs with no workspace, because the API is absent and Mulai fails, so it reaches the no-workspace branch of D14, which makes no request. `tests/navigation.test.tsx` mirrors the flow and must pass unchanged. | D14 keeps the exact text "Belum ada perangkat". See "What the Android job proves" in Notes. |
| D20 | No API change. The four gaps below all have an honest client answer, so `contracts/openapi.json` and `schema.generated.ts` stay untouched. | Principle 3. See the API gaps table. |
| D21 | **Lihat periode data** sets `workspace.initialPeriod`, as Beranda does, and appears only when the state is `none` and the current period is not already that period. | The service has no per-asset data range, and the prototype's `dataRange` reads local readings. A button that changes nothing would be a dead end. |
| D22 | Sumber data lists one entry per binding, from `asset.bindings` joined to `asset.sources`: label, origin, transport, interval and resolution, effective range, and whether it is the reference source. Null cadence or resolution says "tidak diketahui". | Principles 7 and 9. `resolution_mwh` null means unknown, and the handoff asks for origin, time and resolution. Past bindings stay listed because the service returns them. |
| D23 | 014 does not call `/assets/{id}/measurements`, render `HDHistoryChart`, or offer Lihat riwayat, Ubah detail, Arsipkan or a Diarsipkan list. | 015 and 016. PR #29's chart stays for 015. |
| D24 | Accessibility: rows and ranking rows are one `role="link"` with a full `aria-label` and `minHeight` 48. No `numberOfLines` and no `allowFontScaling`. Failures use the always-mounted `HDProgressStatus` region, and the period line announces through `HDPeriodSelector`. Safe areas come from `HDScreen` and `HDTabBar`. No animation is added. | UX-13, UX-14, rule 009, `docs/design/components/AssetRow.md`. |
| D25 | Nothing here needs 026's routes or 027's screens. PR #31 is merged, and none of the reads 014 uses changed with it. 014 still does not edit `schema.generated.ts` or run `make generate-api`. Only T002 calls 026's routes, once, to record what an imported source looks like. If 027 or 035 merges first, T052 repoints that entry point and nothing else moves. | Measured from `5ec2fba` to `6563a2f`: the mobile app changes only in `schema.generated.ts` (zero removed lines, no asset, summary or notice type touched) and `e2e/android-smoke.sh`. `app/energy/` and `app/insights/` have no change, and in `app/assets/` only `add_binding` gains an optional `effective_to`. Seven scenarios read the same before and after (Notes). |
| D26 | Tests use responses recorded from the service in `tests/fixtures/assets.json`, the way `insights.json` was recorded. | No golden file covers `/assets/{id}`, `/assets/{id}/summary` or `/sites/{id}/assets`. `golden/summary-scope.json` is the 24–25 Oktober window, while `h-scope` opens on 25 Oktober alone. |
| D27 | `HDAssetRow` keeps `HD.AssetRow`'s props: `name`, `kind` (`device`, `circuit`, `group`, `meter`), `location`, `kwh`, `quality`, `qualityLabel`, `onOpen`. `kwh` is the formatted string or null, because values never become numbers here. Native additions, recorded as system changes: `category`, `sources` (one line per unresolved source) and `stale` (a flag, because `stale` as a `quality` value could not sit beside `partial`). The model maps `site_total` to `meter`, and the row shows it as "Meter lokasi". | Architecture: `src/components/hd/` ports with "the same name and meaning as `window.HD`". `docs/design/components/index.d.ts` L187. 013 recorded `HDEnergyMetric`'s native conflict state the same way. |

### API gaps, and what 014 does instead

| The spec needs | The API gives | 014 does | Change needed |
|---|---|---|---|
| Category and location on a row | Not on the summary row | Second read, D1 | None |
| Per-asset staleness | Only in `/insights` notices | Reads notices, D3 | None |
| Per-source last capture | Not exposed | Asset-level `latest_measurement_at`, and the stale notice's body names the last reading | None |
| Per-asset data range for Lihat periode data | Not exposed | `workspace.initialPeriod`, D21 | None |

## States

### List

| State | When | Shows |
|---|---|---|
| Workspace loading | `status === 'loading'` | "Memuat ruang kerja…" |
| No workspace | `workspace === null` | Empty S04, no request |
| First read | No summary yet, no error | "Memuat data perangkat…" in the status region, no number |
| First read failed | No summary yet, error | `ReadFailure` "Data perangkat belum dapat dimuat" |
| Empty | `summary.assets.length === 0` | Empty S04 |
| Populated | Rows exist | Period, scope, provenance, scope notice if invalid, actions, rows, order note, allocation note if flagged, Pengaturan |
| Period change pending | Placeholder data | Previous rows with their own period label |
| Read failed with rows known | Kept rows, error | Rows, selector, `ReadFailure` "Data perangkat belum dapat diperbarui" with "Angka yang tampil adalah data terakhir yang terkonfirmasi." |
| Location read failed | `useAssets` error | Rows without location, plus "Lokasi dan kategori belum dapat dimuat." |
| Stale check failed | `useInsights` error | Rows, plus "Status pembaruan sumber belum dapat diperiksa." |

### Row

The value and quality come from `assetRowModel`. Stale is separate and adds to any state.

| Row data | Value | Quality line |
|---|---|---|
| `conflict_sources` present | `— kWh` | "Lebih dari satu sumber · nilai tidak dijumlahkan", then one `{label}: {kWh}` line per source |
| Reason `insufficient_resolution` | `— kWh` | "Resolusi data belum cukup untuk periode ini" |
| Reason `no_data` | `— kWh` | "Belum ada data pada periode ini" |
| Any other null value | `— kWh` | "Data belum tersedia" |
| Value, coverage not `1.000` | `1,620 kWh` | "Kelengkapan data: 96,4% periode" |
| `0.000`, coverage `1.000` | `0,000 kWh` | "Nol terukur dengan data lengkap" |
| Value, coverage `1.000` | `8,400 kWh` | "Kelengkapan data: 100% periode" |
| Stale notice for this asset | Unchanged | Adds "Data belum diperbarui" |

### Detail

| State | When | Shows |
|---|---|---|
| Workspace loading | `status === 'loading'` | "Memuat ruang kerja…" |
| Not available | No workspace, no ID, or `NOT_FOUND` | Title and notice "Perangkat tidak ditemukan", "Perangkat ini tidak ada di ruang kerja aktif.", `ID referensi` when known, `SessionEndedNotice`, Kembali |
| First read | No summary and no asset yet | Title "Perangkat", "Memuat perangkat…" |
| First read failed | No summary, other error | Title from the asset if known, `ReadFailure` "Perangkat belum dapat dimuat" |
| Summary pending, asset known | Asset read done, summary not yet | Title from the asset, "Memuat perangkat…", Sumber data |
| Complete, partial or zero | Value present | `HDEnergyMetric` with every gap, `HDDataQuality`, Sumber data |
| No value | `state === 'none'` | `HDEnergyMetric` with `emptyDetail`, and Lihat periode data under D21 |
| Conflict | `conflict_sources` present | `HDNotice` "Lebih dari satu sumber untuk beban yang sama" with one value per source, the service's message, and no total. Coverage is null, so `HDDataQuality` has no Kelengkapan data row |
| Stale | Notice for this asset | `HDNotice` tone attention with the service's `title` and `body` |
| Period read failed | Kept summary, error | Kept numbers, selector, `ReadFailure` "Data perangkat belum dapat diperbarui" with the confirmed-data sentence |
| Source read failed | Summary present, `useAsset` error | Energy stays, `ReadFailure` "Sumber data belum dapat dimuat" |
| Stale check failed | `useInsights` error | Everything stays, plus "Status pembaruan sumber belum dapat diperiksa." |

## Copy

All product copy is Indonesian (principle 10). New strings not in the tables above:

| Where | Text |
|---|---|
| Row order note | "Urutan berdasarkan energi tercatat pada periode ini. Urutan bukan penilaian boros atau hemat." |
| List scope notice | Title "Total gabungan belum dapat dihitung", body: every `scope.issues[].message` joined by a space, then " Nilai masing-masing tetap ditampilkan." |
| Scope kind labels | `device` Perangkat, `group` Grup, `circuit` Sirkuit, `site_total` Meter lokasi |
| Row and detail meta | `{kind} · {location} · {category}`, leaving out what is absent |
| Detail scope label | "Cakupan pengukuran: 1 perangkat (hanya beban yang diukur sumber ini)" for a device, else "Cakupan pengukuran: 1 meter lokasi", "1 grup", "1 sirkuit" |
| Origin labels | `simulated` Simulasi, `import` Impor CSV, `dataset_replay` Putar ulang dataset, `live` Langsung |
| Transport labels | `simulated_live` adds "Simulasi koneksi", `historical` adds "Data historis", `none` adds nothing |
| Source rows | "Sumber", "Asal", "Interval dan resolusi", "Berlaku", "Peran". With no binding: "Belum ada sumber untuk perangkat ini." |
| Interval and resolution | `1 jam · resolusi 0,001 kWh`, with "interval tidak diketahui" and "resolusi tidak diketahui" for null |
| Effective range | "mulai {date time}", adding " sampai {date time}" when ended |
| Reference role | Authoritative: "Sumber acuan". Otherwise: "Belum dipilih sebagai sumber acuan" |
| Data quality terms | "Kelengkapan data", "Pengukuran terakhir", "Asal data", as on Beranda |
| Value for a screen reader | `nilai belum tersedia` replaces `— kWh` in the row's `aria-label` |
| Beranda action | "Lihat perangkat terbesar" |

The word "mati" appears only in the service's "Ini bukan tanda perangkat mati." Nothing says a device is off.

---

## Phase 1: Setup

- [X] T001 Record the baseline: run `make check` in `applications/hematdaya-mobile/`, confirm `git merge-base --is-ancestor 6563a2f HEAD`, and write the test, suite and coverage numbers into Notes in `specs/014-perangkat-s04-s06/tasks.md`.
- [X] T002 Record `applications/hematdaya-mobile/tests/fixtures/assets.json` from the merged service. Start a throwaway `postgres:17-alpine` on port 55432 (`POSTGRES_USER=app`, `POSTGRES_PASSWORD=app`, `POSTGRES_DB=app`), then in `applications/hematdaya-api/` run `DATABASE_URL=postgresql+asyncpg://app:app@localhost:55432/app uv run alembic upgrade head` and `uv run uvicorn app.main:app --port 8001` with the same `DATABASE_URL`. With a script kept outside the repository, for each of `h-base`, `h-scope`, `h-stale-offline`, `h-learning-partial`, `h-zero`, `empty` and `i-base`: `POST /api/v1/demo/sessions` with a 22-plus character `Idempotency-Key` and a 43-plus character `X-Demo-Replay-Proof`, then store under the scenario name `{initial_period, summary, assets, notices, details}`, where `summary`, `assets` and `notices` come from `/sites/{id}/summary`, `/sites/{id}/assets?limit=100` and `/sites/{id}/insights` at the initial period, and `details` maps each asset name to `{asset, summary}` from `/assets/{id}` and `/assets/{id}/summary`. For `h-base` also store `today` (site summary at `preset=today`) and `today_asset` (Kulkas's asset summary at `preset=today`). Also store `imported`, the same shape, from an `empty` session after `POST /sites/{id}/imports/preview` (multipart: `mapping` of `{"scope": "disjoint", "timezone_confirmed": true}`, `file` holding a CSV with header `interval_start,interval_end,asset,energy_wh` and two hourly rows on 2026-10-20 for each of Router and Kulkas, as `TWO_ASSETS_CSV` in `test_import_commit.py`) and `POST /imports/{id}/commit` with `{"acknowledge_skipped": false}` and an `Idempotency-Key`. Never store `token` or `site_id`. End the file with a newline, stop the servers and remove the container. If Docker is unavailable, stop and report it as an environment blocker. Do not hand-write the file.

---

## Phase 2: Foundational

**Purpose**: The client reads, labels, hooks and the focus fix both stories need. No screen changes yet.

### Tests first

- [X] T003 [P] Add `describe('asset reads')` to `applications/hematdaya-mobile/tests/data-layer.test.tsx`. `getAssets('site 1', 'tok')` requests `/api/v1/sites/site%201/assets?limit=100` with the bearer token, follows a two-page `next_cursor` (second call carries `cursor=`) and returns both pages' items in order, and stops after 20 pages if a cursor never ends. `getAsset('a/b', 'tok')` encodes the ID. `getAssetSummary('a 1', { preset: 'today' }, 'tok')` requests `/api/v1/assets/a%201/summary?preset=today`. Each rejects `{ secret: 'x' }` with `UNEXPECTED_RESPONSE`. A 404 envelope gives `ApiError` with code `NOT_FOUND` and its `requestId`.
- [X] T004 [P] Add table tests to `applications/hematdaya-mobile/tests/format.test.ts`: `formatCadence` gives 3600 → `1 jam`, 7200 → `2 jam`, 900 → `15 menit`, 90 → `90 detik`. `formatResolution` gives 1000 → `0,001 kWh`, 1500 → `0,0015 kWh`, 1 → `0,000001 kWh`, 1000000 → `1 kWh`. `formatAssetMeta` gives (`device`, `Dapur`, `Pendingin makanan`) → `Perangkat · Dapur · Pendingin makanan`, (`meter`, `Teras`, null) → `Meter lokasi · Teras`, (`group`, null, null) → `Grup`, (`circuit`, null, `Mesin`) → `Sirkuit · Mesin`.
- [X] T005 [P] Create `applications/hematdaya-mobile/tests/asset-model.test.ts`. `assetRowModel(row, asset, staleIds)`: every row of the States table, using Recorded rows where they exist and a crafted row for `insufficient_resolution` and for an unknown reason `future_reason`; a null value gives `kwh: null` and never `0,000 kWh`; `kind` is `device`, `group` and `circuit` as sent and `meter` for `site_total`; `location` and `category` come from the asset, and a missing `asset` gives null for both; stale adds to a partial row and replaces nothing. `staleAssetIds(notices)` keeps only `kind === 'stale'` with an `asset_id`, from Recorded `h-stale-offline` and `h-learning-partial`. `assetDetailModel(summary, asset, notices)`: from Recorded, Kulkas gives period `19–25 Oktober 2026`, the device scope label, `8,400 kWh` and no share field; Pompa Air in `h-learning-partial` gives state `partial` and gap `24–25 Oktober 2026` with no name prefix; Kulkas in `h-scope` gives state `conflict` and two source lines at `1,000 kWh`; Meter utama gives `Cakupan pengukuran: 1 meter lokasi`; source rows give `Simulasi`, `1 jam · resolusi 0,001 kWh` and `Sumber acuan`; `Simulasi koneksi` for Router in `h-stale-offline`; `Belum dipilih sebagai sumber acuan` for both Kulkas sources in `h-scope`; Kulkas in `imported` gives `Impor CSV · Data historis` and `interval tidak diketahui · resolusi tidak diketahui`, because that source's cadence and resolution are null; an undefined `asset` gives `meta` with the kind alone, empty `sourceRows` and empty `origins`. `shownOrigins(origins, scenarioId)`: keeps a non-empty list, gives `['simulated']` for an empty list in a demo scenario, and `[]` for `empty`.
- [X] T006 [P] Add `describe('screen focus')` to `applications/hematdaya-mobile/tests/navigation.test.tsx`: with `Platform.OS = 'web'`, clear `Text.prototype.focus` (a shared Jest mock), `renderRouter({ index: () => <HDScreen title="Judul"><View /></HDScreen> }, { initialUrl: '/' })`, and expect `Text.prototype.focus` last called with `{ preventScroll: true }`. Restore `Platform.OS` in `afterEach`. Measured today: called with no argument, so this fails.
- [X] T007 Checkpoint: run `npx jest tests/data-layer.test.tsx tests/format.test.ts tests/asset-model.test.ts tests/navigation.test.tsx`. Record in Notes in `specs/014-perangkat-s04-s06/tasks.md` that T003 to T006 fail for the stated reason. Do not write code before this.

### Code

- [X] T008 Extend `applications/hematdaya-mobile/src/api/client.ts`. Types from `components['schemas']`: `Asset` (`AssetResponse`), `AssetPage`, `AssetDetail`, `AssetSource` (`SourceResponse`), `AssetBinding` (`BindingResponse`), `AssetEnergy` (`AssetEnergyResponse`), `ScopeKind`, `SourceOrigin`, `TransportStatus`. Guards `isAssetPage` (`items` array of records with string `id`, `next_cursor` string or null) and `isAssetDetail` (string `id` and `name`, `bindings` and `sources` arrays). Functions `getAssets(siteId, token)` (limit 100, follows `next_cursor`, at most 20 pages, returns `Asset[]`), `getAsset(assetId, token)` and `getAssetSummary(assetId, period, token)` (reuses `isSummary`). Encode every ID. Do not touch `schema.generated.ts`.
- [X] T009 [P] Add `formatCadence(seconds: number)`, `formatResolution(mwh: number)`, `export type AssetKind = 'device' | 'circuit' | 'group' | 'meter'`, `KIND_LABEL` and `formatAssetMeta(kind, location, category)` to `applications/hematdaya-mobile/src/lib/format.ts`. `formatResolution` moves the decimal point six places on the digit string, trims trailing zeros and calls `formatKwh`, with no floating-point division, like `formatRatio`. `formatAssetMeta` joins what is present with ` · `. The row and the detail both use it, so it sits here, below both.
- [X] T010 Add `export function shownOrigins(origins: string[], scenarioId: string | undefined): string[]` to `applications/hematdaya-mobile/src/features/energy/beranda-model.ts`, holding the rule at `beranda.tsx` L141–142 and its comment, and use it from `applications/hematdaya-mobile/src/app/(tabs)/(beranda)/beranda.tsx`. Behaviour stays the same.
- [X] T011 Create `applications/hematdaya-mobile/src/features/assets/asset-model.ts` with `assetRowModel`, `staleAssetIds` and `assetDetailModel`, per the States and Copy tables. `assetRowModel` returns `{ assetId, name, kind, location, category, kwh, quality, qualityLabel, sources, stale }` with `kwh` from `formatKwh` or null, and `quality` of `complete`, `partial` or `unavailable`: a conflict or a null value is `unavailable`, and a measured zero with full coverage is `complete`. It holds `KIND_BY_SCOPE`, mapping `site_total` to `meter`. `assetDetailModel` calls `berandaModel(summary)` and returns its `periodLabel`, `timezone`, `state`, `kwh`, `qualifier`, `completeness`, `emptyDetail`, `latest` and `allocated`, overriding `scopeLabel` and `gaps` (every `row.gaps` entry through `formatGap`, no name prefix), and adds `name`, `meta` (from `formatAssetMeta`), `issues`, `sources` (conflict lines), `sourceRows` (D22), `origins` (the unique `asset.sources[].origin`, empty with no asset, so the screen falls back to `shownOrigins`, per D5) and `staleNotices`. Compare coverage as a string, as `berandaModel` does. No `Number()` and no `parseFloat`.
- [X] T012 [P] Create the hooks. `applications/hematdaya-mobile/src/features/assets/useAssets.ts`: `useAssets()` with key `['assets', siteId]`, and `useAsset(assetId)` with key `['asset', assetId]`, enabled only with a workspace and an ID. `applications/hematdaya-mobile/src/features/assets/useAssetSummary.ts`: key `['asset-summary', siteId, assetId, period]`, `placeholderData: keepPreviousData`, enabled only with workspace, period and ID. `applications/hematdaya-mobile/src/features/assets/useLastConfirmed.ts`: `useLastConfirmed(query)` keeps the last `data` where `isPlaceholderData` is false, using the set-state-during-render pattern, and returns `query.data ?? kept`.
- [X] T013 [P] Add `openAsset` to `applications/hematdaya-mobile/src/features/navigation.ts`: it takes an ID and pushes `inTab('asset/' + encodeURIComponent(id))`, the same shape as `openEvidence`.
- [X] T014 [P] Change `applications/hematdaya-mobile/src/components/hd/HDScreen.tsx` to call `.focus({ preventScroll: true })` on web, with a comment saying that a return from a stack screen must keep the reader's place. Native code stays.
- [X] T015 [P] Create `applications/hematdaya-mobile/src/features/assets/ReadFailure.tsx` with props `{ error: unknown; label: string; retrying: boolean; onRetry: () => void; kept?: boolean }`. A null `error` renders `<HDProgressStatus state={null} />`, so the status region stays mounted. Otherwise `ApiError.from(error)`, `state="failure"`, `detail` of `message`, then `ID referensi: {requestId}.` when present, then "Angka yang tampil adalah data terakhir yang terkonfirmasi." when `kept`. The action is `HDButton` variant `text`, icon `refresh`, "Coba lagi", `loading={retrying}`, only when `recovery.retryable === true`.
- [X] T016 Run `npx jest tests/data-layer.test.tsx tests/format.test.ts tests/asset-model.test.ts tests/navigation.test.tsx tests/demo-journey.test.tsx`, `make typecheck` and `make lint` until they pass. `demo-journey` covers T010. `make lint` checks that `useLastConfirmed`'s state update during render passes the project's React rules: if it does not, use `useEffect` and record why in Notes in `specs/014-perangkat-s04-s06/tasks.md`.

**Checkpoint**: Reads, labels, hooks and the focus fix exist. No screen uses them yet.

---

## Phase 3: User Story 1 - See every measured thing (Priority: P1) MVP

**Goal**: S04 lists every measured asset with its scope kind and quality, in every state, and never shows a fake zero or a control.

**Independent Test**: Open Perangkat in `h-base` and in `h-scope`.

### Tests first

- [X] T017 [P] [US1] Add `describe('HDAssetRow')` to `applications/hematdaya-mobile/tests/components.test.tsx`: one `role="link"` named `Kulkas, Perangkat, Dapur, Pendingin makanan, 8,400 kWh, Kelengkapan data: 100% periode`, and showing the text `Perangkat · Dapur · Pendingin makanan`; `kind="meter"` shows "Meter lokasi"; a press calls `onOpen` once, `within(row)` finds no `button` and no `switch`; `kwh={null}` shows `— kWh`, says `nilai belum tersedia` in the name and never `0`; the 60-character name "Pompa Air Area Produksi Belakang Gedung Selatan Lantai Dua A" appears whole with no `numberOfLines` prop; `StyleSheet.flatten(row.props.style).minHeight` is at least 48; `sources` lines and "Data belum diperbarui" render and join the name when given.
- [X] T018 [US1] Create `applications/hematdaya-mobile/tests/perangkat.test.tsx` with a first-line comment naming when and from which service `Recorded` came, `storeWorkspace(scenario)` (as `saran.test.tsx`, site ID `site-{scenario}`, `initialPeriod` from Recorded), and `mockApi({ summary, assets, insights, asset, assetSummary, create })` dispatching on pathname regexes in this order: `^/api/v1/demo/sessions$` (201 with `{ token, site_id: 'site-{scenario}', scenario_id, expires_at, initial_period }` from the request body), `^/api/v1/sites/[^/]+/summary$`, `^/api/v1/sites/[^/]+/assets$`, `^/api/v1/sites/[^/]+/insights$` (answering `{ window, observations: [], notices, learning_count: 0, comparable_count: 0 }`), `^/api/v1/assets/[^/]+/summary$`, `^/api/v1/assets/[^/]+$`, and 404 `{}` for anything else. Each handler defaults to Recorded: the scenario comes from `site-{scenario}` in the path, and asset routes find their entry by asset ID across Recorded's `details`. Then `describe('Perangkat list')`: `h-base` shows four rows inside the list named "Daftar perangkat, urut energi tercatat", in the order Kulkas, TV, Pompa Air, Router, each with its kind, location and category line and its value (`8,400`, `2,520`, `2,100`, `1,680 kWh`); "Periode aktif: 19–25 Oktober 2026 · Asia/Jakarta", "Cakupan pengukuran: 4 perangkat", "Demo · Data simulasi"; no `14,700 kWh`, because the list never shows a total. `h-scope` shows Meter utama first as "Meter lokasi · Teras · Meter rumah" at `10,000 kWh`, Kulkas last at `— kWh` with `Colokan simulasi Kulkas (sumber kedua): 1,000 kWh` and `Sumber demo (simulasi): 1,000 kWh`; every Recorded issue message visible under "Total gabungan belum dapat dihitung", with "Nilai masing-masing tetap ditampilkan."; no "Pilih cakupan". In any row: no `switch` role and no `/paling boros/i`, `/nyalakan|matikan/i`. `i-base` shows Oven first at `72,000 kWh` with "Perangkat · Area produksi · Pemanas/memasak".
- [X] T019 [US1] Add failure tests to `applications/hematdaya-mobile/tests/perangkat.test.tsx`. A pending first read shows "Memuat data perangkat…" in a `status` region and no `/kWh/`. A 500 with `recovery.retryable: false` and an extra `debug_info: 'fake-secret-123'` in the envelope shows "Data perangkat belum dapat dimuat" inside a `status` region, the message and "ID referensi: ref_1", no "Coba lagi", no `/kWh/`, no `/fake-secret-123/`. A failure with `{ retryable: true, max_attempts: 1 }` (no query retry, so no timers) shows "Coba lagi", and pressing it shows the rows. While a Hari ini read is still pending, the four rows and "Periode aktif: 19–25 Oktober 2026 · Asia/Jakarta" stay, and no `0,000 kWh` shows. Choosing Hari ini when that read fails keeps all four rows and their values, the selector, "Periode aktif: 19–25 Oktober 2026 · Asia/Jakarta", "Data perangkat belum dapat diperbarui" and the confirmed-data sentence, with no `0,000 kWh`; choosing "7 hari lengkap terakhir" clears the failure. A refresh that fails through Beranda's Perbarui leaves the rows on Perangkat with the failure status. A failed `/assets` read keeps kWh and quality, drops location, and shows "Lokasi dan kategori belum dapat dimuat." A failed `/insights` read keeps the rows and shows "Status pembaruan sumber belum dapat diperiksa."
- [X] T020 [US1] Add empty tests to `applications/hematdaya-mobile/tests/perangkat.test.tsx`. With no stored workspace: "Belum ada perangkat", and no `/summary` or `/assets` request. With `empty`: "Belum ada perangkat", no `/kWh/`, no "Periode aktif", no "Lihat rencana fitur ini". **Tambah sumber** opens heading "Sumber dan meter" with "Segera hadir" and tab Perangkat selected, and Kembali returns; **Impor data** opens "Impor data CSV"; **Coba demo** opens "Pilih data demo". A 401 `SESSION_EXPIRED` on the summary shows "Sesi demo sudah berakhir" and "Belum ada perangkat". Pressing **Coba demo** from there, choosing Industri and pressing Buka demo shows Oven and never Kulkas.
- [X] T021 [US1] Add quality tests to `applications/hematdaya-mobile/tests/perangkat.test.tsx`. `h-learning-partial`: Pompa Air "Kelengkapan data: 71,4% periode", Kulkas "Kelengkapan data: 98,8% periode". `h-zero`: every row `0,000 kWh` and "Nol terukur dengan data lengkap". `h-base` `today`: every row `— kWh` and "Belum ada data pada periode ini", no `0,000 kWh`. `h-stale-offline`: Router shows both "Data belum diperbarui" and "Kelengkapan data: 96,4% periode", the other rows do not, and the screen has no `/\bmati\b/i`. A summary with `allocated_estimate: true` shows Beranda's estimate sentence. A summary with an archived asset in `scope.excluded` shows "Tidak termasuk: {name}." `imported`, stored with site ID `site-imported` and scenario ID `empty`: rows Kulkas and Router, each showing only "Perangkat" as its kind, location and category line, "Kelengkapan data: 1,1% periode", "Data impor" and no "Demo · Data simulasi". Choosing Hari ini on Perangkat sends `preset=today`, and tab Beranda then shows "Periode aktif: 26 Oktober 2026".
- [X] T022 [US1] Checkpoint: run `npx jest tests/components.test.tsx tests/perangkat.test.tsx`. Record in Notes in `specs/014-perangkat-s04-s06/tasks.md` that T017 to T021 fail for the stated reason. Do not write code before this.

### Code

- [X] T023 [P] [US1] Create `applications/hematdaya-mobile/src/components/hd/HDAssetRow.tsx` per D27, with props `{ name, kind, location, category, kwh, quality, qualityLabel, sources, stale, onOpen }`, showing `formatAssetMeta(kind, location, category)` under the name. One `Pressable` with `role="link"` and an `aria-label` joining name, the same kind, location and category, value (`nilai belum tersedia` when `kwh` is null), `qualityLabel`, `sources` and "Data belum diperbarui" when stale, with `, `. `qualityLabel` uses tone `attention` for `partial` and `unavailable`, and the stale line uses tone `attention`. Plain `style`: `minHeight: tokens.size.targetMinimum`, `flexDirection: 'row'`, `flexWrap: 'wrap'`, `alignItems: 'flex-start'`. Text column: `flexGrow: 1`, `flexShrink: 1`, `flexBasis: 180`, `minWidth: 0`, so the value drops below the name instead of squeezing it at large text. Value block: `marginLeft: 'auto'`, the value text (`kwh ?? '— kWh'`) and `HDIcon` `chevronRight`. Add the focus ring with `onFocus` and `onBlur` as `HDButton` does. No `numberOfLines`, no nested pressable.
- [X] T024 [US1] Create `applications/hematdaya-mobile/src/features/assets/PerangkatScreen.tsx` per the List states and D1 to D3, D7, D10 to D12, D14 and D15. `PerangkatScreen` branches on `useWorkspace()` as `BerandaScreen` does: `HDScreen` title "Perangkat", subtitle "Perangkat, grup, sirkuit, dan meter lokasi". `<WorkspacePerangkat key={workspace.siteId} />` holds `useSummary`, `useAssets`, `useInsights` and `useLastConfirmed`. Populated reading order: `HDPeriodSelector`; `model.scopeLabel` with "Hanya mencakup sumber yang dipilih." and the same `Tidak termasuk` sentence as Beranda; `HDProvenanceTag` from `shownOrigins`; scope `HDNotice` tone `attention` when `scope.valid` is false, with no action until 029; `ReadFailure`; **Tambah sumber** primary and **Impor data**; the location-failure and stale-check-failure lines, as `HDText` variant `label`; `View role="list"` with `aria-label="Daftar perangkat, urut energi tercatat"` and rows from `assetRowModel` inside `role="listitem"`, keyed by asset ID, calling `openAsset`; the order note; the allocation note; Pengaturan. `EmptyPerangkat` follows `EmptyBeranda`'s shape with the `DemoSheet` and its `returnFocusTo` ref.
- [X] T025 [US1] Replace `applications/hematdaya-mobile/src/app/(tabs)/(perangkat)/perangkat.tsx` with `export default PerangkatScreen`, as `(saran)/saran.tsx` does.
- [X] T026 [US1] Run `npx jest tests/components.test.tsx tests/perangkat.test.tsx tests/navigation.test.tsx` until they pass. `follows the Android smoke flow` must pass unchanged.

**Checkpoint**: US1 stands alone. Rows do nothing useful yet beyond pushing a route that has no screen, so US2 follows before review.

---

## Phase 4: User Story 2 - Open one asset in context (Priority: P1) MVP

**Goal**: One tap from a list row or from Beranda opens S06 with the same period and values, and back returns to the same place.

**Independent Test**: Scroll, open, go back. From Beranda, count one tap to the asset.

### Tests first

- [X] T027 [US2] Add `describe('asset detail')` to `applications/hematdaya-mobile/tests/perangkat.test.tsx`. Pressing the Kulkas row shows heading "Kulkas", "Perangkat · Dapur · Pendingin makanan", "Periode aktif: 19–25 Oktober 2026 · Asia/Jakarta", the device scope label, `8,400 kWh`, "Kelengkapan data: 100% periode", "Demo · Data simulasi", and under "Sumber data": `Sumber demo (simulasi)`, `Simulasi`, `1 jam · resolusi 0,001 kWh`, "mulai 28 September 2026 00.00", "Sumber acuan"; `HDDataQuality` rows "Pengukuran terakhir" with "26 Oktober 2026 00.00 (data simulasi)" and "Asal data"; tab Perangkat stays selected. Requests are `/api/v1/assets/{id}/summary?preset=last_7_days` and `/api/v1/assets/{id}`, and none contains `/measurements`. No `/100,00%/`, no "Lihat riwayat", "Ubah detail", "Arsipkan", "Pilih sumber acuan". `/asset/{id}` opened by address renders the same detail.
- [X] T028 [US2] Add state tests to `applications/hematdaya-mobile/tests/perangkat.test.tsx`. Pompa Air in `h-learning-partial`: "Sebagian data belum tersedia · Kelengkapan data: 71,4% periode" and "Data 24–25 Oktober 2026 belum tersedia."; Kulkas: "Data 22 Oktober 2026 14.00–16.00 belum tersedia." `h-zero`: `0,000 kWh` and "Nol terukur dengan data lengkap · Kelengkapan data: 100% periode". `h-base` `today_asset`: "Belum ada energi pada periode ini", "Tidak ditampilkan sebagai 0 kWh", no `0,000 kWh`, "Demo · Data simulasi" still there, and **Lihat periode data** returns to `8,400 kWh`. A no-data response on the workspace's initial period shows no **Lihat periode data**. Kulkas in `h-scope`: "Lebih dari satu sumber untuk beban yang sama", both source values, the service's message, no `2,000 kWh`, no "Total gabungan belum dapat dihitung", both sources "Belum dipilih sebagai sumber acuan", "Demo · Data simulasi". Meter utama: "Cakupan pengukuran: 1 meter lokasi", `10,000 kWh`. Router in `h-stale-offline`: "Data belum diperbarui · Router", the service's body, `1,620 kWh` and the partial qualifier together; the only `/\bmati\b/` is inside "Ini bukan tanda perangkat mati." A one-asset summary with `allocated_estimate: true` shows Beranda's estimate sentence. A crafted asset with empty `bindings` and `sources` shows "Belum ada sumber untuk perangkat ini." and keeps "Demo · Data simulasi" through the fallback. Kulkas in `imported`: "Data impor", no "Demo · Data simulasi", `Impor CSV · Data historis`, `interval tidak diketahui · resolusi tidak diketahui`.
- [X] T029 [US2] Add return tests to `applications/hematdaya-mobile/tests/perangkat.test.tsx`. Type `2026-10-12` into "Tanggal mulai" on the list, press a row, press Kembali: heading "Perangkat", tab Perangkat selected, the input still holds the text, and the summary request count is unchanged, which proves the list stayed mounted. Press Hari ini on the list and open a row: the asset summary request carries `preset=today`, and the period line matches the list's. Press Hari ini on detail, then Kembali: the list shows "Periode aktif: 26 Oktober 2026" and `— kWh` rows.
- [X] T030 [US2] Add Beranda tests to `applications/hematdaya-mobile/tests/perangkat.test.tsx`. `h-base`: **Lihat perangkat terbesar** opens heading "Kulkas" in one press with the same "Periode aktif" line and tab Beranda selected, and Kembali shows heading "Beranda". The Pompa Air ranking row (`role="link"`) opens Pompa Air. `h-zero` and `h-scope` show no **Lihat perangkat terbesar**. For each `h-base` asset, the kWh text on the Beranda ranking, the list row and the detail is the same string, and the coverage in Beranda's data table, on the row and on detail is the same percentage (SC-001). `8,400 kWh · 57,14%` and the data table still show.
- [X] T031 [US2] Add failure tests to `applications/hematdaya-mobile/tests/perangkat.test.tsx`. 404 `NOT_FOUND` on either read: "Perangkat tidak ditemukan", the reference ID, no "Coba lagi". No workspace at `/asset/x`: the same, with no `/api/v1/assets` request. 401 `SESSION_EXPIRED` on the asset summary: "Perangkat tidak ditemukan", "Sesi demo sudah berakhir", no "Memuat perangkat…". A pending first read: "Memuat perangkat…" in a `status` region. A first read failure with `{ retryable: true, max_attempts: 1 }`: "Perangkat belum dapat dimuat", "Coba lagi", recovers on press. A non-retryable one with a fake secret in the envelope: message, reference, no "Coba lagi", no secret. Hari ini failing on detail: `8,400 kWh`, selector, "Data perangkat belum dapat diperbarui", the confirmed-data sentence. `/assets/{id}` failing alone: `8,400 kWh`, "Sumber data belum dapat dimuat", "Demo · Data simulasi" through the fallback. `/insights` failing: `8,400 kWh` and "Status pembaruan sumber belum dapat diperiksa."
- [X] T032 [P] [US2] Add `describe('HDContributionRanking')` to `applications/hematdaya-mobile/tests/components.test.tsx`: each item is one `role="link"` named `{name}, {kwh}, {share}` with `minHeight` at least 48, a press calls `onOpen` with `assetId`, two items with the same name and different IDs both render with no key warning, and a null share shows the existing no-percentage sentence.
- [X] T033 [P] [US2] Add `test_asset_summary_row_matches_the_site_summary_row` to `applications/hematdaya-api/tests/integration/test_summary.py`, with the Condition and Expected docstring from rule 003 and a parametrize over `h-base`, `h-scope` and `h-learning-partial`: at each scenario's initial period, every asset's row from `/assets/{id}/summary` equals its row from `/sites/{id}/summary`, leaving out `share_percent`. This passes on arrival, because it pins behaviour measured in Notes, and it is the API half of SC-001.
- [X] T034 [US2] Checkpoint: run `npx jest tests/components.test.tsx tests/perangkat.test.tsx`. Record in Notes in `specs/014-perangkat-s04-s06/tasks.md` that T027 to T032 fail for the stated reason, and that T033 passes against Postgres. Do not write code before this.

### Code

- [X] T035 [US2] Create `applications/hematdaya-mobile/src/features/assets/AssetDetailScreen.tsx` per the Detail states and D4 to D6, D11 to D13 and D21 to D23, with `{ assetId }: { assetId: string | undefined }`. Branch on `useWorkspace()`, then mount an inner `AssetDetail` keyed by site and asset ID, holding `useAssetSummary`, `useAsset`, `useInsights` and `useLastConfirmed`. Treat `ApiError.from(error).code === 'NOT_FOUND'` from either read as not available. Reading order: `HDScreen` with `onBack={back}`, title from the row or asset name, subtitle `meta`; `HDPeriodSelector`; stale `HDNotice` entries; conflict `HDNotice` or `HDEnergyMetric` with `issues={[]}` and the D21 action; the allocation note; `ReadFailure` for the summary, and the stale-check-failure line when `useInsights` failed; `HDDataQuality` with Kelengkapan data (when `completeness` is not null), Pengukuran terakhir (when `latest` is not null) and Asal data, worded as on Beranda for simulated data and using the origin label otherwise; Sumber data rows, "Belum ada sumber untuk perangkat ini." when `bindings` is empty, or `ReadFailure` for the asset. Leave a one-line comment where 015's Lihat riwayat goes, before Sumber data.
- [X] T036 [US2] Create `applications/hematdaya-mobile/src/app/(tabs)/(beranda,perangkat,saran)/asset/[id].tsx`: read `id` with `useLocalSearchParams<{ id: string }>()` and render `<AssetDetailScreen assetId={id} />`, as `saran/[id].tsx` does.
- [X] T037 [P] [US2] Add `assetId: asset.asset_id` to `ranking` items in `applications/hematdaya-mobile/src/features/energy/beranda-model.ts`, and to the `BerandaModel` type.
- [X] T038 [P] [US2] Change `applications/hematdaya-mobile/src/components/hd/HDContributionRanking.tsx`: `Item` gains `assetId`, the component gains required `onOpen: (assetId: string) => void`, each `listitem` is keyed by `assetId` and holds one `Pressable` with `role="link"`, `aria-label` of name, kWh and share when present, and `minHeight: tokens.size.targetMinimum`. Text and bar stay as they are.
- [X] T039 [US2] Wire `applications/hematdaya-mobile/src/app/(tabs)/(beranda)/beranda.tsx`: take `openAsset` from `useTabNavigation`, pass `onOpen={openAsset}` to `HDContributionRanking`, and above the ranking render `HDButton` variant `primary`, icon `chevronRight`, "Lihat perangkat terbesar" when `largest && largest.share !== null`.
- [X] T040 [US2] Run `npx jest tests/components.test.tsx tests/perangkat.test.tsx tests/demo-journey.test.tsx tests/saran.test.tsx tests/navigation.test.tsx` until they pass.

**Checkpoint**: Both stories work in Jest. Nothing has run in a real runtime yet.

---

## Phase 5: Polish

- [X] T041 [P] Write the flip tests. In `applications/hematdaya-mobile/tests/registry.test.ts`, `claims only what has shipped` expects `demo`, `ringkasan-energi`, `kontributor`, `daftar-perangkat`, `saran`, `bukti-saran`, in that order. In `applications/hematdaya-mobile/tests/navigation.test.tsx`, add `lists only what is still planned in settings`: no link "Daftar perangkat, segera hadir" and no link "Data demo, segera hadir", while "Riwayat perangkat, segera hadir" and "Jadwal pemakaian, segera hadir" stay.
- [X] T042 Checkpoint: run `npx jest tests/registry.test.ts tests/navigation.test.tsx`, and record in Notes in `specs/014-perangkat-s04-s06/tasks.md` that T041's assertions fail.
- [X] T043 Set `status: 'available'` on `daftar-perangkat` in `applications/hematdaya-mobile/src/features/registry.ts`. Change nothing else there.
- [X] T044 Filter `FEATURES` to `status === 'coming_soon'` in `applications/hematdaya-mobile/src/app/(tabs)/(beranda,perangkat,saran)/pengaturan.tsx`. `FeatureRow` and `HDComingSoon` stay as they are.
- [X] T045 Confirm `applications/hematdaya-mobile/e2e/smoke.yaml` and `applications/hematdaya-mobile/e2e/android-smoke.sh` have no diff against `$(git merge-base HEAD origin/main)` and that `follows the Android smoke flow` passes. If a later edit makes either untrue, restore the flow's strings rather than editing the flow.
- [X] T046 [P] Update `applications/hematdaya-mobile/README.md`: add `tests/perangkat.test.tsx` and `tests/asset-model.test.ts` to the test table, and `src/features/assets/` to "Where things live" (rule 002).
- [X] T047 Run guards from `applications/hematdaya-mobile/`, and expect no matches: `grep -rnE "allowFontScaling|numberOfLines|FlatList|Number\(|parseFloat|Animated|animated: true" src/features/assets src/components/hd/HDAssetRow.tsx`, and `grep -rn "HDHistoryChart\|/measurements" src/features/assets`. Run `git diff --exit-code "$(git merge-base HEAD origin/main)" -- ../../contracts src/api/schema.generated.ts`, which compares against the fork point because these files did change between `5ec2fba` and `6563a2f`, and may change again on `main` before T052. Record the output in Notes in `specs/014-perangkat-s04-s06/tasks.md`.
- [X] T048 Walk the web build against a live API, at 320 × 640. Start the API as in T002 with `CORS_ALLOWED_ORIGINS='["http://localhost:8099"]'`, and the app with `CI=1 EXPO_PUBLIC_API_URL=http://localhost:8001 npx expo start --web --port 8099`. Open scenarios the sheet does not offer by creating a session with curl and setting `sessionStorage['hematdaya.workspace.v1']` to `{ token, siteId, scenarioId, expiresAt, initialPeriod }`, then reloading. Check `h-base`, `i-base`, `h-scope`, `h-stale-offline`, `h-learning-partial`, `h-zero` and `empty`. For a long name, `PATCH /api/v1/assets/{id}` with "Pompa Air Area Produksi Belakang Gedung Selatan Lantai Dua A" and confirm it wraps whole with no horizontal scroll, then repeat at 160 px wide for the layout at 200% text. Record what was seen in Notes in `specs/014-perangkat-s04-s06/tasks.md`, as a web run only.
- [X] T049 In the same run, measure scroll (SC-002) and record the numbers in Notes in `specs/014-perangkat-s04-s06/tasks.md`. In the browser console, take the visible scroller: `[...document.querySelectorAll('div')].filter(e => e.offsetParent && /auto|scroll/.test(getComputedStyle(e).overflowY)).sort((a, b) => b.scrollHeight - a.scrollHeight)[0]`, set `scrollTop = 300` on Perangkat, press a row, press Kembali, and read `scrollTop`. Repeat with a tab round trip, and from Beranda through a ranking row. Name the browser. Firefox and Safari count only if actually run.
- [X] T050 Run `make check`, `make doctor` and `make export` in `applications/hematdaya-mobile/`, `uv run pytest tests/integration/test_summary.py` in `applications/hematdaya-api/` against the throwaway Postgres, and `python3 docs/roadmap/check_traceability.py`. Record each result in Notes in `specs/014-perangkat-s04-s06/tasks.md`. Remove the container afterwards.
- [X] T051 Update the **Status** line of `specs/014-perangkat-s04-s06/spec.md`, naming the runtimes actually exercised and saying Android beyond the smoke flow was not run, and tick finished tasks in `specs/014-perangkat-s04-s06/tasks.md`.
- [X] T052 Left for the parent session, not an implementing agent: run `git fetch origin` and merge or rebase `origin/main` into `m2/perangkat`. If 027 or 035 merged in the meantime, point that entry point in `applications/hematdaya-mobile/src/features/assets/PerangkatScreen.tsx` at the route they added, and extend the expected list in `applications/hematdaya-mobile/tests/registry.test.ts` with what they flipped. Re-run `make check`, then commit, push and open the PR with `pr-generate-description`. Name P1 as reviewer for the items under "For P1 review". Read the `hematdaya-android-smoke` job's result on the PR before calling any Android claim done. Only the parent session commits, and it records the PR number in `specs/014-perangkat-s04-s06/tasks.md`.

---

## Requirement coverage

| Requirement | Tasks |
|---|---|
| FR-001 recorded kWh and quality, or explicit unavailable | T005, T011, T017, T018, T021, T023, T024 |
| FR-002 shared period, scope as the service states it | T012, T021, T024, T029, T035 |
| FR-003 detail in the shared tab folder | T013, T027, T030, T036 |
| FR-004 Tambah sumber and Impor data stay reachable | T020, T024 |
| FR-005 period, scope and origin beside every number, simulated and imported kept apart | T002, T005, T010, T018, T021, T027, T028, T031, T035 |
| FR-006 no client sort, sum or computation, staleness from notices | T004, T005, T009, T011, T018, T021, T047 |
| FR-007 message, reference ID, retry only when allowed | T015, T019, T031 |
| FR-008 one link, targets, labels, font scale, safe areas, status region, no animation | T017, T019, T023, T031, T032, T047, T048 |
| FR-009 no S11 link until 029 | T018, T027, T028 |
| FR-010 Settings lists only `coming_soon` | T041, T044 |
| FR-011 no API or contract change, no dependency on 027 or 035 | T008, T024, T047, T052 |
| US1 scenario 1 | T018, T024, T025 |
| US1 scenario 2 | T018, T024 |
| US1 scenario 3 | T017, T018, T023 |
| US1 scenario 4 | T020, T024 |
| US2 scenario 1 | T027, T028, T035, T036 |
| US2 scenario 2 | T014, T029, T049 |
| US2 scenario 3 | T028, T035 |
| US2 scenario 4 | T030, T037, T038, T039 |
| US2 scenario 5 | T031, T035 |
| Edge: full names wrap | T017, T023, T048 |
| Edge: stale source | T005, T021, T028 |
| Edge: failure keeps a known list or detail | T012, T015, T019, T031 |
| Edge: two unresolved sources | T005, T018, T028 |
| Edge: a failed side read removes only that fact | T019, T031 |
| SC-001 values agree | T030, T033 |
| SC-002 scroll restored | T006, T014, T029, T049 (web). Android: not run, see Notes |
| SC-003 smoke job with the flow unchanged | T026, T045, T052 |
| UX-13 gap, unknown, zero, incomplete | T005, T018, T021, T028 |
| UX-14 same units, reduced motion | T030, T047 |
| UX-05 back keeps period and input | T029 |
| S04 | US1 |
| S06, the parts 014 owns | US2 |
| P03 one tap from Beranda | T030, T039 |
| Registry flip and its readers | T041, T043, T044 |
| Owner isolation on detail | T031, and `test_isolation.py` already covers both routes |
| Client contract | T003, T008, T047 |

T001, T002, the checkpoints (T007, T022, T034, T042), the run tasks (T016, T026, T040, T050), T046 and T051 serve the rows above without adding behaviour of their own.

## Dependencies & Execution Order

- **Setup (T001, T002) → Foundational (T003–T016) → US1 (T017–T026) → US2 (T027–T040) → Polish (T041–T052).**
- T008 before T011 and T012. T009 and T010 before T011. T015 needs nothing but `ApiError`.
- US2 needs US1's list for its tests and `openAsset` from T013. Both stories are P1, and neither ships alone, because a row must open something.
- T037 and T038 before T039. T010 and T037 both edit `beranda-model.ts`, in different phases.
- T048 and T049 need T044. T050 after everything that changes code. T052 last, in the parent session.

### Parallel example

T003, T004, T005 and T006 touch different test files and can run together. So can T009, T013, T014 and T015 after T008. T017 can run beside T018 and T023 beside T024. Tasks that share `tests/perangkat.test.tsx` run in order. T032, T033, T037 and T038 touch separate files. T041 and T046 can run any time after T040.

## Implementation Strategy

Both stories are P1 and the roadmap's round 5 asks for both, so the MVP for this spec is the whole spec. US1 is the first review point. US2 needs the closest reading where it touches P1's Beranda. Stop after each checkpoint and run the tests before moving on. Do not take 015's chart or 016's sheets in passing, even though `AssetDetailScreen` makes them look close.

## Notes

Record the baseline, failing-test checkpoints and the web walk here as tasks finish. `speckit-analyze` ran over this file on 2026-11-07, and `spec.md`, `plan.md` and this file were amended to match its findings. All three were then checked and updated against `6563a2f`, after PR #31 merged.

### Evidence behind the decisions (2026-11-07, no repository file changed)

Run first on merged code at `5ec2fba`, on a throwaway `postgres:17-alpine` container on port 55432 and a web build on port 8099, with scripts kept outside the repository and both removed afterwards. The browser was Chromium 152 at 320 × 640. It is a web run and proves nothing native. At `6563a2f` the API reads and the Jest probes were run again, with the results in the last rows below. The browser rows were not repeated, because the mobile app's runtime code did not change: the only source file changed is `schema.generated.ts`, which holds types.

| Check | Result | Decision |
|---|---|---|
| Each asset's row from `/assets/{id}/summary` against `/sites/{id}/summary`, across `h-base`, `h-scope`, `h-stale-offline`, `h-learning-partial`, `h-zero`, `empty` and `i-base` | Equal in every field except `share_percent` | D4, T033 |
| `/assets/{id}/summary` for Kulkas in `h-base` | `share_percent: "100.00"`, three other assets in `excluded` as `not_selected` | D4 |
| `/assets/{id}/summary` at `preset=today` in `h-base` | `energy_kwh: null`, `no_data`, `origins: []`, `latest_measurement_at: null` | D5, D21 |
| `/assets/{id}/summary` for Kulkas in `h-scope` | `energy_kwh: null`, `scope_conflict`, `origins: []`, `coverage.minimum: null`, two `conflict_sources` of `1.000` on 25 Oktober | D5, D6 |
| `/assets/{id}/summary` for Meter utama in `h-scope` | `10.000`, `issues: []`, so a meter alone is valid | D6 |
| `GET /assets/{unknown}`, and an asset read with another session's token | 404 `NOT_FOUND`, `retryable: false`, same message | D13 |
| Notices in `h-stale-offline` | One `stale` with `asset_id`: "Data belum diperbarui · Router", "Pembacaan terakhir 25 Oktober 2026 18.00 (interval 1 jam). Ini bukan tanda perangkat mati." Router's row is `1.620`, `0.964`, one gap | D3 |
| Notices in `h-learning-partial` | `partial` only for Pompa Air (`0.714`). Kulkas at `0.988` has none, because the notice threshold is `0.900` | Rows use `coverage`, not notices |
| `h-scope` order | Meter utama, TV, Pompa Air, Router, Kulkas: unavailable last | D2 |
| Browser, merged Beranda: `scrollTop = 1200`, Pengaturan, Kembali | `0`, same DOM node, `document.activeElement` is the heading | D9 |
| The same with `focus` patched to `preventScroll: true` at runtime | `1200`, and `1200` after a Saran tab round trip | D9 |
| Jest probe outside the repository: Beranda, Hari ini fails with `retryable: false` | Number gone, selector gone, no reference ID, "Coba lagi" offered | D11, D12 |
| Jest probe: typed range input, Pengaturan, Kembali | Input kept, summary requests 1 and 1 | D9, T029 |
| Jest probe: `Text.prototype.focus` on `Platform.OS = 'web'` | A Jest mock, called with no argument | T006 |
| Browser, Settings with a workspace open | All 17 rows labelled "segera hadir", including shipped ones | D18 |
| `grep` for `.status` readers in `src`, `tests`, `e2e` | Only `tests/registry.test.ts` reads a feature's status | D18 |
| PRD §18 | "one site with 20 sources" | D10 |
| `git diff 5ec2fba 6563a2f` under the mobile app | `schema.generated.ts` (zero removed lines, no asset, summary or notice type touched) and `e2e/android-smoke.sh` | D25 |
| `git diff 5ec2fba 6563a2f` for `app/energy/`, `app/insights/`, `contracts/golden/` | No change. `app/assets/`: only `add_binding`'s optional `effective_to` | D25 |
| API at `6563a2f`, head `0009`: rows, notices, asset fields and asset detail keys for the seven scenarios, against the run at `5ec2fba` | All the same, IDs aside, and every asset's row still equals its site row apart from `share_percent` | D25, T033 |
| Jest probes at `6563a2f` | Beranda and input results unchanged. `Text.prototype.focus` still called with no argument | D9, D11, D12, T006 |
| Import into an `empty` session at `6563a2f`, through the API with no client | Source is `Impor CSV · kulkas`, `origin: import`, `transport_status: historical`, `cadence_seconds: null`, `resolution_mwh: null`. Assets have null category and location. Summary at the initial period: `origins: ["import"]`, Kulkas `0.100` at coverage `0.011` | D22, T002 |
| `impor-data` in `registry.ts` and `csv` in the manifest at `6563a2f` | `coming_soon` and `available`. 014 reads neither value | D15, D25 |

### Baseline (T001)

`git merge-base --is-ancestor 6563a2f HEAD`: true, HEAD is `6563a2f`. `make check`, Node 24.8.0, Jest runtime: lint and typecheck clean, 10 suites, 102 tests passed, coverage 92.82% statements, 92.9% lines.

T002 recorded `tests/fixtures/assets.json` from real sessions on a throwaway `postgres:17-alpine`, head `0009`, API on port 8001, all eight entries, 3,957 lines. It holds no `token` and no `site_id`. The import committed 4 rows.

### Failing-test checkpoints (T007, T022, T034, T042)

All in Jest. Each ran before the code it covers.

| Checkpoint | Result | Why they failed |
|---|---|---|
| T007 | 20 failed, 38 passed, and `asset-model.test.ts` could not run | `getAssets`, `getAsset`, `getAssetSummary`, `formatCadence`, `formatResolution` and `formatAssetMeta` not defined. `Text.prototype.focus` called with 0 arguments. `@/features/assets/asset-model` not found. The 38 passes are existing tests in those files |
| T022 | `perangkat.test.tsx` 23 failed, 1 passed, and `components.test.tsx` could not run | No list, status text, "Coba demo" or row on the old screen. `HDAssetRow` not found |
| T034 | 36 failed, 39 passed of 75. Two of the 36 were a helper bug, described below | Detail route absent, no ranking link, no **Lihat perangkat terbesar**. The 39 passes are T017 to T021 and existing tests |
| T033 | 3 passed on arrival, against Postgres | It pins measured behaviour, as the task says |
| T042 | 2 failed, 20 passed | `claims only what has shipped` and `lists only what is still planned in settings` |

Passed from the start, so not proof of the code: `makes no request with no workspace` (the old screen also made none), and `names no largest asset` in `h-zero` and `h-scope` (the button did not exist yet; they failed at first only because of a helper bug, `findByText` matching two scope lines).

Tests changed after their code, each for a test reason:

- `getByRole('list')` and `getByRole('status')` cannot find a plain `View` with a role, because React Native Testing Library finds only accessibility elements, and `accessible` on a container would flatten it on native. So 21 US1 tests still failed with the code in place. They now use `getByLabelText` and assert `role`, as `demo-journey` and `saran` do, and a status text is checked by walking up to `role="status"`. To keep the evidence honest, the corrected US1 tests were run again with the old route file put back for that run: 23 failed and the same 1 passed, then the route was restored.
- T019 and T031 say `{ retryable: true, max_attempts: 1 }` means no query retry. That is not so: see "For P1 review". The tests add `retry_after_seconds: 0`, so the one retry takes no time.
- One assertion, `/kWh$/`, also matched `1 jam · resolusi 0,001 kWh`, and now matches values only.
- T030 also runs on `h-learning-partial`, because every coverage in `h-base` is 100% and would prove little alone.

`useLastConfirmed`'s state update during render passes `make lint`, so no `useEffect` (T016).

### Guards and final checks (T045, T047, T050)

| Check | Result |
|---|---|
| `e2e/smoke.yaml`, `e2e/android-smoke.sh` against `6563a2f` | No diff. `follows the Android smoke flow` passes unchanged |
| T047 first `grep`, `allowFontScaling` and the rest | No match |
| T047 second `grep`, `HDHistoryChart` and `/measurements` | No match |
| `git diff --exit-code` on `contracts` and `schema.generated.ts` | Exit 0 |
| Contract generated to a scratch file with the Makefile's pinned tool, compared with `schema.generated.ts` | Identical. `make generate-api` itself was not run, per D25 |
| `make check`, mobile, Jest | Lint and typecheck clean, 12 suites, 219 tests passed, 94.4% statements, 94.55% lines |
| `make doctor` | 20 of 20 |
| `make export` | Web, Android and iOS JavaScript bundles built. This proves bundling only |
| `uv run pytest tests/integration/test_summary.py`, throwaway Postgres | 18 passed |
| `make check`, API, throwaway Postgres | Lint clean, 1,030 passed, 8 skipped, 99.14% |
| `python3 docs/roadmap/check_traceability.py` | 123 requirements across 46 specs, exit 0 |

### Web walk (T048, T049)

**Web only: Chromium 152 at 320 × 640, against a live API at head `0009` and `expo start --web`. This proves nothing native. Firefox and Safari were not run.** The pane's size emulation also sends an Android user agent string, which does not make this an Android run. Presses in the scroll runs were `element.click()` from the console, because a pointer press could not be placed reliably in the scaled pane.

| Scenario | Seen on the list | Seen on detail |
|---|---|---|
| `h-base` | Kulkas, TV, Pompa Air, Router at `8,400`, `2,520`, `2,100`, `1,680 kWh` | Kulkas opens with the same period line |
| `i-base` | Oven, Kompresor, Mesin Press, Lampu Area, "Perangkat · Area produksi · Pemanas/memasak" | Oven `72,000 kWh`, `Sumber acuan` |
| `h-scope` | Meter utama first as "Meter lokasi · Teras · Meter rumah", Kulkas last at `— kWh` with two source lines, scope notice | Kulkas: no total, both sources "Belum dipilih sebagai sumber acuan". Meter utama: "1 meter lokasi" |
| `h-stale-offline` | Router `1,620 kWh`, "Kelengkapan data: 96,4% periode" and "Data belum diperbarui" together | The service's notice, partial qualifier, gap, "Simulasi · Simulasi koneksi". The only "mati" is the service's sentence |
| `h-learning-partial` | Kulkas 98,8%, Pompa Air 71,4%, in the service's order | Gaps "22 Oktober 2026 14.00–16.00" and "24–25 Oktober 2026" |
| `h-zero` | All `0,000 kWh`, "Nol terukur dengan data lengkap" | Same, with the zero qualifier |
| `empty` | "Belum ada perangkat", three actions, Pengaturan, no number or date | Not applicable |

Width 320: every scenario has `documentElement.scrollWidth` 320 and scroller 320 of 320, on the list and on each detail opened. The 60-character name, set with `PATCH`, wraps to 2 lines in a 153 px row, value below it, nothing clipped. No console errors on the first load of `h-base`.

Width 160, standing in for 200% text: the name wraps whole to 7 lines, the row stays inside the page (16 to 144), and the value drops below the name. The detail heading wraps to 8 lines. Document width is 160. **One failure outside 014's modules:** `HDPeriodSelector`'s "✓ 7 hari lengkap terakhir" runs to x = 202 and is cut off, because its preset cannot wrap and the scroller hides horizontal overflow (`scrollWidth` 221 of 160). Beranda does the same, and also its "Demo · Data simulasi" tag to x = 163. The tab bar's labels touch at this width too. Not changed here, and reported below.

Settings with a workspace open: 11 links, all still planned. No "Daftar perangkat" and no "Data demo".

**Scroll (SC-002), Chromium 152:**

| Path | Before | After |
|---|---|---|
| Perangkat, `scrollTop = 300`, Kulkas row, Kembali | 300 | 300, same DOM node, focus on the heading |
| Perangkat, 300, Saran tab, Perangkat tab | 300 | 300 |
| Beranda, 600, Pompa Air ranking row, Kembali | 600 | 600 |
| Beranda, 600, **Lihat perangkat terbesar**, Kembali | 600 | 600 |

Android: **not run**.

### What the Android job proves

`hematdaya-android-smoke` runs on PRs touching the mobile app, on an API 34 `pixel_6` emulator, with no API. On this PR it can prove that the debug APK still builds, that Metro bundles the route tree including `asset/[id]`, that the app starts, that the welcome flow fails honestly, and that the Perangkat tab renders its no-workspace state with "Belum ada perangkat". It cannot reach a workspace, so it proves nothing about the populated list, a row press, detail, hardware back, scroll on Android, font scale, TalkBack or measured touch targets. There is no local Android SDK. SC-002's Android half therefore stays **not run**. Jest shows the list stays mounted, and that is an inference about Android, not evidence from it.

Since `6563a2f`, `e2e/android-smoke.sh` sets `hide_error_dialogs` before the flow, so a slow emulator's system dialog no longer covers the app. A hang or crash in the app should still fail the flow, because Android then kills the app and the next step cannot find its text. The cause would show in the job's logcat and not as a dialog in a screenshot. 014 does not edit that script.

### For P1 review

- `src/components/hd/HDScreen.tsx`: `focus({ preventScroll: true })` on web. Every screen benefits. Beranda and Saran also return to their place.
- `src/features/energy/beranda-model.ts`: `shownOrigins` and ranking `assetId`.
- `src/components/hd/HDContributionRanking.tsx`: rows become links, required `onOpen`, keyed by ID.
- `src/app/(tabs)/(beranda)/beranda.tsx`: **Lihat perangkat terbesar**, ranking links, `shownOrigins`.
- `src/features/navigation.ts`: `openAsset`.
- `src/api/client.ts`: three reads and their guards.
- `src/app/(tabs)/(beranda,perangkat,saran)/pengaturan.tsx`: lists only `coming_soon`, so five shipped features leave "Rencana fitur" too.
- `applications/hematdaya-api/tests/integration/test_summary.py`: one new test, no API change.

Unchanged: `useSummary`, `useInsights`, `NavigationContextProvider`, `WorkspaceProvider`, `query-client.ts`, `schema.generated.ts`, `contracts/openapi.json`.

Found while implementing, reported and not changed:

- `src/api/query-client.ts`: `shouldRetry` exceeds the service's `max_attempts` by one. TanStack first asks with a count of 0 (`retryer.ts`), while the function's comment and `data-layer.test.tsx` assume the first failure counts as 1. Measured by a probe, since deleted: `max_attempts: 1` sends 2 requests and `max_attempts: 3` sends 4. Rule 008 item 8 and rule 009 say to stop at the limit. D12's reasoning still holds.
- `src/components/hd/HDPeriodSelector.tsx`: a preset cannot wrap, so "7 hari lengkap terakhir" is cut off at 160 px (Web walk). It affects every screen with the selector.
- `src/features/energy/beranda-model.ts`: `scopeLabel` counts everything as "perangkat", so `h-scope`'s list says "5 perangkat" with a site meter among the five. The list uses this label as it is.

Gaps in P1's merged code, reported and not changed: a failed period change on Beranda loses the number and the selector (D11); Beranda and Saran offer **Coba lagi** on non-retryable failures and show no reference ID (D12, rule 009); once 027 lets someone import into a seeded demo workspace, `shownOrigins` keeps "Demo · Data simulasi" on a no-data period and `HDProvenanceTag` names only simulated data when a period mixes both origins. An `empty` workspace is not affected, and detail lists each source's own origin.

### For later specs

- **015**: Lihat riwayat goes in `AssetDetailScreen.tsx`, marked by a comment. `HDHistoryChart` still draws with `View`, while architecture and 015's plan ask for `react-native-svg`.
- **016**: invalidate `['assets', siteId]`, `['asset', assetId]`, `['asset-summary', siteId, assetId, period]` and `['summary', siteId, period]`. The Diarsipkan list and an archived asset's detail are yours. `/segera-hadir/daftar-perangkat` by direct address still says "Segera hadir", with no in-app link left to it.
- **027 and 035**: replace `openFeature('impor-data')` and `openFeature('sumber-meter')` in `PerangkatScreen.tsx`. 027's plan names only S02's entry, so S04's is an extra edit. After an import, Lihat periode data can only offer `workspace.initialPeriod` (D21), which may not hold the imported dates, so 027's "land on the imported period" needs its own `setPeriod`.
- **029**: add the S11 action to the list's scope notice and to detail's conflict notice. The service's message already says "Pilih sumber acuan", with no link until then.
- **034**: `useLastConfirmed` lives in memory only. Persistence and the offline label are yours.
- **043**: `HDScreen` sends accessibility focus to the heading on every return, which may scroll under TalkBack, and keyboard focus returns to the heading rather than the opened row. Check both on a device.

### Conflicts in other documents (not edited here)

| Document | Says | Code or other source says |
|---|---|---|
| Task brief for this spec | `e2e/smoke.yaml` asserts "Belum ada perangkat" for the `empty` scenario | The flow has no API and no workspace, so it reaches the no-workspace state. 003's FR-004 says the same |
| `docs/roadmap/architecture.md` | Navigation context holds period, scope and site | `NavigationContextProvider` holds period and site. Scope arrives with 028 and 029 |
| `docs/reference/prototype/NATIVE-HANDOFF.md` | Restore list scroll with `FlatList` or a saved offset | D9 and D10. The prototype handoff is an oracle, not binding |
| `specs/013-beranda-s03/plan.md` | Lists `HDScopeSummary.tsx` | Not in the tree. 029's plan adds it, and the list uses `HDNotice` until then |
| `docs/roadmap/README.md` graph | 014 depends on 010 and 013 | 014 calls no 010 route, and 015 does. It also reads 021's notices, and `check_traceability.py` refuses a later number under **Depends on**, so the header cannot list 021 |
| `specs/015-history-chart/spec.md` **Covers** | No P03 | P03 ends at history, which 015 delivers. 014 proves only the one tap to the asset, so P03 has no complete home in `traceability.md` |
| `specs/014-perangkat-s04-s06/spec.md` **Covers** | No UX-05, though US2 cites it | Adding it would make `traceability.md` stale, and that file is outside this change. T029 tests it anyway. Add it with `check_traceability.py --write` in the PR if P1 agrees |
| `docs/product/PRD-EN.md` S06 and `docs/product/design-handoff-EN.md` S06 | Related insights, and a Saran row to S08 | No spec owns them. See Open questions |

## Open questions

1. **Android evidence for SC-002.** Default in place: record "not run" and ship. Widening the smoke job to reach a workspace needs an API or a fake one in CI, which is the owner's call with P1.
2. **`empty` scenario clock.** Still open with the owner. Default in place: 014 depends on no answer (D14).
3. **Related insights on S06.** The PRD lists them and the handoff adds a Saran row to S08, and no spec owns them: 014, 015 and 016 cover S06 without naming them, and 022 stops at S07 and S08. Default in place: not built in 014. The code is small once someone owns it, because `InsightResponse.asset_id` exists and `useInsights` is already mounted on detail.
