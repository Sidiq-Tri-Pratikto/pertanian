# Implementation Plan: Accounts on mobile

**Branch**: `037-auth-mobile` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
src/features/auth/{useSession.ts, session-store.ts, LoginForm.tsx, RegisterForm.tsx}
src/app/masuk.tsx
src/app/daftar.tsx
src/api/client.ts                    # single-flight refresh
```

## Summary

Screens and session handling over 036. The workspace model gains a `user` kind beside `demo`.

## Test Plan

Register, login, restart, logout clears cache, expiry during each save type, explicit retry, no duplicate commit, autofill attributes, focus and error summary.

## Out of Scope

Biometric unlock, password reset by email unless the service sends it. Push.

## Task Outline

1. Session store.
2. Client refresh.
3. Forms.
4. Expiry boundary with drafts.
5. Flip registry.
