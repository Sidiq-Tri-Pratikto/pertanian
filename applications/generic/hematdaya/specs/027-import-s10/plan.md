# Implementation Plan: Import screens

**Branch**: `027-import-s10` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
src/components/hd/HDImportPreview.tsx
src/features/imports/{useImportDraft.ts, InputStep.tsx, MappingStep.tsx, PreviewStep.tsx, ResultStep.tsx}
src/app/(tabs)/(beranda,perangkat,saran)/impor.tsx
```

## Summary

Four-step flow over the import API, with drafts retained in memory across steps.

## Technical Context

**New dependencies**: `expo-document-picker`, `expo-file-system` through `npx expo install`

## Mobile

Read the file as UTF-8 and upload it; pasting uses a multiline `HDTextField`. Keyboard avoidance on mapping fields. `HDImportPreview` takes server counts and computes nothing. The system component's copy "Impor N baris" stands unless the owner chooses "Konfirmasi impor".

## Prototype Reference

`Import`, `EXAMPLES` in `hematdaya-app.js`; `PatternCsvImport`.

## Test Plan

Each example; error summary focus; acknowledgment; unknown result; back retention; replace file; plain-text names; 320 px and large text; Android file picker.

## Out of Scope

Export (038).

## Task Outline

1. Draft hook.
2. Input step with picker.
3. Mapping step.
4. Preview with HDImportPreview.
5. Result and landing period.
6. Flip registry.
