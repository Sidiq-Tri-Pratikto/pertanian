# Implementation Plan: Discovery, search and saved lists

**Branch**: `018-discovery-api` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
app/discovery/
├── router.py                     # GET /discovery?type=inventions|funding|partners&q=&sector=&stage=&..., /saved-items, /discovery-feedback
├── model/{models.py, schema.py}
├── repository/sqlalchemy/{models.py, repository.py}   # search_documents (GIN on tsv, trgm on title), saved_items, relevance_feedback, alias_terms
├── service/service.py            # query building, sections, cursor
└── service/projection.py         # outbox consumers: invention.published/archived, funding.*, opportunity.*, partner.*
migrations/versions/0009_discovery.py   # CREATE EXTENSION pg_trgm; alias seed rows
```

## API Contract

`GET /api/v1/discovery?type=inventions&sector=Air%20dan%20sanitasi&limit=20` →

```json
{"sections": [{"id": "relevant", "items": [...]}, {"id": "new", "items": [...]}, {"id": "curated", "items": [...]}],
 "filters": {"sector": "Air dan sanitasi"}, "next_cursor": null, "total_estimate": 1,
 "relaxation": null}
```

## Prototype Reference

`vm.discover`, `matchesQuery`, `EN_ALIAS` in `views.js`.

## Test Plan

AC28–AC30; projection add, update and remove through consumers; English alias; one card per raise; saved and feedback per party; private text not searchable; pagination.

## Out of Scope

Matching and ranking by fit (019), dense retrieval (045), trending.

## Task Outline

1. Migration and projection consumers.
2. Query, filters, sections, cursor.
3. Saved items and feedback.
4. Isolation and contract.
