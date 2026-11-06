# Implementation Plan: Android smoke CI

**Branch**: `003-android-smoke-ci` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Summary

Add one GitHub Actions job: prebuild, Gradle debug build, emulator, Metro and Maestro smoke flow.

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

The standard debug APK does not embed the JavaScript bundle. Start Metro from the mobile application directory in CI, wait for its status endpoint, and run `adb reverse tcp:8081 tcp:8081` before launch. Keep Metro running through the smoke flow and capture its logs with logcat on failure. The FastAPI service stays absent.

`smoke.yaml`: launch, assert "Selamat datang", tap "Mulai", assert tabs "Beranda", "Perangkat", "Saran" and "Layanan belum tersedia", tap "Perangkat", then assert "Belum ada perangkat".

## Risks

- Hosted emulators are slow; use KVM acceleration and cache Gradle.
- `expo prebuild` output is not committed (`/android` is ignored).

## Test Plan

Run the valid flow and record the APK, emulator profile and API level. Introduce a deliberate native crash on a throwaway branch and confirm the job fails with a log artifact. Confirm that a mobile or workflow edit triggers the job and an API-only edit does not.

## Out of Scope

iOS (042), release signing (042), Play Store upload.

## Task Outline

1. Add `e2e/smoke.yaml`.
2. Add `hematdaya-android-smoke.yml` with the monorepo path filter, Gradle cache, KVM, emulator runner, Metro readiness and forwarding, Maestro and log artifacts.
3. Prove failure on a throwaway branch.
4. Record the first run in `docs/roadmap/README.md`.
