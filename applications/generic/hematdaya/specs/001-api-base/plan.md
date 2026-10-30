# Implementation Plan: API base

**Branch**: `001-api-base` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Summary

Trim the starter service to a truthful base: capability manifest, PRD health routes, Indonesian failures, committed contract. No tables exist yet.

## Technical Context

**Language/Version**: Python 3.13, FastAPI, Pydantic
**Storage**: Postgres 17 configured; no migrations yet
**Testing**: pytest, Postgres through `make run-dependencies`
**Target Platform**: Linux container
**Project Type**: Mobile plus API

## Constitution Check

Monitoring only (principle 6): route table test. Smallest diff: the `items` example was removed in the bootstrap commit, so no migration exists to drop later.

## Project Structure

```text
applications/hematdaya-api/app/
├── capabilities/
│   ├── router.py                 # GET /capabilities
│   ├── model/schema.py           # manifest response models
│   └── service/service.py        # compositions, validation, manifest
├── core/errors/public.py         # Indonesian messages, field_message()
├── core/errors/handlers.py       # field messages in validation details
├── health/router.py              # /health/live, /health/ready
└── main.py                       # API_PREFIX, startup validation
tests/unit/capabilities/test_capabilities.py
tests/unit/core/test_read_only_contract.py
contracts/openapi.json
```

## API Contract

`GET /api/v1/capabilities` → 200:

```json
{
  "schema_version": 1,
  "source_release": "0.1.0",
  "composition": {"id": "core-plus-optional", "version": 1},
  "capabilities": [{"id": "core", "optional": false, "status": "planned"}],
  "adapters": [{"id": "demo", "status": "planned"}],
  "policies": [{"id": "baseline", "version": 1}]
}
```

`status` is `planned`, `simulated` or `available`. There is deliberately no `connected`.

## Test Plan

- Manifest fields and honest statuses; core-only; invalid compositions; unknown composition stops startup.
- Route table has no actuation path.
- Validation details are Indonesian and never echo values.
- Liveness without a database; readiness failure envelope; readiness against real Postgres.

## Out of Scope

Authorization, tables, capability guards on routes (011).
