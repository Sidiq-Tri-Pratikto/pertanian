# Implementation Plan: Android smoke CI

**Branch**: `m0/android-smoke-ci` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

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
applications/hematdaya-mobile/e2e/android-smoke.sh
```

`android-smoke.sh` exists because the emulator runner executes each `script` line in its own shell, so the steps that share state must live in one file.

## Flow

The standard debug APK does not embed the JavaScript bundle. Start Metro from the mobile application directory in CI, wait for its status endpoint, and run `adb reverse tcp:8081 tcp:8081` before launch. Keep Metro running through the smoke flow. Keep its log and logcat as separate files, and upload both on every run. The FastAPI service stays absent.

`smoke.yaml`: launch, assert "Selamat datang", tap "Mulai", assert tabs "Beranda", "Perangkat", "Saran" and "Layanan belum tersedia", tap "Perangkat", then assert "Belum ada perangkat".

Only a failed emulator boot retries, once. The job tells a boot failure from a flow failure with a marker the script creates first. A final gate fails the job unless one attempt succeeded, and a retry leaves a visible warning.

The job summary and the `android-smoke-evidence` artifact record the live API level and display, the configured device profile, and the APK name, size and SHA-256.

## Risks

- Hosted emulators are slow; use KVM acceleration and cache Gradle.
- The repository is private and KVM on its hosted runner is unproven. A preflight fails the job at once if `/dev/kvm` is absent, which means the entry condition is unmet.
- A run costs Actions minutes on a private repository, so a new push cancels the PR's run in progress.
- `expo prebuild` output is not committed (`/android` is ignored), and a local run can rewrite `package.json`, so restore it afterward.

## Test Plan

Run the valid flow and record the APK, emulator profile and API level. Break a native import on a throwaway branch and confirm the job fails with a log artifact that names the missing module. Set the boot timeout too low on a throwaway branch and confirm one retry and a visible failure. Base each throwaway PR on this feature's branch, so its diff holds one kind of change, and confirm that a mobile or workflow edit triggers the job and an API-only edit does not.

## Out of Scope

iOS (042), release signing (042), Play Store upload, making this job a required check.

## Task Outline

1. Add `e2e/smoke.yaml` and `e2e/android-smoke.sh`.
2. Add `hematdaya-android-smoke.yml` with the monorepo path filter, Gradle cache, KVM preflight, emulator runner with one boot retry, Metro readiness and forwarding, Maestro and evidence artifacts.
3. Prove failure and the boot retry on throwaway branches, and prove the path filter.
4. Record the first run in `docs/roadmap/README.md`.
