# Implementation Plan: Support requests and project budgets

**Branch**: `013-support-requests-api` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
app/needs/
├── router.py                     # /support-requests, /support-requests/{id}, /activate, /pause, /close, /budgets
├── model/{models.py, schema.py}  # SupportForm, RelationshipForm, BudgetRequest with Money fields
├── repository/sqlalchemy/{models.py, repository.py}   # support_requests, project_budgets, project_budget_lines
└── service/service.py            # create, update (new version), status transitions, budget validation
migrations/versions/0006_needs.py
```

## API Contract

```json
{
  "id": "...", "version": 2, "invention_id": "...", "invention_version": 1,
  "outcome": "Validasi prototipe enam bulan", "support_forms": ["project_funding", "testing_support"],
  "relationship_form": "PROJECT", "scope": "Validasi prototipe", "months": 6, "region": "Indonesia",
  "accepts_partial": true, "accepts_noncash": false, "status": "ACTIVE",
  "budget": {"min": "20000.0000", "max": "30000.0000", "currency": "USD", "period": "6 bulan",
             "scope": "biaya pilot enam bulan", "estimated_on": "2026-10-30", "assumptions": "Uji lapangan di dua lokasi",
             "unknown_reason": null, "lines": []}
}
```

Unknown money: `"min": null, "max": null, "unknown_reason": "not_determined"`.

## Prototype Reference

`domain.js`: `supportRequests()`, `saveSupportRequest`, `parseAmount`, `cmpDec`; oracles "AC16" and "F01-GAP" in `domain.test.mjs`.

## Test Plan

AC16, AC17; F01-GAP null range then completed; zero rule; lines arithmetic and mismatch explanation; status transitions; stale version; isolation.

## Out of Scope

Comparison with partner ranges (019), web forms (015).

## Task Outline

1. Migration with checks; failing AC tests.
2. Requests with versions and status.
3. Budgets and lines.
4. Events, contract, isolation.
