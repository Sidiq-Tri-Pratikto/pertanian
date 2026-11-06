# Implementation Plan: Data rights

**Branch**: `038-data-rights` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
app/exports/
├── router.py
├── model/{models.py, schema.py}
├── repository/{base_repository.py, sqlalchemy/}
└── service/{export.py, deletion.py, csv_safety.py}
migrations/versions/0015_create_exports_and_deletions.py
src/features/account/{ExportSection.tsx, DeleteSiteSheet.tsx}
```

## Summary

Export, delete, and stated retention.

## API Contract

`POST /api/v1/sites/{site_id}/exports`, `GET /api/v1/exports/{id}`, `DELETE /api/v1/sites/{site_id}`, and `GET /api/v1/sites/{site_id}/deletion-status`.

Authorize each download through the API against the owner, export expiry and site deletion state. The link must never bypass that check by pointing to public or independently authorized storage. Bound export size and apply 036's shared rate limiter.

After explicit scope confirmation, mark the site unavailable and create its deletion record in one transaction. The record carries the owner, site ID, request time, status, and configured purge/backup deadlines. Keep status lookup available to that owner after active site data is gone. Foreign callers receive `NOT_FOUND`. Make a repeated deletion return the same request. Purge jobs use retry-safe transitions and publish status without returning deleted content.

Persist a minimal deletion intent in the independent durable ledger before acknowledging deletion. Reconcile an interrupted request by the same deletion ID and complete outstanding revocation during recovery. Retain the marker for the lifetime of applicable backups. 040 specifies how to verify and apply it before a restored database can serve traffic.

## Test Plan

- Export content, formula safety with `=`, `+`, `-`, `@`, tab, round trip, expiry.
- Owner only, explicit deletion scope, repeat request, old export link revoked.
- Owner can poll purge after site removal, foreign status returns `NOT_FOUND`, purge retry and deadline using a controlled clock, demo reset unaffected.

## Out of Scope

Legal retention policy text, which the owner must supply.

## Task Outline

1. CSV safety tests.
2. Export service.
3. Deletion service.
4. Mobile sections.
