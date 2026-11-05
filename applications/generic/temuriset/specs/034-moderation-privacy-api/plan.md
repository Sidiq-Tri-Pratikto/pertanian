# Implementation Plan: Reports, moderation and privacy requests

**Branch**: `034-moderation-privacy-api` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
applications/temuriset-api/
├── app/moderation/router.py
├── app/moderation/__main__.py
├── app/moderation/service/{reports,suspension,privacy,retention}.py
├── app/moderation/repository/sqlalchemy/
├── app/access/service/policy.py
├── app/documents/service/{jobs,service,storage_service}.py
└── migrations/versions/0009_moderation.py
```

The merged migration chain ends at 0008. Revision 0009 adds reports, scoped grants, listing suspensions, privacy requests, retention policies and holds. It adds document states for pending erasure and erased bytes.

The API exposes account-scoped reads and writes at `/reports` and `/privacy-requests`, including the fresh export download. Live operator scope gates `/operator/reports` and `/operator/privacy-requests`, including case actions, protected case-file downloads and fulfilment. The local administration command manages scoped grants.

## Test Plan

AC64 and AC66, current public listing reads and suspension effects, report and export isolation, operator scope, exact file grants, retention holds, and erase retry. Spec 018 owns the deferred public discovery projection check. Production outcome mail depends on 042.

## Out of Scope

Web (035), legal process.

## Task Outline

1. Reports and operator queue.
2. Suspension effects.
3. Privacy requests with retention policy data.
