---
name: robust-error-handling
description: >-
  Audits a whole project or a named slice (paths, modules, a diff) in Python
  against the project error-handling constitution (EH-01 to EH-13): typed
  error families, a central resolver for third-party failures, two-clause user
  messages, stable codes, sanitized debug_info, recovery and retry guidance, a
  public API envelope, centralized records reached by reference ID, ownership,
  and failure-path tests. Writes one Markdown file in the audited project with
  P0/P1/P2 findings and a dependency-ordered remediation plan where each
  subtask is one PR. Read-only: it never changes application code; executing
  a subtask is the implement-error-handling skill's job. Use when the user
  asks for an error-handling audit, review, scan, gap analysis, or
  remediation plan, or mentions the error-handling convention or mandate.
---

# Robust Error Handling Audit and Plan

The policy is [references/error-handling-constitution.md](references/error-handling-constitution.md) (rules EH-01 to EH-13, appendix safeguards X-01 to X-07). Read it fully before auditing. The check catalog and P0/P1/P2 rubric are in [references/rules.md](references/rules.md). The target shapes are in [references/contract.md](references/contract.md). Planning rules are in [references/planning.md](references/planning.md). The output format is [references/report-template.md](references/report-template.md).

`references/error-handling-constitution.md` is a symlink to `.specify/memory/error-handling.md`; edit only that file.

Every failure a person, an agent, or an external client can hit keeps three things apart. This is the **separation test**:

1. **Human clause**: the message a person reads: what happened, then what to do next.
2. **Agent field**: the structured values an agent or log pipeline parses: internal `code`, `debug_info` (`error_type`, `original_message`, optional `traceback`), and `recovery` (`retryable`, `retry_after_seconds`, `max_attempts`, internal `escalate_when`).
3. **Producer**: the typed raise, or the single resolver branch, that chose that error.

They are never folded into one string. A class name inside the message, a traceback inside `__str__` / `getMessage()`, or `debug_info` on the wire fails the test.

**Outcomes are mandatory; patterns are recommended.** A shared base class, a typed taxonomy, and a central resolver are the recommended way to meet the outcomes. Another architecture passes when the report records the deviation, its reason, and the evidence that the outcome still holds. Do not label a raw throw a violation until you have traced it to the boundary that exposes it.

Wrong-vs-right examples, load only the languages in scope: [Python](references/python.md).

Report only findings you verified by reading the code; a scanner hit is a lead, not a finding.

## Usage

```
/robust-error-handling [path ...] [--diff <base>] [--out <file>] [--run-tests]
```

- No path: the whole repository, including monorepo packages. Paths or `--diff <base>` narrow the scope.
- Default mode is **audit-only**: write the report and plan, change no application code, run no test suite. The verification level is `source only`.
- `--run-tests`: also run the scope's existing test suite once (step 5).
- `--out` default: `docs/error-handling/audit-<YYYY-MM-DD>.md` in the audited application root (`applications/<app>/` in a monorepo; create the directory). This file is meant to be committed so the project owner can track the plan.
- Checkpoints for large audits: `.tmp/error-handling-audit/` (inspected-path ledger, candidate list). Do not commit them.
- To execute a subtask from the plan, use the `implement-error-handling` skill with the `EH-Tnn` ID. This skill never edits application code.

## Process

```
- [ ] 1. Pin the scope
- [ ] 2. Map the error surfaces and the baseline
- [ ] 3. Collect candidates
- [ ] 4. Verify, classify, and prioritize
- [ ] 5. Audit failure-path tests, CI, and release evidence
- [ ] 6. Evaluate the rules and the completeness test
- [ ] 7. Plan the remediation subtasks
- [ ] 8. Write the report
```

### 1. Pin the scope

Read `AGENTS.md`, `CLAUDE.md`, project constitution files, `docs/error-handling/deviation.md`, error catalogs, API schemas, runbooks, PR templates, and CI config. Apply documented project deviations when they have evidence; report conflicts with the constitution, never waive a mandatory outcome silently.

