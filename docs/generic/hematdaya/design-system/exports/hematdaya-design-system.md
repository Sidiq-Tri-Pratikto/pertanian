# HematDaya Design System 1.0.0-draft

Single-file guide concatenated from the system's README, guide sections and component READMEs. Authority remains project/tokens.json and the component files.


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
- Errors name the field or row and the fix: "Baris data 4 · kolom energi_kwh: "dua" bukan angka. Tulis angka, misalnya 0,250." Data-row numbers exclude the header and blank lines. Include a separately labelled physical file line only when the parser supplies its actual position; never derive it by adding 1 to the data-row number, because blank lines and multiline quoted fields can change that position.
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


## Token registry

Generated by `tools/build.mjs` from `tokens.json` (sha256 `e3d38810b79576e3…`). Do not edit by hand: change `tokens.json`, then rebuild.

**Rules.** Components read semantic or component aliases, never primitives. ID `color.action.primary.background` is CSS `--color-action-primary-background` (dots become hyphens; camelCase segments are kept). Colour aliases are live (`{palette-forest-700}`); spacing, radius and duration aliases are recorded as `Alias: <token>.` in the usage note and checked for equality on every build. Type styles are classes (`.type-body`) sized in rem so the user's text-size setting scales them.

Build result: **0 integrity errors** — 130 tokens, every alias resolves, no cycles, no duplicate names, no raw colours in bundle.css/bundle.js, every `var(--…)` used exists.

## Semantic tokens

| ID | CSS | Type | Value | Resolved | Usage |
|---|---|---|---|---|---|
| `color.background.canvas` | `--color-background-canvas` | color | `{palette.neutral.canvas}` | `#f6f7f3` | Page background behind every screen. |
| `color.background.surface` | `--color-background-surface` | color | `{palette.neutral.white}` | `#ffffff` | Grouped content, inputs, sheets, navigation bar. |
| `color.background.subtle` | `--color-background-subtle` | color | `{palette.neutral.subtle}` | `#eceeea` | Hover on surface, disabled controls, neutral notices. Never a selected state on its own. |
| `color.text.primary` | `--color-text-primary` | color | `{palette.neutral.ink}` | `#17221d` | Body text, values and headings on canvas, surface, subtle and every status background. |
| `color.text.secondary` | `--color-text-secondary` | color | `{palette.neutral.secondary}` | `#4c5f55` | Labels, help and metadata on canvas, surface and subtle. Never for scope, cost or gap limitations that change a value's meaning. |
| `color.text.link` | `--color-text-link` | color | `{palette.forest.700}` | `#1f6947` | Underlined inline links on canvas and surface. |
| `color.border.decorative` | `--color-border-decorative` | color | `{palette.neutral.borderDecorative}` | `#cad4cc` | Dividers between groups and list rows. Decorative only. |
| `color.border.control` | `--color-border-control` | color | `{palette.neutral.borderControl}` | `#6e8175` | Input, choice and secondary-button boundaries on surface, canvas and subtle. |
| `color.action.primary.background` | `--color-action-primary-background` | color | `{palette.forest.700}` | `#1f6947` | Fill of the one primary action per task step. |
| `color.action.primary.hover` | `--color-action-primary-hover` | color | `{palette.forest.800}` | `#175237` | Primary fill on pointer hover. |
| `color.action.primary.pressed` | `--color-action-primary-pressed` | color | `{palette.forest.900}` | `#123f2b` | Primary fill while pressed. |
| `color.action.primary.foreground` | `--color-action-primary-foreground` | color | `{palette.neutral.white}` | `#ffffff` | Label and icon on primary, hover and pressed fills. |
| `color.action.secondary.background` | `--color-action-secondary-background` | color | `{palette.neutral.white}` | `#ffffff` | Secondary button fill. |
| `color.action.secondary.foreground` | `--color-action-secondary-foreground` | color | `{palette.forest.700}` | `#1f6947` | Secondary and text-button label on surface and canvas. |
| `color.action.secondary.hover` | `--color-action-secondary-hover` | color | `{palette.forest.100}` | `#e5f0e8` | Secondary and text-button fill on pointer hover. |
| `color.action.destructive.background` | `--color-action-destructive-background` | color | `{palette.red.700}` | `#a32929` | Destructive confirmation fill (removing a draft, deleting an import). Never an energy value. |
| `color.action.destructive.hover` | `--color-action-destructive-hover` | color | `{palette.red.800}` | `#821f1f` | Destructive fill on hover and press. |
| `color.action.destructive.foreground` | `--color-action-destructive-foreground` | color | `{palette.neutral.white}` | `#ffffff` | Label on destructive fills. |
| `color.selection.background` | `--color-selection-background` | color | `{palette.forest.100}` | `#e5f0e8` | Selected tab, chosen option row, active period. Always paired with a non-colour cue. |
| `color.selection.foreground` | `--color-selection-foreground` | color | `{palette.forest.700}` | `#1f6947` | Text and icon on color-selection-background. |
| `color.selection.indicator` | `--color-selection-indicator` | color | `{palette.forest.700}` | `#1f6947` | The 3px bar or thick border that marks selection beyond colour. |
| `color.focus.ring` | `--color-focus-ring` | color | `{palette.blue.700}` | `#145cc5` | Outer keyboard focus ring, drawn outside color-focus-gap. |
| `color.focus.gap` | `--color-focus-gap` | color | `{palette.neutral.white}` | `#ffffff` | The separation layer between a control and its focus ring. |
| `color.status.info.foreground` | `--color-status-info-foreground` | color | `{palette.blue.700}` | `#145cc5` | Informational icon and label on color-status-info-background or surface. |
| `color.status.info.background` | `--color-status-info-background` | color | `{palette.blue.50}` | `#edf3ff` | Informational notice surface. |
| `color.status.attention.foreground` | `--color-status-attention-foreground` | color | `{palette.amber.800}` | `#7a4b00` | Attention icon and label (partial data, stale source) on its background, surface or canvas. Not for ordinary continuous use. |
| `color.status.attention.background` | `--color-status-attention-background` | color | `{palette.amber.50}` | `#fff3d6` | Attention notice surface. |
| `color.status.error.foreground` | `--color-status-error-foreground` | color | `{palette.red.700}` | `#a32929` | Rejected input and failed operations: text, icon, field border. Never a large energy contributor. |
| `color.status.error.background` | `--color-status-error-background` | color | `{palette.red.50}` | `#fdedec` | Error notice and error summary surface. |
| `color.status.success.foreground` | `--color-status-success-foreground` | color | `{palette.forest.700}` | `#1f6947` | Confirmed save only, after acknowledgment. Never declares equipment efficient. |
| `color.status.success.background` | `--color-status-success-background` | color | `{palette.forest.100}` | `#e5f0e8` | Confirmed-save notice surface. |
| `color.status.neutral.background` | `--color-status-neutral-background` | color | `{palette.neutral.subtle}` | `#eceeea` | Neutral notice surface (learning, no eligible finding). |
| `color.disabled.foreground` | `--color-disabled-foreground` | color | `{palette.neutral.secondary}` | `#4c5f55` | Label of a disabled control on color-disabled-background; the reason text stays color-text-secondary. |
| `color.disabled.background` | `--color-disabled-background` | color | `{palette.neutral.subtle}` | `#eceeea` | Disabled control fill. No blanket opacity. |
| `color.chart.current` | `--color-chart-current` | color | `{palette.forest.700}` | `#1f6947` | Current-period bars, solid fill, on surface. |
| `color.chart.reference` | `--color-chart-reference` | color | `{palette.blue.reference}` | `#536b91` | Reference-period bar outline, dashed, on surface. |
| `color.chart.referenceFill` | `--color-chart-referenceFill` | color | `{palette.blue.50}` | `#edf3ff` | Reference-period bar interior behind its dashed outline. |
| `color.chart.missingMarker` | `--color-chart-missingMarker` | color | `{palette.neutral.secondary}` | `#4c5f55` | Diagonal hatch and label marking an unavailable period. A gap is never drawn as zero. |
| `color.chart.baseline` | `--color-chart-baseline` | color | `{palette.neutral.borderControl}` | `#6e8175` | Zero baseline and measured-zero tick. |
| `color.chart.gridline` | `--color-chart-gridline` | color | `{palette.neutral.borderDecorative}` | `#cad4cc` | Scale gridline; decorative, values are always printed. |
| `color.chart.track` | `--color-chart-track` | color | `{palette.neutral.subtle}` | `#eceeea` | Empty track behind a ranking bar; decorative. |
| `color.overlay.backdrop` | `--color-overlay-backdrop` | color | `rgba(23, 34, 29, 0.48)` | `rgba(23, 34, 29, 0.48)` | Scrim behind an open SheetDialog (ink at 48%). |
| `space.page.gutter` | `--space-page-gutter` | dimension | `16px` | `16px` | Alias: space-16. Side gutter below 768 CSS px. |
| `space.page.gutterWide` | `--space-page-gutterWide` | dimension | `24px` | `24px` | Alias: space-24. Side gutter from 768 CSS px. |
| `space.group.gap` | `--space-group-gap` | dimension | `16px` | `16px` | Alias: space-16. Between items inside one information group. |
| `space.section.gap` | `--space-section-gap` | dimension | `32px` | `32px` | Alias: space-32. Between information groups on a screen. |
| `space.stack.tight` | `--space-stack-tight` | dimension | `8px` | `8px` | Alias: space-8. Between a value and its qualifier. |
| `space.stack` | `--space-stack` | dimension | `12px` | `12px` | Alias: space-12. Between related lines in a group. |
| `space.inline.gap` | `--space-inline-gap` | dimension | `8px` | `8px` | Alias: space-8. Between icon and label, between buttons. |
| `space.control.paddingX` | `--space-control-paddingX` | dimension | `16px` | `16px` | Alias: space-16. Horizontal padding inside buttons and fields. |
| `space.control.paddingY` | `--space-control-paddingY` | dimension | `12px` | `12px` | Alias: space-12. Vertical padding inside buttons and fields. |
| `radius.control` | `--radius-control` | dimension | `8px` | `8px` | Alias: radius-8. Buttons, fields, option rows. |
| `radius.surface` | `--radius-surface` | dimension | `12px` | `12px` | Alias: radius-12. Information groups and notices. |
| `radius.sheet` | `--radius-sheet` | dimension | `16px` | `16px` | Alias: radius-16. Sheet top corners, dialog. |
| `radius.chip` | `--radius-chip` | dimension | `9999px` | `9999px` | Alias: radius-full. Provenance tag such as Demo · Data simulasi. |
| `size.target.minimum` | `--size-target-minimum` | dimension | `48px` | `48px` | Minimum hit area for every interactive control (48 CSS px web, 48dp Android, 48pt logical iOS). Product policy above WCAG 2.5.8. |
| `size.icon.default` | `--size-icon-default` | dimension | `24px` | `24px` | Icon artwork in navigation and icon buttons; its hit area stays 48. |
| `size.icon.small` | `--size-icon-small` | dimension | `20px` | `20px` | Icon artwork beside text in notices and quality rows. |
| `size.border.control` | `--size-border-control` | dimension | `1px` | `1px` | Control and group border width. |
| `size.border.selected` | `--size-border-selected` | dimension | `3px` | `3px` | Selection indicator bar and selected-option border, the non-colour selected cue. |
| `size.focus.ringWidth` | `--size-focus-ringWidth` | dimension | `2px` | `2px` | Width of color-focus-ring. |
| `size.focus.gapWidth` | `--size-focus-gapWidth` | dimension | `2px` | `2px` | Width of color-focus-gap between control and ring. |
| `size.stroke.chart` | `--size-stroke-chart` | dimension | `2px` | `2px` | Reference-bar dashed outline, missing-data hatch stroke, baseline. |
| `size.chart.plotHeight` | `--size-chart-plotHeight` | dimension | `160px` | `160px` | Plot height of HD.HistoryChart. |
| `size.chart.barThickness` | `--size-chart-barThickness` | dimension | `12px` | `12px` | Bar thickness in HD.ContributionRanking. |
| `size.content.maxWidth` | `--size-content-maxWidth` | dimension | `1200px` | `1200px` | Maximum comfortable content width. |
| `size.content.readingWidth` | `--size-content-readingWidth` | dimension | `720px` | `720px` | Main reading column maximum on wide layouts. |
| `size.sheet.maxWidth` | `--size-sheet-maxWidth` | dimension | `560px` | `560px` | SheetDialog width from 768 CSS px. |
| `size.breakpoint.wide` | `--size-breakpoint-wide` | dimension | `768px` | `768px` | Layout switch to the optional supporting column. CSS media queries cannot read custom properties, so bundle.css repeats 768px there; keep them equal. |
| `font.weight.regular` | `--font-weight-regular` | fontWeight | `400` | `400` | Body and labels. Web 400; Android Typeface normal; iOS .regular. |
| `font.weight.medium` | `--font-weight-medium` | fontWeight | `500` | `500` | Reserved mapping (Android medium, iOS .medium); unused in 1.0.0-draft. |
| `font.weight.semibold` | `--font-weight-semibold` | fontWeight | `600` | `600` | Headings, labels, button text. Web 600; Android medium/bold fallback; iOS .semibold. |
| `duration.progressCycle` | `--duration-progressCycle` | duration | `900ms` | `900ms` | Added in 1.0.0-draft. One rotation of the loading spinner; the spinner stops under reduced motion and its text still says work is in progress. |
| `duration.feedback` | `--duration-feedback` | duration | `120ms` | `120ms` | Alias: duration-120. Hover and press colour change. |
| `duration.overlay` | `--duration-overlay` | duration | `180ms` | `180ms` | Alias: duration-180. Sheet entry. |
| `easing.standard` | `--easing-standard` | cubicBezier | `cubic-bezier(0.2, 0, 0, 1)` | `cubic-bezier(0.2, 0, 0, 1)` | Ordinary ease-out for every transition. |
| `shadow.overlay` | `--shadow-overlay` | shadow | `0 8px 24px rgba(23, 34, 29, 0.18)` | `0 8px 24px rgba(23, 34, 29, 0.18)` | SheetDialog only, above color-overlay-backdrop. Default layout is flat: no card shadows. |
| `type.title` | `.type-title` | typography | `1.5rem / 2rem · 600` |  | Screen title (24/32). |
| `type.section` | `.type-section` | typography | `1.25rem / 1.75rem · 600` |  | Content group heading (20/28). |
| `type.metric` | `.type-metric` | typography | `2.125rem / 2.5rem · 600` |  | Primary energy value with its unit (34/40). Tabular numerals. |
| `type.body` | `.type-body` | typography | `1rem / 1.5rem · 400` |  | Main reading, input values, explanations (16/24). |
| `type.body.strong` | `.type-body-strong` | typography | `1rem / 1.5rem · 600` |  | Button labels, notice titles, emphasised values (16/24 semibold). |
| `type.label` | `.type-label` | typography | `0.875rem / 1.25rem · 400` |  | Supporting labels that remain legible (14/20). Quality and scope qualifiers may use it. |
| `type.label.strong` | `.type-label-strong` | typography | `0.875rem / 1.25rem · 600` |  | Field labels, tab labels, qualifier headings (14/20 semibold). |
| `type.caption` | `.type-caption` | typography | `0.75rem / 1.125rem · 400` |  | Nonessential metadata only (12/18). Never scope, cost or gap limitations. |

