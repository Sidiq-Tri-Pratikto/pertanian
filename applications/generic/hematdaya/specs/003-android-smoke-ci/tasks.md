# Tasks: Android smoke CI

**Input**: `specs/003-android-smoke-ci/spec.md`, `plan.md`, generated against `origin/main` at `af1a5aa`
**Branch**: `m0/android-smoke-ci`
**Prerequisites**: 002 is merged. The entry condition (a hosted runner that can boot the emulator) is unproven until T013.
**Tests**: The Maestro flow is the test. The spec requires proof that the job can fail, so T014–T016 are part of this feature, not extras.

**Paths** start at `applications/generic/hematdaya/`. The workflow is at the pertanian repository root: `.github/workflows/hematdaya-android-smoke.yml`. The mobile app is `applications/hematdaya-mobile/`.

## Decisions resolved against the code

| ID | Decision | Why |
|---|---|---|
| D1 | The job calls one script, `applications/hematdaya-mobile/e2e/android-smoke.sh`, from the emulator runner's `script` input. | `reactivecircus/android-emulator-runner` runs each `script` line in its own shell, so `adb reverse`, Maestro and log capture cannot share state across lines. |
| D2 | Boot retry: the first emulator step has `continue-on-error: true` and the script's first action creates `$RUNNER_TEMP/emulator-booted`. A classify step retries once only when that step failed and the marker is absent. A final gate step fails the job unless one attempt succeeded. A retry writes a `::warning::` and a summary line. | The spec retries a flaky boot once and never passes silently. A failing flow must not be retried, and `continue-on-error` alone would hide a failure. |
| D3 | Metro starts before the emulator, in the background, with `CI=1 npx expo start --port 8081`, logging to `$RUNNER_TEMP/smoke/metro.log`. The job waits for `/status` to answer `packager-status:running`, then requests the Android bundle once so the first launch does not wait on a cold bundle. | The debug APK has no embedded JavaScript. A cold bundle on a hosted runner can outlast a launch assertion. |
| D4 | Both `adb reverse tcp:8081 tcp:8081` and Metro stay up through the flow. Nothing forwards port 8000. | The plan's Flow. `EXPO_PUBLIC_API_URL` is unset, so the app calls `localhost:8000` on the emulator, where nothing listens. That is the API-absent state FR-004 asserts. |
| D5 | Third-party actions are pinned by commit SHA with the version in a comment. `actions/*` follow the `@v4` style of `hematdaya-mobile.yml`. Maestro is pinned to one release, downloaded as `maestro.zip` from GitHub and checked against a SHA-256 written in the workflow. It is never installed through `curl \| bash`. | The repository pins third-party actions after the trivy fix (`6920ed6`). A piped installer runs unreviewed code in CI. |
| D6 | The job sets `timeout-minutes: 25`, and `emulator-boot-timeout` is 300 seconds per attempt. | SC-001 is then enforced and an overrun fails visibly. The default of 600 seconds, twice, would not fit beside the build. |
| D7 | A preflight step checks `/dev/kvm` after enabling the KVM udev rule. If absent, it fails with a message naming the entry condition. | The repository is private and KVM on its hosted runner is unproven. A software emulator would burn minutes and then fail unclearly. |
| D8 | Evidence is written in two places: `$GITHUB_STEP_SUMMARY` and an artifact `android-smoke-evidence` with 14-day retention, uploaded with `if: always()`. It holds the live API level, device model, display size and density from `adb shell`, the configured profile, APK name, size and SHA-256, Maestro version, flow report and screenshots, logcat and Metro log. | FR-003 and scenario 2. `ro.product.model` alone does not name `pixel_6`, so the display values tie the run to the profile. The APK itself is not uploaded: nothing needs it and it is large. |
| D9 | The failure proof breaks a native import with `TurboModuleRegistry.getEnforcing('HematDayaMissingModule')` at module scope of `src/app/_layout.tsx`, on a throwaway branch only. The uploaded log must name that module. | The spec's Independent Test says "breaks a native import". The app then fails to start, the flow must fail, and the log must explain why. |
| D10 | Local checks cover what can run here: `actionlint` with shellcheck through Docker, the prebuild output and Metro readiness. No local Android SDK exists, so **native behavior is proven only by the CI run**. | Rule 009: record which runtime was exercised. |
| D11 | Tasks T012–T016 and T018 need GitHub, so they run after the local tasks. | The job only exists there. |
| D12 | Each throwaway PR uses `m0/android-smoke-ci` as its base, is a draft, and carries one kind of change. After reading the result, close it and delete its branch. | A PR to `main` always includes the workflow file, which matches the path filter, so it could never prove an API-only edit is excluded. The trigger has no branch filter, so these PRs still run the job. |
| D13 | PRs get `concurrency` with `cancel-in-progress: true`, keyed on the PR ref. CI sets `MAESTRO_CLI_NO_ANALYTICS=1`, `EXPO_NO_TELEMETRY=1` and `MAESTRO_DRIVER_STARTUP_TIMEOUT=180000`. | A run costs Actions minutes on a private repository. CI sends no telemetry, and a hosted emulator can be slow to start the driver. |

