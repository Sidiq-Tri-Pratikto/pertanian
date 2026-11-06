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
└── service/{service.py, calculate.py}   # exact cost and one final rounding step
migrations/versions/0006_create_tariffs.py
```

## API Contract

| Route | Behaviour |
|---|---|
| `GET /api/v1/sites/{site_id}/tariffs` | Effective-dated list |
| `POST /api/v1/sites/{site_id}/tariffs` | Requires `Idempotency-Key`. Accepts `rate_idr_per_kwh` (decimal string), optional `effective_from` defaulting to the site clock, and `is_correction` for an explicitly confirmed retroactive change |

Bind each tariff operation key to owner, site and confirmed payload. Resolve the effective time once and store the result and audit with the tariff. Matching replay returns that result. Reusing the key for a changed draft returns a conflict.

Summary gains:

```json
"cost": {"amount_idr": "22050", "covered_energy_kwh": "14.700", "uncovered_energy_kwh": "0.000",
         "tariffs": [{"rate_idr_per_kwh": "1500", "effective_from": "2026-09-27T17:00:00Z", "provenance": "synthetic"}],
         "uniform_split_available": false, "split_estimate": false, "unavailable_reason": null}
```

Site and asset summaries accept `allow_uniform_tariff_split`, defaulting to false. Apply it only to valid interval-energy records whose source semantics support a proportional estimate. Prefer finer valid intervals when available. Report `uniform_split_available` when the user can accept a suitable split. When the estimate is not allowed or suitable, keep the affected energy uncovered and explain why. Return a qualified partial amount when other portions have known prices, or a null amount with its reason when none do. Represent fractional nano-rupiah contributions as exact ratios before final IDR rounding, and conserve energy across covered and uncovered parts.

## Prototype Reference

`costOfParts`, `tariffAt`, `nanoToRp`, tests AT-08, AT-09.

## Test Plan

Run the cost oracles and test absent and zero tariffs, accepted and declined splits, unsuitable intervals, fractional allocation with one final rounding, and tariff gaps. Verify audit for retroactive corrections, lost-response replay with the same effective time and one audit entry, disabled capability handling and foreign-site rejection. Update the golden responses.

## Out of Scope

Demand, reactive, tiered or time-of-use billing.

## Task Outline

1. Pure cost tests.
2. Migration.
3. Service and router with guard.
4. Merge into summary; demo scenarios seed the synthetic tariff.
5. Flip `cost`; update goldens and contract.
