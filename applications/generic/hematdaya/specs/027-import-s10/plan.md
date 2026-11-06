# Implementation Plan: Import screens

**Branch**: `027-import-s10` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
src/components/hd/HDImportPreview.tsx
src/features/imports/{useImportDraft.ts, InputStep.tsx, MappingStep.tsx, PreviewStep.tsx, ResultStep.tsx}
src/app/(tabs)/(beranda,perangkat,saran)/impor.tsx
```

## Summary

Four-step flow over the import API. Retain file context and mapping across steps, and land on the imported period in the populated Beranda from 013.

## Technical Context

**New dependencies**: `expo-document-picker`, `expo-file-system` through `npx expo install`

## Mobile

Enforce the file-size limit before reading a selected UTF-8 file and uploading it. Use a multiline `HDTextField` for pasted content and keep mapping fields visible when the keyboard opens. `HDImportPreview` takes server counts and computes nothing. Use the handoff's step actions and show the exact accepted row count in the confirmation.

Create one operation key per confirmed preview. Keep the preview ID, key, and acceptance payload through pending and unknown results. Prevent concurrent submissions. On timeout, offer Periksa status and fetch the existing import before another commit. Show the stored result if found. Retry an unresolved operation with the same key and payload. If a browser restart drops access to a selected file, request reselection when the bytes are needed and never claim they were recovered.

## Prototype Reference

`Import`, `EXAMPLES` in `hematdaya-app.js`; `PatternCsvImport`.

## Test Plan

- Each example, empty workspace to imported-period totals, error summary focus, acknowledgment.
- Lost commit response with status-first recovery, retry with the same operation key, double tap while pending, back retention.
- Replace file, file reselection after browser restart, plain-text names, 320 px and large text.
- Android file picker.

## Out of Scope

Export (038).

## Task Outline

1. Draft hook.
2. Input step with picker.
3. Mapping step.
4. Preview with HDImportPreview.
5. Result and landing period.
6. Flip registry.