## Component tokens

| ID | CSS | Type | Value | Resolved | Usage |
|---|---|---|---|---|---|
| `button.primary.background` | `--button-primary-background` | color | `{color.action.primary.background}` | `#1f6947` | Component alias: HD.Button primary fill. |
| `button.primary.foreground` | `--button-primary-foreground` | color | `{color.action.primary.foreground}` | `#ffffff` | Component alias: HD.Button primary label. |
| `field.border` | `--field-border` | color | `{color.border.control}` | `#6e8175` | Component alias: HD.TextField, HD.NumericField and select boundary. |
| `field.border.error` | `--field-border-error` | color | `{color.status.error.foreground}` | `#a32929` | Component alias: field boundary when the field has an error message. |
| `tab.selected.background` | `--tab-selected-background` | color | `{color.selection.background}` | `#e5f0e8` | Component alias: HD.TabNavigation current destination fill. |
| `tab.selected.indicator` | `--tab-selected-indicator` | color | `{color.selection.indicator}` | `#1f6947` | Component alias: HD.TabNavigation current destination bar. |

## Primitive tokens

| ID | CSS | Type | Value | Resolved | Usage |
|---|---|---|---|---|---|
| `palette.neutral.canvas` | `--palette-neutral-canvas` | color | `#f6f7f3` | `#f6f7f3` | Primitive (seed). Warm neutral canvas. Consumed only through color-background-canvas. |
| `palette.neutral.white` | `--palette-neutral-white` | color | `#ffffff` | `#ffffff` | Primitive (seed). Surface, focus gap and text on dark fills. Consumed through color-background-surface, color-focus-gap, color-action-primary-foreground. |
| `palette.neutral.subtle` | `--palette-neutral-subtle` | color | `#eceeea` | `#eceeea` | Primitive (added in 1.0.0-draft). Quiet surface for hover, disabled controls, neutral notices and chart tracks. palette-neutral-secondary on it is 5.85:1, palette-neutral-borderControl on it is 3.55:1. |
| `palette.neutral.ink` | `--palette-neutral-ink` | color | `#17221d` | `#17221d` | Primitive (seed). Primary text. Consumed through color-text-primary. |
| `palette.neutral.secondary` | `--palette-neutral-secondary` | color | `#4c5f55` | `#4c5f55` | Primitive (seed). Supporting text that stays readable; also the missing-data hatch. 6.83:1 on white. |
| `palette.neutral.borderDecorative` | `--palette-neutral-borderDecorative` | color | `#cad4cc` | `#cad4cc` | Primitive (seed). Decorative grouping only: 1.52:1 on white, so never the only way to find a control. |
| `palette.neutral.borderControl` | `--palette-neutral-borderControl` | color | `#6e8175` | `#6e8175` | Primitive (seed). Essential control boundaries: 4.15:1 on white, 3.86:1 on canvas. |
| `palette.forest.700` | `--palette-forest-700` | color | `#1f6947` | `#1f6947` | Primitive (seed). Primary action, selected emphasis, current chart series. |
| `palette.forest.800` | `--palette-forest-800` | color | `#175237` | `#175237` | Primitive (seed). Primary hover where hover exists. |
| `palette.forest.900` | `--palette-forest-900` | color | `#123f2b` | `#123f2b` | Primitive (seed). Primary pressed. |
| `palette.forest.100` | `--palette-forest-100` | color | `#e5f0e8` | `#e5f0e8` | Primitive (seed). Selected and success supporting surface. |
| `palette.blue.700` | `--palette-blue-700` | color | `#145cc5` | `#145cc5` | Primitive (seed). Focus ring and informational text. |
| `palette.blue.50` | `--palette-blue-50` | color | `#edf3ff` | `#edf3ff` | Primitive (seed). Informational supporting surface; reference-bar fill. |
| `palette.blue.reference` | `--palette-blue-reference` | color | `#536b91` | `#536b91` | Primitive (seed). Historical/reference chart series, always with a dashed outline as the second distinction. |
| `palette.amber.800` | `--palette-amber-800` | color | `#7a4b00` | `#7a4b00` | Primitive (seed). Attention text and icons. |
| `palette.amber.50` | `--palette-amber-50` | color | `#fff3d6` | `#fff3d6` | Primitive (seed). Attention supporting surface. |
| `palette.red.700` | `--palette-red-700` | color | `#a32929` | `#a32929` | Primitive (seed). Error text and border; destructive action fill. |
| `palette.red.800` | `--palette-red-800` | color | `#821f1f` | `#821f1f` | Primitive (added in 1.0.0-draft). Destructive hover/pressed fill; white on it is 9.70:1. |
| `palette.red.50` | `--palette-red-50` | color | `#fdedec` | `#fdedec` | Primitive (seed). Error supporting surface. |
| `space.0` | `--space-0` | dimension | `0px` | `0px` | Primitive. No gap. |
| `space.4` | `--space-4` | dimension | `4px` | `4px` | Primitive. Icon-to-text nudge. |
| `space.8` | `--space-8` | dimension | `8px` | `8px` | Primitive. Tight stacks, inline gaps. |
| `space.12` | `--space-12` | dimension | `12px` | `12px` | Primitive. Control vertical padding, related lines. |
| `space.16` | `--space-16` | dimension | `16px` | `16px` | Primitive. Mobile gutter, group gap, control horizontal padding. |
| `space.20` | `--space-20` | dimension | `20px` | `20px` | Primitive. Notice padding. |
| `space.24` | `--space-24` | dimension | `24px` | `24px` | Primitive. Wide gutter, sheet padding. |
| `space.32` | `--space-32` | dimension | `32px` | `32px` | Primitive. Section gap. |
| `space.40` | `--space-40` | dimension | `40px` | `40px` | Primitive. Large section gap on wide layouts. |
| `space.48` | `--space-48` | dimension | `48px` | `48px` | Primitive. Equals the minimum target; empty-state padding. |
| `space.64` | `--space-64` | dimension | `64px` | `64px` | Primitive. Bottom clearance above a fixed bar. |
| `radius.0` | `--radius-0` | dimension | `0px` | `0px` | Primitive. Square: chart bars, table cells. |
| `radius.8` | `--radius-8` | dimension | `8px` | `8px` | Primitive. |
| `radius.12` | `--radius-12` | dimension | `12px` | `12px` | Primitive. |
| `radius.16` | `--radius-16` | dimension | `16px` | `16px` | Primitive. |
| `radius.full` | `--radius-full` | dimension | `9999px` | `9999px` | Primitive. Compact chips only. |
| `duration.0` | `--duration-0` | duration | `0ms` | `0ms` | Primitive. Instant; every transition under reduced motion. |
| `duration.120` | `--duration-120` | duration | `120ms` | `120ms` | Primitive. Control feedback (hover, press). |
| `duration.180` | `--duration-180` | duration | `180ms` | `180ms` | Primitive. Sheet entry, disclosure chevron. |
| `font.sans` | `--font-sans` | fontFamily | `system-ui, -apple-system, "Segoe UI", "Noto Sans", Roboto, "Helvetica Neue", Arial, sans-serif` | `system-ui, -apple-system, "Segoe UI", "Noto Sans", Roboto, "Helvetica Neue", Arial, sans-serif` | System sans-serif stack; no font files are fetched. |

