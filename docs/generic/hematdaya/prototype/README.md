# HematDaya — interactive prototype delivery

Recorded 24 October 2026 (Asia/Jakarta). Product contract: PRD Generic 1.2 + Claude Design handoff 1.2.1. Source release `hematdaya-proto-0.1.0`, calculation `hd-calc-1`, policy `hd-change-1`. Design system: HematDaya Design System 1.0.0-draft (draft, not owner-approved).

## 1. Runtime declaration

| Item | Actual |
|---|---|
| Claude Design runtime | Design canvas artifact (type "Design", contract 0.2.47), private: https://claude.ai/artifact/QZcyAN22MXHhjC3CBcQzf6 |
| Native execution | **Not available.** This is a responsive browser simulation. No Android/iOS build exists. |
| App framework | React 18 (supplied by the canvas; React 18.3.1 from the design system's `components/lib` in the standalone page), plain ES2017, no build step |
| Backend | **Backend simulasi**: an in-browser mock of the future server contract (`project/app/hematdaya-domain.js`, `api.*`). No account, server, storage, broker, push or network call. |
| Data | Deterministic simulated fixtures (origin `simulated`), user CSV imports (origin `import`), one optional simulated source. Synthetic tariff Rp1.500/kWh, not a PLN rate. |

## 2. What is where

| Path | Role |
|---|---|
| `project/canvas.json`, `project/Main.dc.html`, `project/Wide.dc.html` | Canvas index and two playable artboards (phone 390×844; fluid wide page). Both mount the same app. |
| `project/app/hematdaya-domain.js` | The single accepted-data authority: fixtures, virtual clock, calculations, CSV parser/preview/commit, schedules, metrics, insight rules, composition manifest, mock API. Runs in browser and Node. |
| `project/app/hematdaya-app.js` | S01–S12 screens composed from `window.HD` components. Holds navigation, drafts and operation status only; every number comes from the domain module. |
| `project/app/app.css` | App layout helpers (token-only). |
| `project/ds/hematdaya/` | Installed design-system copy (bundle.js/css and tokens.json copied server-side; `tokens.css` regenerated here, see binding record). `components/lib/` exists locally only for the standalone page. |
| `standalone.html` | Local test page loading the identical files; adds browser-history integration (`history: true`). |
| `tests/domain.test.js` | 36 fixture/boundary/recovery assertions; `node tests/domain.test.js --json tests/domain-results.json`. |
| `tests/browser-helper.js` | DOM driver used for the browser walkthroughs. |
| `design-system-binding.json` | Binding and deviation record. |
| `ACCEPTANCE.md` | Acceptance matrix with pass / fail / not run / blocked and evidence. |
| `NATIVE-HANDOFF.md` | Expo/React Native engineering handoff. |

Run locally:

```bash
python3 -m http.server 8811 --bind 127.0.0.1 --directory docs/generic/hematdaya/prototype
```

then open `http://127.0.0.1:8811/standalone.html`. In the canvas, open the link above and press Play on "HematDaya · ponsel 390 px".

## 3. Route, control and component map

Primary destinations: **Beranda**, **Perangkat**, **Saran** (`HD.Screen` → `HD.TabNavigation`, one stack per tab; detail routes push onto the current tab). Secondary routes: Pengaturan, Tentang demo, Impor data, Tambah sumber, Cakupan & sumber, Metrik, Saran tersembunyi.

| Screen | Route | Main HD components | Working actions → result |
|---|---|---|---|
| S01 Welcome | `welcome` | Screen, ChoiceGroup, Button, SheetDialog, ProgressStatus | Mulai / Lewati → empty local workspace (S02); Coba demo → sheet (Rumah tangga/Industri) → "Menyiapkan data demo…" → S03; context choice changes examples only |
| S02 Empty Beranda | `home` (no readings) | Screen, Button | Impor data → S10; Coba demo → sheet; Lihat meter yang didukung → S05 |
| S03 Beranda | `home` | PeriodSelector, ScopeSummary, EnergyMetric, CostEstimate, Disclosure, DataQuality, ContributionRanking, ChartDataAlternative, OutputMetricPreview, InsightSummary | Period presets/range/"Minggu ini"; Ubah cakupan → S11; Lihat perangkat terbesar → S06 (1 tap); Lihat dasar saran → S08 (1 tap); Lihat semua saran → S07; Perbarui (offline-aware); Atur tarif → S09; Lihat periode data |
| S04 Perangkat | `assets` | AssetRow, Notice, Button | Row → S06; Tambah sumber → S05; Impor data → S10; Pulihkan archived |
| S05 Source setup | `source` | Button, Notice, TextField, ChoiceGroup, ErrorSummary, ProgressStatus | Catalog → planned (Shelly/TP-Link: "Integrasi belum tersedia") or simulated: Lanjut → Simulasikan pembacaan pertama → Simpan sumber simulasi (idempotent op key) |
| S06 Asset detail | `asset` | EnergyMetric, CostEstimate, DataQuality, HistoryChart, ChartDataAlternative, InsightSummary, SheetDialog, TextField, ChoiceGroup | Lihat riwayat / Lihat data; Ubah detail (validated, draft kept); Arsipkan (reversible); Atur pola pemakaian (inherit/none/continuous/custom windows); Atur metrik keluaran → S12 |
| S07 Saran | `saran`, `hidden` | Notice, InsightSummary, Button | Data notices with actions; Lihat bukti → S08; Saran tersembunyi → list → Pulihkan; snoozed list with return time; Saran umum |
| S08 Evidence | `insight` | EvidencePanel, Disclosure, HistoryChart, ChartDataAlternative, ProgressStatus | Membantu / Kurang membantu (pending, failure, retry); Lihat data pembanding; Tunda hingga besok; Sembunyikan (returns with restore link) |
| S09 Settings | `settings`, `demo` | TextField, ChoiceGroup, NumericField, Notice, ErrorSummary, ProgressStatus, SheetDialog | Simpan perubahan (site, context preview, timezone confirmation, effective-dated tariff incl. explicit 0 and clear, schedule editor with overnight/24 jam/effective now or historical correction, notification preference); Tentang demo: scenarios, failure injection, offline, composition, reset |
| S10 Import | `import` | Notice, TextField, ChoiceGroup, ErrorSummary, ImportPreview, ProgressStatus | Periksa berkas → Lihat pratinjau → (ack) Impor N baris → Periksa status on unknown → Lihat periode data |
| S11 Scope | `scope` | ScopeSummary, ChoiceGroup, Notice, ProgressStatus | Source authority, parent/child view, disjoint confirmation, Konfirmasi cakupan (disabled with reason until valid) |
| S12 Metric | `metric` | TextField, ChoiceGroup, NumericField, OutputMetricPreview, ErrorSummary | Pratinjau metrik → Simpan metrik (only after valid preview); Nonaktifkan metrik |

Tokens are consumed by semantic name only (`--color-*`, `--space-*`, `--radius-*`, `--size-*`, `.type-*`); no palette or raw hex in app code.

## 4. Fixture and calculation authority

Generated, not hard-coded: hourly interval-start rows, 28 days × 24 h × 4 assets = 2.688 rows per fixture, integer Wh, 1 Wh resolution, valid zeros, Asia/Jakarta, virtual now 26 Oktober 2026 00.00 (current-period scenarios: 21 Oktober 2026 12.00). Energy is integer mWh, tariff integer milli-rupiah/kWh, cost BigInt nano-rupiah, rounded once for display. The 36 assertions (H/I totals, change variants, current period, parent/child, alternative source, power/counter, overnight and boundary schedules, coverage, CSV thresholds/limits/duplicates/conflicts/idempotency, tariff split, zero output, composition) are listed with results in `ACCEPTANCE.md`. Demo scenarios (Pengaturan → Tentang demo → Skenario demo): 13, readable names, no debug JSON.

## 5. Mock / service ledger

| Capability | Prototype | Future service boundary |
|---|---|---|
| Demo data | Simulated fixtures, isolated per workspace; reset rebuilds only the demo workspace | Same generator as server fixture tests |
| CSV import | Real parser in the browser; preview and atomic commit in memory with op key | `POST /imports/preview`, `POST /imports/{id}/commit`, `GET /imports/{id}` |
| Settings, scope, assets, feedback, metric | Mock calls with 500 ms latency, server-side style validation, injectable reject / interrupted / session-expired / offline | Owner-authorised API routes in PRD §16 |
| Capability composition | `full` vs `core` manifest; disabled capability rejected at the mock boundary even outside the UI | `GET /capabilities` + API/worker enforcement |
| Source enrollment | **Simulated only** ("Simulasi koneksi"); Shelly/TP-Link "Direncanakan" | Verified adapters, enrollment, first reading |
| Authentication, persistence, export, deletion, backup/restore, push, live meter | **Not implemented**; no screen pretends otherwise | Separate server work and evidence |

## 6. Known limitations (concrete)

- No native build; Android/iOS, TalkBack/VoiceOver, OS text scale and hardware back are not run.
- Design editor Play and Claude Design HTML/ZIP export were **not exercised**: the built-in browser in this session is not signed in to claude.ai. The tested HTML is `standalone.html` built from the identical files, not the Claude Design export.
- In the canvas the app uses visible Back only; browser-history integration is enabled only in `standalone.html` (sandboxed frames may block `pushState`).
- State lives in memory: closing the page loses imports; the import screen says a file must be reselected.
- Measurement export (FR-16), owner isolation (AT-41), restore (AT-50), audit display, retroactive tariff audit entries and live staleness from a real source are not implemented.
- One schedule definition per period is compared; holidays and shift rotations are out of scope (PRD).
- `HD.ScheduleWindows` is not used; schedule editing is composed.
- Thresholds (30%/3 MAD/5 r, 90% coverage, stale > 2 intervals) are proposed engineering defaults, not validated accuracy.
- No participant study, field test, savings or efficiency evidence exists.
