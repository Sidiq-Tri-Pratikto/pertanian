# Implementation Plan: Asset edit and archive

**Branch**: `016-asset-edit` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Summary

Add edit, archive and restore actions to asset detail, and an independent archived list to Perangkat. Reuse the form components already shipped in [027](../027-import-s10/spec.md) and integrate against the merged [015 history chart](../015-history-chart/plan.md).

## Project Structure

```text
src/components/hd/{HDTextField.tsx, HDErrorSummary.tsx, HDSheetDialog.tsx} # reuse
src/api/client.ts
src/features/assets/{EditAssetSheet.tsx, ArchiveAssetSheet.tsx, useAssetMutations.ts}
```

## Mobile

Use 027's focusable `HDErrorSummary`, field refs and the existing modal. Keep drafts across sheet dismissal and clear them on confirmation or explicit discard. Trim and validate the name and optional text using the 005 limit of 60 Unicode code points per field. The name is required. Send only normalized fields the user changed relative to the draft baseline. Omit untouched optional fields and use `""` to clear existing text because 005 ignores `null`. After review of divergent data, keep fresh untouched values and build a new PATCH from the reviewed edits. Archive and restore send only the absolute `archived` value.

An acknowledgment is HTTP 200 with a valid asset, the expected ID and all captured submitted values. A known rejection requires a valid public error envelope with a status and code pair that 005 emits before writing. A transport failure, 5xx, unexpected status, malformed response or nonmatching acknowledgment after dispatch leaves the result unknown. Do a fresh GET for the same workspace and compare the captured submitted fields. A match confirms the state at the time of the read. A divergence shows the observed values alongside the retained draft and requires an explicit reviewed new intent. The read can race the original PATCH and cannot prevent another edit. The existing API has no compare-and-set or replay protection, so a new write follows 005's last-write-wins semantics. Never replay the PATCH automatically.

Use one recovery owner for each new GET, including archive list pages and reconciliation. Count the first request toward the total attempt limit and honor `retryable`, `retry_after_seconds` and `max_attempts`. A manual read check or a lifecycle event cannot reset a failed read's budget. On exhausted or terminal recovery, retain confirmed content and the draft and show the safe message and reference. When browser `navigator.onLine` is false or the existing connectivity manager already knows it is offline, retain the intent without dispatch or a reconnect queue. Spec 034 owns native connectivity integration and durable storage.

Scope asset keys and asynchronous effects to the confirmed workspace, credential generation and target asset as applicable. Cancel or ignore stale reads and effects. Merge acknowledged metadata into an existing full detail without dropping bindings or sources, then refresh the affected lists and summaries. Load archived assets independently of the active summary. Follow the cursor with `include_archived=true` on each page, validate archive flags, deduplicate IDs, and expose continuation or an incomplete result at the client bound. Use confirmed archive status for row membership. Keep stale summary totals explicitly tied to their earlier scope until the service supplies refreshed totals.

After the edit and archive flows are verified with merged 015, route S07's learning link through the existing asset list and S06 history in the Saran tab. Preserve period and Back behavior and keep S08's frozen evidence. Then flip only `detail-perangkat`.

## Prototype Reference

`EditSheet`, `ArchiveSheet` in `hematdaya-app.js`.

## Test Plan

Test confirmed saves, draft retention, known refusals and unknown or invalid acknowledgments, a reconciliation read racing an outstanding write, divergent values, and one- and three-attempt GET recovery. Verify validation and focus, known offline submission, scoped cache effects, archive and restore across empty, failed or stale summary states, complete or visibly incomplete cursor results, and the 015 handoff. Extend the existing 005 API tests to verify measurement and binding retention, owner isolation and sanitized public error references.

## Out of Scope

Expected-use profile editor (031), durable offline behavior (034), scope policy changes and related insights on S06.

## Task Outline

1. Integrate merged 015 and test the existing asset contract and shared recovery behavior.
2. Edit sheet.
3. Archive sheet and archived list.
4. Verify the S07 history handoff and flip the combined registry entry.
