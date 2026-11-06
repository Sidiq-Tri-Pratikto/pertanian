# temuriset-api

TemuRiset service: FastAPI, async SQLAlchemy, Alembic and Postgres 17. It is the one authority for matching, permissions, money semantics and consent; the web client only renders what it returns.

To run the whole product, use `make dev` from the [project root](../../README.md#quick-start). Its [testing guide](../../README.md#testing) covers both applications.

## Run the service alone

Requires [uv](https://docs.astral.sh/uv/) and Docker.

```bash
make install           # Python dependencies and pre-commit hooks
make run-dependencies  # Postgres on host port 5442
make migrate           # creates .env on first use, then applies migrations
make run               # API with reload on port 8020
make demo-seed         # optional: recreate the labelled demo accounts and fixtures (spec 021)
```

Open http://localhost:8020/docs. Use `make run PORT=8030` if port 8020 is taken, and `make stop-dependencies` when you finish.

## Testing

```bash
make test-unit         # no services needed
make run-dependencies  # once, for everything below
make check             # lint, format check, all tests, 80% coverage gate
```

| Path | Covers | Needs |
|---|---|---|
| `tests/unit/capabilities/` | Manifest, compositions and overrides, capability guard, startup configuration checks | Nothing |
| `tests/unit/core/` | Errors, database session, OpenAPI document, no money-movement routes, clock, money and cursors | Nothing |
| `tests/unit/platform/` | Stale versions, request digest, acting-party placeholder, worker backoff and registry | Nothing |
| `tests/unit/health/` | Liveness and readiness | Nothing |
| `tests/integration/` | Real requests against Postgres after migrations | Postgres |
| `tests/integration/identity/` | Sign-up for both personas without an organization, codes wrong, expired and used up, 1,000-guess brute force, rate limits, no account leak, sign-out, cross-origin refusal, `PATCH /me` | Postgres |
| `tests/integration/documents/` | Limits before upload, quarantine and scan (AC13, AC14), scans without text (AC15), signature mismatch, grants, ranges and revocation (AC65), a 20 MB round trip | Postgres |
| `tests/unit/documents/` | ClamAV INSTREAM against a fake daemon, byte sniffing, extraction, chunked storage | Nothing |
| `tests/integration/needs/` | Support requests: exact budgets as strings (F01), invalid ranges per field (AC16), unknown money as null with a reason (AC17), exact line totals, status changes, versions, stale saves | Postgres |
| `tests/unit/needs/` | Budget rules and when two ranges compare directly (AC18) | Nothing |
| `tests/integration/funding/` | One raise with two invention links (AC19), proposed companies, target versions, exact amounts per field, no valuation fields, archived links, and the guard in all three compositions with reads kept (AC67) | Postgres |
| `tests/integration/intake/` | Partner profiles with honest labels (AC22), closing intake against specific targets (AC23), external handoffs (AC24), separate opportunities (AC25), the availability table, versions, states, expiry, readiness, typed requirements, failure paths | Postgres |
| `tests/unit/intake/` | Recipients A–E as data, requirement operators and value shapes, states and the availability table | Nothing |
| `tests/integration/discovery/` | Sections from stated preferences with no trend (AC28–AC30), empty filters echoed with a deliberate relaxation, English aliases and typos, one card per raise, amounts in one currency, saved items and "Kurang relevan" per party, archive removes the row, private notes unsearchable, cursors | Postgres |
| `tests/unit/matching/` | The engine against every prototype matching oracle: F01–F06, AC18, AC20, AC21, AC25, AC27, AC31–AC33, abstain, no checklist, a mandatory failure never positive | Nothing |
| `tests/integration/matching/` | Golden results in `contracts/golden/` byte for byte over HTTP (`UPDATE_GOLDEN=1` rewrites them), the F01-GAP repair, stored and reproducible runs, owner-only sources, another party's file proves nothing, the funding guard | Postgres |
| `tests/integration/pitches/` | Preflight pins, shareable files and the template brief per fixture, the summarizer off, failing or untraceable (AC35, AC68), export redaction (AC36); submission with grants and notification, replay and conflict (AC37, AC38), duplicates (AC39), races, closed targets (AC26), stale and expired preflights (AC34), required files, frozen snapshots, the daily limit; decisions (AC40–AC42) with races, stale submissions, retries, the other side and a view-only member; revision rounds, draft answers, honest answers, missing required answers, new file versions, item review (AC43–AC45) | Postgres |
| `tests/unit/briefs/` | Amount grouping and the summary traceability check | Nothing |
| `tests/unit/pitches/` | The pitch state table against PRD section 7, every status and action pair | Nothing |
| `tests/unit/discussion/` | Whose turn for both parties in every pitch and scheduling state | Nothing |
| `tests/integration/discussion/` | Next action and queue per party, messages with `since` and retries, tasks after approval, notifications once per event and party, a failing consumer that never repeats the decision (AC46), strangers (AC48) | Postgres |
| `tests/integration/scheduling/` | J04 conflicts and half-open acceptance (AC50), 50 parallel acceptances, racing overlapping bookings, replacement (AC51), 72-hour and all-past expiry, elapsed meetings and outcomes (AC47), ICS (AC68), invalid proposals | Postgres |
| `tests/integration/demo/` | Demo routes absent outside demo mode, the labelled picker, no email for demo accounts, two resets with identical ids, real accounts untouched, goldens and variants on seeded data, demo activity counts nowhere (AC03) | Postgres |
| `tests/unit/demo/` | Production refuses demo mode unless marked a demonstration | Nothing |
| `tests/integration/portfolio/` | Drafts, each publication rule, immutable versions (AC07–AC11), stale drafts, archive, public projection, outbox events | Postgres |
| `tests/integration/access/` | Organizations, capabilities (AC04), hidden organizations (AC05), a removed member's job denied (AC06), invitations expired and revoked, stale context, last manager | Postgres |
| `tests/integration/moderation/` | Private cases, scope and audit, suspension, protected downloads, policy-based privacy requests and deferred erasure | Postgres |
| `tests/integration/test_isolation.py` | Every data route called as an unrelated party returns `NOT_FOUND` or nothing; fails when a new route is not registered | Postgres |
| `tests/integration/platform/` | Idempotent replay and conflict, 20 parallel requests with one key, operations, append-only audit, outbox atomic with the request, worker retries, two workers, jobs | Postgres |

Run one test with `uv run pytest tests/unit/health/test_health.py -v`, or match by name with `uv run pytest tests -k capabilities`. `make test-coverage` also writes an HTML report to `htmlcov/index.html`.

## Configuration

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `DATABASE_URL` | yes | | Async SQLAlchemy URL |
| `SERVICE_NAME` | no | `temuriset-api` | Name on failure records |
| `ENVIRONMENT` | no | `development` | Deployment environment |
| `LOG_LEVEL` | no | `INFO` | Log level |
| `CORS_ALLOWED_ORIGINS` | no | `[]` | JSON list of browser origins; the web client proxies through its own origin and needs none |
| `COMPOSITION` | no | `generic-base` | `generic-base`, `generic-with-review` or `project-support-only`; anything else stops startup |
| `COMPOSITION_OVERRIDES` | no | `{}` | JSON object switching capabilities on or off on top of the composition, for example `{"organization_review": true}`. An unknown capability, a missing dependency or a secret-looking value stops startup |
| `FILE_SCANNER` | no | `development-accept` | `clamav` or `development-accept`; the second stops startup outside development |
| `WEB_ORIGIN` | no | `http://localhost:3020` | Origin of the web client; an unsafe request carrying the session cookie from any other origin gets `FORBIDDEN` |
| `SESSION_COOKIE_SECURE` | no | unset | `Secure` flag on `tr_session`; unset means secure everywhere but development |
| `MAILBOX_ADAPTER` | no | `development` | Select `development` for the local mailbox table, `loopback-relay` for a synthetic development relay, or `disabled`. Outside development, use `disabled`. |
| `EMAIL_RELAY_URL` | relay only | unset | HTTP(S) endpoint on a literal loopback IP, for example `http://127.0.0.1:8090/deliver`. |
| `EMAIL_RELAY_SENDER` | relay only | unset | Synthetic address supplied to the local relay as the sender. |
| `EMAIL_ENVELOPE_KEY` | relay only | unset | Independent Fernet key for short-lived code and invitation envelopes. Give the API and worker the same key through their local secret configuration. |
| `CODE_REQUESTS_PER_EMAIL_PER_HOUR` | no | `5` | Sign-in code requests per email per hour |
| `CODE_REQUESTS_PER_ADDRESS_PER_HOUR` | no | `20` | Sign-in code requests per client address per hour |
| `STORAGE_PATH` | no | `.storage` | Private folder for uploaded bytes; downloads always go through the gateway |
| `DEMO_MODE` | no | `false` | Offers the labelled demo accounts, sign-in from the picker and reset under `/api/v1/demo` |
| `DEMO_DEPLOYMENT` | no | `false` | Marks the deployment as a demonstration; outside development, `DEMO_MODE=true` refuses to start without it |
| `CLAMAV_HOST`, `CLAMAV_PORT` | no | `localhost`, `3310` | ClamAV daemon for `FILE_SCANNER=clamav` (`--profile scanner` in `dev-compose.yml`) |
| `SKIP_MIGRATIONS` | no | `false` | Container start skips migrations when `true` |
| `PORT` | no | `8000` | Container listen port (`make run` uses 8020 on the host) |

## Commands

| Command | Does |
|---|---|
| `make openapi` | Export the API contract to `contracts/openapi.json` |
| `make worker` | Run `python -m app.worker`: dispatch outbox events and run jobs; Ctrl+C finishes the current pass |
| `make test-integration` | Integration tests only, needs Postgres |
| `make reset-dependencies` | Stop Postgres and delete its volume, for an empty database |
| `make lint` | Ruff lint and format check |

## Endpoints

| Endpoint | Purpose |
|---|---|
| `GET /health/live` | Liveness |
| `GET /health/ready` | Readiness, checks the database |
| `GET /api/v1/capabilities` | Non-secret deployment manifest; explains, never authorizes |
| `POST /api/v1/auth/code` | Email a six-digit code for `sign_up` or `sign_in`; always 202, so it never reveals whether an account exists |
| `POST /api/v1/auth/verify` | Check the code, set the `tr_session` cookie, return `/me`; sign-up creates the account and its personal party |
| `POST /api/v1/auth/sign-out` | Revoke this session and clear the cookie |
| `GET /api/v1/me`, `PATCH /api/v1/me` | The signed-in account; changes need `expected_version` |
| `POST /api/v1/organizations` | Create an organization; the creator joins with every capability. Needs `Idempotency-Key` |
| `GET /api/v1/organizations/{id}/members` | Members and capabilities, to members only |
| `DELETE /api/v1/organizations/{id}/members/{account_id}` | Remove a member: `acting_party_id`, `expected_version`, `manage_members`; never the last manager |
| `POST`, `GET /api/v1/organizations/{id}/invitations` | Invite an email with capabilities for seven days (`Idempotency-Key`); list invitations |
| `GET /api/v1/invitations/{token}`, `POST .../accept` | What the invitation grants; join. Only the invited email sees it |
| `POST /api/v1/invitations/{id}/revoke` | Revoke a pending invitation |
| `PUT /api/v1/me/context` | Act as the personal party or a joined organization; anything else is `NOT_FOUND` |
| `POST`, `GET /api/v1/inventions` | Start an invention for the acting party (`Idempotency-Key`); list its inventions with drafts and archived ones |
| `GET /api/v1/inventions/{id}` | Owner view: draft, published version, history numbers |
| `PUT /api/v1/inventions/{id}/draft` | Save the whole draft against `expected_version` (`Idempotency-Key`); publication rules do not apply |
| `POST /api/v1/inventions/{id}/publish`, `.../archive` | Publish an immutable version; archive while keeping history. Each needs `Idempotency-Key` |
| `GET /api/v1/inventions/{id}/public` | The published version, nothing private; `NOT_FOUND` when unpublished or archived |
| `POST /api/v1/documents/upload-intents` | Declare title, kind, type and size; unsupported or oversized files are refused before any byte |
| `PUT /api/v1/documents/upload-intents/{id}/content` | Stream the bytes into quarantine; the worker scans, then reads the text |
| `GET /api/v1/documents`, `GET /api/v1/documents/{id}` | The acting party's documents: versions with file, extraction and review states, and grants |
| `POST /api/v1/documents/{id}/grants`, `POST /api/v1/grants/{id}/revoke` | Share one version with one party; revoke and report copies already delivered |
| `GET /api/v1/documents/{id}/versions/{n}/content` | The gateway: re-authorizes every request and range, records grantee downloads, never issues a storage URL |
| `POST /api/v1/support-requests`, `GET /api/v1/support-requests?invention_id=` | Start a draft request for a published invention with an optional budget; list the acting party's requests |
| `GET /api/v1/support-requests/{id}`, `GET /api/v1/support-requests/{id}/versions/{n}` | One request as its owner, and any earlier version as it stood |
| `PUT /api/v1/support-requests/{id}` | Save the content and budget as a new version against `expected_version`; money travels as decimal strings |
| `POST /api/v1/support-requests/{id}/{activate,pause,close}` | Status changes against `expected_version` (`Idempotency-Key`); activation needs an outcome and at least one form of support |
| `POST /api/v1/legal-entities`, `GET /api/v1/legal-entities` | Declare a company (review status `declared`) and list the acting party's |
| `POST /api/v1/funding-requests`, `GET /api/v1/funding-requests`, `GET /api/v1/funding-requests/{id}` | One raise for an existing or proposed company, owning its target and linking published invention versions |
| `PUT /api/v1/funding-requests/{id}`, `GET /api/v1/funding-requests/{id}/versions/{n}` | Save as a new version against `expected_version`; earlier versions stay readable |
| `POST /api/v1/funding-requests/{id}/{activate,pause,close}` | Status changes against `expected_version` (`Idempotency-Key`); activation needs a target and a linked invention |
| `GET /api/v1/partners/{party_id}` | A partner profile as anyone signed in may read it: thesis apart from current availability, labelled by source; `NOT_FOUND` when there is none |
| `PUT /api/v1/partners/{party_id}` | Save one's own profile (`Idempotency-Key`); `expected_version` is null only for the first save |
| `POST /api/v1/partners/{party_id}/handoffs` | Record that the acting party followed an external route (`Idempotency-Key`); never a submitted pitch |
| `POST /api/v1/opportunities`, `GET /api/v1/opportunities?partner_party_id=&limit=` | Start a draft (`Idempotency-Key`); list one's own, or another partner's that are not drafts, each with `target_availability` |
| `GET /api/v1/opportunities/{id}`, `GET /api/v1/opportunities/{id}/versions/{n}` | The current version, or one version as it stood; others never reach a draft or an earlier version |
| `PUT /api/v1/opportunities/{id}` | Save against `expected_version` (`Idempotency-Key`): a draft in place, a live one as the next version, current at once, if it passes the activation check |
| `POST /api/v1/opportunities/{id}/{activate,pause,close}` | Status changes against `expected_version` (`Idempotency-Key`); activation needs a saved profile, the fields a partner must state, and a reason on every mandatory requirement |
| `GET /api/v1/discovery?type=inventions\|funding\|partners&q=&sector=&stage=&support_form=&region=&purpose=&intake=&currency=&basis=&amount_min=&amount_max=&saved=&cursor=&limit=` | Search the public projection in three sections; filters echoed, a deliberate relaxation when nothing matches, never a trend |
| `GET`, `PUT`, `DELETE /api/v1/saved-items[/{subject_type}/{subject_id}]` | The acting party's saved items; saving twice changes nothing |
| `GET`, `PUT`, `DELETE /api/v1/discovery-feedback[/{subject_type}/{subject_id}]` | "Kurang relevan": hides a subject from the acting party's results only |
| `POST /api/v1/matches` | Match an owned support request or raise against every other partner's active opportunity (`Idempotency-Key`); results, then excluded ones |
| `GET /api/v1/match-runs/{id}` | A stored run as it was computed, with engine and policy versions |
| `POST /api/v1/pitches/preflight` | Check an owned source against one opportunity: recipient, pinned versions, rows, shareable files and the template brief, under a 30-minute token; nothing is sent |
| `GET /api/v1/briefs/{id}`, `POST /api/v1/briefs/{id}/summary`, `GET /api/v1/briefs/{id}/export?format=md\|txt` | One's own brief with references; a summary only when traceable; export redacts what depends on a file no longer accessible |
| `POST /api/v1/pitches` | Send on purpose (`Idempotency-Key`) with a fresh preflight token, the edited brief and chosen file versions; `PREFLIGHT_STALE`, `TARGET_CLOSED`, `DUPLICATE_PITCH`, `NOT_READY`, `RATE_LIMITED` |
| `GET /api/v1/pitches?box=outgoing\|incoming`, `GET /api/v1/pitches/{id}` | Sent or received pitches with whose turn it is, and one pitch with its frozen submissions, decisions, rounds and the reader's allowed actions, for its two sides only |
| `POST /api/v1/pitches/{id}/begin-review`, `/decisions`, `/revision-rounds`, `/resubmit`, `/withdraw`, `/close` | Status changes from the PRD section 7 table (`Idempotency-Key`, `expected_version`); `INVALID_TRANSITION`, `STALE_VERSION`, `REQUIRED_ANSWERS_MISSING` |
| `PUT /api/v1/pitches/{id}/revision-items/{item_id}/answer`, `.../review` | Save a draft answer with its version; mark an answered item `ACCEPTED` or `NEEDS_DETAIL` |
| `GET`, `POST /api/v1/pitches/{id}/messages`, `GET`, `POST /api/v1/pitches/{id}/tasks`, `POST /api/v1/tasks/{id}/complete` | The room's messages (poll with `since`) and tasks; sends take `Idempotency-Key` |
| `GET /api/v1/pitches/{id}/next-action`, `GET /api/v1/me/queue` | Whose turn it is on one pitch, and everything waiting for Beranda |
| `GET /api/v1/notifications`, `PUT /api/v1/notifications/{id}/read` | The acting party's in-app notifications (`since`, `unread`) and marking one read |
| `GET /api/v1/pitches/{id}/schedule`, `POST /api/v1/pitches/{id}/schedule-proposals` | Proposals and meetings with expiry evaluated now; propose 2–5 slots of 30 or 60 minutes, or a replacement |
| `POST /api/v1/schedule-proposals/{id}/accept`, `.../cancel`, `POST /api/v1/meetings/{id}/cancel`, `.../outcome`, `GET /api/v1/meetings/{id}/calendar.ics` | Confirm a slot (`BOOKING_CONFLICT`, `PROPOSAL_CLOSED`), cancel, record outcomes, download ICS |
| `POST /api/v1/dev/bookings` | Development only: mark a party busy for browser tests |
| `GET /api/v1/demo/accounts`, `POST /api/v1/demo/sign-in`, `POST /api/v1/demo/reset` | Demo mode only: the labelled accounts, sign-in with no email, and a reset of demo rows with variants `gap`, `scan`, `proposed_entity` |
| `GET /api/v1/dev/mailbox?email=` | Development only: the codes and notes that would have been emailed |
| `GET /api/v1/operations/{id}` | Whether the acting party's operation committed, for a client that lost the response |

### Moderation and privacy

| Endpoints | Purpose |
|---|---|
| `POST /api/v1/reports`, `GET /api/v1/reports[/{report_id}]` | File a private report and read its case receipt |
| `GET /api/v1/operator/reports`, `POST /api/v1/operator/reports/{report_id}/actions` | Scoped queue and versioned, audited case decisions |
| `GET /api/v1/operator/reports/{report_id}/documents/{document_id}/versions/{number}/content` | Protected download after checking the exact live case grant |
| `POST /api/v1/privacy-requests`, `GET /api/v1/privacy-requests[/{request_id}]` | Request an export or deletion and read account-scoped receipts |
| `GET /api/v1/privacy-requests/{request_id}/export` | Download a fresh, authorized JSON export |
| `GET /api/v1/operator/privacy-requests`, `POST /api/v1/operator/privacy-requests/{request_id}/fulfill` | List pending deletions and start versioned fulfilment |

Use `python -m app.moderation --help` from the service for local grant administration. Operator actions require an explicit account grant. A case-file grant names one report, operator, document version, purpose and expiry. Run the worker to finish deletion requests. The development mailbox provides outcome delivery during development. Production delivery depends on spec 042.

## Staging and production runtime

Use the [deployment runbook](../../../../../deployment/temuriset/RUNBOOK.md) for the pinned Compose topology and secret-store setup. Configure `STORAGE_ADAPTER=s3` with the private origin, bucket, region and scoped access keys in `.env.example`. Configure `FILE_SCANNER=clamav` and `MAILBOX_ADAPTER=disabled` outside development. The public capability manifest reports storage and scanner implementations and email readiness. Download and range authorization remain in the API, and storage errors omit provider details.


### Local email relay

Use synthetic accounts with a local relay double. Set `ENVIRONMENT=development` and
`MAILBOX_ADAPTER=loopback-relay` for both the API and worker, supply the relay URL and a synthetic
sender such as `relay@example.test`, and generate a distinct local key:

```bash
export EMAIL_ENVELOPE_KEY="$(uv run python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')"
```

Supply the same key to the API and worker through their local secret environment. Start
the API and worker after migrating the database. The manifest reports the `email` adapter as
`available` with implementation `loopback-relay` in this profile, and S18 offers optional email.

The worker posts JSON with `from`, `to`, `subject` and `body` as plain text strings and a stable
`Idempotency-Key` header. The relay must return 2xx for first acceptance and for subsequent requests
under the same accepted key. It must retain acceptance keys for at least one hour. An attempt is
bounded by five seconds and the JSON request by 8 KiB. The worker does not follow redirects or
consume response bodies. Connection failures, timeouts, 429 and 5xx retry with bounded backoff and
the same key.

Code and invitation material is encrypted in the job and cleared on a terminal attempt or expiry.
It is usable for at most ten minutes and is rechecked against the current challenge or invitation
before sending. Unknown-address sign-in requests keep the same public acknowledgement and do not
queue mail in relay mode. Optional notification delivery is independent of in-app notices, with a
15-minute attempt window and live opt-in, account eligibility and party access checks on each
attempt. The notice links to the authenticated home page without including pitch details.

Release deployments keep `MAILBOX_ADAPTER=disabled`. External email needs approved processing terms,
a sender domain verified for SPF, DKIM and DMARC, and sandbox evidence of delivery and deduplication.
Erasure outcomes use the independent development or disabled path. A production erasure receipt
requires its own approved delivery policy.

The same non-root image accepts the `api`, `worker` and `migrate` commands. The deployment runs `migrate` before API or worker startup. Running the image without a command retains the existing development startup behavior. With disabled mail, sign-in code requests and invitations return `MAIL_UNAVAILABLE`. A deletion outcome can be ready even when its email could not be sent.

## Workspace portability

`POST /api/v1/imports/validate` accepts a raw UTF-8 JSON file with media type `application/json`.
Send `acting_party_id` as a query parameter and an `Idempotency-Key` header.
The upload supports schema version 1, up to 20 MiB and 2,000 records. The file and each row state source
provenance. Each row supplies an external ID, scoped by the acting party and the file's external system.

```json
{
  "schema_version": 1,
  "external_system": "research-registry",
  "provenance": {"source": "Registry"},
  "inventions": [
    {
      "external_id": "experiment-01",
      "provenance": {"source": "Registry"},
      "fields": {"title": "Saringan air", "stage": "PROTOTYPE"}
    }
  ]
}
```

See [the v1 JSON schema](app/portability/service/schema_v1.json) for fields and bounds. The default mapping
covers the title, summary, problem, solution, intended users, sector, stage, keywords and source-reported
facts. Facts preserve reviewed values and links to private evidence. To map `private_notes`, an authorized
portfolio editor sends `map_private_notes=true` when uploading. Omitted fields retain their existing values.
The optional `partner_profile` describes the current acting party. An organization name stays source text.
Rights and relationship assertions remain on the source reference with their provenance.

`GET /api/v1/imports/{run_id}` shows validation, preview and apply independently, with progress and a
page of up to 100 preview rows. Inspect the preview before posting to `/imports/{run_id}/apply` with the
displayed run version. `/imports/{run_id}/cancel` stops the next checkpoint and reports the records
already committed. Resolve a conflict in the owned invention or profile, then upload again and review
the new preview. Each apply checkpoint covers up to 50 records, and changes save as drafts.

`POST /api/v1/exports` accepts explicit invention and document selections, up to 100 per job and 20 MiB
per JSON result. It checks the exact version and any applicable document grant. Check job status at
`GET /api/v1/exports/{export_id}` and fetch the authorized attachment at
`GET /api/v1/exports/{export_id}/download`. A grant or membership change can expire access permanently.
Exports and import staging expire after 24 hours. Exported document attachments are encoded as Base64
and are skipped on import. This workspace export is separate from requests to export account data.
