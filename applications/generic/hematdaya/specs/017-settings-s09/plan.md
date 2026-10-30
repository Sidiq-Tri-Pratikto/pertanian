# Implementation Plan: Site settings

**Branch**: `017-settings-s09` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Summary

The settings shell later PRs extend: site name, context, timezone, draft handling.

## Project Structure

```text
src/components/hd/HDChoiceGroup.tsx   # add select and checkbox types
src/features/settings/{useSiteDraft.ts, SiteSection.tsx}
src/app/(tabs)/(beranda,perangkat,saran)/pengaturan.tsx
app/sites/service/service.py          # audit on update
```

## API

Uses `PATCH /api/v1/sites/{site_id}` from 004; add audit and timezone validation.

## Prototype Reference

`Settings` in `hematdaya-app.js`, test AT-51.

## Test Plan

Context switch parity; timezone window; UTC rows unchanged; rejected save; cancel; session expiry keeps draft (AT-40 ties into 034, 037); no permission prompt.

## Out of Scope

Tariff (019), schedule (031), notifications (045).

## Task Outline

1. Draft hook.
2. Section UI with preview text.
3. Timezone confirmation.
4. Failure handling.
