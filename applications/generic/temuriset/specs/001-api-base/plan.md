# Implementation Plan: API base

**Branch**: `001-api-base` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

## Summary

Instantiate product-starter-wdd (commit 8f9f07e) with `scripts/init.py --name temuriset --app temuriset-api`, drop the `items` example and its migration, reuse HematDaya's reviewed Indonesian error layer and health routes, and add the TemuRiset capability manifest and the no-money-movement route test.

## Technical Context

**Language/Version**: Python 3.13, FastAPI, Pydantic, SQLAlchemy async, Alembic
**Storage**: Postgres 17 on host port 5442; no tables yet
**Testing**: pytest; integration through `make run-dependencies`
**Target Platform**: Linux container
**Project Type**: Web client plus API

## Constitution Check

Principle 1: three compositions only, the ones PRD section 21 asks to prove. Principle 6 and the product boundary: route-table test. No migration exists to drop later.

## Project Structure

```text
applications/temuriset-api/app/
├── capabilities/
│   ├── router.py                 # GET /capabilities
│   ├── model/schema.py           # manifest models, with locale and currencies
│   └── service/service.py        # capabilities, adapters, policies, compositions
├── core/errors/public.py         # Indonesian messages, field_message()
├── core/errors/handlers.py       # Indonesian field messages in validation details
├── health/router.py              # /health/live, /health/ready
└── main.py                       # API_PREFIX, startup validation
tests/unit/capabilities/test_capabilities.py
tests/unit/core/test_no_transaction_routes.py
contracts/openapi.json
```

## API Contract

`GET /api/v1/capabilities` → 200:

```json
{
  "schema_version": 1,
  "source_release": "0.1.0",
  "composition": {"id": "generic-base", "version": 1},
  "default_locale": "id",
  "supported_currencies": ["IDR", "USD"],
  "capabilities": [{"id": "core", "optional": false, "status": "planned"},
                   {"id": "company_funding", "optional": true, "status": "planned"}],
  "adapters": [{"id": "object-storage", "status": "planned"}, {"id": "file-scanner", "status": "planned"},
               {"id": "lexical-rules", "status": "planned"}, {"id": "ics-export", "status": "planned"}],
  "policies": [{"id": "matching-weights", "version": 1}, {"id": "fit-thresholds", "version": 1},
               {"id": "pitch-rate-limit", "version": 1}, {"id": "resubmission-pause", "version": 1},
               {"id": "proposal-expiry", "version": 1}, {"id": "idempotency-retention", "version": 1}]
}
```

`status` is `planned`, `simulated` or `available`.

## Test Plan

Manifest fields and honest statuses for all three compositions; invalid compositions; unknown composition stops startup; no money-movement routes; Indonesian validation details without echoed values; liveness without a database; readiness failure envelope; readiness against Postgres.

## Out of Scope

Authorization, tables, the capability guard on routes (004).
