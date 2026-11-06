# Performance benchmarks

## Local synthetic baseline

Measured 2026-11-06 at 02:22 UTC for [spec 039](../../specs/039-benchmarks/spec.md). The API and worker ran the integrated M7/M10/M11 source at `485028dbf28d9d755c2cf1462e9afb2778ea68bd` with the benchmark harness in the worktree. Alembic head was `0014`, capability manifest schema 1, source release `0.1.0` and composition `generic-base` v1.

| Condition | Local measurement |
|---|---|
| Hardware and OS | Apple M3, 8 physical CPU cores, 16 GiB RAM, macOS 27.2 (26B123), arm64 |
| Runtime | CPython 3.13.16, Uvicorn 0.54.0, FastAPI 0.162.0, HTTPX 0.28.1, asyncpg 0.32.0, SQLAlchemy 2.1.6, PostgreSQL 16.11 (Homebrew) |
| Topology | One native Uvicorn process, one native outbox worker and PostgreSQL in a separate process on the same host. Dedicated synthetic database in a shared PostgreSQL instance. HTTP and PostgreSQL over loopback, with no TLS or edge proxy. Other project validation ran on the same host. |
| Adapters | Local storage, development-accept scanner and disabled mail. Workload reads do not exercise object storage, scanning, mail or the web UI. |
| Verified dataset | 1,000 published inventions (50 per account), 100 active opportunities held by 10 partner parties, 1,000 invention projections and 10 partner projections containing the 100 opportunities. 20 distinct, authenticated synthetic sessions. |
| Workload | 20 closed-loop users with one in-flight request each, in separate standard-read and discovery phases. Standard users cycle through account, portfolio list and owned detail. The discovery page shows up to 20 of the 950 inventions visible to that actor. |
| Cache and timing | The worker drained the seed outbox, projection readiness read PostgreSQL, and session verification touched identity before timing. First pass means one measured cycle per user. Each warmed phase followed a two-second warmup. No application, OS or database cache flush. Discovery has no application response cache. Connections were reused. |

Endpoint latencies are nearest-rank p95 in milliseconds, with the number of
successful samples in parentheses. The first pass sampled each endpoint once
per user. Warmup is shown for context. Each warmed measurement used a ten-second
request window and finished requests already in flight. Across all 3,088 read
attempts there were zero HTTP failures, timeouts, other transport failures or
invalid payloads.

| Endpoint | First pass | Warmup | Warmed | Target | Outcome |
|---|---:|---:|---:|---:|---:|
| `GET /api/v1/me` | 152.832 (20) | 302.695 (50) | 651.002 (151) | 500 | Warmed miss |
| `GET /api/v1/inventions` | 721.924 (20) | 1,011.365 (49) | 1,887.819 (147) | 500 | First-pass and warmed miss |
| `GET /api/v1/inventions/{id}` | 144.324 (20) | 468.692 (34) | 541.428 (134) | 500 | Warmed miss |
| `GET /api/v1/discovery?type=inventions&limit=20` | 275.750 (20) | 205.262 (385) | 168.318 (2,058) | 2,000 | Met |

Standard phases took 0.895, 2.351 and 10.314 seconds of wall time. Discovery
phases took 0.281, 2.083 and 10.034 seconds.

One fresh `POST /api/v1/matches` returned 25 ranked and 75 excluded results
covering all 100 distinct opportunities. End-to-end latency through response
body receipt was **76.833 ms**, within the **2,000 ms** request budget. The job
fallback condition was not triggered.

The separate visibility control received HTTP 401 anonymously. A second party
saw the synthetic invention before the owner archived it. After 1.011 seconds
from the archive request, the second party's search no longer returned it
following the normal outbox worker refresh.

The standard-read misses are tracked in the
[standard-read performance follow-up](../../specs/039-benchmarks/standard-read-follow-up.md).
The shared-host conditions and short windows limit how broadly these numbers can
be applied.

## Synthetic staging baseline

| Workload | Status | Required evidence |
|---|---|---|
| Standard API reads | BLOCKED | Approved isolated HTTPS endpoint and disposable database, authorized synthetic session provisioning and hardware inventory |
| Authorized discovery | BLOCKED | Same staging target and proof that its projection worker is ready |
| Matching and visibility | BLOCKED | Same target with 100 active synthetic opportunities and authorization for the archive control |

Use the release commit, OCI digests, live schema, manifest, topology and hardware
from the staging deployment for these rows.

## Verification

The [runbook](../../applications/temuriset-api/benchmarks/README.md) reproduces
both runs. A 12-invention, 4-opportunity, 4-user smoke run passed with one-second
warmup and measurement windows. It found four candidates (one ranked and three
excluded) in 273.791 ms, received HTTP 401 without a session, and confirmed
projection withdrawal. The full runner returned status 1 for the recorded
standard-read latency misses and emitted the result before exiting.
`make lint` passed. `uv run pytest tests/unit/test_benchmarks.py -q` passed all
five checks for target rejection, missing sessions, incomplete seed, empty
successful samples and a duplicated matching candidate.
