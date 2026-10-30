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
| `GET`, `PUT /api/v1/sites/{site_id}/schedule` | Windows, effective from, `is_correction`, with a preview in the response |
| `GET`, `PUT /api/v1/assets/{asset_id}/schedule` | Mode and optional windows |

Summary gains `outside_schedule`: `inside_kwh`, `outside_kwh`, `estimated`, `schedule_label`, or a reason.

## Prototype Reference

`validateWindows`, `expandWindows`, `effectiveSchedule`, `outsideSplit`, `describeWindow`, tests AT-12, AT-13, AT-15, AT-18.

## Test Plan

All oracles; every validation; mode resolution; versioned correction; comparison withheld across definitions; continuous asset; timezone; capability off; rejected save; foreign site.

## Out of Scope

Holidays, rotations, screens (031).

## Task Outline

1. Pure window tests.
2. Split with conservation.
3. Migration and service.
4. Rule in insights.
5. Router, contract, flip.
