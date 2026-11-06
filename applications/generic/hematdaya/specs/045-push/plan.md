# Implementation Plan: Push notifications

**Branch**: `045-push` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Summary

Optional. `expo-notifications`, a preferences route and a send step after insight evaluation. Sending needs a worker, which is decided here.

Persist a dispatch record with a unique key for owner, observation revision and registration. One worker claims a record atomically. Recheck current consent, registration ownership and visibility from 023 before dispatch. Invalidate queued records on opt-out or unregister and serialize dispatch with that state change. A gateway call already in progress cannot be recalled. Persist accepted, rejected or unknown outcomes. Retry an unknown outcome only with gateway-supported idempotency for the same dispatch key.

## Test Plan

- No prompt by default, opt-in, competing workers claim once, same revision dedupes.
- Opt-out or unregister after queueing, hidden or snoozed observation, failed gateway, response lost after acceptance with and without gateway idempotency.

## Out of Scope

Email, SMS, marketing messages.

## Task Outline

1. Preferences API.
2. Registration on device.
3. Send with dedupe.
