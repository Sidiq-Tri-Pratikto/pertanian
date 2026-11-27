# Implementation Plan: Bilingual foundation (revamp R3)

**Spec**: [spec.md](spec.md)

## API

1. `app/core/locale.py`: `LocaleMiddleware` (ported from HematDaya), `locale()`, `as_locale()`; registered in `app/main.py` outside the error boundary.
2. `app/core/errors/public.py`: `_EN_BY_CODE`, `_EN_BY_STATUS`, `_FIELD_MESSAGES_EN`; `public_error_for_code`, `public_error_for_status` and `field_message` follow `locale()`.
3. `app/subscriptions/service/mail.py`: one text table per language and `/en` paths; `matching.py` reasons and stage names per language; anonymous inventor name per language.
4. `app/identity/service/service.py`: the code email per account or page language.

## Web

1. `src/proxy.ts`, `src/features/i18n/{locale,id,en,messages,LocaleProvider,server,carry}.ts(x)`.
2. `app/layout.tsx` (lang, provider, description), `api/client.ts`, `api/server.ts`, `api/errors.ts`.
3. Shared components with copy read the context: Field, ChoiceGroup, ErrorSummary, SaveState, Select, Dialog.
4. Translated: AuthShell (with the ID/EN switch), StartView, CodeView, DemoPanel, SubscribeView, TopicsFields, ConfirmView, ManageView, TeaserView, not-found, error, and the signed-out page titles.
5. Design system: `.tr-langswitch`.

## Tests

API: `tests/unit/core/test_locale.py`, English subscription mail and errors in `tests/integration/subscriptions`, English code email in `tests/integration/identity`. Web: `tests/i18n.test.tsx`; `e2e/routes.ts` adds four English routes; `e2e/language.spec.ts` checks `lang`, the switch carrying a typed email, and an English service error.
