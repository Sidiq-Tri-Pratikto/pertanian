# Implementation plan — Bilingual MVP

Use the 049 locale store, exact formatters, structured diagnostics and cached Insight display variants. Translate UI-owned labels at their source, with the selected locale and the current data interpolated separately. Leave persisted inputs and names intact. Keep Indonesian as the default and keep routes and operation identities language-independent.

| Route group | Copy and state inventory |
| --- | --- |
| Welcome, demo and Settings | entry, context, scenario choice, expiry, language, accessibility, planned capability labels |
| Home and shared navigation | tabs, period, source and scope, energy and quality, contributors, cost, refresh and cached data |
| Devices, detail, history and edits | list and archive, status, chart and data table, validation, save and retry |
| Insights, evidence, hidden and feedback | visible and hidden lists, offline and retired evidence, structured numbers, acknowledgment and recovery |
| Scope | confirmed and reviewed selection, overlapping sources, refusal, validation, saves and failed reads |
| CSV | file and paste, mapping, preview, acknowledgment, row diagnostics, result, retry and uncertain commit |

Localize shared controls before route copy. Render alternate service copy without remounting any state owner. Add the selector only after the route migration. Reuse prototype state and domain computations, supply localized display labels from the app, and keep language in local storage. Sync the reference and record the binding overrides.

Use one acceptance pass. Run live journeys with local fixtures, responsive and keyboard checks, API and mobile checks, prototype domain tests and bundle export. Record native and spoken accessibility evidence separately.
