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

`POST /api/v1/sites/{site_id}/exports`, `GET /api/v1/exports/{id}`, `DELETE /api/v1/sites/{site_id}`.

## Test Plan

Export content; formula safety with `=`, `+`, `-`, `@`, tab; round trip; expiry; owner only; deletion scope; purge status; demo reset unaffected.

## Out of Scope

Legal retention policy text, which the owner must supply.

## Task Outline

1. CSV safety tests.
2. Export service.
3. Deletion service.
4. Mobile sections.
