# TemuRiset Design System 1.0.0-draft

Single-file guide concatenated from the system's README, guide sections and component READMEs. Authority remains project/tokens.json and the component files.


TemuRiset helps inventors find investors and partners who can advance an invention. This system exists so every screen answers two questions within seconds: **what can I do next, and what does the current evidence mean?** It serves independent inventors and individual investors as comfortably as organization teams, in calm, plain Indonesian.

Release **1.0.0-draft** · review status: draft, not owner-approved · product contract: TemuRiset PRD generic v1.1 · namespace `window.TR` · React 18.3.1 · light theme only. Evidence is in *Validation report*; how the application stage binds to this system is in *Release and consuming*.

## Product rules every screen keeps

- Exactly two public personas: **Inovator** and **Investor/Mitra**. A reviewer or moderator is a scoped capability, never a third persona.
- Show the acting context before send, decide and confirm (`TR.ContextSwitcher` with `readOnly`). Never ask a person to invent a company or institution.
- A patent, company, institution or video is not a universal entry requirement. A recipient may state one for its own opportunity, with the reason beside it.
- Keep these apart in every component and theme: Saat ini / Direncanakan / Diminta; dilaporkan / disediakan / diperiksa; PASS / FAIL / UNKNOWN / NOT_APPLICABLE; Dukungan Proyek / Pendanaan Perusahaan / lisensi; approval / Kerja Sama; selected slot / confirmed meeting.
- UNKNOWN is never FAIL, and never zero. A null amount reads "Belum ditentukan".
- One company raise stays one card, even with several linked inventions. A target and a contribution range are different amounts. No valuation, shares or currency conversion is derived.
- A pitch approval means willingness to discuss. It is not funding, licensing or partnership.
- Both parties confirm the same version. Public relationship fields are their consent intersection, minus live restrictions. Amounts default private.
- Documents default private. Sharing names one recipient and one version. Revocation blocks new retrieval and cannot recall prior copies. Say so.

## Reading order

Open each workspace with `TR.NextStep`: whose turn it is, one sentence, one action. Then the active task. Then supporting detail in `aside` (stacked after the task on narrow screens). Lead invention views with problem, current solution, support sought, financial scope, evidence and responsible people. Put ranking and provenance detail in `TR.Disclosure`; never put a blocking gap there. See *UX principles*.

## Content fundamentals

- Product copy is natural Indonesian, sentence case, addressing the reader as *Anda*. Documentation and identifiers are English.
- Short sentences. Explain an unfamiliar term near its first necessary use.
- Primary actions name their effect: "Siapkan pitching", "Kirim pitching", "Setujui untuk diskusi", "Konfirmasi waktu".
- A pending state says who acts next: "Menunggu Anda", "Menunggu pihak lain".
- Errors say what to fix and keep the input.
- No enum names, HTTP codes, model names or architecture words on business screens. No emoji.
- Glossary and state copy are in *Content and states*. Money and dates come from `TR.format`: `USD 500.000`, `USD 50.000–100.000`, `Senin, 16 November 2026`, `17.00–18.00 WIB (Asia/Jakarta)`.

## Visual foundations

- **Colour.** Slate canvas `tr-sys-color-canvas`, white content `tr-sys-color-surface`, teal only for the one primary action, selection and the your-turn band. Success green appears only after a real result, never for pending work. Amber marks UNKNOWN; red marks a known failure or a rejected input. Blue `tr-sys-color-focus` is reserved for keyboard focus.
- **Components read aliases.** Use `tr-sys-*` or `tr-comp-*` tokens. Never use `tr-ref-*` or raw values in a component.
- **Borders.** `tr-sys-color-border-decorative` separates groups and fails 3:1 on purpose. Every control boundary uses `tr-sys-color-border-control`.
- **Type.** System sans via `--font-sans`, no font downloads. Style classes are `tr-sys-type-body`, `-body-strong`, `-label`, `-support`, `-support-strong`, `-heading-sm`, `-heading-md`, `-heading-lg`, `-amount`. Sizes are rem, so text settings scale them. `tr-sys-type-support` never carries a primary action or a critical gap.
- **Space and shape.** Spacing steps 4 to 64 behind aliases: `tr-sys-space-controlGap`, `tr-sys-space-stack`, `tr-sys-space-section` (`sectionWide` from 48 rem), `tr-sys-layout-gutter` (`gutterWide` from 48 rem). Radii: `tr-sys-radius-control` 6, `tr-sys-radius-surface` 8, `tr-sys-radius-dialog` 12.
- **Layout.** Maximum width `tr-sys-layout-contentMax`, long prose at `tr-sys-layout-readingMeasure`. Below 48 rem one column; above it an optional 20 rem supporting column. No cards inside cards, no big hero areas, no decorative dashboards.
- **Targets and focus.** Common controls are at least `tr-sys-size-controlComfort` (44 CSS px, a product preference; AA asks 24 with exceptions). Focus is a 2 px white gap, then a 2 px blue ring. Selected states always add a non-colour cue: `tr-sys-size-borderSelected`, weight, or a check.
- **Elevation.** `tr-sys-shadow-dialog` for `TR.Dialog` only. Everything else stays flat.
- **Motion.** `tr-sys-motion-feedback` for state feedback only. Reduced motion removes it, and the loading label keeps saying work is in progress. No animated counters, progress charts or pulses.

## Iconography

A small own stroke set (24 grid, 2-unit round stroke, `currentColor`), shipped in the bundle as `TR.Icon`, with no icon library or licence. Icons always support a word; the only exception is the dialog close button, which has the accessible name "Tutup". Sizes are `tr-sys-size-icon` and `tr-sys-size-iconSmall`. There is no logo asset in this release: the wordmark is the word "TemuRiset" in system text. Without a supplied product image, cards use a labelled category band; a missing image is not a problem state. Never invent a product photo, investor credential, rating or funding chart.

## Components

Shared inventory (`TR.*`): Button, Link, TextField, TextArea, Select, ChoiceGroup, Checkbox, FieldError, ErrorSummary, Dialog, Disclosure, Tabs, Status, EmptyState, SaveState, ContextSwitcher, InventionCard, FundingRequestCard, FinancialScope, RequirementRow, FactSource, DocumentItem, RevisionItem, ScheduleSlotList, PartnershipConsent, VersionConflict.

Intentional additions: **NextStep** (the product asks every view to emphasise the next action and whose turn it is, so it needs one owner), **Steps** (the four-step editor), **SummaryList** (check-your-answers with change links), **Screen** (shared frame, so patterns are not unnamed copies), **Icon** (the icon set). Helpers: `TR.format`, `TR.effectiveFields`. `TR.demo` holds fictional fixtures and test controls and is not for production.

Pattern pages, which compose only the components above: *PatternDiscovery* (P01), *PatternPortfolio* (P02), *PatternRevisionSchedule* (P03), *PatternRelationship* (P04), plus *Foundations* and *StateAxes*. Their dashed "Kontrol uji" panels are test controls, not product UI.

## Using it in a page

Load, in order: the compiled tokens CSS, `components/bundle.css`, React 18.3.1 and ReactDOM (`components/lib/`), then `components/bundle.js`. Render with `React.createElement(TR.Button, {…})`. Put `lang="id"` on the document. Pass amounts as decimal strings and `null` for unknown; let components format them. Pass authorized projections only: these components display what they receive and enforce no access rule. Report a save or decision as done only after the server acknowledges it.


## Token registry

Generated by `tools/build.mjs` from `tokens.json` (sha256 `311fe8545a4561c3…`). Do not edit by hand: change `tokens.json`, then rebuild.

**Rules.** Components read semantic or component aliases, never primitives. Logical id `TR.sys.color.action.primary.background` is CSS `--tr-sys-color-action-primary-background`; camelCase segments are kept, so the mapping reverses. Colour aliases are live (`{tr-ref-color-teal-700}`); spacing and radius aliases are recorded as `Alias: <token>.` in the usage note and checked for equality on every build. Type styles are classes sized in rem.

**Export format.** `exports/temuriset-design-system.tokens.json` is custom JSON, `temuriset-tokens/1`. It is not a DTCG file and no DTCG 2025.10 compatibility is claimed; its `dtcgConversion` field states the conversion.

Build result: **0 integrity errors** — 104 tokens, every alias resolves, no cycles, no duplicate names, no raw colours in bundle.css/bundle.js, every `var(--…)` used exists.

## Semantic tokens

