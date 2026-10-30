# Implementation Plan: Android smoke CI

**Branch**: `003-android-smoke-ci` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Summary

Add one GitHub Actions job: prebuild, Gradle debug build, emulator, Maestro smoke flow.

## Technical Context

**Primary Dependencies**: `expo prebuild`, Gradle, `reactivecircus/android-emulator-runner`, Maestro
**Target Platform**: Android API 34 emulator, `pixel_6` profile

## Constitution Check

No app code changes unless the smoke run finds a bug. Maestro is a CI tool and stays out of `package.json`.

## Project Structure

```text
../../../.github/workflows/hematdaya-android-smoke.yml
applications/hematdaya-mobile/e2e/smoke.yaml
```

## Flow

`smoke.yaml`: launch, assert "Selamat datang", tap "Mulai", assert tabs "Beranda", "Perangkat", "Saran", tap "Perangkat", assert "Belum ada perangkat". The API is absent in CI, so Beranda must show the unavailable state and stay usable, which also proves the failure path natively.

## Risks

- Hosted emulators are slow; use KVM acceleration and cache Gradle.
- `expo prebuild` output is not committed (`/android` is ignored).

## Test Plan

Introduce a deliberate native crash on a throwaway branch and confirm the job fails with a log artifact.

## Out of Scope

iOS (042), release signing (042), Play Store upload.

## Task Outline

1. Add `e2e/smoke.yaml`.
2. Add `android-smoke.yml` with path filter, Gradle cache, KVM, emulator runner, Maestro, log artifact.
3. Prove failure on a throwaway branch.
4. Record the first run in `docs/roadmap/README.md`.
