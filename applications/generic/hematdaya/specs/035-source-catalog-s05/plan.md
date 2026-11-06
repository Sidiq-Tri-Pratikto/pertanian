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
| `GET /api/v1/device-catalog` | Entries with status, measurement kind, cadence and channel scope |
| `POST /api/v1/sites/{site_id}/enrollments` | `Idempotency-Key`; simulated provider only |
| `GET /api/v1/enrollments/{id}` | Status, expiry, first reading and stored confirmation result |
| `POST /api/v1/enrollments/{id}/confirm` | `Idempotency-Key` plus name, scope, asset, effective time |

Use the manifest and registry to decide whether the catalog can offer the CSV flow from 027. A missing path leaves a return to the catalog.

Authorize each enrollment through its owning site. On confirmation, acquire the shared site row lock and lock the enrollment. Verify its server-assigned simulated source identity and first reading, and check expiry for pending attempts. In one transaction, create or bind the asset at the reviewed effective time, ingest the first reading, and store the confirmation payload identity and result. A replay of the same operation returns that result, even if the original pending TTL has elapsed. Reject a different payload for a consumed enrollment. An injected write failure leaves no asset, binding, or reading from that confirmation.

## Prototype Reference

`Source` in `hematdaya-app.js`, `firstReading`, `saveSource`, test AT-42.

## Test Plan

- Planned path, CSV available and unavailable, draft retained, simulated flow.
- Lost-response and concurrent confirmation replay, consumed enrollment with a different payload, existing asset binding, expired pending enrollment.
- Atomic rollback, foreign enrollment, no credential fields, no "Terhubung".

## Out of Scope

Real adapters (046).

## Task Outline

1. Catalog data.
2. Enrollment service with idempotency.
3. Steps on mobile.
4. Flip registry.