| ID | CSS | Type | Value | Resolved | Usage |
|---|---|---|---|---|---|
| `TR.sys.color.canvas` | `--tr-sys-color-canvas` | color | `{TR.ref.color.slate.50}` | `#f8fafc` | Application canvas. Holds tr-sys-color-text-primary and tr-sys-color-text-secondary. |
| `TR.sys.color.surface` | `--tr-sys-color-surface` | color | `{TR.ref.color.white}` | `#ffffff` | Primary content surface: cards, forms, dialogs. |
| `TR.sys.color.surface.subtle` | `--tr-sys-color-surface-subtle` | color | `{TR.ref.color.slate.100}` | `#f1f5f9` | Secondary grouping and neutral status backgrounds. |
| `TR.sys.color.text.primary` | `--tr-sys-color-text-primary` | color | `{TR.ref.color.slate.900}` | `#0f172a` | Main text on canvas, surface, subtle, selected and every status surface. |
| `TR.sys.color.text.secondary` | `--tr-sys-color-text-secondary` | color | `{TR.ref.color.slate.600}` | `#475569` | Supporting text on canvas, surface, subtle and selected surfaces. Never the only carrier of a primary action or a blocking gap. |
| `TR.sys.color.link` | `--tr-sys-color-link` | color | `{TR.ref.color.teal.800}` | `#115e59` | Links on canvas, surface, subtle and selected surfaces. Always underlined. |
| `TR.sys.color.action.primary.background` | `--tr-sys-color-action-primary-background` | color | `{TR.ref.color.teal.700}` | `#0f766e` | One primary action per task region. |
| `TR.sys.color.action.primary.hover` | `--tr-sys-color-action-primary-hover` | color | `{TR.ref.color.teal.800}` | `#115e59` | Primary action on hover. |
| `TR.sys.color.action.primary.pressed` | `--tr-sys-color-action-primary-pressed` | color | `{TR.ref.color.teal.900}` | `#134e4a` | Primary action while pressed. |
| `TR.sys.color.action.primary.foreground` | `--tr-sys-color-action-primary-foreground` | color | `{TR.ref.color.white}` | `#ffffff` | Text and icons on the primary action in all its states. |
| `TR.sys.color.action.secondary.foreground` | `--tr-sys-color-action-secondary-foreground` | color | `{TR.ref.color.teal.800}` | `#115e59` | Secondary action label on surface, canvas and subtle. |
| `TR.sys.color.action.secondary.hover` | `--tr-sys-color-action-secondary-hover` | color | `{TR.ref.color.teal.50}` | `#f0fdfa` | Secondary action background on hover. |
| `TR.sys.color.action.danger.background` | `--tr-sys-color-action-danger-background` | color | `{TR.ref.color.red.700}` | `#b91c1c` | Destructive action fill. Used only with copy naming the actual effect. |
| `TR.sys.color.action.danger.hover` | `--tr-sys-color-action-danger-hover` | color | `{TR.ref.color.red.800}` | `#991b1b` | Destructive action on hover and press. |
| `TR.sys.color.action.danger.foreground` | `--tr-sys-color-action-danger-foreground` | color | `{TR.ref.color.white}` | `#ffffff` | Text and icons on the destructive action. |
| `TR.sys.color.selected.surface` | `--tr-sys-color-selected-surface` | color | `{TR.ref.color.teal.50}` | `#f0fdfa` | Selected contextual surface and the your-turn band. Always paired with a non-colour cue. |
| `TR.sys.color.selected.border` | `--tr-sys-color-selected-border` | color | `{TR.ref.color.teal.700}` | `#0f766e` | Selected control boundary, drawn at tr-sys-size-borderSelected. |
| `TR.sys.color.selected.foreground` | `--tr-sys-color-selected-foreground` | color | `{TR.ref.color.teal.800}` | `#115e59` | Text on tr-sys-color-selected-surface that says what is selected or whose turn it is. |
| `TR.sys.color.disabled.surface` | `--tr-sys-color-disabled-surface` | color | `{TR.ref.color.slate.100}` | `#f1f5f9` | Disabled control background. Never blanket opacity. |
| `TR.sys.color.disabled.foreground` | `--tr-sys-color-disabled-foreground` | color | `{TR.ref.color.slate.600}` | `#475569` | Disabled label on tr-sys-color-disabled-surface, kept readable because the reason matters. |
| `TR.sys.color.border.decorative` | `--tr-sys-color-border-decorative` | color | `{TR.ref.color.slate.300}` | `#cbd5e1` | Nonessential dividers only. Fails 3:1 on purpose and must never be the only boundary of a control. |
| `TR.sys.color.border.control` | `--tr-sys-color-border-control` | color | `{TR.ref.color.slate.500}` | `#64748b` | Required control boundary on surface, canvas and subtle. |
| `TR.sys.color.focus` | `--tr-sys-color-focus` | color | `{TR.ref.color.blue.700}` | `#005fcc` | Visible focus ring, always with tr-sys-color-focus-gap inside it. |
| `TR.sys.color.focus.gap` | `--tr-sys-color-focus-gap` | color | `{TR.ref.color.white}` | `#ffffff` | Light separation between a control and its focus ring. |
| `TR.sys.color.danger.text` | `--tr-sys-color-danger-text` | color | `{TR.ref.color.red.700}` | `#b91c1c` | Error text and FAIL labels on surface, canvas and danger surface. |
| `TR.sys.color.danger.surface` | `--tr-sys-color-danger-surface` | color | `{TR.ref.color.red.50}` | `#fef2f2` | Error background. |
| `TR.sys.color.success.text` | `--tr-sys-color-success-text` | color | `{TR.ref.color.green.800}` | `#166534` | Confirmed-success text on surface, canvas and success surface. Only after a real result, never for pending work. |
| `TR.sys.color.success.surface` | `--tr-sys-color-success-surface` | color | `{TR.ref.color.green.50}` | `#f0fdf4` | Success background. |
| `TR.sys.color.warning.text` | `--tr-sys-color-warning-text` | color | `{TR.ref.color.amber.800}` | `#92400e` | UNKNOWN and warning text on surface, canvas and warning surface. |
| `TR.sys.color.warning.surface` | `--tr-sys-color-warning-surface` | color | `{TR.ref.color.amber.50}` | `#fffbeb` | Supporting surface for UNKNOWN and warnings. |
| `TR.sys.color.overlay` | `--tr-sys-color-overlay` | color | `{TR.ref.color.overlay}` | `rgba(15, 23, 42, 0.5)` | Dialog backdrop. |
| `TR.sys.space.controlGap` | `--tr-sys-space-controlGap` | dimension | `0.5rem` | `0.5rem` | Alias: tr-ref-space-8. Gap between neighbouring controls; widen where touch separation needs it. |
| `TR.sys.space.stack` | `--tr-sys-space-stack` | dimension | `1rem` | `1rem` | Alias: tr-ref-space-16. Gap between items in one group. |
| `TR.sys.space.section` | `--tr-sys-space-section` | dimension | `1.5rem` | `1.5rem` | Alias: tr-ref-space-24. Gap between sections below the wide breakpoint. |
| `TR.sys.space.sectionWide` | `--tr-sys-space-sectionWide` | dimension | `2rem` | `2rem` | Alias: tr-ref-space-32. Gap between sections from the wide breakpoint. |
| `TR.sys.layout.gutter` | `--tr-sys-layout-gutter` | dimension | `1rem` | `1rem` | Alias: tr-ref-space-16. Page gutter on narrow screens. |
| `TR.sys.layout.gutterWide` | `--tr-sys-layout-gutterWide` | dimension | `1.5rem` | `1.5rem` | Alias: tr-ref-space-24. Page gutter from the wide breakpoint. |
| `TR.sys.radius.control` | `--tr-sys-radius-control` | dimension | `6px` | `6px` | Alias: tr-ref-radius-6. Controls and status labels. |
| `TR.sys.radius.surface` | `--tr-sys-radius-surface` | dimension | `8px` | `8px` | Alias: tr-ref-radius-8. Ordinary surfaces. |
| `TR.sys.radius.dialog` | `--tr-sys-radius-dialog` | dimension | `12px` | `12px` | Alias: tr-ref-radius-12. Large dialogs. |
| `TR.sys.size.controlComfort` | `--tr-sys-size-controlComfort` | dimension | `2.75rem` | `2.75rem` | Comfortable 44 CSS px minimum for common controls. A product preference; AA itself asks 24 CSS px with exceptions. |
| `TR.sys.size.icon` | `--tr-sys-size-icon` | dimension | `1.25rem` | `1.25rem` | Default glyph, 20 CSS px. |
| `TR.sys.size.iconSmall` | `--tr-sys-size-iconSmall` | dimension | `1.125rem` | `1.125rem` | Small glyph inside status labels, 18 CSS px. |
| `TR.sys.size.border` | `--tr-sys-size-border` | dimension | `1px` | `1px` | Ordinary boundary width. |
| `TR.sys.size.borderSelected` | `--tr-sys-size-borderSelected` | dimension | `2px` | `2px` | Selected and invalid boundary width; the non-colour cue. |
| `TR.sys.size.focusGap` | `--tr-sys-size-focusGap` | dimension | `2px` | `2px` | Light gap inside the focus ring. |
| `TR.sys.size.focusRing` | `--tr-sys-size-focusRing` | dimension | `2px` | `2px` | Focus ring width. |
| `TR.sys.layout.contentMax` | `--tr-sys-layout-contentMax` | dimension | `75rem` | `75rem` | Maximum page width, 1,200 CSS px. |
| `TR.sys.layout.readingMeasure` | `--tr-sys-layout-readingMeasure` | dimension | `65ch` | `65ch` | Long prose measure, about 60 to 70 characters. |
| `TR.sys.layout.asideWidth` | `--tr-sys-layout-asideWidth` | dimension | `20rem` | `20rem` | Supporting column beside the active task from the wide breakpoint. |
| `TR.sys.layout.breakpointWide` | `--tr-sys-layout-breakpointWide` | dimension | `48rem` | `48rem` | Wide layout starts at 768 CSS px. Documents the media query in bundle.css. |
| `TR.sys.motion.feedback` | `--tr-sys-motion-feedback` | duration | `150ms` | `150ms` | State feedback at most. Reduced motion sets it to 0 ms. |
| `TR.sys.motion.easing` | `--tr-sys-motion-easing` | cubicBezier | `cubic-bezier(0.2, 0, 0, 1)` | `cubic-bezier(0.2, 0, 0, 1)` | Standard easing for state feedback. |
| `TR.sys.shadow.dialog` | `--tr-sys-shadow-dialog` | shadow | `0 8px 32px rgba(15, 23, 42, 0.24)` | `0 8px 32px rgba(15, 23, 42, 0.24)` | Dialogs only. Cards and pages stay flat. |
| `TR.sys.type.body` | `.tr-sys-type-body` | typography | `1rem / 1.5 · 400` |  | Running text and answers. |
| `TR.sys.type.body.strong` | `.tr-sys-type-body-strong` | typography | `1rem / 1.5 · 600` |  | Emphasis inside running text. |
| `TR.sys.type.label` | `.tr-sys-type-label` | typography | `1rem / 1.4 · 500` |  | Field labels, buttons and tabs. |
| `TR.sys.type.support` | `.tr-sys-type-support` | typography | `0.875rem / 1.5 · 400` |  | Hints and metadata. Never the sole carrier of a primary action or a critical gap. |
| `TR.sys.type.support.strong` | `.tr-sys-type-support-strong` | typography | `0.875rem / 1.5 · 600` |  | Status labels and short tags. |
| `TR.sys.type.heading.sm` | `.tr-sys-type-heading-sm` | typography | `1.25rem / 1.4 · 600` |  | Card and section headings. |
| `TR.sys.type.heading.md` | `.tr-sys-type-heading-md` | typography | `1.5rem / 1.3 · 600` |  | Task region headings and dialog titles. |
| `TR.sys.type.heading.lg` | `.tr-sys-type-heading-lg` | typography | `2rem / 1.2 · 600` |  | Page titles. |
| `TR.sys.type.amount` | `.tr-sys-type-amount` | typography | `1.25rem / 1.4 · 600` |  | Money with its currency; always tabular and kept with its unit. |

## Component tokens

