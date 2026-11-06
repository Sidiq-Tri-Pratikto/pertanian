# TemuRiset release and operations

## Ownership and change window

The release manager reviews checks, protects `temuriset-v*` tags and holds the exclusive workflow package-write grant. The host operator owns the Linux host, DNS, firewall, TLS, environment secret store and Compose project. The data steward approves backups, restoration targets and access. QA owns the approved synthetic staging accounts, fixture reset and browser results. Assign named operators and agree on a maintenance window, decision deadline and recovery owner in the change record before touching a shared environment.

## Prepare the environment

- Use an approved Linux host with Docker Compose v2 and private volumes. Reserve a distinct Compose project name per environment. Allow client access only to the HTTPS listener. Configure `EDGE_BIND_ADDRESS` for the intended interface and restrict it with the host firewall. Allow only the scanner update egress needed by ClamAV. PostgreSQL, S3, API and ClamAV have no published host ports.
- Point DNS at the approved address. Provision the certificate chain and key from the secret store as private files outside the checkout, then set `TLS_CERT_FILE` and `TLS_KEY_FILE` to their absolute paths. `WEB_ORIGIN` is the browser's exact HTTPS origin, including a nonstandard port when used. Confirm expiry, trust and hostname from the clients before the change.
- Copy [`.env.example`](.env.example) to a private file outside the checkout. Set `TEMURISET_API_IMAGE` and `TEMURISET_WEB_IMAGE` to the manifest's digest references. Set `RELEASE_SHA` and `COMPOSITION` from the approved manifest and environment inventory. Keep `API_URL=http://api:8000` for these images. A different internal address requires its own web build and evidence because Next.js compiles the same-origin rewrites at build time.
- Inject `DATABASE_URL`, `POSTGRES_PASSWORD`, `S3_ACCESS_KEY` and `S3_SECRET_KEY` through the environment secret store. Compose initializes database and role `temuriset`. The database URL must use the matching password and the internal `postgres:5432` address. Percent-encode reserved password characters in the URL. The mounted SeaweedFS identity file at `S3_CONFIG_FILE` uses the shape below with the same S3 credentials and bucket. The store initializes the named bucket. `bucket-ready` verifies scoped access. The pinned SeaweedFS image drops privileges to UID/GID 1000. Give the container's mapped group read access and restrict all other readers. For a Linux host without user namespace remapping, use ownership `root:1000` and mode `0440` inside a root-only secret directory, and check container readability without printing the file. With user namespace remapping, use the corresponding host GID. Restrict Docker and host administrative access. Avoid commands that print the resolved Compose environment.

```json
{"identities":[{"name":"temuriset-runtime","credentials":[{"accessKey":"<secret-store-value>","secretKey":"<secret-store-value>"}],"actions":["Read:temuriset-documents","Write:temuriset-documents","List:temuriset-documents"]}]}
```

Use `ENVIRONMENT=staging` and `MAILBOX_ADAPTER=disabled` for staging and `ENVIRONMENT=production` with disabled mail for production. Sign-in code requests and invitations report `MAIL_UNAVAILABLE` before creating records. A completed deletion keeps its audit and records when the outcome email is unavailable. The approved staging session workflow depends on real authentication from 042 and registered J04 and J05 tests. QA supplies the operator-approved HTTPS origin and a private fixture file with real authorized sessions for synthetic accounts. Run `npx playwright test` from the web application with `E2E_STAGING_URL` and `E2E_STAGING_FIXTURES_FILE` set. The runner requires the named journeys and full baseline suite. The synthetic local smoke uses development mail only inside a disposable loopback project.

## Release and roll out

1. The release manager verifies the trusted commit is on `main` and uses a protected `temuriset-v<major>.<minor>.<patch>` tag. CI runs the application and composition checks, builds both images, and blocks release on HIGH or CRITICAL Trivy findings. Publishing consumes checksummed tested archives. It serializes publication per source SHA and only accepts an absent SHA reference for each package. If a prior attempt left a tag in either package, stop and investigate. An existing SHA tag is never overwritten by the workflow. Registry permissions must exclude other writers. Deploy using the verified immutable digests, and store the manifest in the approved release inventory.
2. The host operator and data steward record current and candidate digests, source commit, composition, capability and adapter inventory, previous trusted release reference and live Alembic head. Take an approved coordinated backup and run the compatibility gate against the exact prior supported release. Follow the [backup and restore instructions](backup/README.md) and [recovery drill](backup/drill.md). Keep the old application compatible during expansion. Retire all old API and worker processes and verify the cutoff before a contract migration changes fields or behavior they depend on. For a newly introduced job kind, drain and stop the old workers before enabling any producer of that kind, including with an additive schema. Across 0014 the old worker can claim erasure jobs it cannot process. Follow the [recovery decision](backup/drill.md#recovery-and-migration-decisions) for any stranded job.
3. Review the release window and quiesce traffic and jobs when the data change requires it. Use the private environment file and selected project. Pull the pinned digests before changing services. Compose starts PostgreSQL, SeaweedFS and ClamAV, runs the dedicated migration once and verifies bucket access before starting API and worker. Confirm both one-shot jobs exited zero, the worker is running and the edge responds on the approved origin.

```bash
docker compose --env-file "$TR_ENV_FILE" -p "$TR_PROJECT" -f deployment/temuriset/compose.staging.yml pull
docker compose --env-file "$TR_ENV_FILE" -p "$TR_PROJECT" -f deployment/temuriset/compose.staging.yml up -d --wait
docker compose --env-file "$TR_ENV_FILE" -p "$TR_PROJECT" -f deployment/temuriset/compose.staging.yml ps -a
curl --fail --silent --show-error "$TR_WEB_ORIGIN/health/ready"
```

4. Record what is actually serving for this composition. Confirm deployed image digests, web origin, `GET /api/v1/capabilities`, live schema and scanner readiness. QA runs the 003 suite and J01–J05 against the approved HTTPS staging URL using independently provisioned and reset synthetic accounts. Keep the browser run, fixture provenance and scope, incident notes and release inventory in approved operator storage. A published manifest starts with no rollout records. Record staging and production rollouts separately by environment, composition, digests, owner, time and result.
5. Before production, validate the operator-approved staging record against the published manifest. The record supplies `environment` (`staging`), `url`, `composition`, `commit`, the exact `images` mapping, and `checks` with `003`, `J01`–`J05`, `restore` and `compat` all passed. The operator verifies provenance and signs off on this evidence before invoking the checker. Restore evidence must describe the rehearsal and compatibility evidence must use the trusted prior release. A local no-op schema check cannot replace that release's evidence.

```bash
uv run --no-project --with jsonschema==4.26.0 python deployment/temuriset/release_manifest.py verify-promotion \
  --manifest "$TR_RELEASE_MANIFEST" --evidence "$TR_APPROVED_STAGING_EVIDENCE" --composition "$TR_COMPOSITION"
```

## Recover from a failed change

Pause traffic and stop affected workers while preserving logs, metadata and volumes. Identify the live Alembic head and last compatible published image set. If the schema is still compatible and the compatibility gate passed, keep the live schema and restart the previous digest-pinned web, API and worker without running their migration role. Otherwise keep the service quiesced and choose a forward repair or coordinated recovery with the data steward. Do not assume an Alembic downgrade can recover data. The [restore instructions](backup/README.md) require an isolated target and verification of both rows and object checksums before switching traffic. Record the decision, actual digests, resulting schema and observed recovery time.
