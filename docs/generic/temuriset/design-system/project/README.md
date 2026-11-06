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