| ID | CSS | Type | Value | Resolved | Usage |
|---|---|---|---|---|---|
| `TR.comp.button.primary.background` | `--tr-comp-button-primary-background` | color | `{TR.sys.color.action.primary.background}` | `#0f766e` | Component alias of the primary action background. |
| `TR.comp.button.primary.hover` | `--tr-comp-button-primary-hover` | color | `{TR.sys.color.action.primary.hover}` | `#115e59` | Component alias of the primary action hover. |
| `TR.comp.button.primary.foreground` | `--tr-comp-button-primary-foreground` | color | `{TR.sys.color.action.primary.foreground}` | `#ffffff` | Component alias of the primary action label. |
| `TR.comp.field.border` | `--tr-comp-field-border` | color | `{TR.sys.color.border.control}` | `#64748b` | Field boundary. |
| `TR.comp.field.borderError` | `--tr-comp-field-borderError` | color | `{TR.sys.color.danger.text}` | `#b91c1c` | Field boundary while invalid, drawn at tr-sys-size-borderSelected. |
| `TR.comp.field.focus` | `--tr-comp-field-focus` | color | `{TR.sys.color.focus}` | `#005fcc` | Field focus ring. |

## Primitive tokens

| ID | CSS | Type | Value | Resolved | Usage |
|---|---|---|---|---|---|
| `TR.ref.color.white` | `--tr-ref-color-white` | color | `#ffffff` | `#ffffff` | Primitive (seed). Surface, focus gap and text on dark fills. Read through tr-sys-color-surface, tr-sys-color-focus-gap and the foreground roles. |
| `TR.ref.color.slate.50` | `--tr-ref-color-slate-50` | color | `#f8fafc` | `#f8fafc` | Primitive (seed). Read through tr-sys-color-canvas. |
| `TR.ref.color.slate.100` | `--tr-ref-color-slate-100` | color | `#f1f5f9` | `#f1f5f9` | Primitive (seed). Read through tr-sys-color-surface-subtle and tr-sys-color-disabled-surface. |
| `TR.ref.color.slate.300` | `--tr-ref-color-slate-300` | color | `#cbd5e1` | `#cbd5e1` | Primitive (seed). Read through tr-sys-color-border-decorative. |
| `TR.ref.color.slate.500` | `--tr-ref-color-slate-500` | color | `#64748b` | `#64748b` | Primitive (seed). Read through tr-sys-color-border-control. |
| `TR.ref.color.slate.600` | `--tr-ref-color-slate-600` | color | `#475569` | `#475569` | Primitive (seed). Read through tr-sys-color-text-secondary and tr-sys-color-disabled-foreground. |
| `TR.ref.color.slate.900` | `--tr-ref-color-slate-900` | color | `#0f172a` | `#0f172a` | Primitive (seed). Read through tr-sys-color-text-primary. |
| `TR.ref.color.teal.50` | `--tr-ref-color-teal-50` | color | `#f0fdfa` | `#f0fdfa` | Primitive (seed). Read through tr-sys-color-selected-surface. |
| `TR.ref.color.teal.700` | `--tr-ref-color-teal-700` | color | `#0f766e` | `#0f766e` | Primitive (seed). Read through tr-sys-color-action-primary-background. |
| `TR.ref.color.teal.800` | `--tr-ref-color-teal-800` | color | `#115e59` | `#115e59` | Primitive (seed). Read through the primary hover, secondary foreground, link and selected foreground roles. |
| `TR.ref.color.teal.900` | `--tr-ref-color-teal-900` | color | `#134e4a` | `#134e4a` | Primitive (added in 1.0.0-draft). Pressed primary action. |
| `TR.ref.color.blue.700` | `--tr-ref-color-blue-700` | color | `#005fcc` | `#005fcc` | Primitive (seed). Read through tr-sys-color-focus only; blue never carries product meaning here. |
| `TR.ref.color.red.50` | `--tr-ref-color-red-50` | color | `#fef2f2` | `#fef2f2` | Primitive (seed). Read through tr-sys-color-danger-surface. |
| `TR.ref.color.red.700` | `--tr-ref-color-red-700` | color | `#b91c1c` | `#b91c1c` | Primitive (seed). Read through tr-sys-color-danger-text and the destructive action. |
| `TR.ref.color.red.800` | `--tr-ref-color-red-800` | color | `#991b1b` | `#991b1b` | Primitive (added in 1.0.0-draft). Destructive action hover. |
| `TR.ref.color.green.50` | `--tr-ref-color-green-50` | color | `#f0fdf4` | `#f0fdf4` | Primitive (seed). Read through tr-sys-color-success-surface. |
| `TR.ref.color.green.800` | `--tr-ref-color-green-800` | color | `#166534` | `#166534` | Primitive (seed). Read through tr-sys-color-success-text. |
| `TR.ref.color.amber.50` | `--tr-ref-color-amber-50` | color | `#fffbeb` | `#fffbeb` | Primitive (seed). Read through tr-sys-color-warning-surface. |
| `TR.ref.color.amber.800` | `--tr-ref-color-amber-800` | color | `#92400e` | `#92400e` | Primitive (seed). Read through tr-sys-color-warning-text. |
| `TR.ref.color.overlay` | `--tr-ref-color-overlay` | color | `rgba(15, 23, 42, 0.5)` | `rgba(15, 23, 42, 0.5)` | Primitive (added in 1.0.0-draft). Dialog backdrop only; never behind text that must be read. |
| `TR.ref.space.4` | `--tr-ref-space-4` | dimension | `0.25rem` | `0.25rem` | Primitive. 4 CSS px at default text size. |
| `TR.ref.space.8` | `--tr-ref-space-8` | dimension | `0.5rem` | `0.5rem` | Primitive. 8 CSS px. |
| `TR.ref.space.12` | `--tr-ref-space-12` | dimension | `0.75rem` | `0.75rem` | Primitive. 12 CSS px. |
| `TR.ref.space.16` | `--tr-ref-space-16` | dimension | `1rem` | `1rem` | Primitive. 16 CSS px. |
| `TR.ref.space.24` | `--tr-ref-space-24` | dimension | `1.5rem` | `1.5rem` | Primitive. 24 CSS px. |
| `TR.ref.space.32` | `--tr-ref-space-32` | dimension | `2rem` | `2rem` | Primitive. 32 CSS px. |
| `TR.ref.space.48` | `--tr-ref-space-48` | dimension | `3rem` | `3rem` | Primitive. 48 CSS px. |
| `TR.ref.space.64` | `--tr-ref-space-64` | dimension | `4rem` | `4rem` | Primitive. 64 CSS px. |
| `TR.ref.radius.6` | `--tr-ref-radius-6` | dimension | `6px` | `6px` | Primitive. Read through tr-sys-radius-control. |
| `TR.ref.radius.8` | `--tr-ref-radius-8` | dimension | `8px` | `8px` | Primitive. Read through tr-sys-radius-surface. |
| `TR.ref.radius.12` | `--tr-ref-radius-12` | dimension | `12px` | `12px` | Primitive. Read through tr-sys-radius-dialog. |
| `TR.ref.weight.regular` | `--tr-ref-weight-regular` | fontWeight | `400` | `400` | Body text. |
| `TR.ref.weight.medium` | `--tr-ref-weight-medium` | fontWeight | `500` | `500` | Labels and actions. |
| `TR.ref.weight.semibold` | `--tr-ref-weight-semibold` | fontWeight | `600` | `600` | Headings, amounts and status labels. |
| `TR.font.sans` | `--font-sans` | fontFamily | `system-ui, -apple-system, "Segoe UI", "Helvetica Neue", Arial, sans-serif` | `system-ui, -apple-system, "Segoe UI", "Helvetica Neue", Arial, sans-serif` | System sans-serif stack; no font files are fetched. |

## Computed contrast of resolved pairs

WCAG 2 relative-luminance ratios of opaque resolved token values, rounded for display. These are token calculations; rendered checks are in the validation report.

