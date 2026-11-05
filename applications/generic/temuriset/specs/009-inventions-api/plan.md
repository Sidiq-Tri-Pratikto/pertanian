# Implementation Plan: Inventions and publication versions

**Branch**: `009-inventions-api` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
app/portfolio/
├── router.py                     # /inventions, /inventions/{id}, /versions, /draft, /publish, /archive, /public
├── model/{models.py, schema.py}  # Stage enum: IDEA, PROTOTYPE, PILOT, WORKING, MARKET
├── repository/sqlalchemy/{models.py, repository.py}   # inventions, invention_versions, invention_facts, invention_claims
├── service/service.py            # create, save_draft, publish, archive, projection
├── service/validation.py         # publication rules, Indonesian field messages
└── service/review_hook.py        # PublicationGate protocol; default passes (033 replaces)
migrations/versions/0004_portfolio.py
```

## API Contract

- `POST /api/v1/inventions` `{acting_party_id}` → invention with empty draft.
- `GET /api/v1/inventions?mine=true` (managing party's list, drafts included).
- `GET /api/v1/inventions/{id}` → owner view: draft, published version, history numbers.
- `PUT /api/v1/inventions/{id}/draft` `{expected_version, title, summary, problem, solution, intended_users, sector, stage, keywords, facts[], claims[]}`.
- `POST /api/v1/inventions/{id}/publish` `{expected_version}` (Idempotency-Key) → `{"version": 2, "status": "PUBLISHED"}` or `PENDING_REVIEW` from 033.
- `POST /api/v1/inventions/{id}/archive` `{expected_version}`.
- `GET /api/v1/inventions/{id}/public` → public projection of the published version; `NOT_FOUND` when unpublished or archived.

## Prototype Reference

`domain.js`: `inventions()` fixtures for F01–F06 field shapes; `publishInvention` validation; `startDraft` and `saveDraft`.

## Test Plan

AC07–AC11; draft save without publication rules; each publication rule with its field message; stale draft; archive keeps history; projection hides private fields; isolation harness; outbox events written once.

## Out of Scope

Documents (010), support requests (013), funding links (014), organization review (033), web (011).

## Task Outline

1. Migration and failing AC tests.
2. Draft save with versioning.
3. Publication validation and immutable versions.
4. Facts and claims.
5. Archive, projection, outbox events.
6. Isolation and contract.
