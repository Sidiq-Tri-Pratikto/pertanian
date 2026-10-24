HematDaya monitors recorded electricity and gives evidence-based advice for household, business and industrial sites. It never switches anything on or off. This system exists so every screen states **what was measured, for which assets, in which period, how complete it is, and what is still unknown** — in calm, plain Indonesian.

Release **1.0.0-draft** · review status: draft, not owner-approved · product contract: HematDaya PRD Generic 1.2 · runtime: private Claude Design System artifact, React 18.3.1 previews, namespace `window.HD`. Validation evidence is in *Validation report*; how a later app project binds to this system is in *Release, themes and consuming*.

## Product rules every screen keeps

- Exactly three primary destinations: **Beranda**, **Perangkat**, **Saran** (`HD.TabNavigation` cannot take a fourth). Settings, import, evidence, schedules and output metrics are secondary routes.
- Monitoring and advice only. No power-toggle symbol, switch, relay, remote, thermostat or "turn off" action. AC is one optional category, never a requirement.
- Tariff, schedule and output metrics are optional. Without them the core (energy, scope, completeness, contribution, change) is complete.
- Unknown is never zero: missing tariff = "Biaya belum dihitung — tarif belum diatur", not Rp0. No data = "Belum ada data energi", no 0 kWh. A gap is hatched, never drawn as 0.
- Measured zero is a valid value: `0,000 kWh` with complete coverage, and no percentages from a zero total.
- Physical scope and temporal completeness are different facts, shown separately. Main-meter and submeter values are never added (10 + 1 is never 11).
- No diagnoses, efficiency scores, waste verdicts, savings, carbon claims, streaks or guilt.

## Reading order

Period and measurement scope → recorded kWh → qualified optional cost → completeness and freshness → contribution → eligible observation. Qualifications sit next to the number they change; calculation detail goes in `HD.Disclosure` ("Detail perhitungan"). Compose screens in that order with `HD.EnergyMetric`, `HD.CostEstimate`, `HD.DataQuality`, `HD.ContributionRanking`, `HD.InsightSummary`.

## Content fundamentals

- Product copy is natural Indonesian, sentence case, addressed as *Anda* only when needed. Documentation and token/component names are English.
- Use the approved phrases exactly: "Energi yang dipantau", "Estimasi biaya energi terpantau", "Biaya belum dihitung — tarif belum diatur", "Cakupan pengukuran: 4 perangkat", "Kelengkapan data: 92% periode" (temporal, never "akurat"), "Sebagian data belum tersedia", "Data belum diperbarui" (never "perangkat mati"), "Belum cukup periode pembanding", "Belum dapat dibandingkan: <alasan>", "Penyebab perubahan belum diketahui", "Demo · Data simulasi", "Saran umum".
- Formatting comes from `HD.format`, never hand-typed: `14,700 kWh` (three decimals), `Rp22.050` (rounded once from the unrounded product), `57,14%`, `+1,400 kWh`, `19–25 Oktober 2026`, `07.00–17.00`, `Asia/Jakarta`.
- Errors name the field or row and the fix: "Baris data 4 (baris file 5) · kolom energi_kwh: "dua" bukan angka. Tulis angka, misalnya 0,250." Row numbers count data rows; file line = data row + 1.
- No MQTT, module names, trace codes, tenant terms or analysis thresholds in ordinary screens. Do not uppercase sentences. No emoji.

## Visual foundations

