# Tasks — Localization foundation

- [x] T013 Check the spec, plan and tasks against merged dependencies.
- [x] T014 [US1] Implement request locale and localize API errors, scope and CSV diagnostics.
- [x] T015 [US1] Add bilingual display variants for the same Insights revision and notices.
- [x] T016 [US2] Implement device preference, typed catalogs and exact localized formatters.
- [x] T017 [US2] Separate language selection, saved read display and explicit import recovery.
- [x] T018 Verify API, client, contracts and the locale-switch regression cases.

## Analysis

FR-001 and FR-002 map to T014, FR-003 to T015, FR-004 to T016 and T017, and FR-005 to T017. T018 covers all five. Locale middleware must wrap fallback error responses. Render copy variants at the original Insights read so changing the UI language cannot evaluate or publish data. Keep the client control gated until 050.

## Acceptance evidence

- API `make check` against local PostgreSQL passed with 1,083 tests, 8 skips, and 97.02% coverage. The final focused run passed 95 tests, including simultaneous locales, stored and legacy CSV previews, and the same evidence revision in both languages.
- Mobile lint, typecheck and 581 tests passed on the merged 048 base. The locale switch sent zero visible or hidden Insights list requests, preserved the cached query, and sent zero mutation requests. Stable previews refresh by ID, outdated responses cannot replace current copy, and an unknown commit sends no status check or retry on a locale change.
- Regenerating the API OpenAPI document and the TypeScript contract produced byte-identical files. The Android, iOS and web JavaScript bundles exported successfully.
