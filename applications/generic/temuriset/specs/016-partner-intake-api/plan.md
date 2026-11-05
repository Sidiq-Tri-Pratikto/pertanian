# Implementation Plan: Partner profiles, opportunities and typed requirements

**Branch**: `016-partner-intake-api` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
app/intake/
├── router.py                     # /partners/{party_id}, /opportunities, /{id}, /activate, /pause, /close, /handoffs
├── model/{models.py, schema.py}  # Operator, AppliesAt, VerificationMode enums
├── repository/sqlalchemy/{models.py, repository.py}   # partner_profiles, opportunities, opportunity_versions, requirements, external_handoffs
├── service/service.py
└── service/requirements.py       # operator and value-shape validation per field
tests/factories/recipients.py     # A1, A2, A3, B1, B2, C1, D1, E (shared with 019, 021)
migrations/versions/0008_intake.py
```

## API Contract

Opportunity version:

```json
{
  "id": "...", "opportunity_id": "...", "number": 1, "status": "ACTIVE",
  "title": "Validasi prototipe enam bulan", "outcome": "Prototipe teruji di lapangan dalam enam bulan.",
  "included": "Uji fungsi dan uji lapangan terbatas", "excluded": "Sertifikasi dan produksi massal",
  "accepted_stages": ["PROTOTYPE", "PILOT"], "relationship_forms": ["PROJECT"],
  "financial": {"subject": "partner", "min": "15000.0000", "max": "40000.0000", "currency": "USD",
                "period": "6 bulan", "scope": "biaya pilot enam bulan"},
  "requirements": [{"id": "...", "label": "Berkas uji fungsi", "field": "document:function", "operator": "exists",
                    "value": true, "mandatory": true, "applies_at": "SUBMISSION",
                    "verification_mode": "DOCUMENT_PRESENT", "reason": "Mitra perlu melihat bukti fungsi sebelum menyiapkan uji."}]
}
```

## Prototype Reference

`partners()`, `opportunities()`, `req()` in `domain.js`; `vm.partner`, `vm.opportunity`.

## Test Plan

AC22–AC25; personal-party investor; operator validation; narrative requirement as manual review; state transitions and expiry; versions on edit; isolation.

## Out of Scope

Evaluation (019), web (017), discovery listing (018).

## Task Outline

1. Migration; recipient factories; failing AC tests.
2. Profiles.
3. Opportunities with versions and states.
4. Requirements validation.
5. External handoff events, contract, isolation.
