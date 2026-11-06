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
| `tests/portfolio.test.tsx` | Editor state machine, save and focus, failed save retried with the same key, conflict, publication errors per step, preview, owner and partner detail |
| `tests/documents.test.tsx` | Limits before upload, upload progress and polling, cancel, three states, grants, the revoke dialog with focus return and Escape |
| `tests/needs.test.tsx` | F01 money labels, open ranges and the Beranda queue, invalid range with focus and kept values, `?return=`, activation errors, one raise card, proposed company, funding off, entity then raise saved, axe |
| `tests/money.test.ts` | String-only money formatter against the `TR.format` cases: grouping, decimals, unknown, open-ended and equal ranges |
| `e2e/needs.spec.ts` | Chromium: F01 from step 3, invalid range, Beranda queue for an open range, `?return=`, J02 raise for two inventions and Back from an invention |
| `e2e/documents.spec.ts` | Chromium: PDF scanned and read, scan needing manual reading, rejected file, size limit, revocation then refusal (AC65) |
| `e2e/portfolio.spec.ts` | Chromium: four steps to version 1, failed save and retry, conflict from another tab, partner view |
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
| `/start`, `/start?masuk=1` | S01: sign up (persona, name, email, language, time zone) or sign in; never an organization. With demo mode, a picker of labelled demo accounts and "Atur ulang demo" |
| `/start/kode` | The code step: where the code went, resend, attempts left |
| `/inventions` | S04 Inovasi Saya: drafts, published and archived, "Ada draf perubahan", **Tambah inovasi** |
| `/inventions/<id>` | S04 detail: owner view with facts, provenance and claims, or the public projection for others |
| `/inventions/<id>/edit?step=1..4` | S05 editor: basics, evidence with private documents (upload, three states, grants, revoke), support (coming), public preview and **Terbitkan versi N** |
| `/support-requests` | S06 list: support requests per invention, company raises, and starting either |
| `/opportunities` | Kebutuhan/Mandat: the acting party's mandates with status and version, and starting one |
| `/opportunities/<id>/edit` | S09: edit, review, then activate a mandate; requirements with stage and verification mode |
| `/partners/<partyId>` | S08: a partner's profile, source and availability labels, contact route and mandates; the owner edits here |
| `/support-requests/<id>` | S06 detail and form: labelled money, outcome, forms of support, budget; `?return=` goes back after saving |
| `/funding-requests/<id>` | S07: one raise card, target and contribution apart, linked inventions |
| `/funding-requests/<id>/edit` | S07 editor, or a notice when the deployment does not run company funding |
| `/discover?type=&q=&sector=&stage=&saved=` | S03: inventions, company funding (one card per raise) or partners in labelled sections, filters in the address so Back restores them, save and "Kurang relevan"; empty filters explain themselves |
| `/matches`, `/matches?source=SUPPORT_REQUEST:<id>` | S10: pick a need, then each mandate's label, reasons, gap and one action, with rows and the score note on request; "Mandat tidak direkomendasikan" and partners' own forms apart |
| `/pitches/new?source=<TYPE>:<id>&target=<opportunity>` | S11: recipient and sender, pinned versions, requirement rows, files to share by checkbox, the editable "Brief pitching", what sending does, then **Kirim pitching**; stale, lost, duplicate and not-ready states |
| `/pitches/<id>?tab=ringkasan\|revisi\|dokumen\|diskusi\|jadwal\|riwayat` | S13: whose turn, the decision dialogs (approve, reject with a reason, withdraw, close), itemized revision requests, honest answers with attachments and resubmission, item review, shared files and every submission; Diskusi with messages polled every 30 seconds and tasks; Jadwal with proposals in the reader's zone, explicit confirmation, conflicts, expiry, replacement, outcomes and ICS; an unrelated account sees only "Anda belum memiliki akses" |
| `/partnerships/new?pitch=<id>` | S15 proposal from a completed meeting, with the API's eligible types, a public ceiling and separate consent |
| `/partnerships/<id>` | S15 current version, confirmations, correction history, public preview, restriction and claim review |
| `/profiles/<partyId>` | S16 signed-out profile with published biography and inventions, and current consented relationship fields |
| `/undangan/<token>` | What an invitation grants, then **Terima undangan** |
| `/home` | S02 Beranda: what waits first as `TR.NextStep`, the rest by turn, and in-app notifications |
| `/inventions` | Inovasi Saya |
| `/discover` | S03 Temukan Investor/Mitra, or Jelajahi for partners |
| `/opportunities` | Kebutuhan/Mandat |
| `/pitches`, `/pitches?box=masuk`, `/pitches?box=diskusi` | S12 lists: sent pitches, Pitching Masuk, and the discussion box, with whose turn, update time and filters (`giliran`, `status`) kept in the address |
| `/settings` | S18: account, organizations, members and invitations of the acting organization, biography publication, private reports and their case status, export and deletion requests, service check, planned features, **Keluar** |
| `/segera-hadir/<feature>` | What a planned feature will do |

The persona lives in an http-only cookie until accounts arrive in spec 008. It picks menus and language, never access.

## Staging browser checks

The [deployment runbook](../../../../../deployment/temuriset/RUNBOOK.md) uses the standalone web image with `API_URL=http://api:8000` at build and runtime. Use that internal address or build another image when the target changes. The browser stays on the web origin.

For the deployed suite, set `E2E_STAGING_URL` to the approved HTTPS origin and `E2E_STAGING_FIXTURES_FILE` to an operator-provisioned private JSON file outside the checkout. Run `npx playwright test` without a test filter. In this mode Playwright uses the deployed app, requires the 003 and `j01.spec.ts` through `j05.spec.ts` files and checks authenticated fixtures against `/api/v1/me`. It does not start a local server. The report must contain successful results for every required suite and rejects skipped journeys.

The fixture file has `origin`, `synthetic: true`, `syntheticEmailDomain` set to the operator-approved lowercase DNS domain dedicated to staging accounts, and a `sessions` object keyed by `project > test file > test title`, including any enclosing suite titles. Each entry maps a persona to an array of unused `{ "email": "fixture@qa.example.org", "session": "<operator-provisioned token>" }` values, in test invocation order. The address must be lowercase and its domain must exactly match `syntheticEmailDomain`. QA uses synthetic, fresh accounts authenticated through the approved staging access path and revokes them after the run. Keep session files and outputs in approved restricted storage. The 042 authentication path and journey prerequisites remain required before a real staging acceptance run. `make e2e` is for the local production build with the development API and synthetic fixture creation.

## Workspace portability

Open **Impor dan ekspor data** from **Inovasi Saya** at `/inventions/import`. Choose a version 1 JSON file
(up to 20 MiB and 2,000 records), review the planned creates, updates and conflicts, then confirm the
acting party and apply. Validation, preview and apply show separate progress. Cancellation keeps
the records already saved. Resolve a conflict on the existing invention or profile, then upload the file
again to get a fresh preview.

The file uses `schema_version`, `external_system`, source `provenance` and invention rows with
`external_id`, `provenance` and `fields`. See the [API guide](../temuriset-api/README.md#workspace-portability)
for an example and the supported field mapping. Private notes require explicit selection.

Select an invention version, a document ID and version you may download, or both, then wait for the JSON
export. The web page downloads the result through the authenticated API gateway and shows a denial when
access is lost. Results expire after 24 hours.
