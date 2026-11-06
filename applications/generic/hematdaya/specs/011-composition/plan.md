# Implementation Plan: Composition enforcement

**Branch**: `011-composition` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Summary

Add `CapabilityGuard`, injected into services of optional modules, and a two-composition test run.

## Project Structure

```text
app/capabilities/service/guard.py    # CapabilityGuard.require("cost")
tests/unit/capabilities/test_guard.py
../../../.github/workflows/hematdaya-api.yml             # COMPOSITION matrix for energy tests
```

## Design

`CapabilityGuard(composition_id).require(capability)` raises `CapabilityDisabledError`. Services receive it through the constructor, so tests and workers use the same path. Test a guarded use case without shipping a placeholder endpoint. For actual optional use cases, resolve ownership first, then check the composition and operation prerequisites before reading or computing the optional result. Use the same protected service path for any worker entry point.

Composition selection and manifest availability are independent. A capability enabled by composition can still be `planned`. The optional module supplies its route and summary value. Define the shared `capability_disabled` reason now and apply it to the actual summary fields in 018, 030 and 032. Demo/CSV and core rules must remain independent of the optional guard.

## Errors

| Code | Public | HTTP | Recovery |
|---|---|---|---|
| `APP-CAPABILITY-DISABLED` | `CAPABILITY_DISABLED` | 403 | Not retryable |

## Prototype Reference

`requireCap`, `validateComposition`, `manifest`, test AT-53.

## Test Plan

Guard allow and deny, including a direct guarded use-case call. Test invalid composition, owner rejection before capability lookup, and the same energy goldens under both configurations. Record AT-47 and AT-53 as partial. Later CSV and demo specs provide the usable core-only journey evidence. Later optional modules verify each real route, direct service and worker invocation where present, disabled summary fields, prerequisites, ownership and unchanged core totals.

## Out of Scope

Deployment records and upgrade process (039).

## Task Outline

1. Failing guard tests.
2. Guard and typed error.
3. Shared disabled reason and future module contract.
4. CI matrix.
