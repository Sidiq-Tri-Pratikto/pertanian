# Feature Specification: Android smoke CI

**Feature Branch**: `m0/android-smoke-ci`
**Created**: 2026-10-30
**Status**: Built, awaiting review
**Milestone**: M0 Foundations
**Depends on**: 002
**Size**: S
**Covers**: AT-48
**Flips**: none

**Entry condition**: a GitHub repository with Actions enabled and a hosted runner that can boot the Android emulator.

## User Scenarios & Testing

### User Story 1 - Every PR proves the app starts on Android (Priority: P1)

**Why this priority**: Everything so far ran on web. Finding a native-only failure at 042 would be too late, because 40 PRs would sit on top of it.

**Independent Test**: Open a PR that breaks a native import and watch the job fail.

**Acceptance Scenarios**:

1. **Given** a qualifying PR, **When** the Android job runs, **Then** it builds a debug APK, boots an emulator, launches the app with its JavaScript, and passes the welcome → Mulai → three tabs flow. Since 012, Mulai needs the API, which this job does not run: the flow asserts Mulai's honest failure with Coba lagi, then opens the three tabs through `hematdaya://beranda`.
2. **Given** the app crashes on start, **When** the job runs, **Then** it fails and uploads the log.

### Edge Cases

- A flaky emulator boot retries once, then fails visibly. It never passes silently.
- Run on qualifying pushes to `main` and PRs touching `applications/generic/hematdaya/applications/hematdaya-mobile/**` or `.github/workflows/hematdaya-android-smoke.yml`. Keep API-only changes outside the path filter.

## Requirements

### Functional Requirements

- **FR-001**: CI MUST build a native Android debug binary from the repository with no EAS account.
- **FR-002**: CI MUST run a scripted smoke flow on an emulator.
- **FR-003**: The evidence MUST name the API level and device profile.
- **FR-004**: With the API absent, the smoke flow MUST assert the unavailable state on Beranda and still open Perangkat.

### Key Entities

None.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The job finishes in under 25 minutes on a hosted runner.
- **SC-002**: AT-48 gains its first real Android evidence. iOS stays **not run** until 042.
