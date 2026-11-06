# Implementation Plan: Preflight and editable brief

**Branch**: `022-preflight-brief-api` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
app/briefs/
├── router.py                     # POST /pitches/preflight; POST /briefs; GET /briefs/{id}; GET /briefs/{id}/export?format=md|txt
├── service/preflight.py          # run matching for one target, pin versions, list shareable files
├── service/template.py           # deterministic brief with sentence-level references
├── service/summarizer_service.py # SummarizerPort; OffSummarizer; validation of outputs
└── repository/sqlalchemy/        # preflights, briefs, brief_dependencies
migrations/versions/0011_briefs.py
```

## API Contract

```json
{"preflight_id": "...", "token": "...", "expires_at": "...", "readiness": "READY_TO_SUBMIT",
 "recipient": {"party_id": "...", "name": "Mitra A"}, "opportunity": {"id": "...", "version": 1, "title": "..."},
 "source": {"type": "SUPPORT_REQUEST", "id": "...", "version": 2}, "inventions": [{"id": "...", "version": 1}],
 "rows": [...], "shareable_files": [{"document_id": "...", "version": 1, "title": "Laporan uji fungsi ClearSpring",
 "file_state": "AVAILABLE", "review_state": "PROVIDED_UNREVIEWED"}], "brief": {"id": "...", "text": "...", "summarizer": "off"}}
```

## Prototype Reference

`preflight`, `templateBrief` in `domain.js`; `vm.preflight` states.

## Test Plan

AC34–AC36, AC68; token expiry and invalidation on each pinned input; template contents per fixture; summarizer failure keeps template; export permissions; isolation.

## Out of Scope

Submission (023), web (024), real AI adapter (044).

## Task Outline

1. Failing AC tests.
2. Preflight with pins and shareable files.
3. Template brief with references.
4. Summarizer port and validation.
5. Export with redaction.
