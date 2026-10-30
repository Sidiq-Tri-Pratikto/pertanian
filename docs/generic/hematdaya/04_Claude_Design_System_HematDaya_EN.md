# HematDaya — Claude Design System Handoff

Handoff version: 1.0. Prepared October 24, 2026, Asia/Jakarta.
Product contract: HematDaya PRD Generic 1.2. Specification language: English. Product UI examples: Indonesian.
Requested system name: **HematDaya Design System**. Requested initial system version: **1.0.0-draft** until its checks and review status are recorded.

**Attach this file alone for the design-system stage.** It contains the necessary product context, foundations, component contracts, example data, validation gates, delivery requirements, and ready prompt. It does not require access to the repository, earlier chats, another attachment, a live meter, or credentials. Build the reusable design system and a component/pattern workbench first. The full application prototype is a subsequent stage.

This file requests future work in Claude Design; it is not an existing component library, published Claude design system, native application, or completed accessibility audit. All implementation/runtime checks start **not run**. Document-level colour checks below have a narrower, explicitly stated meaning.

## 1. Objective and authority

Create a coherent, reusable **product design system**, including semantic tokens, component behaviour, content rules, data-visualization patterns, responsive/accessibility rules, and an inspectable implementation reference. A mood board, colour palette, brand presentation, or gallery of disconnected components is insufficient.

The owner wants the same foundation to serve household, business, and industrial electricity-monitoring applications. The accepted engineering direction is a modular monolith with shared domain rules, optional capabilities, adapters, bounded product composition, and reproducible releases. The design system must support this reuse through shared component and semantic-token contracts. It does not require a plugin framework, universal UI builder, tenant administration, billing, or client-specific calculation branches.

Authority has two dimensions:

1. **Product behaviour:** latest explicit owner decision, then the product contract summarized here and represented by PRD 1.2. A visual choice cannot change measurement meaning, optionality, permissions, or arithmetic.
2. **Visual and interaction implementation:** owner-approved design-system release, then its documented components and patterns. The palette in this brief is a proposed seed to refine with evidence; do not claim it is a pre-existing approved brand.

Name the generated system, record its version and review status, and record the actual runtime. Continue through reversible design decisions and explain them. Do not wait for approval to complete the requested local/private system; leave unresolved choices and unavailable platform functions clearly recorded. Publishing or setting an organization-wide default is a separate action requiring the owner's explicit instruction.

## 2. Product context that the system must preserve

HematDaya helps a person understand recorded electricity within a declared measurement scope, inspect changes, and choose what to investigate. It only **monitors and advises**. There are no power switches, relays, AC remotes, mains cutoff, thermostat controls, arrival automation, or unattended actions.

The same UI primitives must work for a refrigerator, router, pump, lamp, television, oven, compressor, production machine, circuit, group of loads, or whole-location meter. AC is one possible category and is never required. A category or an offline source does not establish equipment identity, a fault, waste, occupancy, or whether the equipment is off.

Use three persistent labelled destinations: **Beranda**, **Perangkat**, **Saran**. Settings, imports, scope resolution, evidence, schedules, and output metrics are secondary routes. “Perangkat” includes circuits and groups with clear scope labels. Do not introduce a fourth top-level production, integrations, reports, or AI destination.

Core user questions are:

- What energy was recorded, in what period, and for which measured assets?
- What is the estimated energy cost if an applicable tariff is known?
- Which measured contributor is largest within a valid selection?
- What changed against a comparable earlier period?
- What evidence and limitations support the observation?

Schedules and output/intensity metrics are optional. Households must receive complete core value without production inputs or operating hours. Industrial users can also use the core without them. Tariff is optional; missing tariff means unknown cost, not free electricity. Context selection changes examples, not permissions or calculations.

The product's shared conceptual model is **Site → Asset → Measurement source**, with explicit source bindings and measurement boundaries. A physical measurement scope and temporal data completeness are different facts. Main-meter and submeter values can overlap and cannot be blindly added.

Initial product language is Indonesian, currency IDR, and timezone Asia/Jakarta. Design-system documentation, component names, token names, and engineering notes may be English. All example product controls, messages, field labels, and chart descriptions must use natural Indonesian.

## 3. Claude Design workflow and actual capability boundaries

Official guidance checked October 24, 2026 describes creating design systems from documents/assets and synchronizing an existing React component library through Claude Code. That makes this brief source material for a newly authored system; it does not establish that a code library already exists. Use the design-system functionality available in the current session. If it is unavailable, produce a portable system document, token export, component reference, and runnable workbench where supported; label this as a local system reference rather than claiming successful registration in Claude's design-system interface. [Official design-system guide](https://support.claude.com/en/articles/14604397-set-up-your-design-system-in-claude-design).

