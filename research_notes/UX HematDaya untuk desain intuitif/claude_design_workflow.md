# Claude Design capabilities and HematDaya prototype workflow

Research date: October 21, 2026. Scope: official Anthropic product documentation and a proposed task-oriented handoff; no Claude Design project was created or executed. Local product authority: [HematDaya generic PRD 1.1](../../docs/generic/hematdaya/01_PRD_HematDaya_Generic_EN.md). All recommendations below are design proposals, not measured user-research findings.

## 1. What can Claude Design currently create, run, and export?

### Takeaway

Claude Design supports working interactive prototypes and engineering handoff. Specify a playable, mobile-first prototype in its available runtime; treat Android/iOS implementation as a subsequent engineering deliverable unless native output is actually supported and verified in the user's session.

### Cited Findings

- Current Help Center documentation places Claude Design in ordinary conversations, the Artifacts tab, and Claude Code. It supports canvas editing, design-system context, and interactive prototypes. The standalone `claude.ai/design` service is scheduled to close December 14, 2026. Current availability includes Free, Pro, Max, Team, and Enterprise, subject to organizational settings. — [Get started with Claude Design](https://support.claude.com/en/articles/14604416-get-started-with-claude-design)
- The same current guide lists ZIP, standalone HTML, PDF, PPTX, Google Slides, partner tools, and Claude Code handoff among exports. Its caveats include unreliable basic simultaneous editing, incomplete design-system imports, no version-history facility, and shared Claude usage limits. — [Get started with Claude Design](https://support.claude.com/en/articles/14604416-get-started-with-claude-design)
- The official Academy tutorial says that clickable artboards run with **Play**; when no Play button appears, explicitly request clickability. A complete prototype can export as a single HTML web page; an individual artboard can export as PNG, PDF, or HTML ZIP. It also describes taking the design link into Claude Code with engineering edit access. — [Using Claude for prototypes and UX](https://academy.claude.com/tutorials/using-claude-design-for-prototypes-and-ux)
- Official administrator documentation describes HTML bundles and Claude Code handoff. Previews run inside a sandboxed iframe on a separate Anthropic content domain; preview code cannot access the editor, Claude account, or login. — [Claude Design admin guide](https://support.claude.com/en/articles/14604406-claude-design-admin-guide-for-team-and-enterprise-plans)
- The April 17 launch announcement described interactive prototypes, code-powered experiences, standalone HTML, and a Claude Code handoff bundle. Its initial paid-plan and research-preview availability differs from current Help Center availability. Use the launch article as historical context rather than current plan guidance. — [Introducing Claude Design by Anthropic Labs](https://www.anthropic.com/news/claude-design-anthropic-labs)
- The current artifact guide requires cloud code execution/file creation to be enabled. Its feature table distinguishes ordinary artifact creation from connected apps and stored artifact data, which are available on paid plans. — [What are artifacts and how do I use them?](https://support.claude.com/en/articles/17153992-what-are-artifacts-and-how-do-i-use-them)

### Inferences

- Safest runtime request: “Build a working, stateful prototype in the runtime available to Claude Design. If native execution is unavailable, make a responsive browser simulation with mobile navigation and supply a native implementation handoff. State the runtime and tested platforms.” This is a compatibility proposal, not an Anthropic guarantee of native builds.
- A web simulation can validate information hierarchy, screen transitions, copy, fixture arithmetic, and many recovery interactions. It cannot establish native safe-area, keyboard, screen-reader, permission, secure-storage, or installed-app behavior. Platform acceptance must retain separate Android, iOS, and web results.
- PDF/PNG alone cannot satisfy the requested playable prototype. Prefer a live playable design plus a verified interactive HTML export and source/project archive when the session exposes those exports.
- ZIP is an available export format; do not assume its contents are a clean Expo/React Native project. Inspect the downloaded project, document its runtime, and identify assets/source that can actually be reused.
- Avoid requiring connected apps, paid storage, credentials, live telemetry, push, or external APIs for the core demonstration. An in-memory deterministic fixture mode is the smallest self-contained baseline. If persistence is used, label and scope it to demo data and explain reset behavior.

### Gaps

- No opened official source promises Expo, React Native, Flutter, APK, AAB, IPA, App Store submission, or native device execution directly from Claude Design. Do not frame these as supported export capabilities.
- Exact export layout, library availability, sandbox capabilities, file-picker behavior, browser persistence, and external-network permissions were not tested in an actual Claude Design session. Request graceful runtime-specific fallbacks and report any limitation honestly.
- No actual prototype was run; all HematDaya behavior and user-task acceptance remains unexecuted.

## 2. How should a single standalone handoff guide the prototype?

### Takeaway

Make the handoff complete enough to attach by itself: product authority, full PRD snapshot, task priorities, screen/state contracts, deterministic fixtures, exact copy, exclusions, and observable acceptance results. Organize the build around what a person needs to understand and do, then use visual polish to support those tasks.

### Cited Findings

- Anthropic recommends describing the feature journey step by step, explicitly requesting working interactions, giving screens/components clear names, recording design decisions, and asking for empty, loading, error, small-data, and large-data states before implementation. — [Using Claude for prototypes and UX](https://academy.claude.com/tutorials/using-claude-design-for-prototypes-and-ux)
- Design systems can be extracted from uploaded assets or synced from an existing React component library through Claude Code `/design-sync`. A design system covers color, typography, components, and layout patterns; source quality limits the result. — [Set up your design system in Claude Design](https://support.claude.com/en/articles/14604397-set-up-your-design-system-in-claude-design)
- HematDaya requires three primary destinations (**Beranda**, **Perangkat**, **Saran**), an optional context preset, no mandatory AC/schedule/output data, scope-safe calculations, conservative evidence-based advice, and Indonesian interface text. Its preferred future implementation stack is Expo/React Native/TypeScript for Android/iOS/web, with shared domain rules and a server; this is a proposed implementation rather than an existing verified system. — [Local PRD, sections 2–9 and 15](../../docs/generic/hematdaya/01_PRD_HematDaya_Generic_EN.md)
- Product acceptance explicitly separates missing data, measured zero, learning, missing tariff, stale source, historical import, client offline, conflicting scope, invalid CSV, and unsupported adapters. It also requires retained drafts/navigation context, data provenance, quality, and actual evidence for platform and user-study claims. — [Local PRD, sections 13–14 and 20](../../docs/generic/hematdaya/01_PRD_HematDaya_Generic_EN.md)

### Inferences

The proposed standalone file should contain these elements in this order:

1. **Authority and outcome:** version/date; English specification and Indonesian product UI; build an operational prototype, not a marketing page or screen gallery. Latest explicit owner instruction overrides the embedded PRD; preserve the PRD's requirement IDs. Clearly distinguish prototype coverage from eventual release scope.
2. **Complete PRD snapshot:** copy the entire approved English generic PRD verbatim into an appendix. A local path or “see separate attachment” is insufficient when this file must work alone. Derived design guidance must not quietly alter formulae, optionality, fixture values, or release gates.
3. **User tasks and success criteria:** hardware-free start; determine measured energy and coverage; find the largest contributor; inspect its history; understand an observation's evidence; recover an invalid import; distinguish stale data from an appliance being off. Cover household and industry separately with the same navigation/domain logic.
4. **Task-first screen flow:** welcome → optional context/skip → household or industrial demo → Beranda → contributor → detail/history; Beranda → Saran → evidence; empty state → import → validation/mapping → preview → explicit confirm; settings → optional setup → preview → confirm/cancel. No forced login, production form, tariff, schedule, or hardware on the demo path.
5. **Screen contract:** named artboards/screens S01–S12, purpose, primary action, optional actions, input fields, displayed provenance and quality, back destination, and exact state behavior. Use three labelled tabs everywhere; settings/import/scenarios remain secondary. “Perangkat” includes devices, circuits, and groups with visible scope labels.
6. **State and interaction contract:** specify visible effects, saved versus draft data, retry/cancel/back behavior, error copy, loading, keyboard/focus, and conflict resolution. A button should do its stated action or visibly explain unavailability. A static screen change that pretends to save, connect, import, or authenticate is insufficient.
7. **Fixture and calculation authority:** deterministic virtual now, exact interval data generation, shared calculations, consistent view models across screens, and assertable expected values. Never fabricate chart points independently of the energy table or insight evidence.
8. **Visual and accessibility specification:** Indonesian numeric/date formats; readable scale; required targets/contrast as proposed checks, not assumed compliance; text chart equivalents; focus and selected-tab states; flexible long asset names; reduced motion; responsive widths from the PRD. Proposed initial visual tokens may be supplied if no real design system exists, clearly labeled as newly proposed rather than established brand assets.
9. **Verification matrix:** task, fixture/input, expected behavior, actual result, runtime/platform, evidence, and status. Available statuses should distinguish pass, fail, not run, blocked, and simulated. Completion in a browser does not mark Android or iOS passed.
10. **Handoff contents:** source/project export when supported; runnable HTML/browser build when supported; tokens/components; named route/state map; fixture definitions and assertions; calculations; API/mock boundary; recovery cases; native mapping; known limitations and remaining implementation work.

Proposed demo arithmetic checkpoints, copied from the product contract rather than new research:

- **Household:** completed week 19–25 October 2026, 14.700 kWh; at explicitly synthetic Rp1,500/kWh, Rp22,050. Kulkas is largest at 8.400 kWh, about 57.14%. Router, Pompa Air, TV complete the fixture; no AC. Base data produces no change alert. Variant TV increases 1.400 kWh to 3.920 kWh; site total 16.100 kWh, Rp24,150; no off-schedule claim when no schedule exists.
- **Industry:** same week, 144.000 kWh, Rp216,000 at synthetic tariff. Oven contributes 72.000 kWh, 50%. Kompresor, Mesin Press, Lampu Area complete the fixture; no AC. Optional 2,880 units makes 0.050 kWh/unit; disabling the metric preserves core functionality. Outside-window variant adds 3.000 kWh, site 147.000 kWh/Rp220,500; zero baseline means no percentage; no verified-waste claim.
- **Clock/provenance:** virtual now October 26, 2026 00.00 Asia/Jakarta; use “19–25 Oktober”, not a populated current week. Label “Demo · Data simulasi”. Emit 2,688 hourly readings per main fixture over four completed weeks and include valid zeros. Product labels should use Indonesian decimal formatting even when specification oracles use decimal points.
- **Boundary checks:** 10 kWh parent plus 1 kWh child is a valid 10 kWh parent view or 1 kWh child view, never 11. Missing tariff is unknown cost, not Rp0. Offline is not off. Historical imports are dated records, not live meters. Invalid CSV preserves prior data; failed saves preserve drafts.

### Gaps

- The existing PRD is specification evidence, not implemented functionality or customer validation. These priorities are proposed, and require separate household and industry testing.
- A compact prompt cannot replace the embedded measurement, schema, insight, fixture, and acceptance contract. The final writer should embed the complete PRD rather than omit difficult sections for brevity.

## 3. What exact execution prompt and review gates should be used?

### Takeaway

The prompt should require working tasks, explicit simulated boundaries, and testable output. Ask Claude Design to build incrementally while continuing through the full agreed prototype scope, then report what actually ran and what remains for native implementation.

### Cited Findings

- Anthropic's recommended workflow supports context assets, conversational refinement, local canvas edits, and engineering handoff. The current artifact system starts designs private, with explicit sharing controls. — [Claude Design admin guide](https://support.claude.com/en/articles/14604406-claude-design-admin-guide-for-team-and-enterprise-plans); [What are artifacts and how do I use them?](https://support.claude.com/en/articles/17153992-what-are-artifacts-and-how-do-i-use-them)
- HematDaya's PRD forbids physical controls, unverified integration success, invented diagnoses/savings, secrets in exports, and pass claims without runtime-specific evidence. CSV/demo may operate without broker, vendor account, cloud AI, or push. — [Local PRD, sections 2, 6.3, 15, 19–23](../../docs/generic/hematdaya/01_PRD_HematDaya_Generic_EN.md)

### Inferences

The following English prompt is a proposed reusable starting instruction. The handoff attached alongside it must contain the full PRD and explicit screen/state/fixture contracts described above.

> Build HematDaya as a working, stateful, mobile-first interactive application prototype in Claude Design, using the attached self-contained handoff as the complete product authority. Read the full document, including its embedded English PRD, before choosing screens or calculations. All user-facing interface text must be natural Indonesian. This is an electricity monitoring and evidence-based advice product for household, business, and industrial contexts. Use one shared product and three labelled primary destinations: Beranda, Perangkat, Saran.
>
> Begin by identifying the prototype runtime and the route/state map. Use the runtime actually available here. If native Android/iOS execution is unavailable, build a responsive browser simulation with mobile navigation and provide a separate native implementation handoff for the proposed Expo/React Native stack. Do not claim a browser preview is a native app or promise unsupported native exports. Do not stop at static artboards, screenshots, decorative charts, or a landing page: make the screens playable and connect every promised task to working state changes.
>
> Build and verify the core household journey first, then the industrial journey using the same components and rules, then import/recovery and optional settings. Continue until all agreed prototype gates are covered or an actual runtime limitation is documented. Use explicit assumptions for reversible layout choices; list unresolved product decisions instead of silently changing the contract. Keep hardware, login, schedules, production metrics, tariffs, push permissions, paid services, and external accounts out of the required demo path.
>
> Use the deterministic fixture definitions, shared virtual clock, energy/cost arithmetic, contribution/scope rules, and evidence snapshots from the handoff. Derive every chart and displayed value from the same fixture/calculation authority. Add small assertions for household, industry, changed-usage variants, no tariff, partial data, valid zero, parent/child overlap, duplicate sources, invalid CSV, and zero/missing output. Keep measured zero, missing, partial, stale, historical import, and client offline visibly distinct. Invalid imports and failed settings saves must preserve drafts and previous confirmed data. A retry must not duplicate an import or binding.
>
> Implement household and industrial scenarios without AC. Let industrial users complete the core tasks without production data or a schedule. Explain the selected measurement scope wherever it changes the meaning of a total or contribution. Never double-count a parent and child or alternative sources. Do not claim an offline meter proves equipment is off. Do not call extra energy waste or invent a fault cause. Missing tariff is unknown cost, not zero. Label synthetic tariff, simulated data, mocked backend, and unavailable integrations explicitly.
>
> Make the primary tasks easy to discover with clear Indonesian labels, visible selected state, one main action per task screen, accessible touch targets and focus, text alternatives for charts, readable expanded text, safe-area aware layouts, and retained period/scope/navigation context. Expose scenario/reset controls through a secondary tester entry; ordinary product screens must remain free of debug jargon. Reset affects only the isolated demo.
>
> No credentials, real telemetry, physical switching, device control, publication, external sharing, or production deployment are authorized. Unsupported hardware setup must explain its status instead of faking “Terhubung”. If a real connection or authentication path cannot be implemented in this runtime, show a clearly labeled simulation/unavailable path and preserve it in the handoff as pending work.
>
> Before finishing, run the prototype through both segment walkthroughs, invalid-import recovery, scope conflict, stale/offline, optional schedule, and optional output cases. Check the stated responsive widths, keyboard/focus, long Indonesian names, and larger text where the runtime permits. Record expected versus actual results and name the tested runtime; leave unexecuted native and research checks “not run”. Do not invent user studies or savings results.
>
> Deliver the playable design, verified interactive HTML and project/source export where available, a concise route/state map, design tokens/components, fixture assertions, mocked-versus-implemented boundary, native implementation notes, and the acceptance matrix. Test exported interaction behavior separately from the in-editor preview; report unsupported exports plainly. Keep the project private unless I later authorize sharing or publication.

Proposed review gates for the writer to add to the handoff:

- **Gate A — semantics:** correct product scope, Indonesian UI, exactly three primary tabs, no AC/control requirements, optional setup remains optional.
- **Gate B — runnable tasks:** a reviewer can start a demo, change period/scope, find the contributor, inspect history/evidence, change and restore feedback, and recover invalid input. Claimed actions must have observable outcomes.
- **Gate C — calculation/state integrity:** fixture oracles pass; values reconcile across views; quality flags combine independently; no duplicate commits, fake-zero gaps, or invalid aggregation.
- **Gate D — usability/accessibility review:** layout, labels, focus, contrast, target size, motion, long text, and responsive checks have recorded evidence; native-specific checks remain separate.
- **Gate E — reusable handoff:** playable/exported build actually opens; source/export format is identified; native work is mapped rather than claimed complete; platform/user-study status is honest.

### Gaps

- This prompt was not trialed in Claude Design, and no export or prototype behavior was validated. Results depend on the actual session's available runtime, capabilities, and usage limits.
- No participant study was performed. Proposed “intuitive” behavior needs observed first-use tasks in household and industrial groups separately; passing fixture calculations alone cannot demonstrate usability.
- A source archive and implementation notes may reduce engineering ambiguity but do not establish production security, physical-meter compatibility, native performance, or release readiness.
