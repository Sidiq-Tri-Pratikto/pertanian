# Implementation Plan: Accounts API

**Branch**: `036-auth-api` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
app/auth/
├── router.py
├── model/{models.py, schema.py}
├── repository/{base_repository.py, sqlalchemy/}
└── service/{passwords.py, tokens.py, service.py, rate_limit.py}
migrations/versions/0014_create_users_and_sessions.py
```

## Summary

Real accounts with revocable sessions, plus the web session decision.

## Decisions to Take in This PR

- **Web sessions**: recommended, an `HttpOnly`, `Secure`, `SameSite` cookie for refresh on web, with CSRF protection; bearer access token in memory. Native keeps refresh in `expo-secure-store`.
- **Rate limiting**: Postgres counters first. Add Redis only if 041 shows a need.
- **Library**: `argon2-cffi`; access tokens as signed JWT with short expiry, or opaque with a lookup. Justify the choice in the PR.

## Settings

`JWT_SECRET` or key reference, `ACCESS_TOKEN_MINUTES`, `REFRESH_TOKEN_DAYS`, rate limits. No default secret in production.

## Prototype Reference

None: the prototype deliberately had no authentication.

## Test Plan

Register, login, refresh rotation, reuse detection, logout, expiry, enumeration resistance, rate limit, route walk for isolation, sanitizer, demo principal still works.

## Out of Scope

Team permissions, social login, cross-site dashboards.

## Task Outline

1. Decide and record web session handling.
2. Migration.
3. Passwords and tokens, tests first.
4. Router and resolver.
5. Rate limits on auth, imports, exports.
6. Route-walk isolation test.