- **Colour.** Warm neutral canvas `color-background-canvas`, white grouped surfaces `color-background-surface`, ink text `color-text-primary`, supporting text `color-text-secondary`. One restrained green, `color-action-primary-background`, for the single primary action per step, selection (`color-selection-*`) and the current chart series. Green never says a device is efficient. Amber `color-status-attention-*` marks a condition worth attention (partial, stale, offline), not ordinary use. Red `color-status-error-*` is for rejected input and failed operations only, never a large contributor. Blue `color-focus-ring` is reserved for keyboard focus and info.
- **Components read aliases only.** Use semantic tokens (`color-*`, `space-page-gutter`, `radius-control`, `size-target-minimum`) or the six component aliases (`button-primary-*`, `field-border*`, `tab-selected-*`). Never use `palette-*` or raw hex in a component.
- **Borders.** `color-border-decorative` (1.52:1) only separates groups; every control boundary uses `color-border-control` (≥3.55:1 on every surface). Disabled controls keep a dashed control border and a readable label (`color-disabled-*`, 5.85:1) — no blanket opacity.
- **Type.** System sans (`--font-sans`), no font downloads, tabular numerals for values. Styles are classes: `type-title` 24/32, `type-section` 20/28, `type-metric` 34/40, `type-body` 16/24, `type-body-strong`, `type-label` 14/20, `type-label-strong`, `type-caption` 12/18 (nonessential metadata only — never scope, cost or gap limits). Sizes are rem so the user's text setting scales them. Long asset names wrap; never truncate the only identifier.
- **Space and shape.** Spacing steps 0–64 (`space-4` … `space-64`) behind semantic aliases: `space-page-gutter` 16 (24 from 768 px), `space-group-gap` 16, `space-section-gap` 32, `space-stack-tight` 8, `space-control-paddingX/Y` 16/12. Radii `radius-control` 8, `radius-surface` 12, `radius-sheet` 16, `radius-chip` for the provenance tag only.
- **Layout.** Flat. One reading column below 768 CSS px; from 768 an optional supporting column (`HD.Screen` `aside`) beside a main column up to `size-content-readingWidth`, total width up to `size-content-maxWidth`. No cards inside cards, no floating statistic cards, no hero areas, no gauges. Elevation (`shadow-overlay` over `color-overlay-backdrop`) is for `HD.SheetDialog` only.
- **Targets and focus.** Every control is at least `size-target-minimum` (48 CSS px / 48dp / 48pt). Focus is a 2 px white gap (`color-focus-gap`) then a 2 px blue ring (`color-focus-ring`), drawn by `--hd-ring`; it is separate from hover, selected and pressed. Selected states always add a non-colour cue: `size-border-selected` bar or border, semibold label, check icon.
- **Motion.** `duration-feedback` 120 ms for hover/press, `duration-overlay` 180 ms for sheet entry, `easing-standard`. Reduced motion removes all of it; the loading spinner stops and its text keeps saying work is in progress. No animated counters, blinking warnings, pulsing gauges or morphing charts.
- **Charts.** Sorted horizontal bars on a common zero baseline for contribution; daily bars for a week. Current = solid `color-chart-current`; reference = `color-chart-referenceFill` with a dashed `color-chart-reference` outline and legend text; gap = `color-chart-missingMarker` hatch with "Tidak ada data"; measured zero = a baseline tick. Every chart has a text summary and `HD.ChartDataAlternative` with the same values. No donuts for ranking, no smoothing, no 3D, no hover-only values.

## Iconography

A small own stroke set drawn for HematDaya (24-unit grid, 2-unit round stroke, `currentColor`), shipped inside the bundle as `HD.Icon` — no external icon library or licence. Names: home, devices, saran, chevronRight/Left/Down, close, info, attention, error, success, unknown, refresh, calendar, clock, offline, upload, scope, file. Artwork is `size-icon-default` 24 or `size-icon-small` 20 inside a 48 hit area. Icons always sit beside text except `HD.IconButton` with an Indonesian `label` ("Tutup", "Kembali"). There is no power symbol. The wordmark is the word "HematDaya" in system text; there is no logo asset in this release.

## Components

Primitives: `HD.Button`, `HD.IconButton`, `HD.TextField`, `HD.NumericField`, `HD.ChoiceGroup`, `HD.PeriodSelector`, `HD.TabNavigation`, `HD.SheetDialog`, `HD.Disclosure`, `HD.Notice`, `HD.ErrorSummary`, `HD.ProgressStatus`.
Domain: `HD.EnergyMetric`, `HD.CostEstimate`, `HD.ScopeSummary`, `HD.DataQuality`, `HD.AssetRow`, `HD.ContributionRanking`, `HD.HistoryChart`, `HD.ChartDataAlternative`, `HD.InsightSummary`, `HD.EvidencePanel`, `HD.ImportPreview`, `HD.ScheduleWindows`, `HD.OutputMetricPreview`.
Intentional additions: `HD.Screen` (the shared screen frame with wordmark, provenance tag, title, optional supporting column and the three-tab bar, so patterns are not unnamed copies) and `HD.Icon` (the icon set). Helpers: `HD.format`.

Pattern pages (examples, not exports): *PatternHouseholdBeranda*, *PatternEvidence*, *PatternCsvImport*, *PatternIndustrial*. They compose only the components above; their dashed "Kontrol uji" panels are test controls, not product UI.

## Using it in a page

Load, in order: the compiled tokens CSS, `components/bundle.css`, React 18.3.1 and ReactDOM (`components/lib/`), then `components/bundle.js`; render with `React.createElement(HD.EnergyMetric, {…})`. Put `lang="id"` on the document. Pass canonical numbers (`kwh: 14.7`, `tariff: 1500`, `null` for unknown) and let components format them. Provide the period and scope labels, the virtual or real "today" in Asia/Jakarta, and the save outcome (`saving` → `success` only after the server acknowledges). Each component's guidelines say what it needs and what it refuses to show.
