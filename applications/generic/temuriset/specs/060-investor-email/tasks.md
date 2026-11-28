# Tasks: Investor email revamp (HTML with text fallback)

**Input**: Design documents from `applications/generic/temuriset/specs/060-investor-email/` (`spec.md`, `plan.md`), `docs/roadmap/revamp-2-demo-feedback.md`, `docs/roadmap/architecture.md`, and `.specify/memory/constitution.md`.
**Branch**: `f/060-investor-email` | **Track**: B | **Needs**: 046, 053, 056

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: User story label (`US1`, `US2`, `US3`, `US4`, `US5`)

---

## Phase 1: Migration, Mailbox Port & Loopback Relay (FR-002, FR-006)

- [X] T001 [US1] Create Alembic migration `applications/generic/temuriset/applications/temuriset-api/migrations/versions/0027_mailbox_html.py` adding nullable `mailbox_messages.html` (`TEXT`) and new table `unsubscribe_links` (`id`, `created_at`, `kind` in `('subscription','follow')`, `target_id`, `token_sha256` unique, `expires_at`); add `MailboxMessageRecord.html` in `app/identity/repository/sqlalchemy/models.py` and `UnsubscribeLinkRecord` in `app/subscriptions/repository/sqlalchemy/models.py`
- [X] T002 [US1] Extend `MailboxAdapter.send`, `DevelopmentMailbox.send`, `DisabledMailbox.send`, `LoopbackMailbox.send`, and `deliver_to_relay` in `app/identity/service/mailbox_service.py` with `html: str | None = None` and `headers: dict[str, str] | None = None`, raise `_MAX_MESSAGE_BYTES` from `8192` to `131072` (128 KB), update `app/identity/service/mail_jobs.py` (`_SecretMessage` + `deliver_secret`) to pass `html` and `headers`, and add `html: str | None = None` to `MailboxMessageResponse` (`app/identity/model/schema.py`) and `GET /api/v1/dev/mailbox` (`app/dev/router.py`)

---

## Phase 2: Email Content Model, Text & HTML Renderers (US1, US2, FR-001, FR-005)

- [X] T003 [P] [US1] Create `app/subscriptions/service/email/` package (`__init__.py`, `tokens.py`, `content.py`, `render_text.py`, `render_html.py`) implementing `Card` and `EmailContent` dataclasses, design tokens, plain-text renderer, and stdlib-only inline-styled responsive HTML renderer (`<html lang>`, `color-scheme`, hidden preheader, 600 px single-column `role="presentation"` tables, 44 px bulletproof buttons, `html.escape` on all dynamic strings, optional photo with alt text, < 100 KB)
- [X] T004 [US1] Refactor `app/subscriptions/service/mail.py` builders (`confirm`, `already_subscribed`, `alert`, `digest`, `follow_confirm`, `already_following`, `follow_update`) to construct `EmailContent` (with TKT, public photo, field test, matched reasons chips, demo badge, bilingual ID/EN copy, footer manage/unsubscribe/language links) and return `(subject, text, html, headers)` including RFC 8058 `List-Unsubscribe` and `List-Unsubscribe-Post` headers on alerts, digests, and follow updates

---

## Phase 3: One-Click Unsubscribe, Subscription Locale & Dev Preview (US3, US4, US5)

- [X] T005 [US3] Create `app/subscriptions/service/unsubscribe.py` to mint 365-day hashed `unsubscribe_links` tokens (`mint_unsubscribe_token`) and handle idempotent one-click unsubscribe for both subscriptions and follows (`consume_one_click`), returning `200 {"status": "unsubscribed"}` or `404 NotFoundError` for unknown/expired tokens
- [X] T006 [US3] Wire `html`, `headers`, and one-click token minting in `app/subscriptions/service/service.py` (`SubscriptionService`) and `app/subscriptions/service/follows.py` (`FollowService`); extend `SubscriptionResponse` with `locale`, `UpdateTopicsRequest` with optional `topics` and `locale`, and `SubscriptionService.update` to update topics and/or locale
- [X] T007 [US3] Add `POST /api/v1/unsubscribe/one-click` (query `t`, form `List-Unsubscribe=One-Click`, no cookie required) and update `PUT /api/v1/subscriptions/manage` in `app/subscriptions/router.py`; exclude `/api/v1/unsubscribe/one-click` from access logs in `app/core/logging.py`; add new routes to `NOT_DATA_ROUTES` in `tests/integration/test_isolation.py`
- [X] T008 [P] [US5] Add `GET /api/v1/dev/mail-preview/{template}?lang=id|en` (`confirm`, `already`, `alert`, `digest`, `follow_confirm`, `follow_already`, `follow_update`) in `app/dev/router.py` and document demo step in `docs/demo/scenario.md`

---

## Phase 4: Web Manage Language Control & Contracts (US4)

- [X] T009 [US4] Regenerate `contracts/openapi.json` and `applications/temuriset-web/src/api/schema.generated.ts`
- [X] T010 [US4] Update `applications/temuriset-web/src/features/subscriptions/api.ts`, `src/views/subscriptions/ManageView.tsx`, `src/features/i18n/id.ts`, `src/features/i18n/en.ts`, and `src/features/i18n/app-en/mail.ts` to allow changing subscription email language (`Bahasa Indonesia` / `English`) at `#bahasa-email` alongside topics

---

## Phase 5: Tests, Compatibility & Spec Status

- [X] T011 [P] [US1] Write unit tests `tests/unit/subscriptions/test_email_render.py` covering all 7 templates × 2 languages (ID/EN), text & HTML parity, XSS escaping (`<script>` in title), HTML size < 100 KB, accessibility (`lang`, `alt`, `role="presentation"`, no `<style>`/scripts/empty links)
- [X] T012 [P] [US3] Write integration tests `tests/integration/subscriptions/test_email_html.py` and `tests/integration/subscriptions/test_one_click.py` covering multipart alert/digest/follow HTML + headers, dev mailbox `html`, dev mail-preview route, cookie-less idempotent one-click unsubscribe (subscription & follow, 404 unknown/expired, relay recheck drops queued mail), and subscription `locale` update
- [X] T013 [P] [US4] Write web test `applications/temuriset-web/tests/manage-language.test.tsx` covering changing subscription email language on `ManageView`
- [X] T014 Run `alembic upgrade head && alembic downgrade -1 && alembic upgrade head && alembic check`, `migration_compat.sh`, targeted API tests (`test_email_render.py`, `test_email_html.py`, `test_one_click.py`, `test_subscriptions.py`, `test_follows.py`, `test_mail_relay.py`, `test_isolation.py`), `ruff check/format`, and Web `eslint`, `tsc`, targeted `vitest`, `next build`
- [X] T015 Update `**Status**` in `specs/060-investor-email/spec.md` to `Built, awaiting review` and mark all tasks `[X]`