| Foreground | Background | Ratio | Min | Role | Result |
|---|---|---:|---:|---|---|
| `TR.sys.color.text.primary` #0f172a | `TR.sys.color.canvas` #f8fafc | 17.0629:1 | 4.5:1 | Main text | pass |
| `TR.sys.color.text.secondary` #475569 | `TR.sys.color.canvas` #f8fafc | 7.2425:1 | 4.5:1 | Supporting text | pass |
| `TR.sys.color.link` #115e59 | `TR.sys.color.canvas` #f8fafc | 7.2481:1 | 4.5:1 | Link | pass |
| `TR.sys.color.text.primary` #0f172a | `TR.sys.color.surface` #ffffff | 17.8525:1 | 4.5:1 | Main text | pass |
| `TR.sys.color.text.secondary` #475569 | `TR.sys.color.surface` #ffffff | 7.5777:1 | 4.5:1 | Supporting text | pass |
| `TR.sys.color.link` #115e59 | `TR.sys.color.surface` #ffffff | 7.5835:1 | 4.5:1 | Link | pass |
| `TR.sys.color.text.primary` #0f172a | `TR.sys.color.surface.subtle` #f1f5f9 | 16.2960:1 | 4.5:1 | Main text | pass |
| `TR.sys.color.text.secondary` #475569 | `TR.sys.color.surface.subtle` #f1f5f9 | 6.9170:1 | 4.5:1 | Supporting text | pass |
| `TR.sys.color.link` #115e59 | `TR.sys.color.surface.subtle` #f1f5f9 | 6.9223:1 | 4.5:1 | Link | pass |
| `TR.sys.color.text.primary` #0f172a | `TR.sys.color.selected.surface` #f0fdfa | 17.1177:1 | 4.5:1 | Main text | pass |
| `TR.sys.color.text.secondary` #475569 | `TR.sys.color.selected.surface` #f0fdfa | 7.2657:1 | 4.5:1 | Supporting text | pass |
| `TR.sys.color.link` #115e59 | `TR.sys.color.selected.surface` #f0fdfa | 7.2713:1 | 4.5:1 | Link | pass |
| `TR.sys.color.text.primary` #0f172a | `TR.sys.color.danger.surface` #fef2f2 | 16.3199:1 | 4.5:1 | Main text on status surface | pass |
| `TR.sys.color.text.primary` #0f172a | `TR.sys.color.success.surface` #f0fdf4 | 17.0547:1 | 4.5:1 | Main text on status surface | pass |
| `TR.sys.color.text.primary` #0f172a | `TR.sys.color.warning.surface` #fffbeb | 17.2154:1 | 4.5:1 | Main text on status surface | pass |
| `TR.sys.color.danger.text` #b91c1c | `TR.sys.color.surface` #ffffff | 6.4700:1 | 4.5:1 | danger text and icon | pass |
| `TR.sys.color.danger.text` #b91c1c | `TR.sys.color.canvas` #f8fafc | 6.1839:1 | 4.5:1 | danger text and icon | pass |
| `TR.sys.color.danger.text` #b91c1c | `TR.sys.color.danger.surface` #fef2f2 | 5.9146:1 | 4.5:1 | danger text and icon | pass |
| `TR.sys.color.success.text` #166534 | `TR.sys.color.surface` #ffffff | 7.1303:1 | 4.5:1 | success text and icon | pass |
| `TR.sys.color.success.text` #166534 | `TR.sys.color.canvas` #f8fafc | 6.8149:1 | 4.5:1 | success text and icon | pass |
| `TR.sys.color.success.text` #166534 | `TR.sys.color.success.surface` #f0fdf4 | 6.8117:1 | 4.5:1 | success text and icon | pass |
| `TR.sys.color.warning.text` #92400e | `TR.sys.color.surface` #ffffff | 7.0900:1 | 4.5:1 | warning text and icon | pass |
| `TR.sys.color.warning.text` #92400e | `TR.sys.color.canvas` #f8fafc | 6.7765:1 | 4.5:1 | warning text and icon | pass |
| `TR.sys.color.warning.text` #92400e | `TR.sys.color.warning.surface` #fffbeb | 6.8370:1 | 4.5:1 | warning text and icon | pass |
| `TR.sys.color.action.primary.foreground` #ffffff | `TR.sys.color.action.primary.background` #0f766e | 5.4733:1 | 4.5:1 | Primary label | pass |
| `TR.sys.color.action.primary.foreground` #ffffff | `TR.sys.color.action.primary.hover` #115e59 | 7.5835:1 | 4.5:1 | Primary label, hover | pass |
| `TR.sys.color.action.primary.foreground` #ffffff | `TR.sys.color.action.primary.pressed` #134e4a | 9.4751:1 | 4.5:1 | Primary label, pressed | pass |
| `TR.sys.color.action.danger.foreground` #ffffff | `TR.sys.color.action.danger.background` #b91c1c | 6.4700:1 | 4.5:1 | Destructive label | pass |
| `TR.sys.color.action.danger.foreground` #ffffff | `TR.sys.color.action.danger.hover` #991b1b | 8.3101:1 | 4.5:1 | Destructive label, hover | pass |
| `TR.sys.color.action.secondary.foreground` #115e59 | `TR.sys.color.surface` #ffffff | 7.5835:1 | 4.5:1 | Secondary label | pass |
| `TR.sys.color.action.secondary.foreground` #115e59 | `TR.sys.color.action.secondary.hover` #f0fdfa | 7.2713:1 | 4.5:1 | Secondary label, hover | pass |
| `TR.sys.color.selected.foreground` #115e59 | `TR.sys.color.selected.surface` #f0fdfa | 7.2713:1 | 4.5:1 | Selected text | pass |
| `TR.sys.color.disabled.foreground` #475569 | `TR.sys.color.disabled.surface` #f1f5f9 | 6.9170:1 | 4.5:1 | Disabled label stays readable | pass |
| `TR.sys.color.focus` #005fcc | `TR.sys.color.canvas` #f8fafc | 5.7202:1 | 3:1 | Focus ring | pass |
| `TR.sys.color.focus` #005fcc | `TR.sys.color.surface` #ffffff | 5.9849:1 | 3:1 | Focus ring | pass |
| `TR.sys.color.focus` #005fcc | `TR.sys.color.surface.subtle` #f1f5f9 | 5.4631:1 | 3:1 | Focus ring | pass |
| `TR.sys.color.focus` #005fcc | `TR.sys.color.selected.surface` #f0fdfa | 5.7386:1 | 3:1 | Focus ring | pass |
| `TR.sys.color.focus` #005fcc | `TR.sys.color.danger.surface` #fef2f2 | 5.4711:1 | 3:1 | Focus ring | pass |
| `TR.sys.color.focus` #005fcc | `TR.sys.color.success.surface` #f0fdf4 | 5.7175:1 | 3:1 | Focus ring | pass |
| `TR.sys.color.focus` #005fcc | `TR.sys.color.warning.surface` #fffbeb | 5.7713:1 | 3:1 | Focus ring | pass |
| `TR.sys.color.focus` #005fcc | `TR.sys.color.focus.gap` #ffffff | 5.9849:1 | 3:1 | Focus ring against its gap | pass |
| `TR.sys.color.action.primary.background` #0f766e | `TR.sys.color.focus.gap` #ffffff | 5.4733:1 | 3:1 | Primary fill against focus gap | pass |
| `TR.sys.color.border.control` #64748b | `TR.sys.color.surface` #ffffff | 4.7588:1 | 3:1 | Control boundary | pass |
| `TR.sys.color.border.control` #64748b | `TR.sys.color.canvas` #f8fafc | 4.5484:1 | 3:1 | Control boundary | pass |
| `TR.sys.color.border.control` #64748b | `TR.sys.color.surface.subtle` #f1f5f9 | 4.3439:1 | 3:1 | Control boundary | pass |
| `TR.sys.color.selected.border` #0f766e | `TR.sys.color.selected.surface` #f0fdfa | 5.2480:1 | 3:1 | Selected boundary | pass |
| `TR.comp.field.borderError` #b91c1c | `TR.sys.color.surface` #ffffff | 6.4700:1 | 3:1 | Invalid field boundary | pass |
| `TR.sys.color.border.decorative` #cbd5e1 | `TR.sys.color.surface` #ffffff | 1.4847:1 | 3:1 | Decorative border (expected to fail: decorative only) | fail (restricted to decorative use) |

Semantic tokens not referenced by bundle.css/bundle.js (kept as declared roles): `TR.sys.color.action.primary.hover`, `TR.sys.layout.breakpointWide`.


## UX principles

These rules make the product easy for a first-time inventor and quick for a busy investor. Each one names the component that carries it, so following the component follows the rule. They are design decisions and hypotheses: no participant has tested them yet.

## 1. One next step

A person should never have to work out what to do. Open every workspace with `TR.NextStep`.

- Say whose turn it is in words: "Menunggu Anda" or "Menunggu pihak lain".
- Give one sentence of reason and one action named by its effect.
- When it waits on someone else, say that nothing is needed now. Do not offer busywork.
- Show one `primary` button per task region. Everything else is `secondary`.

## 2. Tell people what a result means for them

A label alone is not enough. Pair `TR.Status` with one sentence.

| Instead of | Write |
|---|---|
| Unknown | Belum diketahui. Kewenangan hak belum diperiksa. Ini bukan penolakan. |
| Approved | Disetujui untuk diskusi. Mitra bersedia berdiskusi. Ini belum berarti pendanaan atau kerja sama. |
| Revoked | Akses dicabut. Unduhan baru diblokir, tetapi salinan yang sudah diunduh tidak dapat ditarik. |

## 3. Work is never lost

Fear of losing work makes people stop. Protect it, then say so.

- Show `TR.SaveState` beside the page heading. Use a location: "Tersimpan di demo ini".
- A draft saves with gaps. Require support details when sending, not when saving.
- After an error, keep every nonsecret value. Focus `TR.ErrorSummary`, link to each field, and repeat the inline words.
- On a stale version, `TR.VersionConflict` shows the retained draft and one recovery.
- One failed upload never clears other answers.
- A failed replacement leaves the existing meeting in force, and the message says so.

## 4. Ask for less, reveal when relevant

- Show fields only for the selected purpose. Do not delete unrelated saved drafts when the purpose changes.
- Put the task first. Put ranking, provenance and score detail in `TR.Disclosure`.
- Keep blocking gaps visible at all times. List gaps first, and do not make people open anything to learn why they are blocked.
- Never require a company, patent or institution just to continue.

## 5. Explain the wait and the block

- A disabled action says why, right beside it: `disabledReason`.
- An empty result says why and offers a next action: `TR.EmptyState`. It never loosens a mandatory requirement on its own.
- A later-stage requirement is marked "Tidak menghalangi pengajuan". Future work never looks like today's blocker.

## 6. Check before anything consequential

- Use `TR.SummaryList` with `Ubah` links before sending, publishing or confirming.
- Show the acting context and the exact recipient and version.
- Use `TR.Dialog` for short confirmations. Use an ordinary page for long work.
- Save the word "terkirim" for after the server confirms.

## 7. Respect time and money

- Money always says what it is an amount of, with its unit and period: `TR.FinancialScope`.
- Times appear in the reader's zone with its label, and the other party's time beside it: `TR.ScheduleSlotList`.

## 8. Comfortable on a phone and with a keyboard

- Common controls are 44 CSS px. Whole rows are targets for choices.
- The phone bar shows four destinations plus Lainnya, and stops sticking when large text would make it cover content.
- Every action works by keyboard. Focus is always visible and is not hidden by sticky bars.
- Reading order stays the same at every width: task first, support after.

## Task-time goals to verify later

The PRD proposes these and they are not yet measured: at least 80% of defined tasks completed without help, a prepared pitch in under five minutes, slot selection in under two minutes, and correct understanding that approval is not funding. Run them with 5–8 people covering independent inventors, startup managers and investors or partners, including keyboard and mobile use.


## Content and states

## Shared glossary

| Meaning | Product copy |
|---|---|
| Main personas | Inovator; Investor/Mitra |
| Portfolio and navigation | Inovasi Saya; Temukan Investor/Mitra; Pitching dan Diskusi |
| Financial subjects | Dukungan Proyek; Pendanaan Perusahaan; Target Pendanaan; Kisaran kontribusi per investor |
| Action responsibility | Menunggu Anda; Menunggu pihak lain |
| Draft status | Belum tersimpan; Menyimpan; Tersimpan di demo ini; Gagal menyimpan |
| Evidence | Dilaporkan sumber; Disediakan, belum diperiksa; Diperiksa untuk kriteria ini; Belum diketahui |
| Capability timing | Saat ini; Direncanakan; Diminta |
| Pitch decisions | Setujui untuk diskusi; Minta revisi; Tolak |
| Revision responses | Dapat dipenuhi; Perlu diskusi; Belum dapat dipenuhi |
| Scheduling | Pilih waktu; Konfirmasi waktu; Usulkan waktu lain; Waktu sudah bentrok |
| Relationship | Kerja Sama; Menunggu konfirmasi; Dikonfirmasi kedua pihak |
| Company status | Perusahaan belum didirikan; Badan usaha telah disebutkan, status pemeriksaan ditampilkan terpisah |

## Independent state axes

Changing one axis never implies a change in another. *StateAxes* makes them operable, with buttons for the five required combinations.

