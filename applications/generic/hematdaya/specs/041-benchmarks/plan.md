# Implementation Plan: Benchmarks

**Branch**: `041-benchmarks` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
applications/hematdaya-api/benchmarks/{seed_large_site.py, run_summary.py, run_import.py}
docs/operations/benchmarks.md
```

## Summary

Measure §18 on the pilot host. No optimization in this PR.

## Test Plan

The benchmark is the evidence. Record `EXPLAIN ANALYZE` for the slowest query.

## Out of Scope

Rollups, caching, workers: each gets its own spec if a target fails.

## Task Outline

1. Seed script.
2. Summary and import runs.
3. Record results.
