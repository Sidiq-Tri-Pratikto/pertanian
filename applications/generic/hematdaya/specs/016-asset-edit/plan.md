# Implementation Plan: Asset edit and archive

**Branch**: `016-asset-edit` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Summary

Edit and archive sheets on asset detail, plus the first form components.

## Project Structure

```text
src/components/hd/HDTextField.tsx
src/components/hd/HDErrorSummary.tsx
src/features/assets/{EditAssetSheet.tsx, ArchiveAssetSheet.tsx, useAssetMutations.ts}
```

## Mobile

`HDErrorSummary` focuses itself and links to fields through `ref.focus()`. Keep drafts until explicitly discarded. Send edits and the absolute `archived` state via 005's PATCH route. Invalidate asset and summary queries after acknowledgment. On timeout, keep confirmed content visible and reconcile with GET before offering another save. If the returned values already match the requested state, use the read as confirmation. Otherwise show current values and preserve the draft for explicit review and a fresh save. An automatic retry would require a service-side precondition against overwriting a concurrent edit.

## Prototype Reference

`EditSheet`, `ArchiveSheet` in `hematdaya-app.js`.

## Test Plan

Test confirmed saves, draft retention after rejection, a lost response after commit, and a concurrent edit before reconciliation. Verify validation, focus, archive and restore, unchanged measurements and binding history, and owner isolation in the API tests from 005.

## Out of Scope

Expected-use profile editor (031).

## Task Outline

1. HDTextField, HDErrorSummary with tests.
2. Edit sheet.
3. Archive sheet and archived list.
4. Flip registry together with 015.