| Axis | Values | Component | Rule |
|---|---|---|---|
| Draft saving | local, saving, saved, failed, conflict | `TR.SaveState` | Accurate location and time; input retained |
| File availability | CREATED, UPLOADING, QUARANTINED, AVAILABLE, REJECTED | `TR.DocumentItem` | Presence cannot bypass quarantine |
| Extraction | NOT_REQUESTED, PENDING, RUNNING, SUCCEEDED, FAILED, NEEDS_MANUAL_INPUT | `TR.DocumentItem` | A safe scan stays available without OCR |
| Review | PROVIDED_UNREVIEWED, REVIEWED_SUPPORTED, REVIEWED_UNSUPPORTED, NEEDS_CLARIFICATION, EXPIRED, SUPERSEDED | `TR.DocumentItem`, `TR.FactSource` | No automatic verified badge |
| Requirement | PASS, FAIL, UNKNOWN, NOT_APPLICABLE | `TR.RequirementRow` | Reason, stage and next action |
| Pitch | Dikirim, Sedang ditinjau, Revisi diminta, Disetujui untuk diskusi, Ditolak, Ditarik, Ditutup | `TR.Status`, `TR.NextStep` | Approval remains a discussion state |
| Scheduling | Open, selected, accepted, expired, superseded, cancelled | `TR.ScheduleSlotList` | No booking until acceptance succeeds |
| Relationship | Draf, Menunggu konfirmasi, Perubahan diminta, Ditolak, Dikonfirmasi kedua pihak | `TR.PartnershipConsent` | Exact version, separate public projection |
| Disclosure | Ceiling, per-party subset, effective intersection, restriction | `TR.PartnershipConsent`, `TR.effectiveFields` | No field beyond mutual and current permission |

## Tone mapping

| Tone | Used for | Never for |
|---|---|---|
| `success` | PASS, reviewed support, confirmed meeting, both parties confirmed | Pending work, uploads, single confirmations |
| `danger` | Known FAIL, rejected file, failed action | UNKNOWN or missing information |
| `warning` | UNKNOWN, needs confirmation, quarantine, conflict | Known failure |
| `neutral` | Waiting, unreviewed, later-stage work, not applicable | A result that needs action now |
| `action` | Your turn, selected but unconfirmed | Anything already finished |

## Money and time formatting

Use `TR.format`. Amounts are decimal strings and never pass through floating point.

| Call | Result |
|---|---|
| `money('USD', '500000')` | USD 500.000 |
| `range('USD', '50000', '100000')` | USD 50.000–100.000 |
| `range('USD', null, null)` | Belum ditentukan |
| `slotTime('2026-11-17T09:00:00Z', 60, 'Asia/Jakarta')` | 16.00–17.00 WIB (Asia/Jakarta) |
| `slotTime('2026-11-17T09:00:00Z', 60, 'Asia/Makassar')` | 17.00–18.00 WITA (Asia/Makassar) |
| `overlaps('…09:30', 60, '…09:00', 60)` | true |
| `overlaps('…10:00', 60, '…09:00', 60)` | false (half-open intervals) |


## Pattern assemblies

All names, evidence, amounts and activity are fictional DEMO contracts, not customers, investor interest, reviewed inventions or funding outcomes. Pattern controls simulate state in the browser and prove nothing about file scanning, grant enforcement, simultaneous booking or legal authority.

Assumptions this stage adds to the fixtures: the slot dates (16 and 17 November 2026), the names Rani and Mitra Demo A/B/D, and the short problem sentences. The handoff gives times and amounts but no calendar dates or display names. P04 also uses an illustrative agreed amount, USD 25.000, and start date, 1 December 2026, because the handoff gives field names without values.

## P01 PatternDiscovery

Composes `TR.Screen`, `TR.NextStep`, `TR.Tabs`, `TR.InventionCard`, `TR.FundingRequestCard`, `TR.FinancialScope`, `TR.FactSource`, `TR.Disclosure`, then for preflight `TR.SummaryList`, `TR.RequirementRow`, `TR.ContextSwitcher`, `TR.TextArea` and `TR.VersionConflict`.

Shows a compatible opportunity (F01, "Siap dikirim"), an unknown gap (F02, "Perlu konfirmasi") and a known mismatch (F03, "Tidak cocok untuk mitra ini"). Company funding sits in its own tab. The card shows FRaise01 once, with two linked inventions and no duplicate amounts. The score 71,72–80,00 is behind a disclosure and labelled a review-priority index, not a funding probability.

Three fixtures appear together so one page shows all three outcomes. The application shows results for one selected source request.

Try: Siapkan pitching, then Kirim pitching. Tick "Persyaratan berubah sebelum kirim" first to see a stale preflight keep the message.

## P02 PatternPortfolio

Composes `TR.Steps`, `TR.SaveState`, `TR.TextField`, `TR.TextArea`, `TR.DocumentItem`, `TR.ErrorSummary`, `TR.InventionCard`, `TR.Checkbox`, `TR.ContextSwitcher` and `TR.Dialog`.

Four ordered steps: basics; what exists and evidence; support and financial scope; public preview. F01 starts with an AVAILABLE scan that needs manual input and is unreviewed. "Tanpa anggaran" shows the missing-budget variant: the draft stays saved, the preview reads "Belum ditentukan", and sending is disabled with its reason. "Penyimpanan berikutnya gagal" shows a retained save failure with retry. Typing -1 or a maximum below the minimum on step 3 triggers the error summary. The final send names one recipient, one document and one version.

## P03 PatternRevisionSchedule

Composes `TR.NextStep`, `TR.Tabs`, `TR.RevisionItem`, `TR.ErrorSummary`, `TR.ScheduleSlotList`, `TR.Status` and `TR.FinancialScope`.

A required pilot-budget question and an optional planned-feature question keep their answers. "Belum dapat dipenuhi" is accepted on resubmission once required items are answered. After "Mitra menyetujui diskusi", three slots appear. The 09:30–10:30 UTC slot conflicts with the 09:00–10:00 booking; 10:00–11:00 does not. 09:00 UTC reads 16.00 WIB and 17.00 WITA. A selected slot says "Dipilih, belum dikonfirmasi". With "Penggantian jadwal gagal" ticked, a replacement fails and the original meeting stays in force.

## P04 PatternRelationship

Composes `TR.NextStep`, `TR.PartnershipConsent`, `TR.SummaryList` and `TR.effectiveFields`.

Confirm version 1, then press "Mitra mengoreksi ke versi 2": the correction clears both confirmations. Confirm version 2, then press "Mitra mengonfirmasi versi 2". Only the four fields both parties allow appear publicly. The amount stays private because only one party permits it. "Sembunyikan" narrows a field at once and the copy states it cannot recall downloads. A project relationship is stated not to create equity, even with a monetary amount.


## Validation report

Release 1.0.0-draft, checks run 31 October 2026 (Asia/Jakarta). Results are PASS, FAIL, NOT RUN or BLOCKED. Every preview uses fictional fixtures ("Demo · Data fiktif") and simulated services; that is provenance, not a result. Token arithmetic, a rendered browser check, an export inspection and a participant session are different evidence, and none stands in for another.

## Test surfaces

| Surface | What it is | Used for |
|---|---|---|
| A. Token build | `node tools/build.mjs` (Node 25.2.1) over `tokens.json`, `bundle.css`, `bundle.js` | Integrity, aliases, computed contrast, raw-value scan |
| B. Local workbench | `workbench/index.html` (frame per preview, width, text and motion controls, audit) and `workbench/frame.html?<Preview>` (one preview at the real viewport), served by `python3 -m http.server` from the same `project/` files | Rendered contrast, targets, overflow, keyboard, focus, status, recovery |
| C. Browser | Claude desktop built-in browser, Chrome 152.0.7977.167 engine, Linux x86_64, viewport emulation 320–1280 CSS px, no assistive technology | Runs B |
| D. Artifact page | The private design-system page on claude.ai | See DS-10 |
| E. Logic script | Node VM run of `bundle.js` with 13 assertions on `TR.format` and `TR.effectiveFields` | Money, zones, half-open intervals, consent intersection |

## Gates

| ID | Gate | Expected | Actual | Result |
|---|---|---|---|---|
| DS-01 | Identity and capability honesty | Real surface, version and mode stated | Claude Code desktop session. `DesignSync` exists but needs the user-started `/design-sync` flow, so it was not used. A private artifact was made from the Design System type. Mode: portable local reference mirrored to that artifact. Registration in a design picker is not verified | PASS |
| DS-02 | Token authority and schema | Complete valid export, no false DTCG claim | Surface A: 0 integrity errors, 104 tokens, every alias resolves, no cycles or duplicates, no raw colours in bundle files, every `var(--…)` defined. Export parses as JSON and declares `temuriset-tokens/1` as custom with a DTCG conversion note. DTCG is not claimed | PASS |
| DS-03 | Rendered colour and focus | Real combinations checked | Surface A: 47 of 48 token pairs meet their minimum; the decorative border fails as intended and is used only between groups. Surface B/C: every visible text node in 37 previews at 320, 320 with 200% text, 360, 768 and 1280 px: 185 runs, 3,115 elements, 0 contrast failures. Focus on a real keyboard return measured a white 2 px gap and `rgb(0,95,204)` 2 px ring. Limit: the audit reads text against the nearest opaque background; icon and ring adjacency rest on the token pairs and on inspection of *Foundations* | PASS |
| DS-04 | Primitive interaction | Anatomy, keyboard, focus, errors, loading, disabled reasons | Real key events: Tab then Enter opens `TR.Dialog`; ArrowRight and End move `TR.Tabs`, selection follows, Tab enters the panel. Busy button exposes `aria-busy`. Disabled reason visible and linked. Each primitive has a preview and usage page | PASS |
| DS-05 | Domain meanings | Financial basis, one raise with two inventions, current/planned and requirement distinctions | P01 script: one funding card, target appears once, contribution once, "2 inovasi terkait". F01 shows CURRENT 10 L/jam and PLANNED 20 L/jam. Three outcomes render "Siap dikirim", "Perlu konfirmasi", "Tidak cocok untuk mitra ini". Surface E: null reads "Belum ditentukan" and explicit zero reads `USD 0` | PASS |
| DS-06 | Focus and recovery | Error summary, dialog containment and return, retained input, status changes | Real keys: invalid step 3 focuses the summary, keeps `-1`, sets `aria-invalid`; following the link focuses the field. Dialog: initial focus on the title, Tab wraps Tutup to the last action and Shift+Tab wraps back, Escape closes without sending and returns focus to the opener. `TR.SaveState` is `role="status"`; a failed save kept the text and retry reached saved | PASS |
| DS-07 | Responsive and larger text | 320 reflow, 360, 768, 1280 and 200% text | 185 runs: 0 horizontal overflow, 0 targets under 24 px, 0 unnamed controls. Under 44 px only text links and the *Foundations* specimen links. 200% text at 320 px is root font-size in the frame. At 360 × 740 with 200% text the tab bar goes static and causes no overflow. Long words such as the page title may break at that size. Focus checked against the sticky bar on P01 and P04 at 360 × 740: only the tab panel, taller than the viewport, overlaps it. A last top-bar layout change, wide screens only, was rechecked on the five `TR.Screen` previews at 768 and 1280 px with 0 issues | PASS |
| DS-08 | Four assemblies | P01–P04 operable with labelled fixtures | Scripted clicks on surface C. P01: send, stale preflight kept the edited message and sent nothing, rechecked, sent. P02: save failure, retry, missing budget blocks send with its reason. P03: required answer enforced, "Belum dapat dipenuhi" accepted, 09:30 slot "Waktu sudah bentrok", 10:00 slot allowed, selected is not booked, failed replacement keeps the meeting and the selection. P04: v1 confirm publishes nothing, correction clears confirmations, v2 needs both, amount stays private, hide narrows at once | PASS |
| DS-09 | Independent state axes | Required combinations operable | *StateAxes* buttons produce quarantined file with saved answer; AVAILABLE scan with manual extraction and unreviewed content; UNKNOWN in a saved draft; stale preflight with retained message; confirmed relationship with private amount. Each changed only its own axes | PASS |
| DS-10 | Export inspection | Editor and exports checked separately | Local exports inspected: tokens JSON, manifest JSON, single-file guide, bundle, CSS, types, previews. Publish to the private artifact succeeded (version id 1793451079-003c); an agent read of the published manifest returned fingerprints equal to local `tokens.json`, `bundle.js`, `bundle.css` and `index.d.ts`. The page itself was not seen: see below | PASS for local exports; artifact page BLOCKED |
| DS-11 | Real consumption | Two primitives and a domain assembly, controlled token change | `consuming-sample/index.html` loads the same files and uses `TR.TextField`, `TR.Button`, `TR.InventionCard`; binding line reports 1.0.0-draft, "cocok". Setting `--tr-sys-color-action-primary-background` to `#7c2d12` moved both the primitive button and the card's button from `rgb(15,118,110)` to `rgb(124,45,18)`, and removing it restored both. Applied as a runtime CSS override. This is an imported reference, not inheritance. The pane was hidden during the check, so the transition did not tick; values were read with transitions off | PASS |
| DS-12 | Complete delivery | Manifest, inventory, validation, update procedure | Manifest with fingerprints, 31 component ids, this report and *Release and consuming* | PASS |

