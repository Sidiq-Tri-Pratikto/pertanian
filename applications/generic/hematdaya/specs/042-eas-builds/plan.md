# Implementation Plan: Native builds

**Branch**: `042-eas-builds` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
applications/hematdaya-mobile/eas.json
applications/hematdaya-mobile/assets/images/*
docs/operations/mobile-release.md
```

## Summary

EAS profiles, real assets, device evidence.

Use the HTTPS rehearsal deployment from 039 and the integrated core journeys. Record separate results for Android, iOS and web. A bundle export alone does not count as runtime evidence. Link a web run only if it identifies the tested browser and build. Otherwise record web as not run.

## Decisions to Take in This PR

Owner confirms bundle ID, app name in stores, and any paid accounts.

## Test Plan

- Install, both journeys against HTTPS, cleartext blocked, R8 release run.
- Hardware back on Android, safe areas on iOS, separate runtime and build evidence for Android, iOS and web.

## Out of Scope

Store listing copy, over-the-air update policy unless needed.

## Task Outline

1. `eas.json`.
2. Assets.
3. Preview builds.
4. Device walkthroughs, recorded.
