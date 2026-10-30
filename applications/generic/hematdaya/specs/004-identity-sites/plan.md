# Implementation Plan: Identity and sites

**Branch**: `004-identity-sites` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Summary

First tables and the authorization shape every later route uses. Nothing can authenticate yet in production, so protected routes answer `UNAUTHORIZED` until demo sessions arrive in 008.

## Technical Context

**Storage**: Postgres; first real migration
**Testing**: unit tests with fake repositories; integration tests with two principals through dependency overrides

## Constitution Check

Smallest design: one dependency, no role model, no tenant concept. Failure paths include a foreign site.

## Project Structure

```text
app/identity/
├── model/models.py                 # PrincipalModel
├── repository/{base_repository.py, sqlalchemy/}
├── service/service.py
└── dependencies.py                 # get_current_principal, PrincipalResolver protocol
app/sites/
├── router.py                       # GET, PATCH /sites/{site_id}
├── model/{models.py, schema.py}    # SiteModel, UpdateSiteRequest, SiteResponse
├── repository/{base_repository.py, sqlalchemy/}
└── service/{service.py, clock.py}  # site_clock
migrations/versions/0001_create_principals_and_sites.py
```

## API Contract

| Route | Behaviour |
|---|---|
| `GET /api/v1/sites/{site_id}` | Owner only; `name`, `kind`, `context`, `timezone`, `currency`, `now` |
| `PATCH /api/v1/sites/{site_id}` | Name, context, timezone; validated; audited from 005 |

## Data Model

```sql
principals(id uuid pk, kind text check (kind in ('demo','user')), created_at timestamptz)
sites(id uuid pk, owner_principal_id uuid references principals not null,
      kind text check (kind in ('demo','standard')), name text not null,
      context text check (context in ('household','business','industry','unspecified')) default 'unspecified',
      timezone text not null default 'Asia/Jakarta', currency text not null default 'IDR',
      virtual_now timestamptz, created_at timestamptz,
      check (virtual_now is null or kind = 'demo'))
```

Index `sites(owner_principal_id)`.

## Errors

| Code | Public | HTTP | Note |
|---|---|---|---|
| `APP-AUTH-REQUIRED` | `UNAUTHORIZED` | 401 | Add a `headers` attribute to `AppError` and forward it in `handle_app_error`, so `WWW-Authenticate` is sent |

## Prototype Reference

`emptyWorkspace`, `off`, `localMidnight`, `localDate`, `weekday` in `hematdaya-domain.js`. Use `zoneinfo`, not fixed offsets.

## Test Plan

Owner read; foreign read returns 404; missing credentials returns 401 with header; invalid timezone; CHECK on `virtual_now`; `site_clock` for both kinds; composition unaffected.

## Out of Scope

Creating sites over HTTP (008 creates demo sites; 036 standard ones), users, sessions.

## Task Outline

1. Migration and ORM records.
2. Failing tests for isolation and clock.
3. Identity module and `get_current_principal`.
4. Sites service, router, `site_clock`.
5. Forward error headers; catalog row.
6. Integration tests with two principals.
