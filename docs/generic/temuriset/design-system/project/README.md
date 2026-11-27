TemuRiset helps inventors find investors and partners who can advance an invention. This system exists so every screen answers two questions within seconds: **what can I do next, and what does the current evidence mean?** It serves independent inventors and individual investors as comfortably as organization teams, in calm, plain Indonesian.

Release **1.1.0-draft** · review status: draft, not owner-approved · product contract: TemuRiset PRD generic v1.1 · namespace `window.TR` · React 18.3.1 · light theme only. Evidence is in *Validation report*; how the application stage binds to this system is in *Release and consuming*.

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
- **Type.** IBM Plex Sans via `--font-sans`, self-hosted from `project/fonts/` (load `fonts/fonts.css` before the tokens), with system sans as the fallback. Three weights ship: 400, 600 and 700. Style classes are `tr-sys-type-body`, `-body-strong`, `-label`, `-support`, `-support-strong`, `-heading-sm`, `-heading-md`, `-heading-lg`, `-display`, `-amount`. `-display` is the one page title per screen. Sizes are rem, so text settings scale them. `tr-sys-type-support` never carries a primary action or a critical gap.
- **Space and shape.** Spacing steps 4 to 64 behind aliases: `tr-sys-space-controlGap`, `tr-sys-space-stack`, `tr-sys-space-section` (`sectionWide` from 48 rem), `tr-sys-layout-gutter` (`gutterWide` from 48 rem). Radii: `tr-sys-radius-control` 6, `tr-sys-radius-surface` 8, `tr-sys-radius-dialog` 12.
- **Layout.** Maximum width `tr-sys-layout-contentMax`, long prose at `tr-sys-layout-readingMeasure`. Below 48 rem one column; above it an optional 20 rem supporting column. No cards inside cards, no big hero areas, no decorative dashboards.
- **Targets and focus.** Common controls are at least `tr-sys-size-controlComfort` (44 CSS px, a product preference; AA asks 24 with exceptions). Focus is a 2 px white gap, then a 2 px blue ring. Selected states always add a non-colour cue: `tr-sys-size-borderSelected`, weight, or a check.
- **Elevation.** `tr-sys-shadow-dialog` for `TR.Dialog` only. Everything else stays flat.
- **Motion.** `tr-sys-motion-feedback` for state feedback only. Reduced motion removes it, and the loading label keeps saying work is in progress. No animated counters, progress charts or pulses.

## Iconography

A small own stroke set (24 grid, 2-unit round stroke, `currentColor`), shipped in the bundle as `TR.Icon`, with no icon library or licence. Icons always support a word; the only exception is the dialog close button, which has the accessible name "Tutup". Sizes are `tr-sys-size-icon` and `tr-sys-size-iconSmall`. `TR.Logo` is the mark (two paths meeting at one node: the inventor and the investor who meet) beside the word "TemuRiset" as text; the mark is decorative and the word names it. Photos sit in `tr-media` frames (4:3, `tr-sys-radius-media`) only when an owner published them; without one, cards use a labelled category band, and a missing image is not a problem state. Never invent a product photo, investor credential, rating or funding chart.

## Components

Shared inventory (`TR.*`): Button, Link, TextField, TextArea, Select, ChoiceGroup, Checkbox, FieldError, ErrorSummary, Dialog, Disclosure, Tabs, Status, EmptyState, SaveState, ContextSwitcher, InventionCard, FundingRequestCard, FinancialScope, RequirementRow, FactSource, DocumentItem, RevisionItem, ScheduleSlotList, PartnershipConsent, VersionConflict.

Intentional additions: **NextStep** (the product asks every view to emphasise the next action and whose turn it is, so it needs one owner), **Steps** (the four-step editor), **SummaryList** (check-your-answers with change links), **Screen** (shared frame, so patterns are not unnamed copies), **Icon** (the icon set). Helpers: `TR.format`, `TR.effectiveFields`. `TR.demo` holds fictional fixtures and test controls and is not for production.

Pattern pages, which compose only the components above: *PatternDiscovery* (P01), *PatternPortfolio* (P02), *PatternRevisionSchedule* (P03), *PatternRelationship* (P04), plus *Foundations* and *StateAxes*. Their dashed "Kontrol uji" panels are test controls, not product UI.

## Using it in a page

Load, in order: the compiled tokens CSS, `components/bundle.css`, React 18.3.1 and ReactDOM (`components/lib/`), then `components/bundle.js`. Render with `React.createElement(TR.Button, {…})`. Put `lang="id"` on the document. Pass amounts as decimal strings and `null` for unknown; let components format them. Pass authorized projections only: these components display what they receive and enforce no access rule. Report a save or decision as done only after the server acknowledges it.

## Fonts

IBM Plex Sans 2.0.0 from the `@ibm/plex-sans` package, Latin1 split files, unmodified, under the SIL Open Font License 1.1 (`project/fonts/OFL.txt`; "Plex" is a Reserved Font Name, so the files are never renamed or modified here). Latin1 covers Indonesian and English. SHA-256:

| File | SHA-256 |
|---|---|
| `IBMPlexSans-Regular-Latin1.woff2` | `bdb53f2af84b15e0a742428f5e199dacc3e6fd60776f0aebd9f700e2c97c960f` |
| `IBMPlexSans-SemiBold-Latin1.woff2` | `8251b7fc61b580c2f52550fa69b3c49fb94fc333815ad301ca6b1f6d15420f85` |
| `IBMPlexSans-Bold-Latin1.woff2` | `098277f28ccff8b6128068edc357d59cb9cb3d4e3d15d77e7757c85ba1162c73` |

Release 1.1 (owner decision, 27 November 2026) replaces the 1.0 rules "system sans, no font downloads" and "no logo asset". It also adds `tr-chips`, `tr-list`/`tr-listrow`, `tr-listdetail`, `tr-toolbar` and `tr-media`, and folds in the application's deviations D1 (`:has(input:checked)` choices), D2 (whole words in the tab bar), D11 (`plus` icon) and D16 (compact context bar).