## Computed contrast of resolved pairs

WCAG 2 relative-luminance ratios of the opaque resolved token values. These are token-level calculations: rendered checks (actual elements, states, focus geometry) are in the validation report.

| Foreground | Background | Ratio | Min | Role | Result |
|---|---|---:|---:|---|---|
| `color.text.primary` #17221d | `color.background.canvas` #f6f7f3 | 15.21:1 | 4.5:1 | Body text on canvas | pass |
| `color.text.primary` #17221d | `color.background.surface` #ffffff | 16.37:1 | 4.5:1 | Body text on surface | pass |
| `color.text.primary` #17221d | `color.background.subtle` #eceeea | 14.02:1 | 4.5:1 | Body text on subtle / neutral notice | pass |
| `color.text.primary` #17221d | `color.status.info.background` #edf3ff | 14.70:1 | 4.5:1 | Notice body on info | pass |
| `color.text.primary` #17221d | `color.status.attention.background` #fff3d6 | 14.84:1 | 4.5:1 | Notice body on attention | pass |
| `color.text.primary` #17221d | `color.status.error.background` #fdedec | 14.42:1 | 4.5:1 | Notice body on error | pass |
| `color.text.primary` #17221d | `color.status.success.background` #e5f0e8 | 14.00:1 | 4.5:1 | Notice body on success | pass |
| `color.text.secondary` #4c5f55 | `color.background.surface` #ffffff | 6.83:1 | 4.5:1 | Labels/help on surface | pass |
| `color.text.secondary` #4c5f55 | `color.background.canvas` #f6f7f3 | 6.35:1 | 4.5:1 | Labels/help on canvas | pass |
| `color.text.secondary` #4c5f55 | `color.background.subtle` #eceeea | 5.85:1 | 4.5:1 | Disabled reason / metadata on subtle | pass |
| `color.text.link` #1f6947 | `color.background.surface` #ffffff | 6.62:1 | 4.5:1 | Link on surface | pass |
| `color.text.link` #1f6947 | `color.background.canvas` #f6f7f3 | 6.16:1 | 4.5:1 | Link on canvas | pass |
| `color.action.primary.foreground` #ffffff | `color.action.primary.background` #1f6947 | 6.62:1 | 4.5:1 | Primary label | pass |
| `color.action.primary.foreground` #ffffff | `color.action.primary.hover` #175237 | 9.14:1 | 4.5:1 | Primary label, hover | pass |
| `color.action.primary.foreground` #ffffff | `color.action.primary.pressed` #123f2b | 11.85:1 | 4.5:1 | Primary label, pressed | pass |
| `color.action.secondary.foreground` #1f6947 | `color.action.secondary.background` #ffffff | 6.62:1 | 4.5:1 | Secondary label | pass |
| `color.action.secondary.foreground` #1f6947 | `color.action.secondary.hover` #e5f0e8 | 5.67:1 | 4.5:1 | Secondary label, hover | pass |
| `color.action.secondary.foreground` #1f6947 | `color.background.canvas` #f6f7f3 | 6.16:1 | 4.5:1 | Text button on canvas | pass |
| `color.action.destructive.foreground` #ffffff | `color.action.destructive.background` #a32929 | 7.23:1 | 4.5:1 | Destructive label | pass |
| `color.action.destructive.foreground` #ffffff | `color.action.destructive.hover` #821f1f | 9.70:1 | 4.5:1 | Destructive label, hover | pass |
| `color.selection.foreground` #1f6947 | `color.selection.background` #e5f0e8 | 5.67:1 | 4.5:1 | Selected tab/option text | pass |
| `color.disabled.foreground` #4c5f55 | `color.disabled.background` #eceeea | 5.85:1 | 4.5:1 | Disabled label (kept readable) | pass |
| `color.status.info.foreground` #145cc5 | `color.status.info.background` #edf3ff | 5.60:1 | 4.5:1 | Info label | pass |
| `color.status.info.foreground` #145cc5 | `color.background.surface` #ffffff | 6.24:1 | 4.5:1 | Info label on surface | pass |
| `color.status.attention.foreground` #7a4b00 | `color.status.attention.background` #fff3d6 | 6.72:1 | 4.5:1 | Attention label | pass |
| `color.status.attention.foreground` #7a4b00 | `color.background.surface` #ffffff | 7.41:1 | 4.5:1 | Attention qualifier on surface | pass |
| `color.status.attention.foreground` #7a4b00 | `color.background.canvas` #f6f7f3 | 6.89:1 | 4.5:1 | Attention qualifier on canvas | pass |
| `color.status.error.foreground` #a32929 | `color.status.error.background` #fdedec | 6.37:1 | 4.5:1 | Error label | pass |
| `color.status.error.foreground` #a32929 | `color.background.surface` #ffffff | 7.23:1 | 4.5:1 | Inline field error on surface | pass |
| `color.status.error.foreground` #a32929 | `color.background.canvas` #f6f7f3 | 6.71:1 | 4.5:1 | Inline field error on canvas | pass |
| `color.status.success.foreground` #1f6947 | `color.status.success.background` #e5f0e8 | 5.67:1 | 4.5:1 | Confirmed save label | pass |
| `color.border.control` #6e8175 | `color.background.surface` #ffffff | 4.15:1 | 3:1 | Control boundary on surface | pass |
| `color.border.control` #6e8175 | `color.background.canvas` #f6f7f3 | 3.86:1 | 3:1 | Control boundary on canvas | pass |
| `color.border.control` #6e8175 | `color.background.subtle` #eceeea | 3.55:1 | 3:1 | Disabled control boundary on subtle | pass |
| `field.border.error` #a32929 | `color.background.surface` #ffffff | 7.23:1 | 3:1 | Error field boundary | pass |
| `color.focus.ring` #145cc5 | `color.focus.gap` #ffffff | 6.24:1 | 3:1 | Focus ring against its gap | pass |
| `color.focus.ring` #145cc5 | `color.background.canvas` #f6f7f3 | 5.80:1 | 3:1 | Focus ring on canvas | pass |
| `color.focus.ring` #145cc5 | `color.background.surface` #ffffff | 6.24:1 | 3:1 | Focus ring on surface | pass |
| `color.focus.ring` #145cc5 | `color.background.subtle` #eceeea | 5.34:1 | 3:1 | Focus ring on subtle | pass |
| `color.focus.ring` #145cc5 | `color.selection.background` #e5f0e8 | 5.33:1 | 3:1 | Focus ring on selected row | pass |
| `color.focus.ring` #145cc5 | `color.status.info.background` #edf3ff | 5.60:1 | 3:1 | Focus ring inside info notice | pass |
| `color.focus.ring` #145cc5 | `color.status.attention.background` #fff3d6 | 5.66:1 | 3:1 | Focus ring inside attention notice | pass |
| `color.focus.ring` #145cc5 | `color.status.error.background` #fdedec | 5.50:1 | 3:1 | Focus ring inside error notice | pass |
| `color.action.primary.background` #1f6947 | `color.focus.gap` #ffffff | 6.62:1 | 3:1 | Primary fill edge against focus gap | pass |
| `color.selection.indicator` #1f6947 | `color.background.surface` #ffffff | 6.62:1 | 3:1 | Selected indicator bar | pass |
| `color.chart.current` #1f6947 | `color.background.surface` #ffffff | 6.62:1 | 3:1 | Current series bar | pass |
| `color.chart.reference` #536b91 | `color.background.surface` #ffffff | 5.41:1 | 3:1 | Reference series outline | pass |
| `color.chart.reference` #536b91 | `color.chart.referenceFill` #edf3ff | 4.86:1 | 3:1 | Reference outline on its fill | pass |
| `color.chart.missingMarker` #4c5f55 | `color.background.surface` #ffffff | 6.83:1 | 3:1 | Missing-data hatch | pass |
| `color.chart.baseline` #6e8175 | `color.background.surface` #ffffff | 4.15:1 | 3:1 | Zero baseline / measured-zero tick | pass |
| `color.status.attention.foreground` #7a4b00 | `color.status.attention.background` #fff3d6 | 6.72:1 | 3:1 | Attention icon | pass |
| `color.border.decorative` #cad4cc | `color.background.surface` #ffffff | 1.52:1 | 3:1 | Decorative border (expected to fail: decorative only) | fail (restricted to decorative use) |

