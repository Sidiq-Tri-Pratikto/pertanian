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

**New dependency**: `@react-native-community/datetimepicker` through `npx expo install`

## Prototype Reference

`WindowsEditor`, `ProfileSheet`, schedule part of `Settings` in `hematdaya-app.js`, including the preview that excludes continuous assets.

## Test Plan

Overnight; equal times; multiple windows; effective modes; asset modes; rejection; capability off; keyboard and large text; no schedule shows nothing extra.

## Out of Scope

Holiday handling.

## Task Outline

1. Editor with client validation mirroring the service.
2. Section with server preview.
3. Asset sheet.
4. Outside values in Beranda and detail.
5. Flip registry.