## Not run or blocked

| Check | Status | Why |
|---|---|---|
| Screen readers (NVDA, VoiceOver, TalkBack) | NOT RUN | No assistive technology here. Names, roles and states were checked in the DOM only |
| Status announcements as heard | NOT RUN | `role="status"` presence verified, spoken output not |
| Participant comprehension and task time | NOT RUN | Needs a study; no usability result is claimed, including for the UX principles |
| Real `prefers-reduced-motion` | NOT RUN | The workbench class applies the same rules: transitions 0 s observed. The media query itself was not emulated |
| Browser zoom and OS text-size settings | NOT RUN | 200% was tested as root font-size only |
| Forced colours | NOT RUN | A transparent outline exists for it; not exercised |
| Rendering and keyboard on the artifact page | BLOCKED | The built-in browser showed "Sign in to view this page" for the private artifact. No sign-in was attempted. The owner should open the link and check that the previews render |
| Firefox, Safari, real phones | NOT RUN | One engine only |
| Dark and client themes | NOT RUN | Deferred by the handoff |
| 72 product acceptance scenarios | NOT RUN | Need the application and server. This system does not pass them |

## Known limits

- These components display what they receive. They enforce no authorization, file scanning, booking or consent rule.
- Sessions without `sessionStorage` lose `TR.Disclosure` memory; it falls back to `defaultOpen`.
- P01 places three fixtures on one page to show three outcomes at once. The application shows one source request.
- Native radio and checkbox glyphs are sized in rem through CSS, but the row stays the real target.


## Release and consuming

## Binding record

| Field | Value |
|---|---|
| System | TemuRiset Design System |
| Version | 1.0.0-draft |
| Review status | Draft, not owner-approved |
| Mode | Portable local reference, mirrored to a private artifact made from the Design System type |
| Artifact | https://claude.ai/artifact/KU4iHKHaVL7QgL8bhSgfWV |
| Registered in a Claude design picker | Not verified |
| Published or organization default | No |
| Source of truth | `docs/generic/temuriset/design-system` in the repository |
| Namespace | `window.TR` |
| Token format | `temuriset-tokens/1`, custom JSON. DTCG compatibility is not claimed |
| Consuming artifact | `consuming-sample/index.html`, recorded in `consuming-sample/binding.json` |

## Files for the application stage

| File | Use |
|---|---|
| `project/tokens.json` | Token authority |
| `workbench/tokens.css` | Compiled tokens for a local page |
| `project/components/bundle.css`, `bundle.js`, `lib/*` | Runtime |
| `project/components/index.d.ts` | Props |
| `exports/temuriset-design-system.tokens.json` | Typed export with resolved values |
| `exports/temuriset-design-system.manifest.json` | Identity, inventory, fingerprints, limitations |
| `exports/temuriset-design-system.md` | Single-file guide |
| `consuming-sample/` | Smallest working example |

## Consuming it

**In a static page or prototype.** Copy `tokens.css`, `bundle.css`, `lib/` and `bundle.js`, load them in that order, and render `TR.*` as in `consuming-sample/index.html`. Add a `binding.json` naming the system, version and method, and show or test that `TR.version` matches it.

**In Claude Design or another Claude session.** Supply this reference with the handoff: attach the exports, or point the session at the private artifact if the account can open it. Record the mechanism actually used. A visually similar result is not binding evidence.

**In the Next.js application.** The bundle is one classic script reading `window.React`. Either load it as a script, or port components to typed modules and keep `TR.*` names and token names. Porting makes a new source, so record it as a deviation. Keep amounts as decimal strings across the API boundary. Server-side authorization, booking and consent rules stay on the server: these components display decisions and make none.

## Changing it

1. Change `project/tokens.json`, `project/components/bundle.*` or `tools/catalog.mjs`.
2. Run `node tools/build.mjs` from `docs/generic/temuriset/design-system`. It fails on broken aliases, missing tokens, raw colours or contrast below the minimum.
3. Serve the folder and open `workbench/index.html`. Run the audit on what changed and record results in the validation report.
4. Publish the changed `project/` files to the artifact.
5. Update each consumer deliberately, then recheck it. Nothing updates automatically.

Generated files: `workbench/tokens.css`, `workbench/previews.json`, `project/components/<Name>/README.md` and `preview.html` (except Cover), `project/guide/01-token-registry.md`, everything under `exports/`.

## Versioning

- Patch: fixes with no change to a public name or prop.
- Minor: added tokens, components or props.
- Major: renamed or removed public names, or a changed meaning.
- Keep a deprecated alias mapped until consumers migrate.

## Themes

A brand theme may replace values of `tr-ref-*` and `tr-sys-color-*`. It keeps every semantic name, and must pass every contrast pair in the build. A theme may not change a meaning: UNKNOWN stays distinct from FAIL, success stays reserved for real results, and privacy defaults do not move. Only the light theme exists in this release.


## Component contracts


### TR.Button

One action, named by its effect; at most one primary per task region.

**Anatomy.** Control (44 px comfortable minimum), optional icon or spinner, label, reason line when disabled.

**Consumer provides.** `children`, `intent` primary | secondary | danger, `onClick`, `type`, `icon`, `busy` + `busyLabel`, `disabledReason`, `fullWidth`, `id`, `form`, `describedBy`.

**States.** Default, hover, pressed, focus, busy (repeat clicks ignored, `aria-busy`), disabled-with-reason (dashed boundary, readable label, reason beside it).

**Keyboard and screen reader.** Native `<button>`, name from the visible label; Enter and Space work. Disabled uses `aria-disabled`, so it stays focusable and the reason is read through `aria-describedby`.

**Tokens.** `tr-comp-button-primary-*`, `tr-sys-color-action-*`, `tr-sys-color-disabled-*`, `tr-sys-size-controlComfort`, `tr-sys-radius-control`, `tr-sys-motion-feedback`.

**Responsive.** Labels wrap. Use `fullWidth` in narrow footers.

**Do.** Say the effect: "Kirim pitching", "Setujui untuk diskusi", "Konfirmasi waktu".

**Don't.** Do not write "OK" or "Lanjutkan" for a consequential action. Do not dim a disabled button with opacity or hide why it is disabled.


### TR.Link

Navigation by descriptive text, including contextual change links.

**Anatomy.** Underlined text, optional hidden context, external-route icon with hidden note.

**Consumer provides.** `href`, `children`, `external`, `context` (hidden text naming the field), `onClick` (in-page handling).

**States.** Default, hover, focus.

**Keyboard and screen reader.** Native `<a>`. `context` makes "Ubah" read as "Ubah judul inovasi". External links announce "(membuka situs lain)".

**Tokens.** `tr-sys-color-link`.

**Responsive.** Wraps inside running text.

**Do.** Label an external route as an external route.

**Don't.** Do not imply that opening an external application submitted an in-app pitch.


### TR.TextField

Labelled single-line input for text, email and decimal values.

**Anatomy.** Visible label, requiredness, hint, inline error, input, optional unit.

**Consumer provides.** `label`, `value`, `onChange(value)`, `hint`, `required`, `error`, `type` text | email | decimal, `prefix`, `suffix`, `id`, `name`, `autoComplete`.

**States.** Default, focus, invalid (2 px boundary plus text), filled.

**Keyboard and screen reader.** `<label for>`, `aria-describedby` joins hint and error, `aria-invalid` on error. Decimal uses `inputMode="decimal"` and stays text, so an empty value is never turned into zero.

**Tokens.** `tr-comp-field-*`, `tr-sys-size-controlComfort`, `tr-sys-radius-control`.

**Responsive.** Full width of its container; the unit stays beside the value.

**Do.** Keep nonsecret input on error and show the unit next to the number.

**Don't.** Do not use placeholder text as the label.


### TR.TextArea

Labelled multiline answer that keeps its text through errors and retries.

**Anatomy.** Label, hint, error, resizable area, optional character count.

**Consumer provides.** `label`, `value`, `onChange(value)`, `hint`, `required`, `error`, `rows`, `limit`, `id`.

**States.** Default, focus, invalid, over limit (text and colour).

**Keyboard and screen reader.** Count is linked by `aria-describedby` and is not a live region, so typing is not announced key by key.

**Tokens.** `tr-comp-field-*`, `tr-sys-color-danger-text`.

**Responsive.** Full width; the person can resize it vertically.