Semantic tokens not referenced by bundle.css/bundle.js (kept for consumers): `color.action.primary.background`, `color.action.primary.foreground`, `size.breakpoint.wide`, `font.weight.medium`.


## Content, states and charts

## Domain-state grammar

These are independent dimensions. Combine them; never collapse them into one enum or one red panel.

| State | Presentation | Component |
|---|---|---|
| No data | "Belum ada data energi", import/demo next action; no 0 kWh, no empty chart | `HD.EnergyMetric` `quality: 'unavailable'` |
| Measured zero | `0,000 kWh` with complete coverage; no percentages from a zero total | `HD.EnergyMetric`, `HD.ContributionRanking` |
| Missing tariff | Energy stays; "Biaya belum dihitung — tarif belum diatur"; optional "Atur tarif" | `HD.CostEstimate` `tariff: null` |
| Learning | "Belum cukup periode pembanding"; measured totals still shown | `HD.InsightSummary` `kind: 'learning'` |
| No eligible finding | Honest no-finding text; not an efficiency or safety verdict | `HD.InsightSummary` `kind: 'none'` |
| Partial | Recorded amount qualified next to the number; gap times; data alternative | `HD.EnergyMetric` `partial`, `HD.HistoryChart` `null` points |
| Stale live source | Last measurement time + "Periksa sumber"; never "perangkat mati" | `HD.DataQuality` `freshness.state: 'stale'` |
| Historical import | Date range + "Lihat periode data"; not a failed live connection | `HD.DataQuality` `historical` |
| Client offline | Confirmed values with age; drafts retained; saves unconfirmed | `HD.DataQuality` `client: 'offline'` |
| Scope conflict | Individual values + explanation; choose a valid view before combining | `HD.ScopeSummary` `overlap` |
| Pending / unknown save | Inspectable status; no premature success; check before resending | `HD.ProgressStatus` |
| Unavailable capability | Reason + useful next action; no unqualified "Terhubung" | `disabledReason` on controls and options |

Combinations demonstrated: partial + no tariff (`CostEstimate` partial/missing and `EnergyMetric` partial), partial + stale (`DataQuality`), historical import + client offline (`DataQuality`), learning + measured totals (Household Beranda), measured zero + no percentages (`ContributionRanking`), parent/child 10/1 (Industrial).

## Copy rules

- One primary action per step; buttons start with a verb ("Simpan tarif", "Impor 8 baris", "Periksa status", "Coba lagi").
- Every disabled control says why, in a sentence the user can act on ("Isi tarif terlebih dahulu untuk menyimpan.").
- Field errors name the field and the fix; row errors name the data row and the column. Add a separately labelled physical file line only when its actual position is supplied by the parser; otherwise report the data row only.
- Draft and confirmed are visibly different: "Draf tersimpan di perangkat ini — belum dikirim" versus "Dikonfirmasi server 26 Oktober 2026 09.14".
- Technical detail (methods, policy versions) goes in "Detail perhitungan", never in the main reading path.

## Number and date display

| Value | Display | Source |
|---|---|---|
| 14.7 kWh | `14,700 kWh` | `HD.format.kwh` (three decimals, `id-ID`) |
| 0.05 kWh/unit | `0,050 kWh/unit` | three decimals |
| 22050 IDR | `Rp22.050` | `HD.format.rupiah` — rounds the unrounded product once |
| 8.4 / 14.7 | `57,14%` | `HD.format.percent` — `null` when the denominator is 0 |
| +1.4 kWh, +55.56% | `+1,400 kWh`, `+55,56%` | `signedKwh`, `signedPercent` (U+2212 for minus) |
| 2026-10-19 … 2026-10-25 | `19–25 Oktober 2026` | `HD.format.dateRange` |
| 07:00–17:00 | `07.00–17.00` | `HD.format.time` |

Machine exports and code keep canonical numbers (`14.7`, `1500`); only display is localised.

## Chart grammar

- **Contribution**: `HD.ContributionRanking` — sorted horizontal bars, common zero baseline, direct value + share labels, visible denominator ("Dari total 14,700 kWh perangkat terukur yang dipilih"). "Terbesar di antara perangkat terukur yang dipilih" — never "boros".
- **History**: `HD.HistoryChart` daily bars for a week; hourly with `dense` for a day. Current = solid green; reference = light fill + dashed outline + legend words; gaps = hatch + "Tidak ada data"; measured zero = baseline tick. The scale starts at 0 and keeps 20% headroom; exact values are in the table.
- **Every chart** has a text summary that resolves the same numbers and an `HD.ChartDataAlternative` with the same filter. No hover or drag is required to answer any task.
- **Never**: donuts for ranking, smoothing, interpolation, 3D, animated morphs, a percent when the reference is 0, a gap drawn as 0, an inferred full-day total.


## Pattern assemblies

Four bounded compositions validate meaning and reuse; they are not the S01–S12 application. Each is a preview page (`components/Pattern*/preview.html`) that uses only `HD.*` components and tokens. The dashed "Kontrol uji — bukan bagian UI produk" panel at the top of each page switches fixture states for reviewers and is not product UI. All data is synthetic and the screens carry "Demo · Data simulasi".

## 1. Household Beranda — `PatternHouseholdBeranda`

Mobile populated overview in the prescribed reading order: `HD.PeriodSelector` → `HD.EnergyMetric` (period, scope, 14,700 kWh) → `HD.CostEstimate` → `HD.DataQuality` → `HD.ContributionRanking` → `HD.InsightSummary` (learning), framed by `HD.Screen` with the three-tab bar. No schedule, no output metric, no AC. Test control switches the synthetic tariff (Rp22.050) and the no-tariff variant ("Biaya belum dihitung — tarif belum diatur"). Choosing "Hari ini" or another range shows "Belum ada data energi", not 0 kWh, because the demo data covers 19–25 Oktober 2026 only. From 768 px the scope list moves to the supporting column.

## 2. Evidence and incomplete data — `PatternEvidence`

Saran screen with three sections: (a) TV change, `HD.InsightSummary` + `HD.HistoryChart` (current vs reference, dashed outline) + `HD.ChartDataAlternative` + `HD.EvidencePanel` with harmless feedback whose send can fail then succeed on retry, stay unknown until checked, or succeed; (b) zero baseline: "Pompa Air naik 2,100 kWh", "Persentase tidak tersedia karena pembanding 0 kWh"; (c) partial/gap: Kulkas 12 of 24 hours, hatched gap, hourly table, `HD.DataQuality` partial + stale.

## 3. CSV preview and recovery — `PatternCsvImport`

`HD.ImportPreview` with 10 data rows. 2 invalid: confirming without the acknowledgment raises `HD.ErrorSummary`, which takes focus and links to the checkbox; after acknowledging, "Impor 8 baris" saves. 3 invalid: blocked with a notice and a disabled-with-reason confirm. Save outcomes: failure → "Coba lagi" (draft and acknowledgment retained) → success; unknown → "Periksa status" → the first import is found, with "Baris tidak diimpor dua kali"; success only after the simulated server confirmation. Buttons ignore repeated clicks while saving.

## 4. Industrial reuse — `PatternIndustrial`

Perangkat screen for Pabrik Cikarang using the same components: `HD.EnergyMetric` 144,000 kWh, `HD.CostEstimate` Rp216.000, `HD.ContributionRanking` (Oven 50%), `HD.AssetRow` list including the long name "Pompa Air Area Produksi Belakang" without data, and `HD.ScopeSummary` parent/child: Meteran Utama 10,000 kWh or Kulkas 1,000 kWh, never 11. The test control turns the optional capabilities off (the supporting column disappears and the core stays complete) or on: `HD.OutputMetricPreview` 144 ÷ 2.880 = 0,050 kWh/unit, 0 unit (no intensity), not filled; `HD.ScheduleWindows` with an overnight window.

## Fixture register

| Value | Origin |
|---|---|
| Household week 19–25 Oktober 2026: Kulkas 8.400, Router 1.680, Pompa Air 2.100, TV 2.520 = 14.700 kWh; Rp1,500/kWh = Rp22,050; virtual now 26 Oct 00.00 | Handoff §12 |
| TV 3.920 vs 2.520 kWh (+1.400, +55.56%); site 16.100 kWh, Rp24,150 | Handoff §12 (separate change scenario; current 19–25, reference 12–18 Oktober assigned here) |
| Industrial: Oven 72, Kompresor 36, Mesin Press 24, Lampu Area 12 = 144 kWh, Rp216,000; output 2,880 units = 0.050 kWh/unit | Handoff §12 |
| Main meter 10 kWh includes refrigerator 1 kWh | Handoff §12 |
| Import: 10 rows, 2 invalid accepted with acknowledgment, 3 invalid blocked | Handoff §12 |
| 24 hourly intervals, 12 valid (50%) | Handoff §12 |
| Daily TV split 0.560 / 0.360 kWh; hourly Kulkas 0.050 kWh at 00–06 and 18–24 on 25 Oct (0.600 kWh); Pompa Air reference 0 kWh; Pompa Air Cadangan 0 kWh; Panel Produksi 6 kWh; Sirkuit Dapur 10.5 kWh; Pompa Air Area Produksi Belakang 3.6 kWh / no data; import row messages; timestamps such as 09.14 and 17.58 | Derived for this design system only, labelled in each preview; not canonical fixtures |


## Responsive and native mapping

## Web layout

- Mobile first. One reading column below 768 CSS px (`size-breakpoint-wide`; CSS repeats 768px in media queries because they cannot read custom properties). From 768 px, `HD.Screen` `aside` becomes a supporting column beside a main column up to `size-content-readingWidth` (720 px), centred within `size-content-maxWidth` (1200 px). Reading order in the DOM is main first, then aside, then navigation.
- Gutters `space-page-gutter` 16 px, `space-page-gutterWide` 24 px from 768 px.
- 320 CSS px is a separate reflow check from 360/390/430 phones; 768, 1280 and 1440 are inspected too. Tables become stacked label/value rows below 768 px (`hd-table--stack`) instead of forcing page scroll.
- Text sizes are rem, so a larger default font or a 200% root size scales every style; containers wrap instead of shrinking.
- `HD.TabNavigation` stays sticky at the bottom at every width; it adds `env(safe-area-inset-bottom)`. `HD.SheetDialog` is a bottom sheet below 768 px and a 560 px centred dialog above, with safe-area padding in its footer.