Where to look in this kind of repo:

- **CI**: GitHub Actions under `.github/workflows/`, and each app's `Makefile` and `Dockerfile`. A CI step that runs tests is evidence for G3.
- **AI PR review**: a required review check with error-handling instructions. None means G2 is a gap.
- **Ownership**: prefill the accountable team from `CODEOWNERS`. Name a person only if a file names one; otherwise keep `UNASSIGNED` with the team noted.
- **Internal consumers (X-07)**: in a monorepo, find every sibling service that calls the audited API (search for its base URL, client class, and route paths) and every upstream service the audited code calls. Record them as surfaces.

List the production systems and components in scope, then the in-scope files by language (`rg --files`). Include authored CI and infra config. Exclude vendored, generated, build-output, and migration-snapshot code; record exclusions and why. Test files are in scope for step 5. Record the branch, commit, and dirty-worktree state.

If an earlier `docs/error-handling/audit-*.md` exists, read it: this is a re-audit. Keep its finding and subtask IDs, carry over statuses, and mark closed items instead of renumbering.

Done when: the Scope section can name every component, every included root, every exclusion, and file counts per language.

### 2. Map the error surfaces and the baseline

**Error surfaces** are the boundaries where a failure leaves the code and meets a consumer: HTTP/gRPC/GraphQL handlers, global exception handlers and middleware, auth and validation layers, CLI entry points, queue/stream consumers and schedulers, WebSockets and streaming responses, public SDK/library APIs, and frontend calls to backends and UI error states. Find them by framework idiom (`@app.exception_handler`, `@RestControllerAdvice`, `app.use((err, ...)`, `ErrorBoundary`, `argparse`/`click`/`typer`/`picocli`/`commander`, consumer decorators, `fetch`/axios wrappers).

The **baseline** is what the codebase already has (each present with file, or absent):

- a shared base error and one family shape per module, with a registered fallback code and actionable base default
- a resolver at each third-party integration point whose errors arrive in inconsistent shapes
- an internal code registry and a `debug_info` schema with a central sanitizer
- `recovery` info on errors and a `Retry-After` header where retry is exposed
- a `reference_id` assigned on construction and one boundary recorder writing to centralized logging and the error tracker
- an emergency path when the recorder itself fails
- a public-code map and one response envelope, where a client API exists
- an error catalog outside the source
- an error tracker (hosted or self-managed), error-handling lint rules, the PR checklist lines, and an AI PR-review check

Trace each surface: origin, normalization or resolver, wrapping, terminal handler, sanitized record, public representation, client recovery. An absent baseline item is a systemic finding. A fix reuses a present baseline item; a second envelope, base type, or code style is a finding, not a fix.

### 3. Collect candidates

From the repo root:

```bash
python3 <skill-dir>/scripts/scan_candidates.py <paths...>   # Python, Java, TypeScript/JavaScript
```

Output is `RULE<TAB>file:line<TAB>snippet`; `--json` gives JSON lines and `--include-tests` adds test files. On large repos D6 (broad catch) dominates: save the output to `.tmp/error-handling-audit/candidates.tsv` and verify rule by rule, boundaries first.

- Python, if ruff is available (does not touch repo config): `ruff check --no-cache --isolated --select E722,BLE001,S110,S112,B904,TRY002,TRY400,TRY401,T201,LOG --output-format concise <paths>`
- Java/TypeScript: run the repo's own PMD/Error Prone/ESLint if configured, and note which T3 rules it lacks.

The scanner is regex-based. Missing base types, missing resolvers, missing `debug_info` or `recovery`, internal codes on the wire, and inconsistent envelopes only show up by reading the step 2 surfaces directly.

### 4. Verify, classify, and prioritize

For each candidate, read enough surrounding code, callers, and outer handlers to decide. Apply the separation test. Classify it as:

