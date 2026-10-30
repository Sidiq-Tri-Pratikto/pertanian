# Implementation Plan: Scope API

**Branch**: `028-scope-api` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
app/scope/
├── router.py
├── model/{models.py, schema.py}
├── repository/{base_repository.py, sqlalchemy/}
└── service/{service.py, validity.py}
migrations/versions/0010_create_aggregation_selections.py
```

## Summary

Persist the selection that 009 assumed to be all assets, and add resolution operations.

## API Contract

| Route | Behaviour |
|---|---|
| `GET /api/v1/sites/{site_id}/aggregation-selection` | Assets, revision, issues, relations |
| `PUT /api/v1/sites/{site_id}/aggregation-selection` | Asset IDs and `disjoint_confirmations[]` |
| `POST /api/v1/assets/{asset_id}/source-authority` | Source, effective from, or skip |

## Errors

`APP-SCOPE-OVERLAP` → `SCOPE_CONFLICT` (409) with the overlapping names in `details`.

## Prototype Reference

`scopeIssues`, `saveScope`, `Scope` in `hematdaya-app.js`, tests AT-35, AT-36, AT-36b.

## Test Plan

Oracles; refusal; disjoint confirmation; authority change keeps rows; stale main meter; failed save; audit; foreign asset.

## Out of Scope

Phase-total adapters (046), topology editor.

## Task Outline

1. Migration.
2. Failing oracle tests.
3. Service.
4. Summary reads saved selection.
5. Router and contract.
