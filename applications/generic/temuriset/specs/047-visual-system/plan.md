# Implementation Plan: Visual system 1.1 (revamp R1)

**Spec**: [spec.md](spec.md)

## Design system package (`docs/generic/temuriset/design-system`)

1. `project/tokens.json`: IBM Plex Sans first in `type.families.sans`; weights 400, 600, 700 (medium removed); label 600; heading-lg 700; new `tr-sys-type-display`; new `tr-sys-radius-media`.
2. `project/fonts/`: three IBM Plex Sans 2.0.0 Latin1 woff2 files, `OFL.txt`, `fonts.css`. Hashes in the README.
3. `project/components/bundle.css`: `.tr-logo`, `.tr-media`, `.tr-toolbar`, `.tr-chips`/`.tr-chip`, `.tr-list`/`.tr-listrow`, `.tr-listdetail`; medium weight uses become semibold; folds web deviations D1, D2 and D16.
4. `project/components/bundle.js` and `index.d.ts`: `TR.Logo`, `plus` icon; `Screen` shows the logo and a display title. `tools/catalog.mjs` documents Logo; `tools/build.mjs` version 1.1.0-draft.
5. `workbench/index.html` and `frame.html` load `fonts.css` before the tokens.
6. `node tools/build.mjs` regenerates `workbench/tokens.css`, guide and exports.

## Web (`applications/temuriset-web`)

1. `Makefile` `design` copies `project/fonts/` to `src/design/fonts/`; `tests/design.test.ts` compares all copies byte for byte.
2. `src/app/layout.tsx` imports `@/design/fonts/fonts.css`; `src/app/icon.svg` is the favicon.
3. New `src/components/tr/Logo.tsx`; `Screen.tsx`, `AuthShell.tsx`, `not-found.tsx` and `error.tsx` use the logo and `tr-sys-type-display`.
4. `src/design/app.css` keeps only D15; `docs/roadmap/architecture.md` marks D1, D2, D11, D16 as folded and adds D17 (logo links to `/`).

## Verification

`node tools/build.mjs` (integrity, contrast); web `make check` (lint, typecheck, Vitest incl. drift); `make e2e` (axe, overflow with 200% text at 320 px, keyboard at 4 widths); browser check that the three Plex weights load and the shell shows the logo.
