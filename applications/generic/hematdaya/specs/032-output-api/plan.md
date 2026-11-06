# Implementation Plan: Output metric API

**Branch**: `032-output-api` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
app/output/
├── router.py
├── model/{models.py, schema.py}
├── repository/{base_repository.py, sqlalchemy/}
└── service/{calculate.py, service.py}
app/insights/service/rules.py        # intensity rule
migrations/versions/0012_create_output_metric.py
```

## Summary

Optional capability with explicit denominator semantics, and the intensity rule.

## API Contract

| Route | Behaviour |
|---|---|
| `GET /api/v1/sites/{site_id}/output-metric` | Current metric and its revision |
| `POST /api/v1/sites/{site_id}/output-metric/preview` | Evaluate the full proposed metric and denominator input without writes. Return the result or field-specific reasons. A valid preview includes an opaque revision fingerprint |
| `PUT /api/v1/sites/{site_id}/output-metric` | Confirm the same full draft and fingerprint. Save the metric and reviewed denominator in one transaction |
| `DELETE /api/v1/sites/{site_id}/output-metric` | Disable the metric without modifying readings |
| `GET`, `PUT /api/v1/sites/{site_id}/output-inputs` | Read and edit input records independently after a metric is configured, with period validation, expected revision and audit |

Derive the preview fingerprint from the normalized proposal and revisions for the metric, period input, selected scope, and relevant measurements, read from a consistent snapshot. On confirmation, acquire the shared site row lock and revalidate against the current data before writing. Reject a mismatch. Write an audit record with the actor and affected periods. Invalidate the affected intensity observations in the same transaction for re-evaluation under 021.

Use one comparison compatibility definition for numerator scope, product or area meaning, unit, and actual or estimated method. Require complete matching periods and, for area, equal period length or elapsed window. Propagate the source measurement resolution through each compatible denominator before applying the scale-aware policy. Withhold an automatic alert where resolution or compatibility is unknown.

## Prototype Reference

`computeMetric`, tests AT-22, AT-23, AT-24.

## Test Plan

- Oracles, invalid values, period, product, unit, method and scope mismatches, area windows of unequal length.
- Partial numerator, complete-days-only, uniform confirmation, overlap numerator.
- Resolution propagation, preview leaves data unchanged, changed draft and stale revision, rollback between metric and input writes.
- Audit and insight invalidation, capability off, disable leaves totals.

## Out of Scope

Unit conversion, product mix.

## Task Outline

1. Pure calculation tests.
2. Migration and service.
3. Preview and aggregate save with audit.
4. Intensity rule.
5. Flip `output`.
