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
| `POST /api/v1/demo/sessions` | Body `{scenario_id}`. Requires `Idempotency-Key` with at least 128 random bits and `X-Demo-Replay-Proof` with at least 256 separate random bits. Creation and a valid bounded replay both return the same `{token, site_id, expires_at, initial_period}`. |
| `POST /api/v1/demo/sessions/current/reset` | Reseeds the caller's site |
| `DELETE /api/v1/demo/sessions/current` | Ends the session and deletes its data |

## Settings

`DEMO_SESSION_TTL_HOURS` (72), `DEMO_MAX_ACTIVE_SESSIONS` (200), `DEMO_CREATE_MAX_PER_MINUTE` (30) and `DEMO_CREATE_REPLAY_SECONDS` (300) in `.env.example`. Replay duration must be shorter than session TTL. Use a dedicated secret HMAC key with a version identifier and no tracked value. Retain the preceding key until its replay windows close.

## Data Model

```sql
demo_sessions(id uuid pk, principal_id uuid references principals on delete cascade not null,
  site_id uuid references sites on delete cascade not null, scenario_id text not null,
  token_hash bytea unique not null, expires_at timestamptz not null, created_at timestamptz not null)
demo_create_operations(operation_id text pk, session_id uuid references demo_sessions on delete set null,
  scenario_id text not null, replay_proof_hash bytea not null, key_version text not null,
  initial_period jsonb not null, replay_expires_at timestamptz not null,
  retain_until timestamptz not null, created_at timestamptz not null)
```

Index the session expiry and operation retention deadlines. Keep the original response's initial period as immutable creation metadata. Keep operation IDs through the original session expiry even when the session is explicitly ended first, so a late retry cannot recreate it. Purge an expired demo's site and its dependent records, then its dedicated principal, in one transaction. After purge the API can no longer recognize the token or replay the response. Remove operation records after their own retention deadline.

## Admission, replay and reset

1. Validate key/proof format and the canonical scenario payload. Use one PostgreSQL transaction and a shared database lock for admission and new seeding across instances. Look up an existing operation under the lock before consuming capacity. Constant-time compare the proof digest before checking payload, live session or deadline. Wrong proof returns generic 404. Correct proof with different payload, ended session or elapsed replay window returns 409. Matching in-window replay returns the immutable original response and uses no new capacity.
2. For a new operation, purge expired sessions and operation records. Enforce active capacity and a shared one-minute budget for new anonymous seeds. Count admitted operations in that wall-clock window, including ended sessions whose operation records remain. Reserve and seed in the same transaction. Return 429 before starting a seed when no capacity remains. A failure before commit leaves no new operation, session or seed.
3. Derive the opaque bearer token with versioned HMAC-SHA-256 over an unambiguous encoding of a demo-create domain label, session ID, operation ID and replay proof. Store the bearer and proof digests and key version. On replay, derive the same token from the supplied proof. Redact both headers and the returned token from logs and traces. The client retains the pair only for the bounded recovery window and uses a new pair for a new create intent.
4. Resolve the current session and take 005's shared site write lock before reset, then revalidate the session in that transaction. Replace only that site's scenario state, retaining the original token, site ID and expiry. Use the same set-based 006 ingestion path as creation. Advance the site's binding and measurement revisions for a committed replacement. A failed reset leaves the prior workspace intact. Purge and explicit end also take the affected site locks. Admission takes the shared admission lock first and any site locks in ID order. Reset and explicit end take the site lock only.

Seed optional fixture inputs when their modules provide storage in 018, 030 and 032. The core fixture and its label work before those modules. Keep the simulated demo label separate from the historical view and from actual CSV provenance.

## Errors

| Code | Public | HTTP | Recovery |
|---|---|---|---|
| `APP-DEMO-CAPACITY` | `RATE_LIMITED` | 429 | Retryable, 60 s, maximum 3 total attempts with matching `Retry-After` |
| `APP-SESSION-EXPIRED` | `SESSION_EXPIRED` | 401 | Not retryable; client starts a new session |
| `APP-SCENARIO-UNKNOWN` | `NOT_FOUND` | 404 | Not retryable |
| `APP-DEMO-REPLAY-PROOF-MISMATCH` | `NOT_FOUND` | 404 | Generic, not retryable |
| `APP-DEMO-REPLAY-CONFLICT` | `CONFLICT` | 409 | Verified replay with different payload, ended session or elapsed window. Not retryable. The client can start a new operation explicitly. |

## Prototype Reference

`buildScenario`, reset in `DemoInfo` of `hematdaya-app.js`, isolation behaviour.

## Test Plan

Create, read, exact seeded H rows, empty scenario, isolation, scoped reset and reset rollback. Race distinct operations for the last slot and two copies of one operation. Test a lost response, matching replay, wrong proof, changed payload, elapsed window, replay after explicit session end, shared rate budget, expiry before and after purge, removal of the orphan principal, malformed token and foreign site. Inject fake bearer and proof values and verify neither appears in logs or error bodies.

## Out of Scope

Per-client rate limits (036) and mobile UI (012). This spec includes the shared anonymous creation budget.

## Task Outline

1. Migration and tests.
2. Replay proof, token derivation and hashing.
3. Set-based seed through the shared ingestion service.
4. Session service with atomic admission, replay, reset and purge.
5. Resolver in `get_current_principal`.
6. Router and error catalog, flip the `demo` adapter, and regenerate the contract.
