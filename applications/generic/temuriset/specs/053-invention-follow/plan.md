# Implementation Plan: Follow an invention by email (revamp R6)

**Spec**: [spec.md](spec.md)

## API

1. `migrations/versions/0025_invention_follows.py`; records in `app/subscriptions/repository/sqlalchemy/models.py`.
2. `app/subscriptions/service/follows.py`: `FollowService` (follow, preview, confirm, read, set_language, unfollow, fan_out), `follow_deliverable`, and the `follows.update_fanout` consumer (registered in `app/worker/__main__.py`). One transaction per fan-out (`ponytail:` note).
3. `app/subscriptions/service/service.py`: `rate_limit()` shared by both flows; `subscription_deliverable` rechecks every invention a queued alert or digest names.
4. `app/identity/service/mailbox_service.py` and `mail_jobs.py`: `MailReference.subjects` sealed with the message; kind `follow`.
5. `app/subscriptions/service/mail.py`: confirmation, already-following and update emails in both languages, from `UI-COPY.json`.
6. `app/demo/service/fixtures.py` and `data.py`: `PUBLIC_PAGES` for F01 and F02 with a generated PNG illustration (standard library only).

## Web

1. `features/subscriptions/FollowForm.tsx` on the public page when following is on.
2. `views/subscriptions/FollowConfirmView.tsx` and `FollowManageView.tsx`; routes `app/ikuti/konfirmasi` and `app/ikuti/atur` with `referrer: no-referrer`.
3. `features/i18n`: `follow` copy in both catalogs; `/en/follow/...` maps to `/ikuti/...`.
4. `next.config.ts`: token pages left out of request logs.

## Tests

API: `tests/integration/subscriptions/test_follows.py` (each update once across two inventions with one unfollowed and one switched to English; same answer for every address and a raced confirmation; nothing for followers confirmed after publication; queued follow and alert mail dropped through the real relay), isolation entries, migration round trip, demo seed. Web: `tests/follow.test.tsx`; `e2e/routes.ts` adds four token pages; `e2e/follow.spec.ts` runs the English journey end to end.
