# Implementation Plan: Labelled demo accounts and fixtures

**Branch**: `021-demo-fixtures` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
app/demo/
├── router.py                     # GET /demo/accounts, POST /demo/sign-in, POST /demo/reset, PUT /demo/clock (demo mode only)
├── service/fixtures.py           # F01–F06, FRaise01, Recipients A–E through services; deterministic UUIDv5 ids
├── service/variants.py           # gap, scan, proposed entity
└── service/clock.py              # per-workspace virtual clock for demo parties
Makefile                          # demo-seed
applications/temuriset-web/src/views/StartView.tsx   # demo picker when the manifest says demo
```

## Prototype Reference

`accounts()`, `parties()`, `inventions()`, `JOURNEYS`, clock presets in `views.js`.

## Test Plan

Seed and reset idempotency; metric exclusion; production refusal; demo sign-in only in demo mode; goldens on seeded data.

## Out of Scope

Journey scripts (each owning web spec writes its Playwright journey).

## Task Outline

1. Deterministic fixtures through services.
2. Demo accounts and picker sign-in.
3. Reset and variants.
4. Virtual clock for demo workspaces.
5. Metric exclusion test, registry flip.
