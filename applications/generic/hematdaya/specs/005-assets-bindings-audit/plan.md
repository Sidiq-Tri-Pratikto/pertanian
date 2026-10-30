# Implementation Plan: Assets, bindings and audit

**Branch**: `005-assets-bindings-audit` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Summary

The asset and source model, relations, and the audit trail. No readings yet.

## Technical Context

**Storage**: Postgres; `btree_gist` extension for the partial `EXCLUDE`
**Testing**: fake repositories for rules; integration for constraints

## Constitution Check

No topology editor: a parent reference and an unknown-overlap relation are enough for v1 (PRD §5.2).

## Project Structure

```text
app/assets/
├── router.py
├── model/{models.py, schema.py}
├── repository/{base_repository.py, sqlalchemy/}
└── service/{service.py, relations.py}
app/audit/
├── model/models.py
├── repository/{base_repository.py, sqlalchemy/}
└── service/service.py              # AuditService.record(...)
migrations/versions/0002_create_assets_sources_bindings.py
migrations/versions/0003_create_audit_events.py
```

## API Contract

| Route | Behaviour |
|---|---|
| `GET /api/v1/sites/{site_id}/assets` | Active by default, `include_archived=true` adds archived; deterministic order by name then ID |
| `POST /api/v1/sites/{site_id}/assets` | Name, scope kind, optional category, location, parent, expected use |
| `GET /api/v1/assets/{asset_id}` | Includes bindings and sources |
| `PATCH /api/v1/assets/{asset_id}` | Name, category, location, expected use, `archived` |
| `POST /api/v1/assets/{asset_id}/bindings` | Source, effective from, authoritative |
| `DELETE /api/v1/assets/{asset_id}/bindings/{binding_id}` | Sets `effective_to`; history stays |

## Data Model

Columns as listed in `docs/roadmap/architecture.md`. Binding constraint:

```sql
exclude using gist (asset_id with =, tstzrange(effective_from, effective_to) with &&) where (authoritative)
```

Cycle check in the service with a depth-limited walk of `parent_asset_id`; same-site check by composite lookup.

## Errors

| Code | Public | HTTP | Trigger |
|---|---|---|---|
| `APP-ASSET-CYCLE` | `INVALID_RELATION` | 400 | Self-reference or cycle |
| `APP-BINDING-OVERLAP` | `CONFLICT` | 409 | Authoritative range overlap |

## Prototype Reference

`addAsset`, `addSource`, `bind`, `bound`, `assetById`, `KIND_LABEL` in `hematdaya-domain.js`.

## Test Plan

Rename keeps ID; duplicate names; category does not set expected use; cycle and self-reference; cross-site parent; binding end keeps row; authoritative overlap; non-authoritative overlap allowed; audit in success, none on rollback; owner isolation for all routes.

## Out of Scope

Mobile edit UI (016), scope selection (009, 028), real source enrollment (035).

## Task Outline

1. Migrations with constraints.
2. Failing tests.
3. Audit service.
4. Assets service, relations, repositories.
5. Router and schemas; regenerate contract.
6. Extend AT-41 test.
