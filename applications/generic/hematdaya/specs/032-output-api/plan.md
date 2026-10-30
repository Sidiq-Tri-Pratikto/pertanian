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

`GET`, `PUT`, `DELETE /api/v1/sites/{site_id}/output-metric` and `GET`, `PUT /api/v1/sites/{site_id}/output-inputs`. `POST /api/v1/sites/{site_id}/output-metric/preview` returns the result or a reason with a field name.

## Prototype Reference

`computeMetric`, tests AT-22, AT-23, AT-24.

## Test Plan

Oracles; invalid values; period mismatch; unit mismatch; partial numerator; complete-days-only; uniform confirmation; overlap numerator; capability off; disable leaves totals.

## Out of Scope

Unit conversion, product mix.

## Task Outline

1. Pure calculation tests.
2. Migration and service.
3. Router.
4. Intensity rule.
5. Flip `output`.
