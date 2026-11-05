# Implementation Plan: Private documents, grants and download gateway

**Branch**: `010-documents-api` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
app/documents/
├── router.py                     # upload intents, content upload, versions, grants, gateway
├── model/{models.py, schema.py}
├── repository/sqlalchemy/{models.py, repository.py}   # documents, document_versions, upload_intents, document_grants, download_events
├── service/service.py            # intents, complete, new version, grants, revoke, authorize_download
├── service/storage_service.py    # StorageAdapter: LocalStorage (volume), S3Storage (037)
├── service/scanner_service.py    # ScannerAdapter: ClamAvScanner (clamd socket), DevelopmentAcceptScanner
├── service/sniff.py              # magic-number checks for PDF, DOCX (zip + content types), PNG, JPEG, WEBP
└── service/extraction.py         # PDF text via pypdf; scans -> NEEDS_MANUAL_INPUT
app/worker/registry.py            # document.uploaded -> scan; document.available -> extract
dev-compose.yml                   # optional clamav service behind a profile
migrations/versions/0005_documents.py
```

## API Contract

- `POST /api/v1/documents/upload-intents` `{acting_party_id, title, kind, media_type, size_bytes}` → `{intent_id, upload_url: "/api/v1/documents/upload-intents/{id}/content", expires_at}`.
- `PUT /api/v1/documents/upload-intents/{id}/content` (streamed body) → 202, state `QUARANTINED`.
- `GET /api/v1/documents/{id}` → versions with `file_state`, `extraction_state`, `review_state`, grants (owner only).
- `POST /api/v1/documents/{id}/grants` `{version, grantee_party_id, purpose, pitch_id?}` (Idempotency-Key).
- `POST /api/v1/grants/{id}/revoke` (Idempotency-Key) → `{"revoked": true, "copies_already_delivered": 1}`.
- `GET /api/v1/documents/{id}/versions/{n}/content` (supports `Range`) → bytes or `NOT_FOUND`/`GRANT_REVOKED`.

Codes: `FILE_TOO_LARGE`, `FILE_TYPE_UNSUPPORTED` (422), `FILE_NOT_AVAILABLE` (409), `GRANT_REVOKED` (403, says prior copies cannot be recalled).

## Prototype Reference

`domain.js`: document fixture `doc-f01`, `fetchDocument`, `revokeGrant`; `domain.test.mjs` "AC65 revocation blocks new fetch". Port the F01-SCAN variant.

## Test Plan

AC13–AC15, AC65; size and type refusal before transfer; signature mismatch; interrupted transfer retry; range request after revocation; owner versus grantee versus stranger; worker scan and extraction jobs; production refuses the development scanner; streaming without full buffering.

## Out of Scope

Web upload UI (012), preflight file selection (022, 024), virus-definition updates in production (037).

## Task Outline

1. Migration, adapters as protocols, failing AC tests.
2. Intents, streaming upload, sniffing, limits.
3. Scanner and extraction jobs.
4. Versions and grants.
5. Gateway with ranges and download events.
6. Codes, catalog, contract, manifest flips.
