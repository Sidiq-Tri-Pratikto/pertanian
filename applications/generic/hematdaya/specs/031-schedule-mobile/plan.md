# Implementation Plan: Schedule on mobile

**Branch**: `031-schedule-mobile` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
src/components/hd/HDScheduleWindows.tsx
src/features/schedule/{WindowsEditor.tsx, useScheduleDraft.ts, ScheduleSection.tsx, AssetProfileSheet.tsx}
```

## Summary

Compose the editor from ChoiceGroup and time fields, since `HD.ScheduleWindows` only displays windows. Beranda and detail gain outside-schedule values when applicable.

## Technical Context

**New dependency**: `@react-native-community/datetimepicker` through `npx expo install` for native. On web, use a labelled time field with keyboard input, explicit format help, and errors tied to the field.

## Save Flow

Call the site or asset `/schedule/preview` endpoint from 030 for the complete draft. Keep the confirmed schedule and evidence visible until a separate save succeeds. A draft change invalidates the preview. Save through `PUT /schedule` with the reviewed draft and versions from preview. A rejected or stale save retains the draft, and a stale save asks for a fresh preview.

## Prototype Reference

`WindowsEditor`, `ProfileSheet`, schedule part of `Settings` in `hematdaya-app.js`, including the preview that excludes continuous assets.

## Test Plan

- Overnight, equal times, multiple windows, effective-now and historical correction.
- All asset modes including `none`, preview makes no changes, draft edit invalidates preview, rejected and stale saves preserve confirmed content.
- Capability off, native picker and keyboard-only web editing, large text, no schedule shows nothing extra.

## Out of Scope

Holiday handling.

## Task Outline

1. Editor with client validation mirroring the service.
2. Section with read-only server preview and explicit save.
3. Asset sheet.
4. Outside values in Beranda and detail.
5. Flip registry.
