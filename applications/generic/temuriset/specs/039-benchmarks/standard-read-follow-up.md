# Follow-up spec for standard-read performance

**Status** Planned

The initial local 039 benchmark measured warmed p95
of 651.002 ms for account, 1,887.819 ms for invention list and 541.428 ms for
owned detail against a 500 ms target at 20 concurrent users. The first-pass list
also exceeded 500 ms. A synchronized rerun on a dedicated PostgreSQL instance
met all first-pass and warmed targets. Keep both runs as starting evidence and
use paired repetitions to assess consistency. [Benchmark report](../../docs/roadmap/benchmarks.md)

## Scope

Repeat the same seeded 1,000/100/20 workload on a reserved host and then on an
approved synthetic staging deployment. In a separate diagnostic run, record
route-level query counts and database wait, pool wait and response serialization
time. Check whether loading portfolio versions item by item increases the list
cost with portfolio size, and whether contention in the mixed workload accounts
for the account and detail misses. Use the diagnostic results to identify the
smallest changes to the existing read paths.

## Acceptance

- Preserve account and acting-party authorization, response contracts, ordering
  and portfolio version semantics. Verify cross-party isolation with two actors.
- On recorded hardware using the same dataset and request mix, obtain at least
  three paired first-pass and warmed runs. Each warmed p95 and first-pass list
  p95 must be at most 500 ms with zero request errors.
- Rerun discovery and matching under the same benchmark conditions and retain
  the 2,000 ms budgets. Report separate local and staging results, including any
  remaining misses.