## Native mapping (documentation only — no native code in this release)

| HD component | Android (Compose / Views) | iOS (SwiftUI / UIKit) | React Native |
|---|---|---|---|
| `HD.Button` | `Button`/`OutlinedButton`/`TextButton`; `enabled=false` + visible reason text, or keep enabled and explain on press | `Button` with `.borderedProminent` / `.bordered` / `.plain`; `.disabled` + reason `Text` | `Pressable` `accessibilityRole="button"`, `accessibilityState={{disabled, busy}}` |
| `HD.IconButton` | `IconButton` with `contentDescription` | `Button { Image }` + `.accessibilityLabel` | `Pressable` + `accessibilityLabel`, `hitSlop` to 48 |
| `HD.TextField` / `HD.NumericField` | `OutlinedTextField` with `supportingText`, `isError`; `KeyboardType.Decimal` | `TextField` + `.keyboardType(.decimalPad)`; error `Text` | `TextInput` `keyboardType="decimal-pad"`; parse with `HD.format.parseDecimal` logic |
| `HD.ChoiceGroup` | `RadioButton`/`Checkbox` rows with `Modifier.selectable`/`toggleable`, `Role.RadioButton` | `Picker(.inline)` / `Toggle` styled as checkbox rows | `accessibilityRole="radio"`/`"checkbox"` rows |
| `HD.PeriodSelector` | `FilterChip` group + `DateRangePicker` | segmented `Picker` + `DatePicker` | chips + platform date picker |
| `HD.TabNavigation` | `NavigationBar` with three `NavigationBarItem`s | `TabView` with three tabs | bottom tab navigator, three routes |
| `HD.SheetDialog` | `ModalBottomSheet`; back gesture = `onDismissRequest` | `.sheet` with `presentationDetents`; swipe/Escape = dismiss | `Modal`/bottom sheet with `onRequestClose`, focus to title |
| `HD.Disclosure` | `AnimatedVisibility` header row, `Role.Button`, expanded state description | `DisclosureGroup` | `Pressable` + `accessibilityState={{expanded}}` |
| `HD.Notice` / `HD.ProgressStatus` | inline surfaces; status changes via `LiveRegionMode.Polite` | inline views; `UIAccessibility.post(.announcement)` for status | `accessibilityLiveRegion="polite"` (Android) / `AccessibilityInfo.announceForAccessibility` |
| `HD.ErrorSummary` | list of clickable rows that `requestFocus()` their field | list of buttons using `@AccessibilityFocusState` | list of `Pressable`s calling `ref.focus()` |
| Charts | Canvas/Compose drawing + `semantics { contentDescription }`; data table screen | Swift Charts with `accessibilityChartDescriptor` or custom; table | `react-native-svg` + summary text + table |

Tokens map one to one: `color-*` to theme colours, `space-*`/`radius-*`/`size-*` px to dp (Android) and pt (iOS), type styles rem × 16 to sp/pt with font scaling on. Keyboard avoidance, visible back behaviour, safe areas, dynamic type/font scale and TalkBack/VoiceOver names must be checked separately on devices. CSS viewport resizing does not prove any native behaviour. None of these mappings has been implemented or tested in this release.


## Validation report

Release 1.0.0-draft, checks run 24 October 2026 (Asia/Jakarta). Results are `pass`, `fail`, `not run` or `blocked`. Every preview uses synthetic data ("Demo · Data simulasi"); that is provenance, not a check result. A token calculation, a rendered browser check, a code export and a participant session are different evidence and none stands in for another.

## Test surfaces and runtime

| Surface | What it is | Used for |
|---|---|---|
| A. Token build | `node tools/build.mjs` (Node 25.2.1) over `tokens.json`, `bundle.css`, `bundle.js` | Integrity, alias resolution, computed contrast of resolved pairs, raw-value scan |
| B. Local workbench | `workbench/index.html` (iframe per preview, width/text/motion test controls, audit script) and `workbench/frame.html?<Preview>` (one preview at the real viewport), served by `python3 -m http.server` from the same `project/` files | Rendered contrast, targets, overflow, keyboard, focus, status, recovery |
| C. Browser | Claude desktop built-in browser: Chrome 152.0.7977.167 engine (Claude/3.1623.1), Linux x86_64, DPR 1, viewport emulation 320–1440 CSS px, no assistive technology | Runs B |
| D. Artifact preview frames | The design-system page's live preview iframes on claude.ai | See DS-11; keyboard was not tested there |

## Gates

| ID | Gate | Result | Evidence |
|---|---|---|---|
| DS-01 | Product meaning | pass | `HD.TabNavigation` hard-codes Beranda/Perangkat/Saran (no fourth item possible). No power, switch or remote control exists in the bundle or icon set. Household Beranda renders full core with no tariff, schedule or output; industrial pattern hides optional metrics and keeps the core. Approved copy is used verbatim (README, *Content, states and charts*). |
| DS-02 | Token integrity | pass | Surface A: 0 integrity errors; every colour alias resolves, no cycles, no duplicate names, `Alias:` spacing/radius/duration values equal their targets, no raw colours in bundle.css/bundle.js, every `var(--…)` used is defined (local `--hd-ring` is composed from tokens). Export `exports/hematdaya-design-system.tokens.json` parses as JSON. Known literal exceptions are listed at the top of bundle.css (768px media query, visually-hidden clip, 90vh, rem grid minimums). |
| DS-03 | Colour and type | pass (rendered, light theme) | Surface A: 51 of 52 resolved pairs meet their minimum (*Token registry*); the decorative border (1.52:1) fails as expected and is used only between groups. Surface B/C rendered audit: computed text colour against the nearest opaque background for every visible text node in all 32 previews at 320 px and at 390 px with 200% text — 0 failures across 64 runs and 1,738 text elements (final run after the last code change). Focus ring measured on a focused button: `rgb(255,255,255) 0 0 0 2px, rgb(20,92,197) 0 0 0 4px` (blue ring 6.24:1 on its white gap, ≥5.33:1 on every surface). Hatched gaps and chart overlays (gradients) are excluded from the automatic text audit; their strokes are covered by the token pairs. |
| DS-04 | Primitive behaviour | pass | Each primitive preview shows its states. Keyboard (real key events, surface C): Tab reaches "Atur tarif" with visible ring; Enter opens `HD.SheetDialog`, focus lands on the title; Tab moves to Tutup then the field; typing works; Escape closes and focus returns to "Atur tarif"; reopening keeps the draft ("Draf belum disimpan"); Tab ×5 reaches Simpan, Enter saves (Rp1.500/kWh) and focus returns to the opener. `HD.ErrorSummary`: submit by keyboard moves focus to the summary; following the second link focuses `f-tariff` with `aria-invalid=true` and the error in `aria-describedby`. Disabled-with-reason buttons keep focus and announce the reason via `aria-describedby`. Loading ignores repeated clicks. |
| DS-05 | Domain states | pass | Previews and patterns render no data (no number), measured zero, missing tariff, explicit zero tariff, learning, no eligible finding, partial, stale, historical import, offline, parent/child and unknown overlap, unknown save; combinations listed in *Content, states and charts*. |
| DS-06 | Chart access | pass (web) | Values are printed (ranking labels, per-day values, tables). Current vs reference differ by fill vs dashed outline plus legend text; gaps hatched with "Tidak ada data" and a text gap note; zero-reference shows no percent. Each chart has a summary and an `HD.ChartDataAlternative` with the same rows; tables stack at < 768 px. Screen-reader reading of the chart was not run (see below). |
| DS-07 | Recovery | pass | PatternCsvImport scripted run (surface C): confirm without acknowledgment → ErrorSummary focused, link focuses `ack-input`; acknowledge → summary removed; save → busy, repeated clicks ignored; first attempt failure → "Gagal menyimpan", acknowledgment retained, no import button → "Coba lagi" → busy → "8 baris diimpor · Dikonfirmasi server", one success status. Unknown outcome → "Periksa status" → success plus "Baris tidak diimpor dua kali". 3/10 → blocked notice, confirm `aria-disabled` with reason, click does nothing. |
| DS-08 | Layout and access | pass with limits | Rendered audit at 320 px and 390 px + 200% root text: no horizontal page overflow and no interactive target under 48 × 48 CSS px in any of 32 previews (inline text links excluded). 768 and 1280 px inspected (industrial supporting column). Reduced motion (workbench class, same rules as the media query): spinner `animation: none`, transitions `0s`; normal mode spinner 0.9 s, transitions 0.12 s. Limits: native radio/checkbox glyphs stay 20 px at 200% text (their whole row is the target); browser zoom, OS text-size settings, forced-colours mode and real `prefers-reduced-motion` were not exercised separately; screen readers not run. |
| DS-09 | Composition reuse | pass | Household and industrial patterns use the same `HD.*` components and `tokens.json`; the industrial optional metrics disappear when disabled; ScopeSummary shows 10 or 1, never 11. |
| DS-10 | Theme boundaries | pass (documentation) | Allowed override slots and forbidden changes are in *Release, themes and consuming*. Only the light theme exists; no theme builder. |
| DS-11 | Export fidelity | pass with limits | Inspected: token JSON export, manifest JSON, single-file guide (`exports/hematdaya-design-system.md`, local), bundle/CSS/types, previews (all render with no console errors on surface B). Interactions were verified on surface B, not inside the claude.ai preview frames (surface D). No React Native, Expo, APK or IPA output exists. |
| DS-12 | Consuming-project binding | pass (local import) | `consuming-sample/index.html` loads the published file set and renders `HD.Screen`, `HD.EnergyMetric`, `HD.CostEstimate` (no tariff); its binding line reads "HematDaya Design System 1.0.0-draft (imported local reference); bundle reports 1.0.0-draft — cocok." Computed styles show system tokens applied (metric 34px ink, current tab `rgb(229,240,232)`). This is an imported reference, not automatic inheritance from a registered system; no publication or default was set. |

## Not run or blocked

