# hematdaya-mobile

Mobile client for hematdaya: Expo, React Native, TypeScript, Expo Router.

## Setup

Requires Node from `.nvmrc` (`nvm use`).

```bash
make install
make run      # press a, i or w, or scan the QR code
```

## Configuration

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `EXPO_PUBLIC_API_URL` | no | `http://localhost:8000` | API base URL; shipped inside the bundle, so never a secret |

An Android emulator reaches the host at `http://10.0.2.2:8000`. A physical phone needs the computer's LAN address, and the API must allow it. A browser client needs its origin in the API's `CORS_ALLOWED_ORIGINS`.

## Commands

| Command | Does |
|---|---|
| `make run` | Metro dev server |
| `make web` | Run in a browser |
| `make check` | Lint, typecheck, tests, 80% coverage gate |
| `make doctor` | `expo-doctor` dependency and config checks |
| `make export` | Build JavaScript bundles for Android, iOS and web |
| `make generate-api` | Regenerate `src/api/schema.generated.ts` from `contracts/openapi.json` |

Run `make openapi` in the service first when the API changed.

## Dependency notes

- `overrides.zod` in `package.json` lifts the Expo CLI's build-time `zod` above a high-severity advisory. Remove it once Expo ships a fixed version.
- `openapi-typescript` is pinned in the `Makefile`, not installed: it peers on TypeScript 5 while Expo SDK 58 needs TypeScript 6.
