# Implementation Plan: English for the signed-in app (revamp R7)

**Spec**: [spec.md](spec.md)

1. `src/features/i18n/t.ts`: `t`, `tx` (text passed to shared components), `setAppLocale`, `appLocale`, `intlLocale`; a `react` `cache` store per server request and one shared value for client components (`ponytail:` note on the shared value).
2. `src/features/i18n/server.ts`: `serverLocale` reads `/en` then the `tr_locale` cookie; `resolveRequestLocale`; `titled()` for page titles. `requireMe` resolves the language; `serverGet` forwards it to the service.
3. `src/features/i18n/app-en.ts`: about 1,330 entries keyed by the Indonesian source.
4. Header switch in `components/tr/Screen.tsx`; `AuthShell` and the account form remember the choice.
5. Every view and feature wraps its copy; module-level labels stay data and are translated where they render.
6. API: `next_action.py` answers in the request language.

## Tests

`tests/app-i18n.test.tsx`: every literal key has English, placeholders match, nothing translates at module load, `t()` falls back and fills placeholders, and the shell renders English. Existing Vitest suites stay Indonesian. API unit, discussion and demo suites pass.
