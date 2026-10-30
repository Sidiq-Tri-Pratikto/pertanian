# Implementation Plan: Tariff and cost API

**Branch**: `018-tariff-api` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Summary

The first optional capability module, consuming canonical summaries and adding cost fields.

## Project Structure

```text
app/cost/
├── router.py
├── model/{models.py, schema.py}
├── repository/{base_repository.py, sqlalchemy/}
└── service/{service.py, calculate.py}   # pure integer cost
migrations/versions/0006_create_tariffs.py
```

## API Contract

| Route | Behaviour |
|---|---|
| `GET /api/v1/sites/{site_id}/tariffs` | Effective-dated list |
| `POST /api/v1/sites/{site_id}/tariffs` | `rate_idr_per_kwh` (decimal string), `effective_from`, `is_correction` |

Summary gains:

```json
"cost": {"amount_idr": "22050", "covered_energy_kwh": "14.700", "uncovered_energy_kwh": "0.000",
         "tariffs": [{"rate_idr_per_kwh": "1500", "effective_from": null, "provenance": "synthetic"}],
         "split_estimate": false, "unavailable_reason": null}
```

## Prototype Reference

`costOfParts`, `tariffAt`, `nanoToRp`, tests AT-08, AT-09.

## Test Plan

All oracles; no tariff; zero tariff; split; boundary crossing; tariff gap; retroactive correction with audit; capability off; foreign site; golden update.

## Out of Scope

Demand, reactive, tiered or time-of-use billing.

## Task Outline

1. Pure cost tests.
2. Migration.
3. Service and router with guard.
4. Merge into summary; demo scenarios seed the synthetic tariff.
5. Flip `cost`; update goldens and contract.
