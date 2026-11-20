# TemuRiset demo on Vercel only

A free demo setup: two Vercel projects plus Neon. Not for production (see `../RUNBOOK.md`).

| Part | Where | Notes |
|---|---|---|
| Web (Next.js) | Vercel project, root `applications/generic/temuriset/applications/temuriset-web` | Node 24.x. `API_URL` = the API project's URL, read at build time. |
| API (FastAPI) | Vercel project, root `applications/generic/temuriset/applications/temuriset-api` | Framework preset "Other". Entry `api/index.py`, routing in `vercel.json`. |
| Database | Neon Postgres | Direct (non-pooler) URL, asyncpg form. |
| Files | Neon object storage (S3-compatible) | Bucket `temuriset-documents`. |

## Worker

Vercel has no long-running process. `api/index.py` runs worker passes after every write request, before the
response finishes, so search projections, notifications and document jobs still happen. Time-based jobs (expiries,
the weekly digest) run only when such a pass happens. Database connections are not pooled.

## Migrations

The function does not migrate. Generate the SQL offline and run it in the Neon SQL Editor:

```sh
cd applications/generic/temuriset/applications/temuriset-api
DATABASE_URL=postgresql+asyncpg://x:x@localhost/x uv run alembic upgrade head --sql > migrate.sql
```

For later migrations, use `alembic upgrade <current>:head --sql` so only the new revisions are emitted.

## API environment variables

Fixed: `ENVIRONMENT=staging`, `COMPOSITION=generic-base`, `DEMO_MODE=true`, `DEMO_DEPLOYMENT=true`,
`MAILBOX_ADAPTER=disabled`, `FILE_SCANNER=clamav`, `CLAMAV_PORT=3310`, `STORAGE_ADAPTER=s3`,
`S3_BUCKET=temuriset-documents`, `S3_REGION=ap-southeast-1`, `S3_ENDPOINT_URL=<Neon storage origin>`,
`WEB_ORIGIN=<web project URL, no trailing slash>`.

Secrets: `DATABASE_URL` (`postgresql+asyncpg://USER:PASSWORD@ep-...aws.neon.tech/neondb?ssl=require`),
`S3_ACCESS_KEY`, `S3_SECRET_KEY`.

There is no ClamAV, so uploads stay in quarantine; everything else works.
