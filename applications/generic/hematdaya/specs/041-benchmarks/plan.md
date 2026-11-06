# Implementation Plan: Benchmarks

**Branch**: `041-benchmarks` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
applications/hematdaya-api/benchmarks/{seed_large_site.py, run_summary.py, run_import.py}
docs/operations/benchmarks.md
```

## Summary

Measure §18 on the pilot host. No optimization in this PR.

Use an isolated synthetic dataset and a fixed seed. Record fixture counts, actual import file size and row count, site window, app/database versions, hardware, request count and concurrency. Record cold and warm runs separately with the percentile method and failed requests. Time the complete validation and commit path from 025–026. Keep one evidence row for each §18 target and link other acceptance evidence or record the reason it remains not run.

## Test Plan

Repeat the fixed workload and record `EXPLAIN ANALYZE` for the slowest query on the benchmark database. Verify the response size and history bucket bounds alongside the latency evidence.

## Out of Scope

Rollups, caching, workers: each gets its own spec if a target fails.

## Task Outline

1. Seed script.
2. Summary and import runs.
3. Record results.
