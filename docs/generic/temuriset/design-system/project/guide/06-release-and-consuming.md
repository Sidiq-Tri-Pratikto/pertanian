# Release and consuming

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
