# Implementation Plan: Email delivery adapter (gated)

**Branch**: `042-email-adapter` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

## Task Outline

1. Provider adapter with timeouts and an error resolver.
2. Notification preferences on the account; S18 toggle.
3. Outbox consumer for email with deduplication.
4. Sandbox and failure tests; manifest and registry flips.