| Check | Status | Why |
|---|---|---|
| Screen readers (NVDA, VoiceOver, TalkBack) | not run | No assistive technology in this environment. Names, roles and states were checked in the DOM only. |
| Native Android/iOS: font scaling, safe areas, keyboard avoidance, back behaviour | not run | No native implementation exists; mappings are documentation. |
| Participant comprehension (can a reviewer explain scope and unknowns) | not run | Requires a study; no participant result is claimed. |
| Rendering and keyboard inside the claude.ai preview frames (surface D) | blocked | The built-in browser showed "Sign in to view this page" for the private artifact; no sign-in was attempted. Publish itself succeeded (version id 1792845643-b5b4) and an agent read of `exports/hematdaya-design-system.manifest.json` returned fingerprints matching the local `bundle.js` and `tokens.json`. The owner should open the link and check that the previews render. |
| Page-generated `tokens.css` | not yet present | The Design System page writes `project/tokens.css` only when someone saves on the page; a read of that path returned "no file is published". Consumers can regenerate it from `tokens.json` (`tools/build.mjs` writes the same layout). |
| Forced colours / high contrast mode | not run | Rules exist in bundle.css; not exercised. |
| Dark theme | not applicable | Deferred by the handoff. |
| Registration in Claude Design's design-system picker | not verified | This is a private artifact created from the Design System type; selection in a later Claude Design project must be confirmed there. |

## Known issues

- `::backdrop` reads `--color-overlay-backdrop`; older browsers that do not inherit custom properties into `::backdrop` show no scrim (the dialog still works).
- Native checkbox/radio glyph size does not scale with text; acceptable because the label row is the target, but native apps should use scalable controls.
- Demo daily and hourly splits are uniform derived values; the application stage must use canonical fixtures.


## Release, themes and consuming

## Release record

| Field | Value |
|---|---|
| System | HematDaya Design System |
| Version | 1.0.0-draft (separate from PRD 1.2, app release and analysis-policy versions) |
| Review status | Draft — created and locally validated; not owner-approved |
| Form | Private Claude artifact made from the Design System type (contract 0.2.47) |
| Token schema | `tokens.json` (Design System type list grammar) → export `hematdaya-tokens/1` (custom, documented in *Token registry*; not a W3C DTCG file) |
| Components | `components/bundle.js` (`window.HD`, hand-written ES2017 on React 18.3.1, no build step), `bundle.css`, `index.d.ts` |
| Manifest | `exports/hematdaya-design-system.manifest.json` — identity, version, component IDs, sha256 fingerprints, scope, limitations; no secrets |
| Status ladder | created ✔ · exported ✔ · validated (web, light theme) ✔ · registered in Claude Design picker: not verified · selected in a consuming Claude project: not yet · published/shared: no · organisation default: no |

#### Change log

