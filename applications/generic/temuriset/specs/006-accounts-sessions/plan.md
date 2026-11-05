# Implementation Plan: Accounts and sessions

**Branch**: `006-accounts-sessions` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

## Summary

`identity` module with passwordless email codes, server-side sessions and a development mailbox; personal parties created at verification. Settings gain `WEB_ORIGIN`, `SESSION_COOKIE_SECURE`, `MAILBOX_ADAPTER`.

## Project Structure

```text
app/identity/
├── router.py                     # /auth/code, /auth/verify, /auth/sign-out, /me (GET, PATCH)
├── model/{models.py, schema.py}
├── repository/sqlalchemy/{models.py, repository.py}   # accounts, email_codes, sessions, mailbox_messages
├── service/service.py            # request_code, verify, sign_out, current_principal
├── service/codes.py              # generate, hash, constant-time compare, attempts
├── service/rate_limit.py         # Postgres counters per email and per address, window 1 h
└── service/mailbox_service.py    # MailboxAdapter protocol; DevelopmentMailbox
app/access/repository/sqlalchemy/models.py   # parties (personal only for now)
app/core/security.py              # SessionDep, current principal, Origin check middleware
app/dev/router.py                 # GET /dev/mailbox, only when ENVIRONMENT=development
migrations/versions/0002_identity.py
```

## API Contract

- `POST /api/v1/auth/code` `{email, purpose: "sign_up"|"sign_in", display_name?, locale?, time_zone?, persona?}` → 202 `{"sent": true}` always.
- `POST /api/v1/auth/verify` `{email, code}` → 200 `Me` and `Set-Cookie: tr_session=...`.
- `POST /api/v1/auth/sign-out` → 204, cookie cleared.
- `GET /api/v1/me` → `{"account": {"id", "display_name", "email", "email_verified": true, "locale", "time_zone", "persona", "kind"}, "personal_party_id", "active_party_id", "organizations": []}`.
- `PATCH /api/v1/me` `{display_name?, locale?, time_zone?, persona?, expected_version}`.

Codes: `UNAUTHENTICATED` 401, `CODE_INVALID` 422 (not retryable, states attempts left), `CODE_EXPIRED` 422, `RATE_LIMITED` 429 (retryable, `retry_after_seconds`), `FORBIDDEN` 403 for a failed origin check.

## Security Notes

Codes: `secrets.randbelow(10**6)`, stored as SHA-256 with a per-row salt, 10-minute expiry, five attempts. Tokens: `secrets.token_urlsafe(32)`, stored as SHA-256. Rate limits count in Postgres so any instance enforces them. Logs carry account IDs only.

## Test Plan

AC01 and AC02 as integration tests; wrong, expired and exhausted codes; rate limits; existence not leaked; sign-out; cross-origin POST refused; production refuses the development mailbox; sessions survive a restart; `PATCH /me` stale version.

## Out of Scope

Organizations and memberships (007), web screens (008), real email delivery (042), demo accounts (021).

## Task Outline

1. Migration and repositories, failing AC01/AC02 tests.
2. Codes, rate limits, mailbox adapter.
3. Verify, sessions, cookie, principal dependency, origin middleware.
4. `/me` and `PATCH /me`.
5. Error codes, catalog, contract.
