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

Create and persist the selection that 009 assumed to be all assets. Reuse its validity service for confirmed and proposed states.

## API Contract

| Route | Behaviour |
|---|---|
| `GET /api/v1/sites/{site_id}/aggregation-selection` | Assets, selection revision and site `binding_revision`, issues, relations, and current source authority |
| `POST /api/v1/sites/{site_id}/aggregation-selection/preview` | Evaluate proposed asset IDs, disjoint confirmations, and authority changes with the requested period. Return validity, included/excluded assets, service-calculated totals or refusal, and the revisions used. No writes |
| `PUT /api/v1/sites/{site_id}/aggregation-selection` | Commit the same proposal with expected selection revision and site `binding_revision`. Return the new confirmed revision |

Each authority change names the asset, chosen source and effective time, or an explicit skip that keeps current authority. Validate owner, site, and effective intervals for the whole proposal. Under the shared site row lock from 005, compare expected revisions, revalidate the complete proposal, then persist the selection, authority, confirmations, and audit together. Advance the selection revision for a changed selection and the site `binding_revision` for changed bindings or relations. A rejected or stale request changes none of them. Reads without a saved selection retain the default from 009.

## Errors

`APP-SCOPE-OVERLAP` → `SCOPE_CONFLICT` (409) with the overlapping names in `details`. A typed stale-proposal conflict requires a new preview.

## Prototype Reference

`scopeIssues`, `saveScope`, `Scope` in `hematdaya-app.js`, tests AT-35, AT-36, AT-36b.

## Test Plan

- Oracles, refusal, read-only preview with proposed authority, disjoint confirmation.
- Authority change keeps historical readings, stale main meter, concurrent proposal with stale revisions, rollback of selection, authority, relation, and audit after injected failure.
- Foreign site and asset.

## Out of Scope

Phase-total adapters (046), topology editor.

## Task Outline

1. Migration.
2. Failing oracle tests.
3. Service.
4. Summary reads saved selection.
5. Router and contract.
