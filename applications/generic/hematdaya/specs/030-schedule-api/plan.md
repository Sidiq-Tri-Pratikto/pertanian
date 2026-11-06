# Implementation Plan: Schedule API

**Branch**: `030-schedule-api` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
app/schedules/
├── router.py
├── model/{models.py, schema.py}
├── repository/{base_repository.py, sqlalchemy/}
└── service/{windows.py, effective.py, split.py, service.py}
app/insights/service/rules.py        # outside-window rule
migrations/versions/0011_create_schedules.py
```

## Summary

Optional capability: schedule storage, effective resolution, outside split and one more insight rule.

## API Contract

| Route | Behaviour |
|---|---|
| `GET /api/v1/sites/{site_id}/schedule` | Confirmed windows and version history |
| `POST /api/v1/sites/{site_id}/schedule/preview` | Evaluate proposed windows, effective time, correction flag, and affected period without writes |
| `PUT /api/v1/sites/{site_id}/schedule` | Save the revalidated proposal with its expected version |
| `GET /api/v1/assets/{asset_id}/schedule` | Confirmed override, effective site or asset schedule, and versions |
| `POST /api/v1/assets/{asset_id}/schedule/preview` | Evaluate the proposed mode and optional windows with the same effective-time and correction semantics, without writes |
| `PUT /api/v1/assets/{asset_id}/schedule` | Save the revalidated override with expected asset and inherited site versions, when applicable |

Both previews return the versions used, affected period, and the same split shape used by summaries. `outside_schedule` includes `inside_kwh`, `outside_kwh`, `estimated`, schedule label and version, or an explicit unavailability reason. For `none`, stop before checking the site default. Resolve an effective-now draft to the actual save time on confirmation. An explicit historical correction uses the reviewed effective time and is versioned and audited. Invalidate affected observations in the save transaction for re-evaluation under 021. A preview or a failed save writes neither audit nor evidence.

## Prototype Reference

`validateWindows`, `expandWindows`, `effectiveSchedule`, `outsideSplit`, `describeWindow`, tests AT-12, AT-13, AT-15, AT-18.

## Test Plan

- All oracles, every validation, `none` with a configured site default, read-only site and asset previews.
- Effective-now and versioned correction, stale version rejection, atomic save and invalidation, comparison withheld across definitions.
- Continuous asset, timezone, capability off, rejected save.
- Foreign site and asset.

## Out of Scope

Holidays, rotations, screens (031).

## Task Outline

1. Pure window tests.
2. Split with conservation.
3. Migration and service.
4. Rule in insights.
5. Router, contract, flip.