---

## Phase 1: Setup

**Purpose**: Establish the baseline and read the facts the workflow depends on.

- [X] T001 From `applications/hematdaya-mobile/`, on Node 24 from `.nvmrc`, run `make install`, `make check` and `make doctor`, and record the baseline result in this file's Notes section
- [X] T002 In `applications/hematdaya-mobile/`, run `CI=1 npx expo prebuild --platform android --no-install`. From the generated `android/`, read and record the `applicationId`, `getJSMainModuleName`, Gradle wrapper version and required JDK, and `minSdk`/`targetSdk`. Confirm API 34 is at or above `minSdk`. Delete `android/`, confirm with `git status` that `package.json` and `app.json` are unchanged, and restore them if not
- [X] T003 In `applications/hematdaya-mobile/`, start `CI=1 npx expo start --port 8081`, confirm `curl http://localhost:8081/status` answers `packager-status:running`, and confirm the bundle URL from T002's main module returns 200 with `platform=android&dev=true`. Record the exact URL for T009, then stop Metro

## Phase 2: Foundational

**Purpose**: Resolve the pins the workflow uses. No user story work starts before this.

- [X] T004 Resolve and record in this file's Notes section: the commit SHA of `reactivecircus/android-emulator-runner` v2.38.0 (dereference it if the tag is annotated; the ref currently points at `c9c93e6`); the commit SHA of the latest release of `gradle/actions/setup-gradle`; the SHA-256 of `maestro.zip` for `cli-2.12.1` from that release's `checksums_sha256.txt`

## Phase 3: User Story 1 - Every PR proves the app starts on Android (Priority: P1) 🎯 MVP

**Goal**: A qualifying PR builds a debug APK, boots an emulator, runs the app with its JavaScript and passes the smoke flow, or fails with logs.

**Independent Test**: Open a PR that breaks a native import and watch the job fail with a log artifact.

### Local implementation

