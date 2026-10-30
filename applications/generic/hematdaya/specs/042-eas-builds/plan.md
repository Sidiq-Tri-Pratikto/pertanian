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

## Decisions to Take in This PR

Owner confirms bundle ID, app name in stores, and any paid accounts.

## Test Plan

Install; both journeys; cleartext blocked; R8 release run; hardware back on Android; safe areas on iOS.

## Out of Scope

Store listing copy, over-the-air update policy unless needed.

## Task Outline

1. `eas.json`.
2. Assets.
3. Preview builds.
4. Device walkthroughs, recorded.
