# Feature specification — Bilingual MVP

**Status**: Implemented and verified locally
**Depends on**: 048, 049
**Size**: L
**Covers**: UX-08, UX-12, UX-19, UX-20, AT-39, AT-43, AT-48, AT-57, AT-58

## User stories

### US1 — Read and use every MVP screen in my language

I can explore in plain Indonesian or English and understand the figures, controls and recovery actions in the same language. Each route group below can be exercised with the household or industrial fixture, including its empty, loading, error and saved-data states.

### US2 — Change language without disrupting my work

I can choose the language on Welcome or in Settings, keep my place, and return to the same preference after restarting. While I read offline or an import outcome is unknown, the UI still shows the state and its explicit recovery actions in my language.

## Functional requirements

- **FR-001**. Localize all MVP routes, accessibility names and state messages in the Expo app and standalone prototype. Use Beranda, Perangkat and Saran in Indonesian and Home, Devices and Insights in English.
- **FR-002**. Use the device locale for formatted text, dates, numbers and durations. Keep site timezones, exact energy precision, IDR, file names, user-entered names and CSV input.
- **FR-003**. Expose a persistent language choice on Welcome and in Settings in both builds. Set document language on web and accessibility language where supported. Preserve navigation, period, scope, drafts, acknowledgments and operation keys.
- **FR-004**. Localize from confirmed data and frozen Insight copy while retaining scope refusal, historical or saved-read provenance, and explicit recovery. A language change does not write to the API or request either Insights list.
- **FR-005**. Keep Indonesian defaults in shared prototype components. Record application overrides in binding notes and sync the checked-in prototype reference copy.

## Success criteria

- **SC-001**. Both languages complete the household and industrial journeys in both builds with exact totals, measured zero, safe history, scope refusal, CSV replay, feedback recovery and offline reads.
- **SC-002**. At 320, 390, 768 and 1280 px and at 200% text, controls keep their names, readable labels and operable targets. Charts expose data alternatives.
- **SC-003**. Local checks, web and native bundles, Android runs, iOS runs and spoken accessibility results are recorded separately.
