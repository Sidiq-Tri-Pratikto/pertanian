# Implementation Plan: Mobile shell

**Branch**: `002-mobile-shell` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Summary

Turn the starter's health screen into the HematDaya shell: three tabs, welcome, empty states, one Segera hadir screen, tokens and the first native HD components.

## Technical Context

**Language/Version**: TypeScript 6, Expo SDK 58, React Native 0.88, React 19.3, Node 24
**Primary Dependencies**: Expo Router, `expo-router/ui` headless tabs, `react-native-svg`
**Testing**: Jest, `jest-expo`, React Native Testing Library, `expo-router/testing-library`
**Target Platform**: Android, iOS, web
**Project Type**: Mobile plus API

## Constitution Check

No business logic in the client. No data shown. No dependency beyond `react-native-svg` for the design system's icons.

## Project Structure

```text
applications/hematdaya-mobile/
├── design/tokens.json                       # copy of the system's tokens
├── scripts/generate-tokens.mjs              # make tokens
└── src/
    ├── app/
    │   ├── index.tsx                        # S01
    │   └── (tabs)/
    │       ├── _layout.tsx                  # headless tabs, exactly three
    │       ├── (beranda)/beranda.tsx        # S02
    │       ├── (perangkat)/perangkat.tsx
    │       ├── (saran)/saran.tsx
    │       └── (beranda,perangkat,saran)/   # shared detail stack
    │           ├── pengaturan.tsx
    │           └── segera-hadir/[feature].tsx
    ├── components/hd/                       # HDButton, HDChoiceGroup, HDComingSoon, HDIcon,
    │                                        # HDNotice, HDScreen, HDTabBar, HDTag, HDText
    ├── design/tokens.generated.ts
    └── features/                            # registry, context preset, navigation, service status
```

## Decisions

- Routes are `/beranda`, `/perangkat`, `/saran` rather than `/`, because `/` is S01 and groups add no URL segment.
- One generic `segera-hadir/[feature]` route instead of a placeholder per screen, so no route pretends to exist.
- Later detail routes go in the shared folder so the tab bar stays visible.
- Placeholder icons are solid colour: the system has no logo. Real assets arrive in 042.
- Screen titles receive focus on arrival, on web through `focus()` and on native through `sendAccessibilityEvent`.

## Test Plan

Navigation through the real route tree: welcome, context, three tabs, tab stacks, Segera hadir, Rencana fitur, unknown feature, API up, down and non-retryable. Registry coverage and spec folders. Token values. Button loading and disabled guards. Notice tone words.

## Out of Scope

Persisting the welcome choice, demo, any data, offline detection.
