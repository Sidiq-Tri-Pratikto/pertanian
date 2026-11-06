# Implementation Plan: Partner profiles, opportunities and typed requirements

**Branch**: `016-partner-intake-api` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
app/intake/
├── router.py                     # /partners/{party_id}, /partners/{party_id}/handoffs, /opportunities, /{id}, /{id}/versions/{n}, /activate, /pause, /close
├── model/{models.py, schema.py}  # Operator, AppliesAt, VerificationMode enums
├── repository/sqlalchemy/{models.py, repository.py}   # partner_profiles, opportunities, opportunity_versions, requirements, external_handoffs
├── service/service.py            # profiles, opportunities, states, target_availability
├── service/financial.py          # what an amount means: subject, basis, period, months
├── service/jobs.py               # intake.expire_opportunity
└── service/requirements.py       # operator and value-shape validation per field
tests/factories/recipients.py     # A1, A2, A3, B1, B2, C1, D1, E (shared with 019, 021)
migrations/versions/0008_intake.py
```

## API Contract

Opportunity, with its current version. `version` is for `expected_version`; `number` names the content. `GET /opportunities/{id}/versions/{n}` returns the same content with `opportunity_id` and the version's own `id`.

```json
{
  "id": "...", "partner_party_id": "...", "version": 2, "kind": "SPECIFIC", "status": "ACTIVE", "closes_at": null,
  "number": 1, "title": "Validasi prototipe enam bulan", "outcome": "Prototipe teruji di lapangan dalam enam bulan.",
  "included": "Uji fungsi dan uji lapangan terbatas", "excluded": "Sertifikasi dan produksi massal",
  "support": "Pendanaan proyek dan pendampingan uji", "timing": "Dibuka sampai 31 Desember 2026",
  "accepted_stages": ["PROTOTYPE", "PILOT"], "relationship_forms": ["PROJECT"],
  "sectors": ["Air dan sanitasi"], "keywords": ["prototipe", "validasi"],
  "financial": {"subject": "partner", "basis": "total_period", "min": "15000.0000", "max": "40000.0000",
                "currency": "USD", "period": "6 bulan", "months": 6, "scope": "biaya pilot enam bulan",
                "noncash": "", "terms": "", "unknown_reason": null},
  "requirements": [{"id": "...", "label": "Berkas uji fungsi", "field": "document:function", "operator": "exists",
                    "value": true, "mandatory": true, "applies_at": "SUBMISSION",
                    "verification_mode": "DOCUMENT_PRESENT", "visibility": "PUBLIC", "version": 1,
                    "reason": "Mitra perlu melihat bukti fungsi sebelum menyiapkan uji."}],
  "target_availability": {"available": true, "reason": null}, "general_intake_label": null, "operation_id": "..."
}
```

Status changes are `POST /opportunities/{id}/activate`, `/pause` and `/close`, each its own idempotent operation. A handoff is `POST /partners/{party_id}/handoffs`, naming no opportunity. The prototype's `current` operator is stored as `equals` with the value `CURRENT`, and its `doc:` fields as `document:`. The decisions behind this contract are in `tasks.md` and `docs/roadmap/architecture.md`.

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
