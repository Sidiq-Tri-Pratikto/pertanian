# Implementation Plan: Live meter adapter

**Branch**: `046-live-adapter` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Summary

Gated. Choose the model first, then design. Likely shape: Mosquitto with TLS, an adapter translating into `IngestService`, and a worker entry point using the same use cases.

## Decisions to Take in This PR

Model, broker hosting, credential handling, physical test setup. Verify current vendor documentation at that time. The spike must prove measurement-only permissions, or the model stays planned. Map an authenticated broker identity to an enrolled source server-side, authorize only measurement topics, and revoke source credentials independently of user sessions.

## Test Plan

- Enrollment and valid first reading, duplicate delivery, late data, stale.
- Reference comparison, no control path.
- Verify cross-source topic denial, a forged site/source payload, revocation with an active connection, and refusal of relay/control topics using the adapter credential. Record the negative evidence before flipping the verified model.

## Out of Scope

Multiple vendors, generic IoT framework.

## Task Outline

1. Spike on the real device.
2. Adapter.
3. Enrollment.
4. Field evidence.