**Do.** Size it to the expected answer. State the limit in the hint or count.

**Don't.** Do not cut text at the limit; let the person edit it down.


### TR.Select

Native selection with a visible empty choice.

**Anatomy.** Label, hint, error, browser select.

**Consumer provides.** `label`, `value`, `onChange(value)`, `options` [{value, label, disabledReason}], `emptyLabel` (null removes it), `hint`, `required`, `error`.

**States.** Default, focus, invalid, disabled option with its reason in the text.

**Keyboard and screen reader.** Native keyboard and screen-reader behaviour.

**Tokens.** `tr-comp-field-*`.

**Responsive.** Full width; the platform picker opens on phones.

**Do.** Start empty when no choice has been made.

**Don't.** Do not silently pick a sector, currency or company.


### TR.ChoiceGroup

Mutually exclusive radio choices with whole-row targets.

**Anatomy.** Fieldset, legend, hint, error, rows with label, hint and optional disabled reason.

**Consumer provides.** `legend`, `options` [{value, label, hint, disabledReason}], `value`, `onChange(value)`, `hint`, `required`, `error`, `id` (first radio), `name`.

**States.** Default, hover, focus, selected (2 px boundary plus filled radio), disabled with reason, invalid.

**Keyboard and screen reader.** Native radios: Tab enters the group, arrows move within it. The row is the `<label>`.

**Tokens.** `tr-sys-color-selected-*`, `tr-sys-color-border-control`, `tr-sys-size-borderSelected`.

**Responsive.** One column at every width, so long labels stay readable.

**Do.** Use for support type, relationship type and current or planned status.

**Don't.** Do not delete unrelated saved drafts when the purpose changes.


### TR.Checkbox

Independent yes or no choice; consent stays unchecked until really given.

**Anatomy.** Row label, checkbox, hint, reason. `Checkbox.Group` adds fieldset and legend.

**Consumer provides.** `label`, `checked`, `onChange(checked)`, `hint`, `disabledReason`, `error`, `id`. Group: `legend`, `hint`, `children`.

**States.** Unchecked, checked, focus, disabled with reason, invalid.

**Keyboard and screen reader.** Native checkbox; Space toggles. The row is the `<label>`.

**Tokens.** `tr-sys-color-selected-*`, `tr-sys-size-borderSelected`.

**Responsive.** One column.

**Do.** Ask for one named permission at a time.

**Don't.** Do not precheck a blanket permission for private files or publication.


### TR.FieldError

Plain correction message tied to one field.

**Anatomy.** Icon, hidden "Kesalahan:" prefix, message.

**Consumer provides.** `id`, `children`, `code` (stable error code stored as `data-code`).

**States.** Single state; shown only when the field is invalid.

**Keyboard and screen reader.** Linked from the field through `aria-describedby`. The same words appear in `TR.ErrorSummary`.

**Tokens.** `tr-sys-color-danger-text`.

**Responsive.** Wraps.

**Do.** Say what to fix: "Biaya maksimum tidak boleh lebih kecil dari biaya minimum."

**Don't.** Do not show stack traces, HTTP codes or another party's data. Do not erase the value.


### TR.ErrorSummary

Focused list of what stopped a submission, linking to each field.

**Anatomy.** Focusable region, heading, linked list, optional retry.

**Consumer provides.** `errors` [{fieldId, message}], `focusKey` (change it on each failed attempt), `title`, `children`, `retry` {label, onClick}, `id`.

**States.** Field errors; global retry without a field target.

**Keyboard and screen reader.** Focus moves to the region only when `focusKey` changes, so a background save never steals focus. Each link focuses its field.

**Tokens.** `tr-sys-color-danger-*`, `tr-sys-size-borderSelected`.

**Responsive.** Full width at the top of the task.

**Do.** Repeat the words of the inline errors.

**Don't.** Do not replace it with a disappearing toast.


### TR.Dialog

Modal for one short decision, with safe focus handling.

**Anatomy.** Title, close button, body, primary and secondary effect.

**Consumer provides.** `open`, `onClose`, `title`, `children`, `primary` {label, onClick, busy, busyLabel, intent, disabledReason}, `secondary` {label, onClick}, `initialFocusId`, `returnFocusId`.

**States.** Closed, open, busy, recoverable error shown inside the body.

**Keyboard and screen reader.** Native modal `<dialog>`, labelled by its title. Initial focus lands on the title unless `initialFocusId` is set. Tab and Shift+Tab stay inside. Escape closes without committing. Focus returns to the opener.

**Tokens.** `tr-sys-radius-dialog`, `tr-sys-shadow-dialog`, `tr-sys-color-overlay`.

**Responsive.** Width caps at 40 rem; the body scrolls and the footer stays reachable.

**Do.** Use for a short confirmation, such as sharing one document version.

**Don't.** Do not put multi-step work in a dialog. Prefer an ordinary page. It owns focus, not authorization.


### TR.Disclosure

Keeps supporting detail one click away.

**Anatomy.** Summary toggle with chevron, region.

**Consumer provides.** `label`, `children`, `defaultOpen`, `storageKey` (keeps the state when returning within the session).

**States.** Collapsed, expanded, focus.

**Keyboard and screen reader.** Native `<details>`; Enter and Space toggle and the expanded state is exposed.

**Tokens.** `tr-sys-color-action-secondary-foreground`, `tr-sys-color-border-decorative`.

**Responsive.** Full width.

**Do.** Use for score detail, provenance and calculation notes.

**Don't.** Never hide a blocking gap inside it.


### TR.Tabs

Related views inside one pitch workspace.

**Anatomy.** Tab list, tabs, one panel.

**Consumer provides.** `label`, `tabs` [{id, label, content}], `value`, `onChange(id)`.

**States.** Default, hover, focus, selected (2 px bar, weight and surface).

**Keyboard and screen reader.** ARIA tabs with automatic activation. Arrow keys, Home and End move between tabs; Tab moves to the panel.

**Tokens.** `tr-sys-color-selected-*`, `tr-sys-color-border-control`.

**Responsive.** Tabs wrap to more rows, so every tab stays reachable without hidden scrolling.

**Do.** Keep a logical heading in each panel.

**Don't.** Do not use tabs for ordered steps; use `TR.Steps`.


### TR.Status

A domain result in words, supported by icon and colour.

**Anatomy.** Label with icon; with `children` it becomes a notice with an explanation.

**Consumer provides.** `label`, `tone` neutral | success | danger | warning | action, `icon` (null removes it), `children`, `live` true | alert.

**States.** Five tones. Pending work stays neutral; UNKNOWN is warning with a question mark; FAIL is danger with a cross.

**Keyboard and screen reader.** Meaning is always in the text. `live` adds `role="status"` or `alert` without moving focus.

**Tokens.** `tr-sys-color-success-*`, `tr-sys-color-danger-*`, `tr-sys-color-warning-*`, `tr-sys-color-selected-*`, `tr-sys-color-surface-subtle`.

**Responsive.** Wraps.

**Do.** Pass the real result from the domain and add one sentence on what it means.

**Don't.** Do not derive PASS or approval from colour. Do not paint pending work as success.


### TR.EmptyState

Explains why nothing is here and what to do next.

**Anatomy.** Icon, heading, reason, action.

**Consumer provides.** `kind` noInventions | noMatches | closedIntake | denied, or `title` + `children`; `action`.

**States.** Four distinct reasons.

**Keyboard and screen reader.** Heading plus text; the action is an ordinary control.

**Tokens.** `tr-sys-color-surface`, `tr-sys-color-border-decorative`.

**Responsive.** Centered, one column.

**Do.** Offer a way forward, such as relaxing a filter on purpose.

**Don't.** Do not fill the space with zero amounts, invented trends or recommendations. A denied state never names a protected title.


### TR.SaveState

Says truthfully whether work is saved, and where.

**Anatomy.** Icon or spinner, label, recovery note and retry when failed.

**Consumer provides.** `state` local | saving | saved | failed | conflict, `location` demo | server, `savedAt`, `timeZone`, `onRetry`.

**States.** Belum tersimpan, Menyimpan, Tersimpan di demo ini, Gagal menyimpan, Versi sudah berubah.

**Keyboard and screen reader.** The label is `role="status"`, announced once per state and never per keystroke; focus does not move.

**Tokens.** `tr-sys-color-success-text`, `tr-sys-color-danger-text`, `tr-sys-color-warning-text`.

**Responsive.** Wraps; keep it beside the page heading.

**Do.** State the location. A demo says "Tersimpan di demo ini".

**Don't.** Do not draw a check before the save is acknowledged, or while offline.


### TR.ContextSwitcher

Shows and changes the personal or organization context a person acts in.

**Anatomy.** Labelled select; read-only line before consequential actions.

**Consumer provides.** `value`, `onChange(id)`, `options` [{id, kind personal | organization, name, disabledReason}], `readOnly`, `actionLabel`, `label`, `hint`.

**States.** Personal, organization, unavailable with a safe reason, read-only.

**Keyboard and screen reader.** Native select. Read-only form is plain text.

**Tokens.** `tr-comp-field-*`.

**Responsive.** Sits in the top bar; full width on phones.

**Do.** Show the read-only line before send, decide and confirm.

**Don't.** Do not treat a selection as authority: the server checks membership. Do not force a person to create an organization.


### TR.NextStep

Tells a person whose turn it is and the one thing to do now.

**Anatomy.** Responsibility label, heading, reason, optional due date, one action.

**Consumer provides.** `who` you | other, `title`, `children`, `due`, `action`.

**States.** Menunggu Anda (selected surface, 2 px boundary), Menunggu pihak lain (plain surface, no action needed).

**Keyboard and screen reader.** Section labelled by its heading. Responsibility is in words.

**Tokens.** `tr-sys-color-selected-*`, `tr-sys-size-borderSelected`.

**Responsive.** Full width at the top of the task, before supporting detail.

**Do.** Open every workspace with it. Write one sentence and one effect-named action.

**Don't.** Do not stack several next steps. When it waits on someone else, say so and ask for nothing.


### TR.Steps

Progress through a fixed-order editor.

**Anatomy.** Current step sentence, ordered list with marks.

**Consumer provides.** `steps` [{id, label, done}], `current`, `onSelect(id)`, `label`.

**States.** Done (check plus hidden text), current (filled mark, `aria-current="step"`), to do.

**Keyboard and screen reader.** Navigation landmark with an ordered list. Other steps are buttons when `onSelect` is given.

**Tokens.** `tr-sys-color-action-primary-*`, `tr-sys-color-selected-*`.

**Responsive.** Grid wraps to one column on narrow screens; the sentence always names the current step.

