# hematdaya-mobile

HematDaya mobile client: Expo, React Native, TypeScript, Expo Router, for Android, iOS and web. The product interface is Indonesian. The service computes every number; this app renders it.

The base release is deliberately small: real navigation, design tokens, the API contract, and "Segera hadir" for every planned feature. See `docs/roadmap/README.md`.

To run the whole product, use `./local-start.sh` from the [repository root](../../README.md#quick-start).

## Run the app alone

Requires Node 24. The API must be running for the service status on Beranda; every screen still opens without it.

```bash
nvm use
make install
make web      # browser on http://localhost:8081
make run      # or Metro: press a, i or w, or scan the QR code
```

Node 25 is not supported by React Native 0.88.

## Testing

```bash
make test           # Jest, no API needed
make check          # lint, typecheck, tests, 80% coverage gate
```

| Path | Covers |
|---|---|
| `tests/navigation.test.tsx` | Welcome, exactly three tabs, Segera hadir, service status states |
| `tests/registry.test.ts` | Every planned screen has an entry, and each entry has a spec folder |
| `tests/components.test.tsx` | `HD` components |
| `tests/perangkat.test.tsx` | Perangkat list and asset detail, from responses recorded from the service in `tests/fixtures/assets.json` |
| `tests/asset-model.test.ts` | What a list row and asset detail show, from the same recorded responses |
| `tests/import.test.tsx` | S10 import steps, from file or paste to the Beranda landing, every failure code, unknown commits and web reloads, from responses recorded from the service in `tests/fixtures/imports.json` |
| `tests/import-model.test.ts` | What each import step shows: controls per question, answers, landing period, result, failure outcomes, examples |
| `tests/tokens.test.ts` | Generated tokens match `design/tokens.json` |
| `src/api/errors.test.ts` | Failure envelope parsing |

Run one file with `npx jest tests/navigation.test.tsx`, or keep tests running with `npx jest --watch`. Jest mocks the network, so a test run never proves the app reaches the service: check that in the running app.

## Android smoke CI

The `hematdaya-android-smoke` job (`.github/workflows/hematdaya-android-smoke.yml` at the pertanian repository root) runs on pushes to `main` and on pull requests that touch this app or that workflow. It generates the Android project with `expo prebuild`, builds a debug APK with no EAS account, starts Metro, boots an API 34 `pixel_6` emulator and runs `e2e/smoke.yaml`: welcome, Mulai, the three tabs, "Layanan belum tersedia" on Beranda with the API absent, then Perangkat. The APK exists for this check and nothing distributes it. A failed emulator boot retries once with a warning; a failed flow never retries.

Find the evidence on the run: the job summary states the API level, device profile, display, APK, attempts and result. The `android-smoke-evidence` artifact, kept for 14 days, holds the same values with the flow report, screenshots, logcat and Metro log. iOS stays not run until spec 042.

Maestro is a CI tool outside `package.json`: the workflow downloads one pinned release and checks its SHA-256. `e2e/android-smoke.sh` expects the booted emulator and environment that the workflow provides.

## Configuration

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `EXPO_PUBLIC_API_URL` | no | `http://localhost:8000` | API base URL; shipped inside the bundle, so never a secret |

Where the app needs to reach the service:

| Client | `EXPO_PUBLIC_API_URL` | Also needs |
|---|---|---|
| Browser | `http://localhost:8000` | Its origin in the API's `CORS_ALLOWED_ORIGINS` |
| Android emulator | `http://10.0.2.2:8000` | |
| iOS simulator | `http://localhost:8000` | |
| Phone on the same Wi-Fi | `http://<computer-address>:8000` | Port open in the firewall. `./local-start.sh phone` sets this for you |

## Where things live

| Path | Purpose |
|---|---|
| `src/app/` | Expo Router routes. `(tabs)/` holds exactly Beranda, Perangkat and Saran |
| `src/app/(tabs)/(beranda,perangkat,saran)/` | Detail routes shared by the three tabs, so back stays in the tab |
| `src/components/hd/` | Native HematDaya Design System components, same names and meaning as `window.HD` |
| `src/features/assets/` | Perangkat list and asset detail: reads, row and detail models, screens |
| `src/features/imports/` | S10 CSV import: the draft above the tabs, the four step screens (`impor/[step]`), the pure model and the examples |
| `src/features/registry.ts` | Every planned feature. A feature's pull request flips its `status` |
| `design/tokens.json` | Copy of the design system tokens; `src/design/tokens.generated.ts` is built from it |
| `src/api/` | API client, failure parsing, generated contract |
| `e2e/` | Android smoke flow and the script the CI job runs on the emulator |

## Commands

| Command | Does |
|---|---|
| `make doctor` | `expo-doctor` dependency and config checks |
| `make export` | Build JavaScript bundles for Android, iOS and web |
| `make tokens` | Regenerate `src/design/tokens.generated.ts` from `design/tokens.json` |
| `make generate-api` | Regenerate `src/api/schema.generated.ts` from `contracts/openapi.json` |

Run `make openapi` in the service first when the API changed.

## Dependency notes

- `expo-document-picker` picks the CSV file on Android, iOS and web (on the web it opens an `<input type="file">`). The picked file is uploaded as it is, never read in JavaScript: the service decodes it, so `expo-file-system` is not needed. It copies the file to the cache so the same file can be sent again for every new preview.
- `overrides.zod` in `package.json` lifts the Expo CLI's build-time `zod` above a high-severity advisory. Remove it once Expo ships a fixed version.
- `openapi-typescript` is pinned in the `Makefile`, not installed: it peers on TypeScript 5 while Expo SDK 58 needs TypeScript 6.

## Offline acceptance (Spec 034)

Start a migrated test API and Postgres with `COMPOSITION=core-only`, then start Expo web with `EXPO_PUBLIC_API_URL` pointing to that API. Use synthetic test data because the acceptance flow creates temporary demo workspaces and commits the built-in CSV example.

Run the Chrome matrix from this app directory with Node and installed Chrome. The script expects Playwright to be resolvable from the app or from `HEMATDAYA_PLAYWRIGHT_MODULE`.

```bash
HEMATDAYA_WEB_URL=http://localhost:8081 \
HEMATDAYA_API_URL=http://localhost:8000 \
node e2e/offline-web.mjs
```

Chrome exercises a loaded tab with browser offline mode, then a same-tab cold reload with the app shell reachable and API traffic blocked. It verifies the previous fetch time, a saved asset draft, separate source freshness, owner isolation and the real CSV commit/recovery path. It also checks the learning, measured-zero and scope-refusal cases.

The **HematDaya Android Offline** pull-request workflow builds one embedded JavaScript APK for the exact candidate commit. It uses a Pixel 6 API 34 emulator, pinned Maestro, a dedicated migrated Postgres, the core-only API and test-only loopback. The flow cuts the ADB route and radios for the cold process launch. The `android-offline-evidence` artifact contains the candidate and APK identity, verdict, sanitized request log, screenshots and JUnit. The separate spec 003 job still runs its API-absent flow.

Release the `data-tersimpan` registry change after Chrome and Android pass for the candidate. iOS runtime, the two spec 019 tariff cases and joint P1/P2 walkthroughs have separate evidence.
