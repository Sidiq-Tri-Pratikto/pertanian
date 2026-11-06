# TemuRiset synthetic benchmark

Spec 039 covers standard API reads, discovery and matching. The M7 baseline had
demo fixtures, but no isolated 1,000/100/20 workload or comparable latency
record. The benchmark report records the synchronized M11 source alongside the
initial local baseline. Deployment contracts are in
[037](../../../specs/037-deploy-release/spec.md). See the
[deployment runbook](../../../../../../deployment/temuriset/RUNBOOK.md) for the
supported Linux Compose topology.

## Target and credentials

Use an explicitly approved disposable deployment and a fresh, migrated database
named `temuriset_benchmark` or `temuriset_benchmark_<suffix>`. Select the same
`BENCHMARK_ORIGIN` and `--origin` in both commands. Bind the API and worker
to the benchmark database. Set `WEB_ORIGIN` to the selected origin. Local mode
requires HTTP on an explicit loopback port and a loopback PostgreSQL host.
Staging requires HTTPS with normal certificate validation. HTTPX disables
environment proxies and redirects. The generator refuses a database with any
accounts, inventions, opportunities or search documents. Each cookie belongs to
a visibly labelled synthetic demo account using a reserved `.invalid` address.
The generator calls the internal demo identity service to issue a normal session
and leaves the HTTP demo account allowlist alone.

Use an owner-only directory outside the source tree for the handoff. The generator
creates the file exclusively with mode 0600. The runner verifies its origin,
account set, cookie format and per-session API identity. The CLI reports HTTP
failures without request credentials. Keep the handoff out of commits and uploads.
Destroy it and the disposable database after the run. Each complete run archives
one fixture after timing, so start each repetition on a fresh database.

## Run locally

From the API directory with its locked development dependencies installed,
create a fresh disposable PostgreSQL instance and database, then run the
following in an exported environment inherited by the API, worker and benchmark
processes. Use a separate database, port and private directory for each run.

```sh
export DATABASE_URL=postgresql+asyncpg://postgres@127.0.0.1:55419/temuriset_benchmark
export BENCHMARK_ORIGIN=http://127.0.0.1:8040
export WEB_ORIGIN="$BENCHMARK_ORIGIN"
export ENVIRONMENT=development LOG_LEVEL=WARNING
export COMPOSITION=generic-base STORAGE_ADAPTER=local FILE_SCANNER=development-accept
export MAILBOX_ADAPTER=disabled DEMO_MODE=false
private_dir=$(mktemp -d)
export STORAGE_PATH="$private_dir/storage"
uv run alembic upgrade head

# Separate processes with the same environment.
uv run uvicorn app.main:app --host 127.0.0.1 --port 8040 --workers 1 --no-access-log
uv run python -m app.worker

# From a third terminal with the same environment.
uv run python -m benchmarks.generate --origin "$BENCHMARK_ORIGIN" --handoff "$private_dir/sessions.json"
uv run python -m benchmarks.run --origin "$BENCHMARK_ORIGIN" --handoff "$private_dir/sessions.json" \
  > "$private_dir/result.json"
```

For a smoke run, add `--inventions 12 --opportunities 4 --users 4` to the
generator and `--seconds 1 --warmup-seconds 1` to the runner, using fresh
infrastructure as described above. The runner checks dataset sizes against the
handoff, including the exact set of published IDs, active opportunities,
projection IDs and live sessions. The worker must drain the seed outbox first. Each user owns at least one invention, and the
fixture holds both ranked and excluded matching candidates at the full scale.

## Measurement

Each virtual user sends one request at a time. Standard reads cycle through
`GET /api/v1/me`, the authorized invention list, and an owned invention detail.
Discovery uses a separate workload with `type=inventions&limit=20`. A first-pass
sample uses one cycle per user for standard reads and one request per user for
discovery. Warmed phases each have a two-second diagnostic warmup and a ten-second
measurement window by default. Workers finish requests already in flight when the
window closes. Session readiness requests already touched the identity and DB
paths. No app or OS/DB caches are flushed. This discovery baseline has no
application response cache. Discovery omits the active party’s own listings. The run reuses HTTP connections where possible.

