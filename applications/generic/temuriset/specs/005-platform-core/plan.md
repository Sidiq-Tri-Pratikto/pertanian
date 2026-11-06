# Implementation Plan: Platform core

**Branch**: `005-platform-core` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

## Summary

Cross-cutting primitives every feature uses. No product feature ships here, so no registry entry flips. The actor is a placeholder `party_id` header in tests until 007 supplies the real acting party.

## Project Structure

```text
app/core/clock.py                     # now(), freezable in tests
app/core/types.py                     # Money (string-only decimal), CurrencyCode, Cursor
app/platform/
├── router.py                         # GET /operations/{id}
├── model/{models.py, schema.py}
├── repository/sqlalchemy/{models.py, repository.py}   # idempotency_records, audit_events, outbox_events,
│                                                      # outbox_deliveries, jobs
├── service/idempotency.py            # dependency: begin, replay, conflict, complete
├── service/audit.py                  # record(action, subject, detail)
├── service/outbox.py                 # publish(topic, payload)
└── service/versions.py               # check_expected(current, expected)
app/worker/
├── __main__.py                       # python -m app.worker
├── registry.py                       # topic -> consumers
└── loop.py                           # claim, run, record delivery, backoff
migrations/versions/0001_platform.py
```

## Contract

`GET /api/v1/operations/{id}` → `{"operation_id": "...", "status": "COMMITTED", "result": {"type": "pitch", "id": "..."}}`; statuses `PENDING`, `COMMITTED`, `UNKNOWN`.

Request digest: SHA-256 of actor party, operation name, request path and the canonical JSON body (sorted keys). Stored response: status code and body.

## Prototype Reference

`domain.js`: `mutate()` (key replay, conflict, pre-commit failure, lost-after-commit). Port its four cases as tests.

## Test Plan

Replay, conflict, missing key, stale version, pending completion, parallel keys, operation visibility per actor, outbox atomic with rollback, consumer failure and retry, duplicate delivery ignored, two workers, frozen clock.

## Out of Scope

Real consumers (027), jobs with business meaning (028, 036).

## Task Outline

1. Clock, Money, cursor types with tests.
2. Migration and repositories.
3. Idempotency dependency and operations route.
4. Audit and outbox services with transaction tests.
5. Worker loop, registry, deliveries, backoff.
6. Error codes and catalog.
