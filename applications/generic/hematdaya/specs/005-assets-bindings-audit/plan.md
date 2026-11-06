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
| `GET /api/v1/sites/{site_id}/assets` | Active by default, `include_archived=true` adds archived. `limit` up to 100 and an opaque cursor over deterministic name/ID ordering. |
| `POST /api/v1/sites/{site_id}/assets` | Name, scope kind, optional category, location, parent, expected use |
| `GET /api/v1/assets/{asset_id}` | Includes bindings and sources |
| `PATCH /api/v1/assets/{asset_id}` | Name, category, location, expected use, `archived` |
| `POST /api/v1/assets/{asset_id}/bindings` | Source, effective from, authoritative. Resolve the source within the asset's owned site before binding it. |
| `DELETE /api/v1/assets/{asset_id}/bindings/{binding_id}` | Resolve the binding under the named owned asset. Close an open binding at site time only if it has started and the range remains nonempty. An already closed binding is a no-op. Reject an attempted empty range with a field error. |

## Data Model

Columns as listed in `docs/roadmap/architecture.md`. Binding constraint:

```sql
check (effective_to is null or effective_to > effective_from)
exclude using gist (asset_id with =, tstzrange(effective_from, effective_to, '[)') with &&) where (authoritative)
```

Cycle check in the service with a depth-limited walk of `parent_asset_id`. Use site-scoped lookups for the parent, relation targets and source, and an asset-scoped lookup for the binding. Validate all nested IDs before mutations. Close a binding with a conditional update on its open state so concurrent retries cannot move the effective end or double-write the audit row.

Add a monotonic `binding_revision` to the site. Take the shared site write lock with `SELECT ... FOR UPDATE` on the owned site row before revalidating or changing sources, bindings, or asset and relation state affecting scope validity. Increment the revision once per changed transaction. Import and scope operations reuse the same lock through their transaction, and use the revision to detect a stale preview.

## Errors

| Code | Public | HTTP | Trigger |
|---|---|---|---|
| `APP-ASSET-CYCLE` | `INVALID_RELATION` | 400 | Self-reference or cycle |
| `APP-BINDING-OVERLAP` | `CONFLICT` | 409 | Authoritative range overlap |

## Prototype Reference

`addAsset`, `addSource`, `bind`, `bound`, `assetById`, `KIND_LABEL` in `hematdaya-domain.js`.

## Test Plan

- Rename keeps ID, duplicate names, category does not set expected use, cycle and self-reference.
- Cross-site parent, source and binding ID, binding end keeps the row and remains unchanged on replay or concurrent unlink, invalid end and adjacent valid ranges, authoritative overlap.
- Non-authoritative overlap allowed, shared site lock and revision changes only on commit, audit in success, none on rollback or no-op, owner isolation and pagination for lists.

## Out of Scope

Mobile edit UI (016), scope selection (009, 028), real source enrollment (035).

## Task Outline

1. Migrations with constraints.
2. Failing tests.
3. Audit service.
4. Assets service, relations, repositories.
5. Router and schemas; regenerate contract.
6. Extend AT-41 test.