The runner reports actual phase wall time, per-endpoint attempted and successful
counts, timeouts, other transport failures, HTTP status counts, invalid payloads
and nearest-rank p95 in milliseconds among successful requests (rank
`ceil(0.95 × n)`). First-pass and warmed phases need a successful sample at each
requested endpoint and compare p95 against 500 ms for standard reads and 2,000 ms
for discovery. Warmup reports p95 when successful samples are available, and only
request and payload failures affect its pass status. Those failures also count in
the measured phases.

A fresh idempotent match request from an inventor evaluates opportunities owned
by other parties. The elapsed time covers the HTTP request through response body
receipt. The returned ranked and excluded IDs must cover the catalog exactly once.
The request budget is 2,000 ms. A miss needs a separately validated job path or a
bounded follow-up. Visibility control runs after timing. Anonymous discovery
must be denied, and an authenticated other party must see a synthetic invention
before archiving and stop seeing it after the normal worker refresh.

The result JSON includes UTC time, dataset, phases, matching, visibility and the
runtime capability manifest. Record release commit, Alembic head, hardware, OS,
runtime versions, network topology and cache conditions alongside the result.
Keep the local and staging results in separate rows in
[the benchmark report](../../../docs/roadmap/benchmarks.md).

## Frozen hybrid retrieval comparison

Spec 045's offline command compares the shipped `lexical-rules@1` keyword-overlap
path with dense, BM25/dense hybrid, and hybrid plus reranking. Every mode uses the
same curated source and catalog versions for each query and the same authoritative
rule engine. The fixture carries author-assigned synthetic topical grades,
expected rule outcomes and source grounding, explicit relationship links, and
new or established manager cohorts. Development and held-out pools are disjoint.
The command applies the versioned admission policy and fits no thresholds.

From the API directory, run the synthetic model double in one terminal.

```sh
uv run python -m benchmarks.retrieval serve-double --port 58045
```

Produce and evaluate the artifact from another terminal. The relay receives the
committed fixture's text with model pins. The producer then sends each query's
bounded fused rerank head. The double uses a fixed topic vocabulary over those
texts for vectors and rerank scores. It has no database access and refuses
unrecognized text and model pins.

```sh
scratch=$(mktemp -d)
uv run python -m benchmarks.retrieval produce \
  --endpoint http://127.0.0.1:58045/retrieval --artifact "$scratch/retrieval.json"
uv run python -m benchmarks.retrieval evaluate --artifact "$scratch/retrieval.json" \
  > "$scratch/retrieval-report.json"
```

The producer atomically writes a private artifact tied to the exact fixture digest
and model pins. Keep it outside the repository. Stop the double and remove the
scratch directory after the run.

The report gives each metric's numerator, denominator, and count of queries where
it was undefined. Grades range from 0 for irrelevant to 3 for strongly useful.
Grades 2 and 3 count toward binary relevance. Candidate recall uses the list
before rule exclusion. Returned precision divides by actual results, and
precision@5 divides by five per judged query, including empty displays.
nDCG@5 uses gains of 2 to the power of the grade minus 1, the full judged
catalog's ideal, and the mean over queries with nonzero ideal gain. Topical
judgments are separate from mandatory rule eligibility.

Safety tracks mandatory failures in returned lists, all judged rule outcomes,
provisional UNKNOWN status and reasons, and source support for the factual
reasons on returned results. The command exits with a failure if a safety check
fails. Coverage and abstention measure the share of queries with and without a
returned result. Result counts distinguish shown, excluded, and other
undisplayed catalog entries. Exposure counts actual returned positions and
distinct managers by cohort. Per-query elapsed time covers local in-process
retrieval, rule evaluation and ranking. Real provider cost is unmeasured.

The small synthetic pools demonstrate behavior and reporting. Production
quality, subgroup exposure, latency and cost require the permissioned,
independently reviewed study in [the benchmark report](../../../docs/roadmap/benchmarks.md).
