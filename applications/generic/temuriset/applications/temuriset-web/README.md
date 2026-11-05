# temuriset-web

TemuRiset web client: Next.js App Router, React and TypeScript, built from the TemuRiset Design System. Product copy is Indonesian. It renders what the API returns and never re-implements a rule.

To run the whole product, use `make dev` from the [project root](../../README.md#quick-start). Its [testing guide](../../README.md#testing) covers both applications.

## Run the web app alone

Requires Node 24 (`nvm use`) and a running API.

```bash
make install    # npm ci
make run        # dev server on http://localhost:3020
```

The dev server forwards `/api/v1/*` and `/health/*` to `API_URL`, so browsers only ever call this origin. Use `make run PORT=3030` when port 3020 is taken.

## Testing

```bash
make test           # Vitest, no services needed
make check          # lint (no warnings allowed), typecheck, tests, 80% coverage gate
make build          # production build
make e2e            # Chromium against the production build; needs the API (the root `make e2e` starts it)
```

| Path | Covers |
|---|---|
| `tests/components.test.tsx` | Design-system ports: Status, NextStep, EmptyState, Button, ChoiceGroup, Screen |
| `tests/pages.test.tsx` | Every route signed in and out, safe return paths, settings, invitations |
| `tests/auth.test.tsx` | Sign-up and code screens, error summary focus, context switcher, account and organization forms |
| `e2e/auth.spec.ts` | Chromium journeys: both personas sign up, wrong code, return after sign-in, context switch, invitation, sign-out |
| `tests/service-status.test.tsx` | Service check, retry, final failure, failure parsing |
| `tests/a11y.test.tsx` | axe on each base view (jsdom: no contrast or reflow) |
| `tests/registry.test.ts` | Every planned feature, screen coverage, links to existing spec folders |
| `tests/design.test.ts` | Copied stylesheets equal the design-system source |
| `e2e/` | Browser checks on every route in `e2e/routes.ts`: console and request errors, overflow at 320–1280 px and 200% text, axe with contrast, keyboard focus. Report in `playwright-report/` |

Run one file with `npx vitest run tests/pages.test.tsx`, match by name with `npx vitest run -t "starts at Jelajahi"`, or rerun on save with `npx vitest`. `make test-coverage` writes an HTML report to `coverage/index.html`.

## Configuration

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `API_URL` | no | `http://localhost:8020` | Where `/api/v1` and `/health` are forwarded. Read when the server starts, and fixed into a production build |

## Commands

| Command | Does |
|---|---|
| `make generate-api` | Regenerate `src/api/schema.generated.ts` from `contracts/openapi.json` |
| `make design` | Recopy `tokens.css` and `bundle.css` from `docs/generic/temuriset/design-system` |
| `make start` | Serve the production build on port 3020 |

## Routes

| Route | Screen |
|---|---|
| `/start`, `/start?masuk=1` | S01: sign up (persona, name, email, language, time zone) or sign in; never an organization |
| `/start/kode` | The code step: where the code went, resend, attempts left |
| `/undangan/<token>` | What an invitation grants, then **Terima undangan** |
| `/home` | S02 Beranda |
| `/inventions` | Inovasi Saya |
| `/discover` | S03 Temukan Investor/Mitra, or Jelajahi for partners |
| `/opportunities` | Kebutuhan/Mandat |
| `/pitches`, `/pitches?box=masuk`, `/pitches?box=diskusi` | S12 lists |
| `/settings` | S18: account, organizations, members and invitations of the acting organization, service check, planned features, **Keluar** |
| `/segera-hadir/<feature>` | What a planned feature will do |

The persona lives in an http-only cookie until accounts arrive in spec 008. It picks menus and language, never access.
