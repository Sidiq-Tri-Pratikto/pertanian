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
├── app/discovery/service/projection.py
├── app/{briefs,pitches}/service/
└── migrations/versions/0018_moderation.py
```

The M9 migration chain ends at 0017. Revision 0009 belongs to discovery, and revisions 0014–0017 belong to M8 and M9. The unpublished moderation migration follows them as 0018. The earlier 0009 moderation schema was exercised on isolated local databases, which need rebuilding before testing this chain. Revision 0018 adds reports, scoped grants, listing suspensions, privacy requests, retention policies and holds. It adds document states for pending erasure and erased bytes.

The API exposes account-scoped reads and writes at `/reports` and `/privacy-requests`, including the fresh export download. Live operator scope gates `/operator/reports` and `/operator/privacy-requests`, including case actions, protected case-file downloads and fulfilment. The local administration command manages scoped grants.

## Test Plan

AC64 and AC66, current public listing reads, discovery suspension and restoration, pitch preflight and submission restrictions, report and export isolation, operator scope, exact file grants, retention holds, and erase retry. Test that withdrawn listings and their documents do not expose new content while authorized participants can still see earlier frozen pitch records. Record the retained snapshot category and its reason through the existing policy data.

## Out of Scope

Web (035), legal process, discussion and scheduling (027–029), and public relationship projections (030–032). The production outcome mail adapter depends on 042.

## Task Outline

1. Reports and operator queue.
2. Suspension effects.
3. Privacy requests with retention policy data.
