# Validation report

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
