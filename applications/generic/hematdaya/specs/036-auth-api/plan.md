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

Real owner accounts with revocable sessions and one standard site for the pilot release. Validate core owner isolation using the existing demo and import surfaces. The lab access mechanism in 046 can be developed in parallel.

## Decisions to Take in This PR

- **Web sessions**: use an `HttpOnly`, `Secure`, `SameSite` refresh cookie with CSRF protection and a bearer access token in memory. Native keeps refresh in `expo-secure-store`. Document the same-site deployment and exact origin policy for 039.
- **Rate limiting**: use atomic Postgres counters across instances. Apply them to auth, per-client demo admission alongside the shared budget in 008, and per-principal import preview alongside the file and row limits in 025. Resolve anonymous client identity at trusted ingress and avoid recording the raw identifier in telemetry. 038 applies the shared limiter to exports when those routes ship. Revisit storage only if 041 shows a need.
- **Credentials**: hash passwords with `argon2-cffi`. Store hashes of short-lived opaque access tokens and rotating refresh tokens, scoped to the same session family. Authorize each request against expiry and family state.

## Rotation and revocation

Lock the session family during rotation. Mark the presented refresh token consumed and create its replacement in one transaction. Retain consumed hashes until the family expires so replay can be detected. A known consumed token revokes that family before the typed error is sent. Use the shared error envelope and record. Commit the security state before returning the error response. A rollback must never report successful rotation or logout. An unknown token cannot revoke an arbitrary family.

## Settings

`ACCESS_TOKEN_MINUTES`, `REFRESH_TOKEN_DAYS`, cookie/origin settings and rate limits. Validate bounds at startup and list them in `.env.example`.

## Prototype Reference

None: the prototype deliberately had no authentication.

## Test Plan

Register, login, concurrent refresh on independent connections, committed reuse revocation, logout, expiry, enumeration resistance, rate limit across instances, route walk for isolation, sanitizer, demo data access and refusal on account-only routes. Assert a replacement token and a previously issued access token are both rejected after reuse.

## Out of Scope

Team permissions, social login, cross-site dashboards.

## Task Outline

1. Decide and record web session handling.
2. Migration.
3. Passwords and tokens, tests first.
4. Router and resolver.
5. Apply and test auth, demo and import rate limits. Document how 038 attaches export limits.
6. Route-walk isolation test.
