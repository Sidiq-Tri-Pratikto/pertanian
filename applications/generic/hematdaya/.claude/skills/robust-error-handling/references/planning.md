# Remediation planning

Turn verified findings into subtasks a team can deliver one PR at a time. The plan is the main deliverable for the project owner: each subtask is small enough to review in one sitting, safe to merge on its own, and proves itself with its own tests.

## Sizing

- **One subtask = one PR = one concern.** "Add the sanitizer" and "migrate the payments routes" are two subtasks.
- **Size limit:** about 400 changed production lines or about 10 production files, tests excluded. Size `S` is up to about 150 lines; `M` is up to about 400. Anything estimated larger is split, by module, integration, route group, or package, before it goes in the plan. There is no `L`.
- **Tests travel with the change.** Each subtask lists the failure-path tests that prove it, and they ship in the same PR. Do not create "add tests later" subtasks. The only test-only subtasks are full-chain and gate work in phase 3 that has no production change of its own.
- **Independently mergeable.** After each subtask merges, the system still builds, tests pass, and the public contract is not broken. When a public envelope, code, or status must change, the subtask adds the new behavior alongside the old one (versioned route, header, or flag) and records a deprecation; removing the old shape is a later subtask.
- **Reuse the baseline.** Build on the project's existing base error, registry, envelope, logger, and tracker. Never plan a second base class, envelope, or code style.
- **Consumer first across services (X-07).** When the audited API is called by another internal service, or the audited code calls one, plan the consumer subtask (parse both the old and new envelope, stop copying upstream bodies, send `X-Request-ID`, keep `upstream_request_id`) before the producer subtask that changes the envelope, status, or codes. When the consumer lives in another app or repo, list it as a dependency with its path and audit file.

## Phases and order

Work in this order. Inside a phase, order by dependency, then by priority.

| Phase | Purpose | Typical subtasks |
| --- | --- | --- |
| 0. Containment | Stop active harm now, with the smallest change, even if it is not the final design. Only for P0 findings. | Replace `detail=str(e)` with a fixed safe message; drop a secret-bearing field from logs; stop retrying a non-idempotent write. |
| 1. Foundation | Build the shared pieces the migration needs, in this order. | (a) code registry, base error with registered fallback code and safe default; (b) `debug_info` schema and one sanitizer; (c) `reference_id` on construction, the single boundary recorder to centralized logging/tracker, and the emergency path; (d) public-code map, envelope, `recovery` and `Retry-After`. |
| 2. Migration | Move each surface onto the foundation, one module or integration per subtask. | Resolver for provider X; migrate `orders` routes to typed errors; keep SDK code/`debug_info`/`reference_id` when wrapping in the app; frontend renders `error.message` + `request_id` and branches on `error.code`; worker terminal failures and dead-letter handling. |
| 3. Gates | Prove and protect the behavior. | Full-chain test with fake secrets for each critical surface; handler-failure and sink-outage tests; lint rules (T3); PR checklist lines; AI PR-review instructions; required CI check. |
| 4. Polish | Remaining P2 work. | Message wording, error catalog page, runbooks, retiring deprecated shapes. |

A phase 1 piece the project already has is skipped, not rebuilt. If the project has no client API, skip 1(d) and the envelope work.

## Priority of a subtask

- A subtask's priority is the highest priority among the findings it closes **or unblocks**. A foundation subtask that unblocks a P1 migration is P1.
- Phase order beats priority only through dependencies: a P2 polish subtask never goes before a P1 migration, but a P1 migration waits for the foundation it needs.
- P0 containment subtasks go first and carry no foundation dependency.
- On the first audit of a service, add subtask `EH-T00` (`docs(errors): record legacy baseline exception`): the accountable manager records one approved X-02 covering the open P1/P2 findings, with an expiry date. It never covers a P0. Re-audits update the burn-down instead of adding a new exception.

## Subtask record

Each subtask block in the report has:

- **ID** `EH-Tnn`, stable across re-audits. New subtasks take the next free number; closed ones stay listed as `done`.
- **PR title** in Conventional Commits form, e.g. `feat(errors): add reference_id and boundary recorder`.
- **Priority** (P0/P1/P2), **phase**, **size** (S/M), **depends on** (IDs or none).
- **Closes** (finding IDs) and **rules** (EH and check IDs).
- **Goal**: one sentence, the observable outcome.
- **Scope**: the files or directories it touches. **Out of scope**: what it deliberately leaves for another subtask.
- **Changes**: 3 to 7 bullets.
- **Acceptance tests**: the named failure-path tests and their assertions (message, code, response, `request_id`, record, recovery, fake-secret absence as applicable).
- **Compatibility and rollback**: public contract impact, deprecation notes, how to revert safely.
- **Owner**: engineer and accountable manager, or `UNASSIGNED`.
- **Status**: `todo`, `in-progress`, `done` (needs a `Verified by:` line with test names and command output), or `deferred` (needs a link to the approved PR exception).
- **PR checklist**: the four error-handling lines from EH-13.

## Coverage checks before writing

- Every finding is closed by at least one subtask, and every subtask closes or unblocks at least one finding.
- The dependency graph has no cycles, and every dependency has a lower phase or appears earlier in the same phase.
- No subtask exceeds the size limit.
- The first three subtasks a team can start in parallel are named in the summary.
