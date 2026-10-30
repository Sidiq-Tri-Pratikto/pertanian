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

`CapabilityGuard(composition_id).require(capability)` raises `CapabilityDisabledError`. Services receive it through the constructor, so tests and workers use the same path. No decorator framework and no plugin registry.

## Errors

| Code | Public | HTTP | Recovery |
|---|---|---|---|
| `APP-CAPABILITY-DISABLED` | `CAPABILITY_DISABLED` | 403 | Not retryable |

## Prototype Reference

`requireCap`, `validateComposition`, `manifest`, test AT-53.

## Test Plan

Guard allow and deny; service-level call refused; ownership still first; composition validation; energy goldens under both.

## Out of Scope

Deployment records and upgrade process (039).

## Task Outline

1. Failing guard tests.
2. Guard and typed error.
3. Summary reason field.
4. CI matrix.
