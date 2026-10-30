# Implementation Plan: Demo sessions

**Branch**: `008-demo-sessions` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Summary

Turn scenarios into isolated seeded sites behind an anonymous token. First PR where a real client can authenticate.

## Project Structure

```text
app/demo/
├── router.py                        # scenarios, sessions, reset
├── model/{models.py, schema.py}
├── repository/{base_repository.py, sqlalchemy/}
└── service/{service.py, seed.py}    # set-based seeding
migrations/versions/0005_create_demo_sessions.py
```

## API Contract

| Route | Behaviour |
|---|---|
| `GET /api/v1/demo/scenarios` | ID, name, description, segment. Public |
| `POST /api/v1/demo/sessions` | Body `{scenario_id}`. Returns `{token, site_id, expires_at, initial_period}` once |
| `POST /api/v1/demo/sessions/current/reset` | Reseeds the caller's site |
| `DELETE /api/v1/demo/sessions/current` | Ends the session and deletes its data |

## Settings

`DEMO_SESSION_TTL_HOURS` (72), `DEMO_MAX_ACTIVE_SESSIONS` (200), both in `.env.example`.

## Data Model

```sql
demo_sessions(id uuid pk, principal_id uuid references principals on delete cascade not null,
  site_id uuid references sites on delete cascade not null, scenario_id text not null,
  token_hash bytea unique not null, expires_at timestamptz not null, created_at timestamptz)
```

Index `(expires_at)`. Sites cascade to assets, sources, bindings and measurements, so purge is one delete per expired site.

## Errors

| Code | Public | HTTP | Recovery |
|---|---|---|---|
| `APP-DEMO-CAPACITY` | `RATE_LIMITED` | 429 | Retryable, 60 s |
| `APP-SESSION-EXPIRED` | `SESSION_EXPIRED` | 401 | Not retryable; client starts a new session |
| `APP-SCENARIO-UNKNOWN` | `NOT_FOUND` | 404 | Not retryable |

## Prototype Reference

`buildScenario`, reset in `DemoInfo` of `hematdaya-app.js`, isolation behaviour.

## Test Plan

Create, read, isolation between sessions, reset scope, expiry, purge at creation, cap, malformed token, token never logged (sanitizer test with fake secret), empty scenario, foreign site.

## Out of Scope

Rate limits per client (036), mobile UI (012).

## Task Outline

1. Migration and tests.
2. Token generation and hashing.
3. Set-based seed.
4. Session service with cap and purge.
5. Resolver in `get_current_principal`.
6. Router; flip `demo` adapter; regenerate contract.
