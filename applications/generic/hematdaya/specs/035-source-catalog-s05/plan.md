# Implementation Plan: Source catalog and simulated setup

**Branch**: `035-source-catalog-s05` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
app/catalog/
├── router.py
├── model/{models.py, schema.py}
└── service/{catalog.py, enrollment.py}
migrations/versions/0013_create_enrollments.py
src/features/sources/{CatalogStep.tsx, CapabilityStep.tsx, ConnectStep.tsx, ReviewStep.tsx, useSourceDraft.ts}
src/app/(tabs)/(beranda,perangkat,saran)/sumber.tsx
```

## Summary

Honest catalog plus a simulated path sharing the shape of real enrollment.

## API Contract

| Route | Behaviour |
|---|---|
| `GET /api/v1/device-catalog` | Entries with status |
| `POST /api/v1/sites/{site_id}/enrollments` | `Idempotency-Key`; simulated provider only |
| `GET /api/v1/enrollments/{id}` | Status, expiry, first reading |
| `POST /api/v1/enrollments/{id}/confirm` | Name, scope, asset, effective time |

## Prototype Reference

`Source` in `hematdaya-app.js`, `firstReading`, `saveSource`, test AT-42.

## Test Plan

Planned path; draft retained; simulated flow; retry; existing asset binding; expiry; no credential fields; no "Terhubung".

## Out of Scope

Real adapters (046).

## Task Outline

1. Catalog data.
2. Enrollment service with idempotency.
3. Steps on mobile.
4. Flip registry.
