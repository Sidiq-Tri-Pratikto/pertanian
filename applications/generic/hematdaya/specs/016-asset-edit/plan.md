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

`HDErrorSummary` focuses itself and links to fields, through `ref.focus()`. Drafts are kept in the screen's feature state until explicitly discarded. Mutations invalidate the summary and asset queries only after acknowledgment.

## Prototype Reference

`EditSheet`, `ArchiveSheet` in `hematdaya-app.js`.

## Test Plan

Save success; rejection keeps draft; validation; focus to summary; archive; restore; totals unchanged; owner isolation in API tests from 005.

## Out of Scope

Expected-use profile editor (031).

## Task Outline

1. HDTextField, HDErrorSummary with tests.
2. Edit sheet.
3. Archive sheet and archived list.
4. Flip registry together with 015.
