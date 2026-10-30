# Implementation Plan: Live meter adapter

**Branch**: `046-live-adapter` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Summary

Gated. Choose the model first, then design. Likely shape: Mosquitto with TLS, an adapter translating into `IngestService`, and a worker entry point using the same use cases.

## Decisions to Take in This PR

Model, broker hosting, credential handling, physical test setup. Verify current vendor documentation at that time.

## Test Plan

Enrollment; first reading; duplicate delivery; late data; stale; reference comparison; no control path.

## Out of Scope

Multiple vendors, generic IoT framework.

## Task Outline

1. Spike on the real device.
2. Adapter.
3. Enrollment.
4. Field evidence.
