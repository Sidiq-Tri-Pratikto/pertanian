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

## Session coordination and drafts

Use one in-flight refresh per native session. On web, coordinate refresh across tabs of the same origin and session before any request reaches 036. Waiting tabs receive the outcome in memory. Keep the cookie HTTP-only and keep access tokens out of persistent storage. If safe coordination or recovery after an ambiguous rotation is unavailable, show the sign-in boundary without replaying the consumed credential.

Use 034's owner-scoped persistence. Restore a retained non-secret draft only after the server confirms the same owner and workspace. Logout clears that owner's tokens, cached reads and drafts. After expiry, reconcile unknown save outcomes with the feature's status or revision before offering explicit retry. Reuse the original operation key where the feature supports it.

## Test Plan

Register, login, restart, two web tabs refreshing simultaneously, shared terminal refresh failure, logout clears cache and drafts, different owner cannot recover a prior draft, expiry during each save type, explicit retry, no duplicate commit, autofill attributes, focus and error summary. Run the pilot account expiry checks against import (027) and scope (029). Verify optional saves with their feature releases. Verify enrollment on the integrated user-facing pilot candidate.

## Out of Scope

Biometric unlock, password reset by email unless the service sends it. Push.

## Task Outline

1. Session store.
2. Client refresh.
3. Forms.
4. Expiry boundary with drafts.
5. Flip registry.