- [X] T005 [P] [US1] Write `applications/hematdaya-mobile/e2e/smoke.yaml` with `appId: id.hematdaya.app`: `launchApp` with `clearState: true`; `extendedWaitUntil` for "Selamat datang" with a long timeout for the first bundle; `scrollUntilVisible` then `tapOn` "Mulai"; wait for and assert tabs "Beranda", "Perangkat" and "Saran"; `scrollUntilVisible` "Layanan belum tersedia", which covers the "Memeriksa layanan…" state; take a screenshot; `tapOn` "Perangkat"; assert "Belum ada perangkat"; take a screenshot. These strings come from `src/app/index.tsx`, `src/app/(tabs)/_layout.tsx`, `src/features/ServiceStatus.tsx` and `src/app/(tabs)/(perangkat)/perangkat.tsx`. Do not change app code to make the flow pass
- [X] T006 [P] [US1] Write `applications/hematdaya-mobile/e2e/android-smoke.sh` with `set -euo pipefail` and D1 and D2: create the boot marker first; record `ro.build.version.sdk`, `ro.product.model`, `wm size` and `wm density` into the evidence folder; run `adb reverse tcp:8081 tcp:8081`; install the APK; start `adb logcat` to a file in the background; run `maestro test` with its report and output directed to the evidence folder; then always stop logcat and keep the flow's exit code
- [X] T007 [US1] Create `.github/workflows/hematdaya-android-smoke.yml` with triggers on pushes to `main` and on PRs, both path-filtered to exactly `applications/generic/hematdaya/applications/hematdaya-mobile/**` and `.github/workflows/hematdaya-android-smoke.yml`; `permissions: contents: read`; `timeout-minutes: 25` (D6); `concurrency` and the three environment settings (D13); env for API level 34, profile `pixel_6`, target and `x86_64`; and the KVM udev rule plus `/dev/kvm` preflight (D7)
- [X] T008 [US1] In `.github/workflows/hematdaya-android-smoke.yml`, add setup and build: checkout; Node from `applications/generic/hematdaya/applications/hematdaya-mobile/.nvmrc` with the npm cache; the JDK from T002; pinned Maestro download with checksum check (D5); `npm ci`; `CI=1 npx expo prebuild --platform android --no-install`; Gradle cache through the pinned `setup-gradle`, after prebuild because its cache key needs Gradle files; and `./gradlew assembleDebug -PreactNativeArchitectures=x86_64`. The API service is never started (FR-001, D4)
- [X] T009 [US1] In `.github/workflows/hematdaya-android-smoke.yml`, add Metro start, readiness and bundle preload (D3, using T003's URL), then the emulator steps calling `android-smoke.sh` with the pinned runner: first attempt, classify, single retry and final gate (D2). Set `emulator-boot-timeout: 300` (D6), `disable-animations: true`, and emulator options `-no-window -gpu swiftshader_indirect -noaudio -no-boot-anim -no-snapshot-save`
- [X] T010 [US1] In `.github/workflows/hematdaya-android-smoke.yml`, add `if: always()` steps that stop Metro, write the job summary and upload the `android-smoke-evidence` artifact (D8). The summary states API level, device profile, display, APK, attempts and result, and that iOS stays not run until 042
- [X] T011 [US1] Validate locally: run `actionlint` with shellcheck through its Docker image over the workflow, run shellcheck on `e2e/android-smoke.sh`, parse `e2e/smoke.yaml` as multi-document YAML, and confirm every string the flow asserts exists in the files named in T005. Fix what these find

### Proof on GitHub (needs the pushed branch and open PR)

- [X] T012 [US1] Commit the work as `feat(hematdaya): add Android smoke CI (spec 003)`, staging explicit paths only, sync with `origin/main`, push and open the PR with `pr-generate-description` filling `.github/pull_request_template.md`. Justify Maestro and the emulator runner as new CI tools (constitution, Dependencies), and state that this job is not a required check
- [ ] T013 [US1] On that PR, read the first `hematdaya-android-smoke` run to the end. Confirm the runner has KVM, the flow passes and the summary and artifact hold everything in D8, and record the run URL and cold-cache duration in Notes. Fix real failures. If a failure is an app bug the smoke run found, fix it test-first. If the runner cannot boot the emulator, stop and report the unmet entry condition
- [ ] T014 [US1] Per D12, apply D9 on a throwaway branch and confirm the job fails and uploads logcat and the Metro log, and that the log names `HematDayaMissingModule`. Because the diff holds only a mobile edit, this also proves a mobile edit triggers the job. Record the run URL
- [ ] T015 [US1] Per D12, set `emulator-boot-timeout` too low to boot on a throwaway branch and confirm the job retries once, shows the warning and fails. Because the diff holds only a workflow edit, this also proves a workflow edit triggers the job. Record the run URL
- [ ] T016 [US1] Per D12, edit only `applications/generic/hematdaya/applications/hematdaya-api/README.md` on a throwaway branch and confirm the PR's checks hold no `hematdaya-android-smoke` run while the API workflow did run. Record the PR URL

## Phase 4: Polish

- [X] T017 [P] Add the smoke job to `applications/hematdaya-mobile/README.md`: what it runs, where to find the evidence, and that Maestro is a CI tool outside `package.json`. Correct `README.md:43`, which promises native builds in 003: this job builds an APK for its own check and distributes nothing, so point it to 042
- [ ] T018 Record the first run in `docs/roadmap/README.md`: replace "No native build has run" under "What is proven today" with the run URL, API level, device profile and date, and mark Android smoke as done in the M0 row. State that AT-48 has Android evidence only and iOS stays **not run** until 042 (SC-002)
- [X] T019 [P] Set **Status** in `specs/003-android-smoke-ci/spec.md` to `Built, awaiting review`
- [X] T020 Run `python3 docs/roadmap/check_traceability.py`, then `make check` in `applications/hematdaya-mobile/`, then the hooks as CI does from `applications/hematdaya-api/` (`SKIP=no-commit-to-branch uv run pre-commit run -c ../../.pre-commit-config.yaml --all-files`), and read the output

## Requirement coverage

| Requirement | Tasks |
|---|---|
| FR-001 | T002, T008, T013 |
| FR-002, scenario 1 | T005, T006, T009, T013 |
| FR-003 | T006, T010, T013 |
| FR-004 | T005, T013 |
| Scenario 2 | T006, T010, T014 |
| Edge case: boot retry | T009, T015 |
| Edge case: path filter | T007, T014, T015, T016 |
| SC-001 | T007, T009, T013 |
| SC-002 | T010, T018 |

## Dependencies & Execution Order

- **Setup (T001–T003) → Foundational (T004) → US1 local (T005–T011) → Polish that needs no run (T017, T019, T020) → US1 proof (T012–T016) → T018, then T020 again.**
- T008 depends on T002 and T004. T009 depends on T003, T004 and T006. T010 depends on T009.
- T014–T016 need T013 to pass, so a failure there proves the deliberate break rather than an unfinished job.
- T018 needs T013's run URL.

### Parallel example

T005 and T006 touch different files and can run together. T017 and T019 can run together after T011.

## Implementation Strategy

Complete the local tasks, push, and let the first real run decide what is left. The MVP is T013 passing. This feature has one user story, so it lands as one PR.

## Notes

Record baseline results, resolved pins and run URLs here as tasks finish.

### Baseline (T001, 2026-11-06, Node v24.8.0)

- `make install`: passed. `npm ci` reports 31 audit findings (1 low, 30 moderate), none high.
- `make check`: passed. 6 suites, 47 tests.
- `make doctor`: passed. 20/20 checks.

### Prebuild facts (T002)

| Fact | Value | Source |
|---|---|---|
| `applicationId` | `id.hematdaya.app` | `android/app/build.gradle` |
| Main module | `.expo/.virtual-metro-entry` | The generated `MainApplication.kt` has no `getJSMainModuleName`. It calls `ExpoReactHostFactory.getDefaultReactHost`, whose `jsMainModulePath` defaults to this value |
| Gradle wrapper | 9.4.1 | `android/gradle/wrapper/gradle-wrapper.properties` |
| JDK | 17 | AGP 9.2.1 and Gradle 9.4.1 need at least 17. React Native's plugin sets `jvmToolchain(17)` |
| `minSdk` / `targetSdk` | 24 / 36 | `react-native/gradle/libs.versions.toml`, applied by `expo-root-project`. API 34 is above `minSdk` |
| `compileSdk`, build tools, NDK | 37, 37.0.0, 27.1.12297006 | Same file. AGP downloads what the runner image lacks |

`android/` was deleted afterward. Prebuild reported "no changes" to `package.json`, and `git status` shows `package.json` and `app.json` unchanged.

### Metro (T003)

`/status` answered `packager-status:running` after 3 seconds. The bundle URL returned 200 with 6.1 MB of JavaScript, and Metro stopped cleanly with port 8081 free:

`http://localhost:8081/.expo/.virtual-metro-entry.bundle?platform=android&dev=true`

A second request with the parameters from Expo's manifest URL then bundled 1 module in 126 ms, so differing parameters still share the warmed transform cache. The native app's own request was not observed here.

### Pins (T004)

| Item | Pin |
|---|---|
| `reactivecircus/android-emulator-runner` v2.38.0 | `a421e43855164a8197daf9d8d40fe71c6996bb0d`. The ref `c9c93e6` is an annotated tag, dereferenced to this commit |
| `gradle/actions/setup-gradle` v6.4.1, latest release | `8da46b539cd8fe6ab27ca75128919a18d757604c`. Also an annotated tag, dereferenced |
| Maestro `cli-2.12.1`, `maestro.zip` | SHA-256 `54dbb0716425626604973cbb374c585ca30272375d9ce15177a1152765ddd9d7`, from `checksums_sha256.txt`. The GitHub asset digest matches. Size 349.8 MB |

### Choices within the decisions

- `setup-gradle` uses `cache-provider: basic`. The v6 default is a proprietary provider that is only a free preview on private repositories, and this repository is private. Basic is MIT and free. PR runs restore the cache but do not write it, the action's default, so PRs stay cold until a run on `main` seeds it.
- Emulator `target` is `default`, the runner's default image, for API 34 `x86_64`.
- The classify step kills any leftover `qemu-system` before the retry, because a timed-out boot can leave the emulator holding the AVD.
- The build step runs `./gradlew --stop` to free memory for the emulator.
- The summary step computes the result and the final gate reads it, so the two cannot disagree. A summary that never ran fails the gate. The gate also requires the script's recorded Maestro exit code to be 0.
- The gate is the last step, after the upload, so evidence is uploaded before the job fails.

### Local validation (T011)

Runtime exercised: **no Android runtime**. There is no local Android SDK or Maestro, so nothing here proves native behavior. Only T013 can.

- `rhysd/actionlint:1.7.12`, which includes shellcheck: no findings on the workflow. A probe with an unquoted variable confirmed it does run shellcheck.
- `koalaman/shellcheck:v0.11.0` on `e2e/android-smoke.sh`: no findings.
- `e2e/smoke.yaml` parses as two YAML documents. Every asserted string exists in the file T005 names. The syntax was read against Maestro's `cli-2.12.1` source, not executed.
- The summary and gate scripts, taken from the workflow, ran against 11 outcome combinations with temporary files. Only a successful attempt with a recorded exit code of 0 passed.
- `e2e/android-smoke.sh` ran with fake `adb` and `maestro`. It created the marker, kept exit codes 0, 1 and 7, and stopped logcat each time.

### Final checks (T020, first pass, before T012)

- `python3 docs/roadmap/check_traceability.py`: passed. 123 requirements mapped across 46 specs.
- `make check`: passed. 6 suites, 47 tests, 92.81% line coverage. `make doctor`: passed, 20/20.
- `pre-commit --all-files` from `applications/hematdaya-api/`: passed. It covers tracked files only, so `tasks.md` and `e2e/*` were also run with `--files`: passed.

The dependency order runs T020 again after T018.

### Runs on GitHub (T013)

- [Run 42243173227](https://github.com/Sidiq-Tri-Pratikto/pertanian/actions/runs/42243173227) at `53a155f`: failed after 13 seconds at `setup-gradle`, because its cache key found no Gradle files before prebuild. The step moved after prebuild. No build, emulator or flow ran, so this is not Android evidence. It does show two things: `/dev/kvm` is available on this private repository's hosted runner, and when an early step fails the summary and artifact still upload and the gate fails the job.
- [Run 42245686334](https://github.com/Sidiq-Tri-Pratikto/pertanian/actions/runs/42245686334) at `4c73555`: the debug APK built in 17 minutes 43 seconds with a cold cache (78,286,806 bytes), and Metro served the bundle. Both emulator attempts then failed with `No space left on device` while installing the system image, so no emulator or flow ran. The job now removes toolchains it does not use and records free disk after the build. The retry and gate behaved as designed.
- [Run 42334195199](https://github.com/Sidiq-Tri-Pratikto/pertanian/actions/runs/42334195199) at `ce3c6d7` on PR #31: the app started, but a system dialog, "Quickstep isn't responding", covered its window, so Maestro could not see "Selamat datang". The launcher had stopped responding on a slow emulator, not the app. `android-smoke.sh` now sets `hide_error_dialogs`. Android then kills a process that stops responding instead of asking, so an app that hangs still fails the flow.
