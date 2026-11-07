# Implementation Plan: Import screens

**Branch**: `m5/import-screens` | **Date**: 2026-10-30, revised 2026-11-07 against `42aeebc` | **Spec**: [spec.md](spec.md)

## Project Structure

Paths start at `applications/hematdaya-mobile/`.

```text
src/app/(tabs)/(beranda,perangkat,saran)/impor/[step].tsx   # berkas | pemetaan | pratinjau | hasil
src/app/_layout.tsx                                         # mounts ImportDraftProvider
src/features/imports/{ImportDraftProvider.tsx, draft-store.ts, import-model.ts, examples.ts}
src/features/imports/{ImportScreen.tsx, InputStep.tsx, MappingStep.tsx, PreviewStep.tsx, ResultStep.tsx, ImportStatus.tsx}
src/components/hd/{HDImportPreview.tsx, HDErrorSummary.tsx, HDTextField.tsx}   # new ports
src/components/hd/{HDScreen.tsx, HDChoiceGroup.tsx, HDProvenanceTag.tsx, HDSheetDialog.tsx}   # small extensions
src/lib/focus.ts
src/api/{client.ts, errors.ts}
src/features/navigation.ts, src/features/registry.ts
src/app/(tabs)/(beranda)/beranda.tsx, src/features/assets/PerangkatScreen.tsx, src/features/insights/SaranScreen.tsx   # entry points
package.json, package-lock.json, app.json (if the installer adds the plugin), README.md
tests/{import.test.tsx, import-model.test.ts, fixtures/imports.json, setup.ts}
tests/{components,data-layer,navigation,perangkat,registry}.test.tsx and src/api/errors.test.ts
```

## Summary

Four-step flow over the import API, one route per step so every back gesture is one step back. Retain file context and mapping across steps in a draft above the tabs, and land on the imported period in Beranda. Entry points are S02's **Impor data**, both **Impor data** buttons on Perangkat (014, merged) and Saran's **Tentang impor data**, all of which open "Segera hadir" today. 013 and 014 are merged, so the landing on the populated Beranda is tested here and walked on web.

## Technical Context

**New dependency**: `expo-document-picker`, through `npx expo install` (SDK 58: `~58.0.4`). It covers Android, iOS and web, and the picked file is uploaded as it is, so no file is read in JavaScript and `expo-file-system` is not added. Justification and options are in `tasks.md` D1.

**No API change.** The routes, codes and `details` of 025 and 026 cover every screen state (`tasks.md`, API gaps).

## Mobile

Check the picked file's `size` against 10 MiB before uploading when the picker reports it, and leave the rest to the service's `IMPORT_TOO_LARGE`. Use a multiline `HDTextField`, a new port, for pasted content, and keep the primary action in `HDScreen`'s footer inside a `KeyboardAvoidingView`, so it and the active field stay visible when the keyboard opens. `HDImportPreview` takes server counts and computes nothing. Use the handoff's step actions and show the exact accepted row count beside the confirmation.

Give preview a 120 s timeout and commit 60 s, and keep 10 s for every other call: a 150,000-row preview took 8.94 s and its commit 9.12 s over local HTTP, before any network, and 026 measured 20.62 s for a counter commit, so `TIMEOUT_MS` alone would make a large commit look lost. A preview carries no key and cannot be found after a lost response; it writes no reading, so the app says so and offers a new check.

Create one operation key per commit intent, that is per import ID and acknowledgment. Keep the preview ID, key and acknowledgment through pending and unknown results, and lock the checkbox meanwhile. Prevent concurrent submissions. Any failure that is not a definite refusal, a timeout included, is unknown: offer Periksa status and fetch the existing import before another commit. Show the stored result if found. Retry an unresolved operation with the same key and payload. A definite refusal drops the key, so the next confirmation makes a new one. Branch on the public code per `tasks.md`'s Error behaviour table. If a web reload drops access to a selected file, request reselection when the bytes are needed and never claim they were recovered.

Operation results stay in the draft's state, as `useFeedback` keeps its result. Only the user's own input, the import ID and the commit intent persist, in `sessionStorage` on web.

State `rows_after_site_clock` on the result, and never say data is visible when it is not (`tasks.md` D21). Land on the imported range, or its last 366 days when it is longer, because the summary refuses longer ranges.

## Prototype Reference

`Import`, `EXAMPLES` in `hematdaya-app.js`; `PatternCsvImport`. Examples are ported as data, not code.

## Test Plan

- Each example, empty workspace to imported-period totals, error summary focus, acknowledgment, each failure code.
- Lost commit response with status-first recovery, retry with the same operation key, double tap while pending, back retention.
- Replace file, file reselection after a web reload, plain-text names, 320 px and large text.
- Android file picker: not runnable here, because no local Android SDK exists and the smoke job never opens S10. Recorded as not run.

## Out of Scope

Export (038). Scope confirmation across files (029). Offline and persisted native drafts (034). Changing the `empty` clock (008). Any API change.

## Task Outline

1. Picker dependency and recorded responses.
2. Client calls, error details, focus, components, pure model.
3. Draft provider and the four steps.
4. Failure, unknown result and reload handling.
5. Hostile text.
6. Flip registry and walk the web build.
