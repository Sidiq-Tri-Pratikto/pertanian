# Implementation Plan: Push notifications

**Branch**: `045-push` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Summary

Optional. `expo-notifications`, a preferences route and a send step after insight evaluation. Sending needs a worker, which is decided here.

## Test Plan

No prompt by default; opt-in; dedupe per revision; opt-out; failed gateway.

## Out of Scope

Email, SMS, marketing messages.

## Task Outline

1. Preferences API.
2. Registration on device.
3. Send with dedupe.