**Do.** Allow jumping back without losing input.

**Don't.** Do not use it for resumable unordered work; that is a task list.


### TR.SummaryList

Check-your-answers list with a contextual change link per row.

**Anatomy.** Term, value, change link.

**Consumer provides.** `rows` [{id, label, value, onChange}].

**States.** Read-only row; row with change link.

**Keyboard and screen reader.** `<dl>`. Each link reads "Ubah <field>".

**Tokens.** `tr-sys-color-border-decorative`, `tr-sys-color-link`.

**Responsive.** Stacks below 48 rem; three columns above.

**Do.** Use before every send, publication and confirmation.

**Don't.** Do not put private evidence in a public preview.


### TR.InventionCard

One invention, led by problem, current solution and what it needs.

**Anatomy.** Category band or image, title, manager, facts, scoped money, reasons, gap, one action.

**Consumer provides.** `title`, `category`, `image` {src, alt}, `manager`, `problem`, `solution`, `maturity`, `support`, `financial` (FinancialScope props), `facts`, `reasons`, `gap`, `action`. Pass an authorized projection only.

**States.** With or without image, with or without gap, noncash.

**Keyboard and screen reader.** `<article>` with a heading. The fallback band is labelled text; a missing image is not a problem state.

**Tokens.** `tr-sys-color-surface`, `tr-sys-color-selected-surface`, `tr-sys-radius-surface`.

**Responsive.** Fits a 18 rem column; content stacks.

**Do.** Keep a short reason and one action. Label planned functionality.

**Don't.** Do not add ratings, follower counts, funding progress or invented photos.


### TR.FundingRequestCard

One company raise, even when several inventions support it.

**Anatomy.** Band, company, entity label, facts, target, contribution, linked inventions, one action.

**Consumer provides.** `company`, `proposedEntity`, `stage`, `form`, `purpose`, `currency`, `target`, `desiredMin`, `desiredMax`, `partialAccepted`, `inventions` [titles], `reasons`, `gap`, `action`.

**States.** Existing or named entity, company not yet formed, with or without contribution range.

**Keyboard and screen reader.** `<article>` with a heading; the linked count is text.

**Tokens.** As `TR.InventionCard`.

**Responsive.** Fits a 18 rem column.

**Do.** Show the target and contribution as separate labelled amounts.

**Don't.** Do not repeat the raise per invention, assume a formed company or derive shares or valuation.


### TR.FinancialScope

An amount that always says what it is an amount of.

**Anatomy.** Subject, amount with unit, period, scope, estimate date, assumptions, optional fields.

**Consumer provides.** `subject` project | companyTarget | contribution | investorCheck | partner | license, `currency`, `min`, `max` (decimal strings; null means unknown), `period`, `scope`, `estimateDate`, `assumptions`, `noncash`, `terms`, `compact`, `edit`, `label`.

**States.** Range, single value, unknown ("Belum ditentukan"), noncash.

**Keyboard and screen reader.** Text only. Amount and unit never split across lines.

**Tokens.** `tr-sys-type-amount`, `tr-sys-color-surface-subtle`.

**Responsive.** Amount stays together; the period wraps to the next line.

**Do.** Keep duration beside the range. Compare only like with like.

**Don't.** Do not convert currency, show funding progress or percentages, or render unknown as zero.


### TR.RequirementRow

One requirement, its result in words and what to do about it.

**Anatomy.** Label, result, stage, mandatory flag, verification mode, reason, source, action.

**Consumer provides.** `label`, `result` PASS | FAIL | UNKNOWN | NOT_APPLICABLE, `stage` SUBMISSION | DISCUSSION | PILOT | COMMERCIALIZATION, `mandatory`, `mode` DECLARATION | DOCUMENT_PRESENT | REVIEWER_CONFIRMED, `reason`, `source`, `action`. Render inside `<ul class="tr-reqs">`.

**States.** Four results, plus later-stage work drawn neutral with "Tidak menghalangi pengajuan".

**Keyboard and screen reader.** List item with a heading; results are text.

**Tokens.** Status tones, `tr-sys-color-border-decorative`.

**Responsive.** Result wraps under the label.

**Do.** Show gaps first and say the next action.

**Don't.** Do not turn UNKNOWN into FAIL, or a planned capability into PASS.


### TR.FactSource

Whether a fact exists now, and how far it has been checked.

**Anatomy.** Value, timing tag, provenance tag, review scope, source link.

**Consumer provides.** `value`, `timing` CURRENT | PLANNED | REQUESTED, `provenance` SOURCE_REPORTED | SELF_DECLARED | PROVIDED | REVIEWED | UNKNOWN, `reviewScope`, `sourceHref`, `sourceLabel`.

**States.** Planned and requested tags use a dashed boundary. Only REVIEWED gets a success check.

**Keyboard and screen reader.** Text labels; the source link carries hidden context.

**Tokens.** `tr-sys-color-border-control`, `tr-sys-color-success-*`.

**Responsive.** Wraps.

**Do.** Put it next to the claim it qualifies.

**Don't.** Do not let a source link reveal a protected title. An upload is not a review.


### TR.DocumentItem

A document with file safety, text reading, evidence review and sharing kept apart.

**Anatomy.** Title, version, three independent status axes, sharing sentence, action.

**Consumer provides.** `title`, `version`, `file`, `extraction`, `review`, `grant` {recipient, version, revoked}, `denied`, `action`.

**States.** Every combination of the three axes; denied (no title shown); revoked with its truthful limit.

**Keyboard and screen reader.** `<dl>` of axis names and results. Each result is text.

**Tokens.** Status tones, `tr-sys-color-border-decorative`.

**Responsive.** Axes form one column on phones.

**Do.** Say the sharing limit: one named recipient, one version.

**Don't.** Do not let an upload imply review, or a quarantined file open. Never show a protected title to someone without access.


### TR.RevisionItem

One revision question, its reason, and an answer that may honestly be no.

**Anatomy.** Round and item heading, required flag, question, reason, due date, response, explanation, attachments, review result.

**Consumer provides.** `round`, `index`, `question`, `reason`, `required`, `due`, `value` {response, text}, `onChange(value)`, `attachments`, `review`, `error`, `id`.

**States.** Required, optional, answered, invalid, reviewed.

**Keyboard and screen reader.** Uses `TR.ChoiceGroup` and `TR.TextArea`.

**Tokens.** As its parts.

**Responsive.** One column.

**Do.** Keep each answer in place when one upload fails.

**Don't.** Do not treat "Perlu diskusi" or "Belum dapat dipenuhi" as approval or as an error.


### TR.ScheduleSlotList

Proposed times in a person's own zone; a selection is not a booking.

**Anatomy.** Agenda, slot radios with date, time, zone and duration, the other party's time, actions.

**Consumer provides.** `slots` [{id, start (UTC ISO), minutes, conflict}], `zone`, `otherZone`, `selectedId`, `onSelect(id)`, `confirmedId`, `state` open | expired | superseded | cancelled, `onConfirm`, `onPropose`, `busy`, `agenda`, `error`.

**States.** Open, selected (not confirmed), confirmed, conflict, expired, superseded, cancelled.

**Keyboard and screen reader.** Native radios. Each slot reads full date, time and zone.

**Tokens.** `tr-sys-color-selected-*`, Status tones.

**Responsive.** One column; long dates wrap.

**Do.** Show the IANA-derived zone label and both parties' times.

**Don't.** Do not say booked until acceptance succeeds on the server.


### TR.PartnershipConsent

Both parties confirm one exact version; only what both allow can go public.

**Anatomy.** Version heading, state, summary, field rows with each party's choice and result, actions.

**Consumer provides.** `version`, `type`, `summary`, `fields` [{id, label, value}], `mine` {name, selected, confirmedVersion}, `other` {name, selected, confirmedVersion}, `restricted` [ids], `onToggle(id, checked)`, `onConfirm`, `onRequestChange`, `onRestrict(id)`, `busy`, `readOnly`, `error`.

**States.** Draf, Menunggu konfirmasi, Dikonfirmasi kedua pihak, field private, field public, field hidden by a live restriction.

**Keyboard and screen reader.** Checkboxes before you confirm; plain text after. Results are text with icons.

**Tokens.** Status tones, `tr-sys-color-border-decorative`.

**Responsive.** One column per field.

**Do.** Say that hiding a field cannot recall a download.

**Don't.** One confirmation is never mutual. A new version inherits no confirmation. Amounts stay private by default.


### TR.VersionConflict

Something changed underneath; the person's draft is safe.

**Anatomy.** Warning, what changed, current version, retained draft, recovery actions.

**Consumer provides.** `what`, `currentVersion`, `draft`, `onRefresh`, `refreshLabel`, `onCopy`, `onCompare`.

**States.** Single state with optional actions.

**Keyboard and screen reader.** Labelled group. Place focus on it or announce it after the failed action.

**Tokens.** `tr-sys-color-warning-*`, `tr-sys-color-surface-subtle`.

**Responsive.** Actions wrap.

**Do.** Offer one clear recovery and keep the text.

**Don't.** Do not merge consequential changes silently or reveal protected actor or source details.


### TR.Screen

The app frame: acting context, navigation, title, next step, task and support.

**Anatomy.** Skip link, top bar with wordmark, provenance and context, heading, main column, supporting column, phone tab bar.

**Consumer provides.** `persona` inovator | mitra, `current`, `onNavigate(id)`, `title`, `subtitle`, `back`, `save`, `next`, `aside`, `context`, `provenance`, `children`.

**States.** Inovator or Investor/Mitra navigation; phone bar with Lainnya; static bar when large text would make it cover content.

**Keyboard and screen reader.** Skip link, `<main>`, labelled navigation, `aria-current="page"`.

**Tokens.** `tr-sys-layout-*`, `tr-sys-color-selected-*`.

**Responsive.** Below 48 rem a bar shows four destinations plus Lainnya and support stacks after the task. Above it, five top links and a 20 rem aside.

**Do.** Put the active task before the timeline and context in reading order.

**Don't.** Do not add a third persona or top-level pages for states.


### TR.Icon

Small own stroke set; always beside text unless the control has a name.

**Anatomy.** Inline SVG, 24 grid, `currentColor`, hidden from assistive technology.

**Consumer provides.** `name`, `size` small.

**States.** None.

**Keyboard and screen reader.** `aria-hidden`. Meaning comes from the neighbouring text.

**Tokens.** `tr-sys-size-icon`, `tr-sys-size-iconSmall`.

**Responsive.** Sized in rem.

**Do.** Support a word.

**Don't.** Do not use an icon as the only signal of a status.
