# Implementation Plan: Company funding requests

**Branch**: `014-funding-requests-api` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
app/funding/
├── router.py                     # /funding-requests, /{id}, /activate, /inventions; /legal-entities
├── model/{models.py, schema.py}
├── repository/sqlalchemy/{models.py, repository.py}   # legal_entities, funding_requests, funding_invention_links
└── service/service.py
migrations/versions/0007_funding.py
```

## API Contract

```json
{
  "id": "...", "version": 1, "owner_party_id": "...", "subject_type": "EXISTING_ENTITY",
  "legal_entity": {"id": "...", "name": "Demo Circular Materials Ltd", "review_status": "declared"},
  "financing_stage": "pre_seed", "financing_form": "equity", "currency": "USD",
  "target_amount": "500000.0000", "desired_min": "50000.0000", "desired_max": "100000.0000",
  "accepts_partial": true, "intended_use": "Mengembangkan dua inovasi perusahaan", "timing": null,
  "inventions": [{"invention_id": "...", "version": 1, "title": "LoopMaterial"},
                 {"invention_id": "...", "version": 1, "title": "ReFormPress"}],
  "status": "ACTIVE"
}
```

## Prototype Reference

`fundingRequests()`, `saveFundingRequest`, `setProposedEntity`; oracles "J02 target edit", "AC67", "F05 duplicate".

## Test Plan

AC19, AC67 with each composition; proposed entity; target versioning; archived link refused; isolation.

## Out of Scope

Matching contribution ranges (019), pitches (023), equity relationships (030), web (015).

## Task Outline

1. Migration; failing AC tests.
2. Legal entities.
3. Requests, links, versions.
4. Guard, manifest flip, contract.
