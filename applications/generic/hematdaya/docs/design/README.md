# Design system reference

HematDaya uses **HematDaya Design System 1.0.0-draft** (review status: draft, not owner-approved). It was created in Claude Design as a private artifact: https://claude.ai/artifact/UKpTDTYqPNVwfCuHLjY3ns, version id `1792845682-1490`.

| Path | Content |
|---|---|
| `guide/` | Token registry, content and chart rules, pattern assemblies, responsive and native mapping, validation report, release and consuming |
| `components/*.md` | One contract per `HD.*` component: anatomy, states, keyboard and screen reader, limits |
| `components/index.d.ts` | Prop types of the web components |
| `applications/hematdaya-mobile/design/tokens.json` | The tokens the app is built from |

The web components (`window.HD`) do not run in React Native. `applications/hematdaya-mobile/src/components/hd/` holds native components with the same names, props and meaning, ported when a feature first needs them. Mapping: `guide/04-responsive-and-native.md`.

Two web components calculate in the browser: `CostEstimate` multiplies floats and `ContributionRanking` computes percentages. The native versions take strings from the service instead, because the service is the one calculation authority.

## Known gaps to raise with the system

Recorded while building, and listed in `docs/reference/prototype/design-system-binding.json`:

- `EnergyMetric` and `CostEstimate` say "Belum ada data energi" when a total is withheld for a scope conflict.
- `CostEstimate` cannot show effective-dated tariff splits.
- `ImportPreview` assumes file line = data row + 1, which is wrong with blank lines or multi-line quoted fields.
- Copy differs from the brief: `ImportPreview` says "Impor N baris" (brief: "Konfirmasi impor"), and `EvidencePanel` headings differ. The system's wording stands until the owner decides.

## Updating the system

A system change never reaches this repository by itself. To adopt a new version: copy `tokens.json`, run `make tokens`, update this file, and re-run the contrast, target and text-size checks. A local copy is an imported reference, not inheritance.
