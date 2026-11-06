# Implementation Plan: Site settings

**Branch**: `017-settings-s09` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Summary

The settings shell later PRs extend: site name, context, timezone, draft handling.

## Project Structure

```text
src/components/hd/HDChoiceGroup.tsx   # add select and checkbox types
src/features/settings/{useSiteDraft.ts, SiteSection.tsx}
src/app/(tabs)/(beranda,perangkat,saran)/pengaturan.tsx
app/sites/service/service.py          # reconcile existing validation and audit with safe replay
```

## API

Use `PATCH /api/v1/sites/{site_id}` with 004's IANA validation and the audit contract assigned to 005. Keep update, audit and the result for a stable owner/site-scoped `Idempotency-Key` in one transaction. An identical replay after a lost response returns the saved result without a second audit event. Reject a changed payload for the same key. Reconcile via GET on an unknown outcome before retry. Preserve confirmed values and draft until the outcome is known.

After acknowledgment or reconciliation, refresh the site record and invalidate the site's period-dependent summary, history and comparison queries. Key new requests by site, scope, local dates and effective timezone, and verify the returned resolved window before replacing previous content. In-flight results for the previous timezone must not populate the new view.

## Prototype Reference

`Settings` in `hematdaya-app.js`, test AT-51.

## Test Plan

Test context switch parity and updated timezone boundaries in summaries, history and comparisons. Verify late responses from the previous timezone cannot replace current data and UTC records are unchanged. Cover rejection, one audit event after a lost-response retry, cancellation, draft retention on expiry (AT-40 ties into 034 and 037), and the absence of a notification permission prompt.

## Out of Scope

Tariff (019), schedule (031), notifications (045).

## Task Outline

1. Draft hook.
2. Section UI with preview text.
3. Timezone confirmation.
4. Failure handling.