The same guide currently identifies a limitation in keyboard access to live component previews. Test interactive controls in a separately runnable workbench when the design-system preview container cannot support the check; record the container limitation and the actual test surface separately. Do not mark product keyboard access passed from a static preview. [Official design-system guide](https://support.claude.com/en/articles/14604397-set-up-your-design-system-in-claude-design).

Interactive artboards and HTML/project exports depend on the session. Request an interactive component workbench and inspect supported exports. An exported web component is not automatically a React Native component or a verified Expo project. Document browser/native mappings instead of promising APK/IPA output. [Official prototype tutorial](https://academy.claude.com/tutorials/using-claude-design-for-prototypes-and-ux).

Keep the artifact private. Do not share externally, publish it, change an organization default, connect accounts, request real credentials, buy assets, or deploy a service. Creating a private design-system artifact and a local workbench is the authorized task. Automatic inheritance must be verified in a consuming project; matching colours in one screenshot does not establish a binding.

## 4. UX principles and information hierarchy

Design for comprehension and recovery before visual novelty. The normal reading order is **period and measurement scope → recorded kWh → qualified optional cost → completeness/freshness → contribution → eligible observation**. Important qualifications remain adjacent to the values they change. Calculation metadata is progressively disclosed.

Use calm, precise utility styling: warm neutral canvas, readable dark text, restrained green accent, direct labels, and simple aligned charts. Green may mark a selected control or confirmed save; it must not declare that a refrigerator is efficient or that consumption is desirable. Amber signals a condition needing attention, not ordinary continuous use. Red belongs to rejected input or failed operations, not a large energy contributor.

Prefer flat information groups, modest borders, clear headings, and ample touch areas. Avoid repeated cards inside cards, neon control-room styling, decorative gauges, oversized promotional hero areas, fake efficiency scores, carbon/savings claims, guilt language, streaks, and an AC remote aesthetic. A system should help a user inspect a number, not make unknown data look certain.

Use one primary action per task step, visible selected states beyond colour, predictable back/cancel, and distinct draft/confirmed state. A disabled control needs an inspectable reason. A successful-looking state cannot precede acknowledgment. Error, retry, and accessible status behaviour are part of the component definition.

These decisions build on the product's existing UX research direction: understandable kWh and qualified costs, direct comparisons, explicit missingness, progressive evidence, and neutral task testing. They remain design hypotheses for the intended users. See the primary [energy-feedback study](https://www.wren.uk.com/images/documents/publications/hargreaves_smart_meters.pdf), [graphical-perception research](https://hci.stanford.edu/publications/2010/crowd-perception/heer-chi2010.pdf), and [missing-data research](https://cmci.colorado.edu/visualab/papers/song_VIS_2018.pdf). No HematDaya user-study or savings outcome is asserted.

## 5. Token architecture and naming

Use three layers with explicit aliases:

| Layer | Purpose | Example |
|---|---|---|
| Primitive | Raw palette, dimension, duration, weight | `palette.forest.700`, `space.4` |
| Semantic | Meaning and intended usage | `color.action.primary.background`, `color.text.secondary`, `size.target.minimum` |
| Component | Only a justified component-specific mapping | `button.primary.background` → `color.action.primary.background` |

Components consume semantic or component aliases; they do not repeat unexplained raw hex values, spacing, or durations. Different contexts consume the same meanings. A household preset cannot redefine missing data as zero or make warning colour mean a different thing from the industrial preset.

Token names are stable, English, and platform-neutral. Keep values and units explicit; unitless numbers must have a declared meaning. Maintain a complete resolved token registry plus alias references, with no circular references, missing aliases, duplicate names, or conflicting values. Do not create a token for every individual screen position.

Generate a machine-readable token export and a human-readable registry from the same authority. Use a documented schema and declare any standard-format version actually supported; do not label a custom JSON object standards-compliant without validation. Preserve semantic IDs when mapping to CSS custom properties and future native theme objects. A valid JSON export and an explanatory table are both required; a screenshot of swatches is insufficient.

## 6. Initial light-theme palette and contrast contract

Use this seed as the coherent starting point. A refinement is allowed when its reason and affected component checks are recorded. If a seed colour changes, update aliases, examples, computed contrast, and export together.

| Primitive colour | Seed value | Intended semantic role |
|---|---|---|
| `palette.neutral.canvas` | `#F6F7F3` | Main canvas |
| `palette.neutral.white` | `#FFFFFF` | Surface and text on dark primary actions |
| `palette.neutral.ink` | `#17221D` | Primary text |
| `palette.neutral.secondary` | `#4C5F55` | Supporting text, labels that remain readable |
| `palette.neutral.borderDecorative` | `#CAD4CC` | Decorative grouping only |
| `palette.neutral.borderControl` | `#6E8175` | Essential control boundaries on specified light surfaces |
| `palette.forest.700` | `#1F6947` | Primary action, selected emphasis, current series |
| `palette.forest.800` | `#175237` | Primary hover where hover exists |
| `palette.forest.900` | `#123F2B` | Primary pressed |
| `palette.forest.100` | `#E5F0E8` | Selected/success supporting surface |
| `palette.blue.700` | `#145CC5` | Focus and informational text |
| `palette.blue.50` | `#EDF3FF` | Informational supporting surface |
| `palette.blue.reference` | `#536B91` | Historical/reference series with a second non-colour distinction |
| `palette.amber.800` | `#7A4B00` | Attention text |
| `palette.amber.50` | `#FFF3D6` | Attention supporting surface |
| `palette.red.700` | `#A32929` | Error text/border |
| `palette.red.50` | `#FDEDEC` | Error supporting surface |

Minimum semantic aliases to resolve: `color.background.canvas`, `color.background.surface`, `color.text.primary`, `color.text.secondary`, `color.border.decorative`, `color.border.control`, `color.action.primary.background`, `color.action.primary.hover`, `color.action.primary.pressed`, `color.action.primary.foreground`, `color.selection.background`, `color.selection.foreground`, `color.focus.ring`, `color.status.info.foreground/background`, `color.status.attention.foreground/background`, `color.status.error.foreground/background`, `color.status.success.foreground/background`, `color.chart.current`, `color.chart.reference`, and `color.chart.missingMarker`. Expand paired foreground/background names into separate real tokens in the export; slash notation here is a compact registry instruction, not a token name.

Confirmed, unknown, missing, stale, partial, and disabled are semantic meanings with labels and behaviour, not a rainbow of status chips. Use the smallest set of consistent visual treatments. A disabled state must not blanket-reduce opacity until its explanation becomes unreadable; keep a readable reason and programmatic state.

### 6.1 Document-level seed contrast checks

These ratios were computed from the exact opaque sRGB seed pairs with the WCAG relative-luminance formula while preparing this document. They are not measurements of a rendered artifact, focus geometry, transparent layer, gradient, or native screen.

| Foreground / background | Seed ratio, rounded | Applicable check |
|---|---:|---|
| Ink / canvas | 15.21:1 | Normal text ≥4.5:1 |
| Secondary text / white | 6.83:1 | Normal text ≥4.5:1 |
| White / primary | 6.62:1 | Normal action text ≥4.5:1 |
| White / hover | 9.14:1 | Normal action text ≥4.5:1 |
| White / pressed | 11.85:1 | Normal action text ≥4.5:1 |
| Primary / selected surface | 5.67:1 | Selected text ≥4.5:1 |
| Info text / info surface | 5.60:1 | Normal text ≥4.5:1 |
| Attention text / attention surface | 6.72:1 | Normal text ≥4.5:1 |
| Error text / error surface | 6.37:1 | Normal text ≥4.5:1 |
| Control boundary / white | 4.15:1 | Required boundary ≥3:1 |
| Control boundary / canvas | 3.86:1 | Required boundary ≥3:1 |
| Reference series / white | 5.41:1 | Necessary graphic ≥3:1 |
| Focus blue / canvas | 5.80:1 | Necessary focus information ≥3:1 |
| Decorative border / white | 1.52:1 | Fails an essential-boundary role; decorative use only |

Recompute every actual foreground/background and state used, including chart overlays, errors, selected states, focus, and theme overrides. A blue ring directly touching a differently coloured button may fail despite the canvas pair passing; use a contrasting separation layer/offset and measure the real adjacent surfaces. Do not use the decorative border as the sole means of finding an input or selected control.

## 7. Typography, number formatting, and content

Use a system sans-serif with a documented native/web fallback stack and tabular numerals where supported. No purchased or remotely fetched font is required. Start with the following tokens; values are logical design units mapped explicitly by runtime, not physical-pixel equivalence.

| Role | Font size / line height | Usage |
|---|---|---|
| `type.body` | 16 / 24 | Main reading, input values, meaningful explanations |
| `type.label` | 14 / 20 | Supporting labels that remain legible |
| `type.caption` | 12 / 18 | Nonessential metadata only; never scope/cost/gap limitations |
| `type.section` | 20 / 28 | Content group heading |
| `type.title` | 24 / 32 | Screen title |
| `type.metric` | 34 / 40 | Primary energy value with a readable unit |

Document regular/medium/semibold weights as supported platform mappings. Maintain hierarchy through scale, weight and spacing, not colour alone. Do not uppercase long Indonesian sentences. Keep values and units semantically associated; wrap as a sensible group when needed rather than shrinking the entire screen. Long names such as “Pompa Air Area Produksi Belakang” must wrap without truncating the only asset identification.

Use Indonesian display conventions: `14,700 kWh`, `Rp22.050`, `19–25 Oktober 2026`, `07.00–17.00`, `Asia/Jakarta`. Use three decimals when they convey small loads; a consistent compact display may remove insignificant trailing zeros. Source-code numeric literals and machine exports retain their declared canonical format. Never calculate money from an already rounded displayed number.

Approved copy patterns and intent:

| Product copy | Meaning |
|---|---|
| “Energi yang dipantau” | Recorded amount within selected physical scope |
| “Estimasi biaya energi terpantau” | Energy cost estimate, not the utility bill |
| “Biaya belum dihitung — tarif belum diatur” | Unknown cost, not Rp0 |
| “Cakupan pengukuran: 4 perangkat” | Physical assets selected |
| “Kelengkapan data: 92% periode” | Temporal support, not “92% akurat” |
| “Sebagian data belum tersedia” | Recorded partial result, not zero-filled total |
| “Data belum diperbarui” | Source freshness; does not mean equipment is off |
| “Belum cukup periode pembanding” | Learning; measured totals still available |
| “Belum dapat dibandingkan” | Actual reason must follow |
| “Penyebab perubahan belum diketahui” | No invented diagnosis |
| “Demo · Data simulasi” | Synthetic provenance visible |
| “Saran umum” | General guidance distinct from personalized evidence |

Error messages name the field/row and correction. Define whether a number refers to a data row or a file line. Avoid MQTT, internal module names, JSON trace codes, tenant terminology, or analysis thresholds in ordinary product screens; technical details may appear in a clearly secondary explanation where they help the task.

## 8. Spacing, layout, focus, icons, and motion

Define spacing primitives **0, 4, 8, 12, 16, 20, 24, 32, 40, 48, 64**. Give them documented aliases for page gutters, group gaps, control padding and section gaps. Default mobile gutter is 16; wider comfortable content can use 24 or 32. Avoid one-off spacing fixes that are not reflected in the system.

Use radius tokens **0, 8, 12, 16**, with a fully rounded token only where a compact chip needs it. Default layout is flat. Use elevation only to communicate an overlay/sheet; record the actual shadow/backdrop parameters and verify contrast on the resulting surface. Do not make every statistic a floating card.

Internal minimum target token is **48×48**: CSS px for mobile web, dp for Android, and explicitly mapped point/logical units for iOS. Icon artwork can be 20–24 while its hit area is 48. Adjacent hit areas cannot overlap. Define focus appearance separately from hover, selected and pressed. Prefer a visible outer focus outline with a surface-coloured gap; test against its actual neighbours and under zoom.

Choose one consistent set of simple icons or draw a small consistent vector set if the runtime lacks one. Record the set and actual reuse/licensing information when using an external library; do not invent a license or add an icon dependency unnecessarily. Pair unfamiliar icons with text. Do not use a power-toggle symbol to suggest operating appliances. The initial wordmark can be “HematDaya” in system text; a logo redesign or generated mascot is outside this task.

Motion tokens start at **0, 120, 180 ms** with a documented ordinary ease-out. Reduced-motion mode removes nonessential transitions. No animated cost counter, blinking warning, pulsing consumption gauge, chart morphing that hides changes, or autoplay decoration. Loading reports work in progress and never draws fake measured values.

## 9. Responsive and native mapping

Design mobile first. Verify 320 CSS px reflow separately from ordinary 360/390/430 px phone layouts; also inspect 768, 1280 and 1440 px. Prefer one primary reading column on phones. Wider layouts may place supporting material beside it while preserving reading order and the same three destinations. Use content-driven breakpoints; do not invent different product features by screen width.

Document the initial layout rule, such as one column below 768 CSS px, a restrained optional supporting column above it, and a maximum comfortable content width around 1200. Refine based on actual content. At zoom or larger text, allow a return to a single column. Data alternatives can become stacked rows instead of forcing whole-page horizontal scrolling.

For native implementation, map buttons, text fields, selection controls, screen stacks, tabs and sheets to platform-appropriate semantics. Record safe-area padding, keyboard avoidance, visible back behaviour, text scaling, and screen-reader names separately. CSS viewport resize does not prove Android/iOS behaviour. A decorative phone frame is optional for presentation and cannot crop the real hit area or content during tests.

## 10. Component contracts and workbench

Create named reusable components, not unnamed copies inside each example. Use the `HD.` prefix for component identifiers. Every component record specifies: purpose; anatomy; content slots; supported variants; inputs; states; actions; keyboard/focus and screen-reader behaviour; token dependencies; responsive rules; example data; and limits. Actual source props may follow the runtime's conventions; names here are stable design identifiers, not a promise of a particular implementation language.

Required primitive components:

| Component | Contract and states to demonstrate |
|---|---|
| `HD.Button` | Primary/secondary/text/destructive variants; readable label, full hit area, pressed/focus/disabled-with-reason/loading; loading prevents duplicate submit but does not announce success |
| `HD.IconButton` | Accessible Indonesian name, 48-unit hit area, tooltip only as supplementary help; visible focus, no ambiguous unlabeled action |
| `HD.TextField` | Label, help, draft, error, required/optional meaning, focus and disabled/read-only distinctions; long text and retained draft |
| `HD.NumericField` | Units, finite/non-negative rules when applicable, decimal comma display/input, explicit zero versus empty; no silent conversion of empty to zero |
| `HD.ChoiceGroup` | Radio/checkbox/select semantics as needed; keyboard and selected state; ordinary settings only, no appliance-control switch |
| `HD.PeriodSelector` | Today/week/explicit-range selection with local boundaries; selected state beyond colour; updates committed selection only on the defined action |
| `HD.TabNavigation` | Beranda/Perangkat/Saran; labelled, selected semantics, focus, safe-area space and context retention |
| `HD.SheetDialog` | Non-destructive sheet/dialog with title, focus placement/containment, Escape/back, close and return focus; draft/cancel behaviour specified |
| `HD.Disclosure` | Clear label, expanded state, keyboard operation; important current limitations remain outside the collapsed region |
| `HD.Notice` | Informational/attention/error/success/neutral meanings with text and optional action; persistent explanation rather than colour-only toast |
| `HD.ErrorSummary` | Submit-triggered focus, consistent inline messages, actionable links to fields/rows, explicit row-number convention |
| `HD.ProgressStatus` | Loading/saving/unknown-result/success/failure; programmatic status, inspectable result, retry where appropriate; no unnecessary focus theft |

Required domain components:

| Component | Contract and examples |
|---|---|
| `HD.EnergyMetric` | kWh, period, physical scope, provenance and quality; known zero, partial and unavailable are distinct |
| `HD.CostEstimate` | Applicable tariff and bill limitation; missing tariff explanation, explicit zero tariff, labelled synthetic tariff |
| `HD.ScopeSummary` | Included/excluded assets and parent/child alternatives; unknown overlap blocks a combined total |
| `HD.DataQuality` | Separate temporal completeness, source freshness and client offline; no invented “accuracy” score |
| `HD.AssetRow` | Name, optional location, scope kind, energy and relevant quality; whole row's destination clear; no nested conflicting click targets |
| `HD.ContributionRanking` | Direct labels and common zero-baseline bars/list; visible denominator; zero-total state has no percentages |
| `HD.HistoryChart` | Aligned period/unit/scale, real gaps and explicit gap annotation, current/reference distinctions beyond colour; no inferred values for appearance |
| `HD.ChartDataAlternative` | Same dataset/filter, readable text summary and structured values; no hover or precise drag required to answer the task |
| `HD.InsightSummary` | Observed fact, period, comparison eligibility and qualification; no fault/waste/savings verdict |
| `HD.EvidencePanel` | Observed → comparison → quality/scope → unknown → general investigation → optional harmless feedback; expanded calculation metadata |
| `HD.ImportPreview` | Mapping, assumptions, counts, period, row errors and explicit confirmation; loading/error/retry preserve draft and confirmed data |
| `HD.ScheduleWindows` | Optional weekly multiple/overnight windows, explicit next-day/24-hour choice, inheritance/continuous/no-schedule distinctions |
| `HD.OutputMetricPreview` | Optional numerator/denominator, unit, period and actual/estimated method; missing/zero/invalid output has a reason, not infinity |

Do not implement all business logic merely to claim the design system is complete. Component fixtures can drive representative states. Label any local interaction/mock layer. Demonstrate keyboard, focus, changes and recovery in a runnable workbench, with separate results for the actual surfaces tested.

The workbench should let a reviewer inspect component/state examples, change example state, resize, enlarge text, use keyboard, and inspect chart/data alternatives. Workbench state controls are explicitly test controls, separated from ordinary product UI. A framework-specific Storybook installation is not required; an equivalent self-contained workbench is sufficient.

## 11. Domain-state language and chart grammar

Use the same presentation grammar everywhere:

| State | Required presentation |
|---|---|
| No data | “Belum ada data energi”, import/demo next action, no fake-zero metric/chart |
| Measured zero | `0 kWh` with valid coverage; no `0/0` distribution |
| Missing tariff | Energy remains visible; unknown cost, optional tariff action |
| Learning | Measured facts remain useful; name insufficient comparable history |
| No eligible finding | Honest no-finding message, not an efficiency/safety verdict |
| Partial | Recorded amount qualified near the number, gap times and data alternative |
| Stale live source | Last measurement timestamp and source check/retry; no “perangkat mati” |
| Historical import | Its date range/provenance and “Lihat periode data”; not a failed live connection |
| Client offline | Cached confirmed values with age, drafts retained, saves unconfirmed |
| Scope conflict | Individual values plus explanation; choose a valid view before combining |
| Pending/unknown save | Inspectable progress/operation status; no premature success |
| Unavailable capability | Reason and useful next action; no unqualified fake “Terhubung” |

These are independent dimensions. Show combinations such as partial + no tariff, historical import + client offline, and learning + measured zero. Do not create one giant enum or replace them with a single red error panel.

For contribution, start with sorted horizontal bars/list and a common zero baseline. For a compact weekly history, daily bars are sufficient; use a simple line only when time semantics and gaps are clear. Label period, unit, scope and exact values. Give current/reference series a second distinction such as line style, marker and direct text. Avoid donuts as the main ranking task, decorative charts, unsupported smoothing, three-dimensional encodings, and hover-only values.

Gaps retain their missingness, with explicit unavailable periods and a readable explanation. Zero remains a measured value. Scales and elapsed support must be comparable. A percent is unavailable when its reference is zero. A large contributor is not automatically waste. The text summary and data alternative must resolve the same values and filters as the graphic.

## 12. Demonstration data and representative pattern assemblies

The following synthetic values are sufficient for design-system examples. They are complete bounded examples, not permission to invent a new dataset. The application stage will generate the full canonical fixtures and evaluate all product calculations.

| Example | Exact values and UI interpretation |
|---|---|
| Household completed week | 19–25 October 2026, virtual now October 26 00.00 Asia/Jakarta. Kulkas 8.400, Router 1.680, Pompa Air 2.100, TV 2.520 kWh; total 14.700 kWh. Indonesian UI shows `14,700 kWh`. No AC, schedule or output metric required |
| Household cost | Synthetic Rp1,500/kWh gives Rp22,050, displayed `Rp22.050`; missing tariff gives unknown cost, not Rp0 |
| Household contribution | Kulkas `8.4 / 14.7`, approximately 57.14%; label largest **among selected measured devices**, not highest whole-home bill |
| Household change | TV 3.920 versus matched baseline 2.520 kWh; +1.400 kWh, approximately +55.56%. Site total 16.100 kWh, synthetic cost Rp24,150. Cause unknown; no off-schedule claim without a schedule |
| Industrial completed week | Same dates. Oven 72, Kompresor 36, Mesin Press 24, Lampu Area 12 kWh; total 144.000 kWh, synthetic cost Rp216,000; Oven share 50%. No AC required |
| Optional industrial metric | Matching actual output 2,880 units gives `144 / 2880 = 0.050 kWh/unit`. Hide the metric when not enabled; zero output is not a numeric intensity |
| Parent/child scope | Main meter 10 kWh includes refrigerator 1 kWh. A main-meter view is 10, child-only view is 1, never an additive 11 |
| Import threshold | Ten nonblank data rows: 2 invalid permits explicit acceptance of 8 valid unique rows; 3 invalid blocks commit. Conflicting rows block separately; duplicates are counted, not silently doubled |
| Data gap | A 24-hour source with 12 valid one-hour intervals has 50% temporal coverage. Show only recorded energy, identify missing hours, and do not assert an unknown full-day total |

Numerical literals above use English specification conventions. All product examples use Indonesian display formatting and retain sufficient precision. The stated week must not be labelled a populated “Minggu ini” when virtual now is Monday October 26. If a pattern needs dates or readings beyond these examples, define them explicitly and mark their origin; do not invent evidence.

Create four small **pattern assemblies**, using the same named components rather than detached screen copies:

1. **Household Beranda:** mobile populated overview, no schedule/output, optional cost and a no-tariff variant; demonstrate the prescribed reading order and three-tab shell.
2. **Evidence and incomplete data:** current/reference explanation, a zero-baseline variant without percentage, a partial/gap variant with accessible data, and harmless feedback states.
3. **CSV preview and recovery:** valid counts, 2/10 invalid accepted only after confirmation, 3/10 blocked, error summary/field focus, failed/unknown save and retry without duplicate-success appearance.
4. **Industrial reuse:** asset list or detail plus optional schedule/output preview; same components, tokens and states. Disable optional metrics and retain a useful core. Include the 10/1 scope-resolution example.

These assemblies validate composition and meaning, not the entire S01–S12 application. Do not expand this stage into complete authentication, telemetry ingestion, exports of real data, backend security, or all product routes.

## 13. Accessibility checks and evidence boundaries

Use selected WCAG 2.2 criteria as web checks, plus the stronger product targets. WCAG's 24×24 CSS px AA target minimum includes exceptions; the system's 48-unit target is a separate product policy. Normal text must reach 4.5:1 and necessary non-text control/chart information 3:1 where the relevant criterion applies. Check actual states and adjacent surfaces. [WCAG 2.2](https://www.w3.org/TR/WCAG22/), [Android guidance](https://developer.android.com/guide/topics/ui/accessibility/apps).

Required workbench checks: 200% text resize; 320 CSS px reflow and ordinary phone/tablet/wide widths; keyboard task completion without traps; visible/unobscured focus; modal focus return; meaningful names, roles, states and values; error identification and linked correction; programmatic status; chart summary plus structured data alternative; safe-area/keyboard reachability; and reduced motion. Treat text resize, browser zoom/reflow, native font scaling, and native screen readers as separate procedures. [WAI guidance for complex graphics](https://www.w3.org/WAI/tutorials/images/complex/).

Record runtime, browser/OS, viewport, zoom/text setting, assistive technology if used, component/state, expected/actual result and evidence. A specimen in a design-system editor, a code export, a contrast calculation, and a participant session are different evidence. None automatically grants the others a pass. If a container blocks keyboard testing, demonstrate the same component in the runnable workbench and record both facts. Native implementation, full WCAG conformance, actual user comprehension, and hardware accuracy remain unverified unless tested separately.

## 14. Reuse, themes, and change control

Release one maintained system with stable token/component IDs. Household and industry presets reuse it without separate category libraries. A client theme may override explicitly permitted brand aliases, wordmark/assets and copy while preserving contrast, state meaning, component contracts, physical scope/quality explanations, navigation, and touch/readability targets. A theme cannot grant data access, change units, conceal an unavailable capability, redefine a gap, or alter energy calculations.

Only the initial light theme is required. Dark mode, many fictional client brands, a theme-builder UI, a public component registry, and additional typography families are deferred. Document allowed override slots and revalidation requirements; do not implement speculative variations. A real future client request determines the next theme or capability.

Record a release identifier, token schema version, component inventory, actual source/export format, change log, known issues and compatibility notes. A patch may correct an implementation while preserving the component contract; a changed public token or interaction contract requires a documented migration/version decision. Do not promise that changing a library automatically updates past Claude projects. Verify synchronization or apply a recorded update to each consuming artifact.

The system version is separate from PRD version, application source release, product composition, and analysis-policy version. The product can bind to PRD 1.2 and design-system 1.0.0-draft without confusing those numbers.

## 15. Deliverables and binding record

Create the following outputs within the capabilities actually available. These names describe requested future exports, not files already provided by this handoff:

| Output | Required content |
|---|---|
| Private design-system artifact | Named HematDaya Design System with foundations, reusable named components, pattern assemblies, usage notes and review status; or an honestly labelled portable reference if platform registration is unavailable |
| `hematdaya-design-system.tokens.json` | Valid machine-readable values, types/units, aliases and resolved mappings; documented schema/version; no unresolved references |
| `hematdaya-design-system.md` | Principles, token registry, component anatomy/variants/behaviour, content/chart rules, accessibility checks and native mappings |
| `hematdaya-design-system.manifest.json` | Identity/version, source/export format, component IDs, token schema, supported theme/capability scope, source fingerprint if available, review status and limitations; no secrets |
| Component workbench | Interactive state examples, four pattern assemblies, actual inspection/test route, source/project and HTML where supported |
| Validation report | Expected/actual checks, runtime/evidence, documented contrast pairs, gaps and not-run checks; no invented study or compliance result |
| Consumption instruction | Exact steps to attach/select/import the system for the later app stage, component/token names to request, binding record and update procedure |

The manifest is a small descriptive handoff record, not a provisioning or theme-engine framework. Distinguish **created**, **exported**, **validated**, **registered**, **selected in a consuming project**, and **published/default**; none implies the next. Do not fabricate an artifact ID, sync result, source fingerprint, license, or completed check.

Require the application stage to record:

- System name/version, actual artifact/source identifier when available, and review status.
- How it was supplied: selected Claude artifact, imported reference, code sync, or local draft.
- Token export/schema/version and component inventory actually available.
- Representative component IDs used and any justified local deviation with review impact.
- Which checks ran in the consuming artifact, including updated contrast/resize/state checks.
- Any missing binding or unsupported import. A local approximation cannot be called inheritance from a registered system.

Private selection or attachment can provide consistency without changing an organization default. If publishing/default-setting is needed by a later organizational workflow, explain the exact step and leave it to explicit owner authorization.

## 16. Build order and acceptance gates

Work in this order: establish identity/status → resolve foundations/tokens → create primitive components → create domain components → compose the four patterns → run available checks → export/inspect → verify a consuming sample → provide the binding and update instructions. Keep useful work moving when one export surface is unavailable; record a precise fallback and limit instead of inventing success.

Initial status for each gate is **not run**. Use `pass`, `fail`, `not run`, or `blocked` for execution results; track synthetic/mock provenance separately. “Simulated” does not mean that an accessibility or interaction check passed.

| ID | Gate | Required evidence |
|---|---|---|
| DS-01 | Product meaning | Three destinations, no physical control/AC prerequisite, optional setup, correct labels and evidence limits |
| DS-02 | Token integrity | One registry, complete aliases/resolved values, valid JSON, units, no cycles/undefined mappings and consistent use in components |
| DS-03 | Colour and type | Actual text/non-text/focus pairs measured in relevant states; decorative low-contrast border restricted; readable type and numeric formatting |
| DS-04 | Primitive behaviour | Every required primitive's states, action/focus/error/status behaviour inspectable in the real workbench |
| DS-05 | Domain states | No data, valid zero, missing cost, learning, partial/stale/historical/offline/conflict remain meaningful and can combine |
| DS-06 | Chart access | Exact values, aligned support/scales, non-colour distinction, genuine gaps, text summary and usable structured data alternative |
| DS-07 | Recovery | CSV preview/counts/threshold, draft retention, failed/unknown save, error navigation and retry without false or duplicate success |
| DS-08 | Layout and access | Declared widths, 200% text, 320 CSS px reflow, keyboard/focus/screen-reader checks, reduced motion and platform-specific limits recorded |
| DS-09 | Composition reuse | Household and industrial examples use the same named components/token authority; optional metrics can be absent; 10/1 never becomes 11 |
| DS-10 | Theme boundaries | Allowed overrides documented; no theme can change domain/access/state semantics; no speculative theme-builder implementation |
| DS-11 | Export fidelity | Inspect JSON/source/HTML as available; confirm exported interactions separately from editor preview; name actual runtime/dependencies |
| DS-12 | Consuming-project binding | Reuse a representative component in a consuming sample, record system/version/supply method and actual inheritance/import result; no default/publication claim |

Before delivery, inspect long names, unusually small values, zero totals, large currency strings, absent tariff, and combined error/quality states. Use both household and industrial fixtures. A reviewer should be able to explain the scope and unknowns without opening a hidden calculation section. This is a proposed comprehension check; a real participant study is still a later activity.

## 17. Ready English prompt

Copy the marked block and attach only this design-system handoff. The same prompt is supplied separately for convenience.

<!-- BEGIN READY DESIGN SYSTEM PROMPT -->
Create HematDaya Design System first, using the attached self-contained design-system handoff as the complete brief. Read it before choosing tokens or components. This stage produces a reusable product design system and an interactive component/pattern workbench; the full application prototype comes afterwards. Product examples must be natural Indonesian. Documentation and stable token/component names may be English.

Preserve the product contract: electricity monitoring and evidence-based advice for household, business and industrial contexts; Beranda, Perangkat and Saran as the three primary destinations; no AC requirement or physical controls; optional tariff, schedule and output metrics. Preserve measured scope, missingness, valid zero, temporal completeness, provenance and evidence. Do not invent diagnoses, efficiency scores, waste or savings claims.

Build one semantic token authority, the required HD-prefixed primitive/domain components, documented anatomy and interaction states, content/chart rules, responsive/native mappings, and the four bounded pattern assemblies. Start from the seed foundations and retain or revise them with recorded contrast and usability reasoning. All components must consume shared aliases; avoid unnamed screen copies and scattered raw values. Demonstrate loading, focus, disabled-with-reason, error, unknown-result, retry, and combined data-quality states. Keep the fixture values and Indonesian formatting exact.

Use the design-system capabilities actually available here. Declare the runtime and whether this is a registered Claude system or a portable local reference. If live component previews cannot support keyboard testing, provide a separately runnable workbench and record both surfaces honestly. Verify touch targets, text/graphic contrast, 200% text, 320 CSS px reflow, keyboard/focus, accessible chart data, error/status messages, reduced motion, and available native-relevant checks. Record pass, fail, not run or blocked with evidence; synthetic provenance is separate. Seed colour calculations do not prove a rendered interface passes.

Deliver the private system/reference, valid token JSON, system guide, manifest, component inventory/source where supported, interactive workbench and inspected exports, validation report, and exact instructions for attaching/selecting the same system in the later HematDaya application project. Verify a representative consuming sample and record its binding/version; never claim automatic inheritance or clean native output without evidence. Keep unavailable exports and native/participant checks explicit.

Continue through the complete agreed system stage without expanding into the entire app, a logo redesign, speculative themes, SaaS administration or a plugin framework. Do not request real credentials, connect hardware, publish/share externally, deploy a service, or set an organization-wide default. Keep the artifact private and leave publication/default-setting for a later explicit owner instruction.
<!-- END READY DESIGN SYSTEM PROMPT -->
