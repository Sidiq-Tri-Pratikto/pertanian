# Feature specification — Localization foundation

**Status**: Implemented and verified locally
**Depends on**: 001, 021, 025, 028, 034, 047
**Covers**: UX-08, UX-20, AT-39, AT-57, AT-58

- FR-001. Select Indonesian or English per request using `X-HematDaya-Locale: id` or `X-HematDaya-Locale: en`. Missing or unsupported values select Indonesian. Return the selected language in `Content-Language` and include `X-HematDaya-Locale` in `Vary`. Preserve error codes, recovery, data identity and values.
- FR-002. Localize safe error, scope, and CSV presentation from structured data. Retain legacy preview readability.
- FR-003. Supply both languages' presentation in visible and hidden Insights lists and evidence details for clients sending a supported locale. Both variants use the same frozen evidence revision. Keep existing response fields. Language switching makes no additional Insights request and publishes no revisions.
- FR-004. Use typed client catalogs, exact decimal formatting, the site timezone and persisted device locale. Preserve draft, scope, period, and operation identity during a switch.
- FR-005. Translate an uncertain commit status locally. Check and retry are explicit. An online, loaded preview may refresh by ID while the workspace, preview and selected language still match. Preserve the draft and acknowledgments across that refresh. Render saved reads and their original timestamps in the selected language.
