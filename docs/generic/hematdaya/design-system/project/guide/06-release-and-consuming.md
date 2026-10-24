# Release, themes and consuming

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

### Change log

- **1.0.0-draft** — first release. Seed palette kept unchanged (all seed pairs recomputed and passing). Added `palette-neutral-subtle` (#eceeea) for hover, disabled and neutral surfaces, `palette-red-800` (#821f1f) for destructive hover, and `duration-progressCycle` (900 ms) for the spinner. Type sizes expressed in rem (16 logical units = 1rem) so text resizing works.

### Compatibility

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