- **1.0.0-draft** — first release. Seed palette kept unchanged (all seed pairs recomputed and passing). Added `palette-neutral-subtle` (#eceeea) for hover, disabled and neutral surfaces, `palette-red-800` (#821f1f) for destructive hover, and `duration-progressCycle` (900 ms) for the spinner. Type sizes expressed in rem (16 logical units = 1rem) so text resizing works.

#### Compatibility

A patch (1.0.x) may fix implementation without changing token names or component props. Renaming or removing a token, a prop, a state meaning or a copy pattern needs a minor/major version and a migration note. Changing this system never updates earlier Claude projects automatically: each consuming project records the version it used and is updated deliberately.

## Themes

Only the light theme exists. A future client theme may override: brand-facing aliases (`color-action-primary-*`, `color-selection-*`, `color-chart-current`), the wordmark text/asset, and approved copy wording. It must re-run contrast for every pair in *Token registry*, keep focus, target and type sizes, and keep these unchanged: state meanings (missing ≠ zero, gap ≠ zero, attention ≠ error), component contracts, scope and quality explanations, the three destinations, units and all calculations. A theme cannot grant data access or hide an unavailable capability. Dark mode, extra brands and a theme builder are deferred until a real request.

## Consuming this system in the HematDaya application stage

1. **Supply.** In the Claude project for the application prototype, select or attach this design system: the private artifact `https://claude.ai/artifact/UKpTDTYqPNVwfCuHLjY3ns` ("HematDaya Design System"). If Claude Design lists it in its design-system picker, select it there; if not, attach the link (or the exported files) and say "Use HematDaya Design System 1.0.0-draft". Do not publish it or make it an organisation default to do this.
2. **Read.** The consuming agent reads `project/README.md` first, then the guide sections and the `components/<Name>/README.md` of each component it uses. Files to load in a web prototype: compiled tokens CSS (the page's `tokens.css`, or regenerate from `tokens.json`), `components/bundle.css`, `components/lib/react*.js`, `components/bundle.js`.
3. **Request by name.** Ask for screens composed from `HD.Screen`, `HD.TabNavigation`, `HD.PeriodSelector`, `HD.EnergyMetric`, `HD.CostEstimate`, `HD.DataQuality`, `HD.ScopeSummary`, `HD.ContributionRanking`, `HD.HistoryChart` + `HD.ChartDataAlternative`, `HD.InsightSummary`, `HD.EvidencePanel`, `HD.AssetRow`, `HD.ImportPreview` + `HD.ErrorSummary` + `HD.ProgressStatus`, and optional `HD.ScheduleWindows`, `HD.OutputMetricPreview`; tokens by semantic name (`color-status-attention-foreground`, `space-section-gap`, `size-target-minimum`).
4. **Record the binding** in the application project:

```json
{
  "designSystem": { "name": "HematDaya Design System", "version": "1.0.0-draft", "artifact": "https://claude.ai/artifact/UKpTDTYqPNVwfCuHLjY3ns", "reviewStatus": "draft" },
  "supply": "selected Claude artifact | imported reference | code sync | local draft",
  "tokenExport": "hematdaya-tokens/1",
  "componentsUsed": ["HD.EnergyMetric", "..."],
  "localDeviations": [{ "what": "", "why": "", "reviewImpact": "" }],
  "checksRunInConsumer": ["contrast", "200% text", "320 px reflow", "keyboard", "states"],
  "missingBindingOrUnsupportedImport": []
}
```

5. **Re-check in the consumer.** Contrast, 200% text, 320 px reflow, keyboard and the state matrix must be re-run on the consuming screens; this report does not transfer. A local copy is an imported reference, never "inheritance from a registered system".
6. **Update.** When a new system version is released, update the binding record, re-run the consumer checks and note any migration.

The local reference sample (`consuming-sample/` beside this system's source folder) shows the import route working for version 1.0.0-draft; see DS-12.

## Source folder (outside the artifact)

The authoring source lives in the HematDaya docs repository at `docs/generic/hematdaya/design-system/`: `project/` (exactly the files published here), `tools/build.mjs` (validation and generated outputs), `workbench/` (runnable test surface), `consuming-sample/`, `exports/` (the three handoff-named files: `hematdaya-design-system.tokens.json`, `.manifest.json`, `.md`). Rebuild with `node tools/build.mjs`; run the workbench with `python3 -m http.server 8787 --directory docs/generic/hematdaya/design-system` and open `/workbench/`.


## Component contracts


### HD.Button

One action, labelled with a verb in Indonesian; at most one primary per task step.

**Anatomy.** Container (48 min height) · optional icon or spinner · label · reason line when disabled.

**Consumer provides.** `children` label, `variant` primary | secondary | text | destructive, `onClick`, optional `type`, `icon`, `loading` + `loadingLabel`, `disabledReason`, `fullWidth`.

**Variants and states.** Default, hover, pressed, focus (ring), loading (spinner + "Menyimpan…", clicks ignored, `aria-busy`), disabled-with-reason (dashed border, readable label, reason shown under it and linked with `aria-describedby`).

**Keyboard and screen reader.** Native `<button>`; Enter/Space. Disabled uses `aria-disabled` so it stays focusable and the reason is read. Loading never announces success — pair with `HD.ProgressStatus`.

**Tokens.** `button-primary-*`, `color-action-*`, `color-disabled-*`, `space-control-padding*`, `radius-control`, `size-target-minimum`, `duration-feedback`.

**Responsive.** Labels wrap; `fullWidth` in narrow sheets and footers.

**Example.** Primary "Simpan tarif"; text "Atur tarif"; destructive "Buang draf".

**Limits.** No power/on/off actions. Destructive is for discarding drafts or imports, never for energy values. Do not blanket-dim disabled buttons.


### HD.IconButton

Icon-only (or icon + label) action with an Indonesian accessible name and a 48 × 48 hit area.

**Anatomy.** 48 hit area · 24 icon · optional visible label · reason line.

**Consumer provides.** `icon`, `label` (required, e.g. "Tutup"), `showLabel` for unfamiliar icons, `tooltip` (supplementary), `onClick`, `disabledReason`.

**Variants and states.** Default, hover, focus, disabled-with-reason.

**Keyboard and screen reader.** `aria-label` = `label` when the label is hidden. Tooltip is never the only name.

**Tokens.** `size-target-minimum`, `size-icon-default`, `color-text-primary`, `color-background-subtle`.

**Responsive.** Same at every width.

**Example.** Close a sheet: `icon: 'close', label: 'Tutup'`; back: `chevronLeft` + "Kembali".

**Limits.** No ambiguous unlabeled actions; no power symbol.


### HD.TextField

Labelled single- or multi-line text input with help, error, required/optional and draft states.

**Anatomy.** Label + (wajib)/(opsional)/(hanya baca) marker · help · error (above input) · input · note (draft or disabled reason).

**Consumer provides.** `label`, `value`, `onChange(value)`, optional `help`, `error`, `required` | `optional`, `readOnly`, `disabledReason`, `draftNote`, `multiline`, `type`, `id`.

**Variants and states.** Empty, filled, focus, error (2 px red border + message), read-only (dashed, focusable, copyable), disabled-with-reason (read-only + `aria-disabled` + visible reason), long value, retained draft note.

**Keyboard and screen reader.** Label is a real `<label for>`; help, error and note are joined in `aria-describedby`; `aria-invalid` on error.

**Tokens.** `field-border`, `field-border-error`, `color-text-*`, `color-disabled-*`, `space-control-padding*`, `radius-control`.

**Responsive.** Full width of its column.

**Example.** "Nama perangkat" (wajib) with "Pompa Air Area Produksi Belakang".

**Limits.** Do not put errors only in placeholder text or colour.


### HD.NumericField

Decimal-comma number input with unit, explicit empty-versus-zero meaning and no silent conversion.

**Anatomy.** Label · help · error · input + unit suffix · interpretation note.

**Consumer provides.** `label`, `value` (raw text), `onChange(text, parsed)`, `unit`, `allowNegative`, `max`, `required` | `optional`, `showErrors`, `error`, `note`.

**Variants and states.** Empty ("Kosong — belum diisi, tidak dianggap 0."), zero ("Tercatat 0 sebagai nilai yang diisi."), valid (`1.500` = 1500, `0,25`), invalid (`1.5` asks for a comma), negative rejected unless allowed.

**Keyboard and screen reader.** `inputmode=decimal`; unit is in `aria-describedby`; parse errors show after blur or when `showErrors`.

**Tokens.** Same as TextField plus `color-background-subtle` for the unit.

**Responsive.** Unit stays attached to the input at every width.

**Example.** "Tarif listrik" in Rp/kWh; "Output produksi" in unit.

**Limits.** Never turn empty into 0; never guess a dot decimal. Use `HD.format.parseDecimal` for the canonical value.


### HD.ChoiceGroup

Radio, checkbox or native select for ordinary settings, with selection shown beyond colour.

**Anatomy.** Fieldset + legend · help · error · option rows (input, label, description, disabled reason).

**Consumer provides.** `type` radio | checkbox | select, `legend`, `options[{value,label,description,disabledReason}]`, `value`, `onChange`, `inline`, `optional`, `error`.

**Variants and states.** Unselected, selected (green fill + 3 px border + semibold + native mark), focus (ring around row), disabled-with-reason (dashed, reason text), error.

**Keyboard and screen reader.** Native inputs: arrows move within radios, Space toggles checkboxes. Disabled options use `disabled` and expose their reason via `aria-describedby`.

**Tokens.** `color-selection-*`, `color-border-control`, `size-border-selected`, `size-target-minimum`.

**Responsive.** Options stack; `inline` wraps.

**Example.** "Konteks penggunaan": Rumah tangga / Usaha / Industri (changes examples, not permissions).

**Limits.** Not a toggle for operating appliances.


### HD.PeriodSelector

Choose today, the last 7 complete local days or an explicit range; presets commit when chosen, a range commits on "Terapkan".

**Anatomy.** Group label · preset buttons (pressed state + check) · two date fields + Terapkan · error · "Periode aktif" line with timezone and pending note.

**Consumer provides.** `value` {preset,start,end} (committed), `onCommit`, `today` (local ISO date in Asia/Jakarta, virtual now in demos), optional `label`, `timezone`.

**Variants and states.** Preset selected, range draft pending ("Pilihan tanggal belum diterapkan"), invalid range, committed.

**Keyboard and screen reader.** Presets are buttons with `aria-pressed`; the active period line is a polite live region.

**Tokens.** `color-selection-*`, `size-border-selected`, `space-*`.

**Responsive.** Presets wrap; range fields stack below 20 rem.

**Example.** today 2026-10-26 → "7 hari lengkap terakhir" = 19–25 Oktober 2026.

**Limits.** Never label a completed week "Minggu ini" on Monday. The app computes data for the committed period only.


### HD.TabNavigation

The three persistent destinations Beranda, Perangkat and Saran — fixed, labelled, current page marked.

**Anatomy.** Bar · three items (icon + label) · current indicator bar + fill + semibold.

**Consumer provides.** `current`, `onNavigate` or `hrefs`.

**Variants and states.** Default, hover, focus, current.

**Keyboard and screen reader.** `<nav aria-label="Navigasi utama">` with links; current has `aria-current="page"`.

**Tokens.** `tab-selected-*`, `color-text-secondary`, `size-border-selected`, `size-target-minimum`.

**Responsive.** Sticky at the bottom inside `HD.Screen` at every width; bottom padding adds `env(safe-area-inset-bottom)`; labels stay visible.

**Example.** `current: 'beranda'`.

**Limits.** Cannot add a fourth destination; no badges that imply urgency.


### HD.SheetDialog

Non-destructive modal sheet (bottom sheet on phones, centred dialog from 768 px) with focus placement, containment and return.

**Anatomy.** Backdrop · sheet · header (title, Tutup) · body · footer actions.

**Consumer provides.** `open`, `title`, `onClose(reason)`, `children`, `footer`.

**Variants and states.** Closed, open, draft present, error inside.

**Keyboard and screen reader.** Native `<dialog>` `showModal()`: background inert, Tab contained, Escape → `onClose('escape')`. Focus goes to the title (or `[data-autofocus]`) and returns to the opener on close.

**Tokens.** `shadow-overlay`, `color-overlay-backdrop`, `radius-sheet`, `size-sheet-maxWidth`, `duration-overlay`.

**Responsive.** Full width at the bottom below 768 px; 560 px centred above; footer respects safe area.

**Example.** "Atur tarif": Escape/Tutup/Batal close without saving, the typed draft stays until Simpan or Buang draf.

**Limits.** Not for destructive confirmation copy without a clear cancel. `::backdrop` reads the token only in browsers where it inherits custom properties.


### HD.Disclosure

Expandable detail for calculation metadata; current limitations stay outside it.

**Anatomy.** Summary row (chevron + label) · body.

**Consumer provides.** `summary`, `children`, `defaultOpen`.

**Variants and states.** Collapsed, expanded, focus.

**Keyboard and screen reader.** Native `<details>/<summary>`; Enter/Space toggles; expanded state is native.

**Tokens.** `color-action-secondary-foreground`, `color-border-decorative`, `duration-overlay`.

**Responsive.** Full width.

**Example.** "Detail perhitungan" with interval counts.

**Limits.** Never hide partial, scope or cost limitations inside.


### HD.Notice

Persistent explanation with a tone word, icon and optional action — not a colour-only toast.

**Anatomy.** Icon · title (hidden tone word prefix) · body · action.

**Consumer provides.** `tone` info | attention | error | success | neutral, `title`, `children`, `action`, `live`.

**Variants and states.** Each tone; success only after confirmation.

**Keyboard and screen reader.** Hidden prefix ("Perhatian:", "Kesalahan:") so meaning is not colour-only. `live` adds `role=status` (or `alert` for error) when it appears in response to an action.

**Tokens.** `color-status-*`, `radius-surface`, `space-16`.

**Responsive.** Full width.

**Example.** Attention "Sebagian data belum tersedia" with "Lihat jam tanpa data".

**Limits.** No stacking several notices for one cause; no success before acknowledgment.


### HD.ErrorSummary

After submit, lists every error as a link to its field or row and takes focus.

**Anatomy.** Heading "Periksa N isian berikut" · row-number convention · links.

**Consumer provides.** `errors[{targetId,text}]`, `submitCount` (increment per submit), `convention`, `title`.

**Variants and states.** Hidden when empty; visible and focused after each submit.

**Keyboard and screen reader.** `role=alert`, focus moves to the summary; each link focuses its target (making rows focusable when needed) and scrolls it into view.

**Tokens.** `color-status-error-*`, `size-focus-ringWidth`, `size-target-minimum`.

**Responsive.** Full width at the top of the form.

**Example.** "Centang konfirmasi bahwa 2 baris tidak valid tidak akan diimpor" → checkbox.

**Limits.** Inline messages must use the same wording as the summary.


### HD.ProgressStatus

Inspectable state of loading or saving, including unknown result, with retry or check — never premature success.

**Anatomy.** Spinner or icon · label · detail · action.

**Consumer provides.** `state` null | loading | saving | unknown | success | failure, `label`, `detail`, `onRetry`, `onCheck`, `checking`.

**Variants and states.** Loading, saving, unknown ("Status penyimpanan belum diketahui" + Periksa status), success (after server confirmation), failure ("Gagal menyimpan" + Coba lagi).

**Keyboard and screen reader.** Always-mounted `role=status` polite region; never moves focus.

**Tokens.** `color-status-*`, `duration-progressCycle`.

**Responsive.** Full width.

**Example.** Unknown → check finds the first save → success, not saved twice.

**Limits.** Do not resend automatically after an unknown result.


### HD.EnergyMetric

Recorded kWh for a period and physical scope, with provenance and the quality qualifier next to the number.

**Anatomy.** Label "Energi yang dipantau" + provenance tag · period · scope · value + unit · qualifier · empty state.

**Consumer provides.** `kwh` (number or null), `quality` complete | partial | unavailable, `completeness`, `gapLabel`, `periodLabel`, `scopeLabel`, `provenance`, `emptyAction`.

**Variants and states.** Complete, partial ("Sebagian data belum tersedia · Kelengkapan data: 50% periode"), measured zero ("Nol terukur dengan data lengkap"), no data ("Belum ada data energi", no number).

**Keyboard and screen reader.** A labelled `<section>`; value and unit are one text run.

**Tokens.** `type-metric`, `color-text-*`, `color-status-attention-foreground`.

**Responsive.** Value and unit wrap as a group.

**Example.** 14,700 kWh · 19–25 Oktober 2026 · Cakupan pengukuran: 4 perangkat · Demo · Data simulasi.

**Limits.** Never show 0 for missing data or a zero-filled full total for partial data.


### HD.CostEstimate

Qualified energy-cost estimate from an optional tariff; missing tariff is unknown, not Rp0.

**Anatomy.** Label · value · tariff × energy line · qualifiers · bill limitation · optional Atur tarif.

**Consumer provides.** `kwh`, `tariff` (null | 0 | number per kWh), `tariffSource` synthetic | user, `partial`, `onSetTariff`.

**Variants and states.** Known (Rp22.050), missing tariff, explicit zero tariff, partial energy, no energy.

**Keyboard and screen reader.** Labelled section; plain text.

**Tokens.** `type-title`, `color-text-*`.

**Responsive.** Wraps.

**Example.** 14,700 kWh × Rp1.500 = Rp22.050 (computed unrounded, rounded once).

**Limits.** Not a utility bill; never compute from a displayed, rounded number.


### HD.ScopeSummary

What is in the measured scope, what is excluded, and how parent/child or unknown overlaps are resolved without adding.

**Anatomy.** Scope line · exclusions · overlap notice · view choice or individual values · included list (disclosure).

**Consumer provides.** `included`, `excluded`, `count`, `unitLabel`, `overlap` none | parentChild | unknown, `parent`, `child`, `view`, `onViewChange`, `values`.

**Variants and states.** Plain scope; parent/child (choose Meteran Utama 10 or Kulkas 1); unknown overlap (no combined total).

**Keyboard and screen reader.** Uses ChoiceGroup and Notice semantics.

**Tokens.** Inherits Notice/ChoiceGroup tokens.

**Responsive.** Stacks.

**Example.** Main meter 10 kWh includes refrigerator 1 kWh: show 10 or 1, never 11.

**Limits.** Do not render a sum when overlap is unknown.


### HD.DataQuality

Separate rows for temporal completeness, source freshness, client offline and provenance — no accuracy score.

**Anatomy.** Rows: icon + term · value · explanation · optional action.

**Consumer provides.** `completeness`, `gaps`, `freshness` {state fresh | stale | historical, lastMeasurement, importRange}, `client`, `cachedAge`, `source`, `onCheckSource`, `onViewPeriod`.

**Variants and states.** Partial, stale live source ("bukan tanda perangkat mati"), historical import ("Lihat periode data"), client offline (drafts retained), demo provenance.

**Keyboard and screen reader.** Description list (`dl`).

**Tokens.** `color-status-attention-foreground`, `color-text-secondary`, `size-icon-small`.

**Responsive.** Stacks.

**Example.** Partial + stale; historical import + offline.

**Limits.** Never merge these into one status or call completeness accuracy.


### HD.AssetRow

One measured asset, circuit, group or meter as a single row link with energy and quality.

**Anatomy.** Name (wraps) · kind · location · quality qualifier · value · chevron.

**Consumer provides.** `name`, `kind` device | circuit | group | meter, `location`, `kwh`, `quality`, `href` or `onOpen`.

**Variants and states.** Complete, partial, stale, unavailable ("— kWh").

**Keyboard and screen reader.** The whole row is one `<a>`; no nested buttons.

**Tokens.** `color-background-surface`, `color-border-decorative`, `size-target-minimum`.

**Responsive.** Name wraps; value stays right.

**Example.** "Pompa Air Area Produksi Belakang" · Perangkat · Area Belakang.

**Limits.** No inline switches or secondary buttons.


### HD.ContributionRanking

Sorted horizontal bars on a zero baseline with direct labels and a visible denominator.

**Anatomy.** Heading · period + denominator · largest-among sentence · list of name, value · share, bar.

**Consumer provides.** `items[{name,kwh}]`, `periodLabel`, `denominatorLabel`, `title`.

**Variants and states.** Normal; zero total (no percentages, neutral notice).

**Keyboard and screen reader.** Ordered list; values are text, bars are `aria-hidden`.

**Tokens.** `color-chart-current`, `color-chart-track`, `color-chart-baseline`, `size-chart-barThickness`.

**Responsive.** Labels wrap above bars.

**Example.** Kulkas 8,400 kWh · 57,14% of 14,700 kWh selected devices.

**Limits.** Largest is not waste; no donut as the main ranking.


### HD.HistoryChart

Aligned daily (or hourly) bars with current/reference distinguished beyond colour and real gaps hatched.

**Anatomy.** Heading · period/scope/unit · legend · scale note · plot · day labels + values · summary + gap note.

**Consumer provides.** `title`, `points[{label,current,reference}]`, `periodLabel`, `scopeLabel`, `unit`, `summary`, `gapNote`, `dense`.

**Variants and states.** Current only, current + reference, gap (null), measured zero (tick), dense 24-hour.

**Keyboard and screen reader.** Plot is `role=img` labelled by the heading and described by the summary; pair with `HD.ChartDataAlternative`.

**Tokens.** `color-chart-*`, `size-stroke-chart`, `size-chart-plotHeight`.

**Responsive.** Columns shrink; `dense` drops per-bar values.

**Example.** TV 3,920 vs 2,520 kWh; Kulkas 12 of 24 hours.

**Limits.** No smoothing, interpolation or inferred values for appearance; no hover-only values.


### HD.ChartDataAlternative

Text summary and structured table resolving the same values and filters as the chart.

**Anatomy.** Summary · disclosure "Lihat data dalam tabel" · table with caption.

**Consumer provides.** `caption`, `columns[{key,label,numeric,format}]`, `rows`, `summary`, `collapsed`.

**Variants and states.** Collapsed, expanded, null cells ("Tidak ada data").

**Keyboard and screen reader.** Real `<table>` with row/column headers; below 768 px rows stack with labels.

**Tokens.** `color-border-*`, `color-text-secondary`.

**Responsive.** Stacked rows on phones; no page scroll.

**Example.** TV per hari table.

**Limits.** Must match the chart exactly.


### HD.InsightSummary

One observed fact with period, comparison eligibility and qualification — no verdict.

**Anatomy.** Fact heading · period + comparison · not-comparable reason · cause unknown · qualification · Lihat bukti.

**Consumer provides.** `kind` change | learning | none, `title`, `periodLabel`, `comparison`, `qualification`, `onOpenEvidence`.

**Variants and states.** Change, not comparable (reason), learning, no eligible finding.

**Keyboard and screen reader.** Labelled section.

**Tokens.** Notice tokens; `color-status-attention-foreground`.

**Responsive.** Stacks.

**Example.** "TV naik 1,400 kWh (+55,56%)" · dibanding 12–18 Oktober 2026.

**Limits.** No fault, waste, savings or off-schedule claim without evidence.


### HD.EvidencePanel

Ordered evidence: observed → comparison → quality/scope → unknown → general guidance → optional harmless feedback, with metadata collapsed.

**Anatomy.** Numbered steps · Saran umum note · feedback buttons + status · Detail perhitungan.

**Consumer provides.** `observed`, `comparison`, `qualityScope`, `unknown`, `guidance`, `onFeedback`, `feedbackState`, `onFeedbackRetry`, `onFeedbackCheck`, `metadata`.

**Variants and states.** Feedback idle, sending, failure + retry, unknown + check, success after confirmation.

**Keyboard and screen reader.** Ordered list with headings; status is polite.

**Tokens.** Shared tokens.

**Responsive.** Stacks.

**Example.** TV +1,400 kWh evidence.

**Limits.** Guidance is labelled "Saran umum"; feedback changes no data or device.


### HD.ImportPreview

CSV preview with counts, mapping, assumptions, row errors, threshold rule and explicit confirmation; save states keep the draft.

**Anatomy.** File + period · counts · mapping/assumptions disclosure · row errors · block notice or acknowledgment · status · confirm.

**Consumer provides.** `fileName`, `totalRows`, `invalidRows`, `duplicateRows`, `conflictRows`, `maxInvalidShare` (0.2), `mapping`, `assumptions`, `errors`, `acknowledged`, `onAcknowledge`, `ackError`, `saveState`, `onConfirm`, `onCheckStatus`.

**Variants and states.** 2/10 invalid needs acknowledgment then imports 8; 3/10 blocked; conflicts block; duplicates counted once; saving, failure (retry), unknown (check), success.

**Keyboard and screen reader.** Row errors are focusable targets for ErrorSummary; confirm is disabled-with-reason when blocked.

**Tokens.** Shared tokens.

**Responsive.** Counts wrap into a grid.

**Example.** energi-oktober.csv, 10 rows.

**Limits.** Never show success before confirmation or import twice after an unknown result.


### HD.ScheduleWindows

Optional weekly schedule: none, explicit 24 hours, inherit from site, or custom windows including overnight.

**Anatomy.** Mode choice · window list.

**Consumer provides.** `mode`, `onModeChange`, `inheritLabel`, `windows[{days,start,end,nextDay}]`.

**Variants and states.** No schedule, continuous, inherit (disabled with reason when site has none), windows, empty windows.

**Keyboard and screen reader.** ChoiceGroup semantics.

**Tokens.** Shared tokens.

**Responsive.** Stacks.

**Example.** Senin–Jumat 07.00–17.00; Senin–Sabtu 22.00–06.00 (berakhir hari berikutnya).

**Limits.** Optional; the core never depends on it.


### HD.OutputMetricPreview

Optional energy-per-output intensity with explicit method; zero, missing or invalid output gives a reason, not infinity.

**Anatomy.** Label · value + unit · numerator ÷ denominator · method · qualifier.

**Consumer provides.** `enabled`, `energyKwh`, `output`, `unit`, `method` actual | estimated, `periodLabel`.

**Variants and states.** Actual (0,050 kWh/unit), estimated, zero output, missing, invalid; `enabled: false` renders nothing.

**Keyboard and screen reader.** Labelled section.

**Tokens.** Shared tokens.

**Responsive.** Wraps.

**Example.** 144,000 kWh ÷ 2.880 unit = 0,050 kWh/unit.

**Limits.** Hidden when not enabled; never a numeric intensity for zero output.


### HD.Screen

Intentional addition: the shared screen frame so pattern assemblies are compositions, not unnamed copies.

**Anatomy.** Top bar (wordmark or back + provenance tag) · title + subtitle · main column · optional aside · sticky TabNavigation.

**Consumer provides.** `title`, `subtitle`, `children`, `aside`, `current`, `onNavigate`, `back`, `provenance`.

**Variants and states.** With/without aside, with back.

**Keyboard and screen reader.** `<main>` labelled by the `h1`; aside labelled.

**Tokens.** `space-page-gutter*`, `size-content-*`, `space-section-gap`.

**Responsive.** One column below 768 px; main + aside above.

**Example.** Beranda · Rumah Bandung · Asia/Jakarta.

**Limits.** Not an app router or shell framework.


### HD.Icon

Intentional addition: the HematDaya stroke icon set, 24-unit grid, currentColor.

**Anatomy.** Single path in a 24 × 24 viewBox.

**Consumer provides.** `name`, `size` default | small.

**Variants and states.** —

**Keyboard and screen reader.** Always `aria-hidden`; meaning comes from adjacent text or IconButton label.

**Tokens.** `size-icon-default`, `size-icon-small`.

**Responsive.** Fixed size.

**Example.** `home`, `devices`, `saran`.

**Limits.** No power symbol; do not use alone.