- a **finding**: check ID and EH rule (e.g. `EH-06 / D4`), priority, confidence, evidence (path:line, symbol, short redacted snippet), trigger and current behavior, impact, fix, acceptance test; or
- a **dismissal** with a one-line reason ("own-logic validation; typed raise, resolver not required").

Group instances that share one root cause and one fix under one finding with all locations; a single global handler or resolver often closes dozens of call sites.

Assign **P0, P1, or P2** to every finding using the rubric in rules.md, judged by consequence: what the person sees, what an agent can branch on, what an operator can reconstruct, what leaks. Confidence (high/medium/low) is separate from priority. Hypotheses you could not confirm go to the verification queue with a provisional priority and the exact check needed; they are not counted as findings.

Done when: every candidate and every step 2 surface is a finding, a dismissal, or a queued verification, and the counts reconcile.

### 5. Audit failure-path tests, CI, and release evidence

For each surface and each P0/P1 finding, find the test that exercises its failure path, for the expected error and the unexpected-failure fallback. Check that it asserts T1 to T9: public code, exact two-clause message, `request_id` as its own field, `recovery` and `Retry-After`, no internals or `debug_info` on the client payload, the centralized record found by that `request_id`, fake secret values absent everywhere, and survival of a failing logger or handler. Find regression tests for reported error defects (T6).

Check the PR template for the four error-handling checklist lines, AI PR-review instructions, and CI gates (G1 to G3). A CI file proves configuration, not branch protection or green runs; list those as unknown when you cannot see them.

Only with `--run-tests`: run the existing test suite for the scope once with the repo's documented command (inspect the script first; never target production) and record the command and pass/fail counts. A failing or unrunnable suite is a blocker for the report, not a reason to stop. Without the flag, record "not run, source only" and judge tests by reading them.

### 6. Evaluate the rules and the completeness test

For each of EH-01 to EH-13 record `verified`, `gap found`, `not applicable` (with reason), or `unverified` (with missing evidence), naming the level: source inspection, local execution, or CI/operational evidence. Do the same for applicable X-01 to X-07. Answer the constitution's seven completeness questions with evidence; any "no" means the scope is not complete.

### 7. Plan the remediation subtasks

Follow [references/planning.md](references/planning.md). Turn the findings into subtasks `EH-Tnn`, each one PR, ordered by phase and dependency, each with its own acceptance tests and a size within the limit. Every finding is closed by at least one subtask; every subtask closes or unblocks at least one finding.

### 8. Write the report

Follow [references/report-template.md](references/report-template.md) and write it to the `--out` path. Every finding and subtask has engineer and accountable-manager fields; they stay `UNASSIGNED` unless the user or ownership metadata (CODEOWNERS, project docs) names them, and each `UNASSIGNED` is an open ownership gap. Never invent people, approvals, CI results, or production behavior. Raise each blocker to the user when you find it, not only in the report.

The summary section always includes, in plain language for the project owner: what P0/P1/P2 mean, why each finding got its priority, how many PRs to expect (this scope and an estimate for the unaudited remainder), and an ordered "what to do next" table with who, size, and "done when". Keep these sections even on a re-audit.

Done when: the file exists and the reply gives its path, P0/P1/P2 counts, the completeness answers, the top three subtasks to start with, and the blockers.

When a public code, envelope field, or exit code changes in a planned subtask, record it under Breaking changes. A published code is never repurposed; a public code is deprecated with notice.

## Evidence and privacy discipline

- Never copy real secrets, PII, prompts, or sensitive payloads into the report. Redact values and keep the location.
- Never call sampling or keyword hits a full audit. If any in-scope code remains uninspected, mark the report partial and list the remaining paths.
- Distinguish expected validation rejections from system failures: they need the public contract and privacy rules, not an error-level incident record.
- Treat GraphQL `errors`/`extensions`, RFC 9457 Problem Details, and documented result types as potentially compliant contracts.
- Use local mocks and fake values for verification. Do not contact production services or run chaos tests in production.
