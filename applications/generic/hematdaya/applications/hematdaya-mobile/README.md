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
| `tests/tokens.test.ts` | Generated tokens match `design/tokens.json` |
| `src/api/errors.test.ts` | Failure envelope parsing |

Run one file with `npx jest tests/navigation.test.tsx`, or keep tests running with `npx jest --watch`. Jest mocks the network, so a test run never proves the app reaches the service: check that in the running app.

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
| `src/features/registry.ts` | Every planned feature. A feature's pull request flips its `status` |
| `design/tokens.json` | Copy of the design system tokens; `src/design/tokens.generated.ts` is built from it |
| `src/api/` | API client, failure parsing, generated contract |

## Commands

| Command | Does |
|---|---|
| `make doctor` | `expo-doctor` dependency and config checks |
| `make export` | Build JavaScript bundles for Android, iOS and web |
| `make tokens` | Regenerate `src/design/tokens.generated.ts` from `design/tokens.json` |
| `make generate-api` | Regenerate `src/api/schema.generated.ts` from `contracts/openapi.json` |

Run `make openapi` in the service first when the API changed.

## Dependency notes

- `overrides.zod` in `package.json` lifts the Expo CLI's build-time `zod` above a high-severity advisory. Remove it once Expo ships a fixed version.
- `openapi-typescript` is pinned in the `Makefile`, not installed: it peers on TypeScript 5 while Expo SDK 58 needs TypeScript 6.
