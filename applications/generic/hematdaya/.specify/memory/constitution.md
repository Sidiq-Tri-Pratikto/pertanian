<!--
Sync Impact Report
Version: 2.1.0
Ratified: 2026-10-30
Amended: 2026-11-09
Changes: 2.1.0 makes meter connection the primary monitoring path and separates lab access from live release; 2.0.0 adds English alongside default Indonesian; 1.2.0 adds the HematDaya product principles and prohibitions; 1.1.0 adds TypeScript mobile applications; 1.0.0 is the initial constitution from the starter template.
-->

# Constitution

Authoritative engineering standards for `hematdaya`. This document says WHAT applies. `.claude/rules/` says HOW. When guidance conflicts, resolve it in this order:

1. `.specify/memory/constitution.md` (this file)
2. `.specify/memory/error-handling.md`
3. `AGENTS.md`
4. `.claude/rules/`
5. `.claude/skills/`

## Project Overview

**Product:** HematDaya helps people understand how electricity is used within a declared measurement scope and decide what to investigate. The same product serves households, businesses and industrial sites, on Android, iOS and web, with Indonesian as the default and English as a selectable language.

**Main features:**

- Recorded energy, qualified cost, contribution and history for a selected period and scope, with completeness and freshness shown beside the numbers.
- Meter connection is the primary path for monitoring actual use. Demo and historical CSV import remain complete hardware-free options. Isolated lab access is separate from user-facing release, which requires verified measurement-only access and physical evidence.
- Evidence-based observations from matched historical comparisons, with stated limitations and optional feedback.
- Optional tariff, expected-use schedule and energy-per-output metric. The core stays complete without them.
- Scope-safe aggregation that never double counts parent and child meters or alternative sources.

**Out of scope:** physical control of any kind, fault diagnosis, automatic appliance identification, verified savings claims, billing reconciliation, solar and net energy, cross-site dashboards, and team permissions. See `docs/product/PRD-EN.md` sections 4 and 5.

## Core Principles

1. **Simple designs (KISS/YAGNI).** Build the smallest design that satisfies the requirement. Add nothing speculative.
2. **Test-first reliability.** Establish a failing test or concrete validation path before implementing. Keep the suite green.
3. **Smallest justified diff.** Change only what the task requires. Report unrelated gaps instead of fixing them in passing.
4. **Evidence over assertion.** Ground every claim in a command that was run and its output.
5. **No secrets in tracked files.** Credentials live in the environment, never in the repository.
6. **Monitoring and advice only.** No screen, route, adapter or credential can switch equipment. Advice never commands.
7. **Unknown is never zero.** A missing value is `null` with a reason. A gap is a gap, measured zero is a real value, and missing tariff is not Rp0.
8. **One calculation authority.** The service computes energy, cost, coverage and evidence. Clients format what they receive and never recalculate it.
9. **Honest scope and provenance.** Every number states its period, measurement scope and origin. Simulated, imported and live data stay distinct, and combined totals are refused when loads may overlap.
10. **Natural bilingual product interface.** Use plain Indonesian by default and provide equivalent English across the MVP. Code, specs and documentation are English.

## Standards

### Code Quality

- All code passes `make check` (lint, format, tests) before merge.
- Pre-commit hooks stay installed and passing.
- Comments explain why, not what. Public APIs have docstrings.
- See: `.claude/rules/001-code-standards.md`, `.claude/rules/002-documentation.md`.
- Mobile: `.claude/rules/009-mobile.md`.

### Architecture

- Applications live in `applications/<app>/`, each with its own dependencies and Makefile.
- Features follow one module shape. See: `.claude/rules/005-module-structure.md`.
- Business logic stays independent of transport and storage. See: `.claude/rules/006-architecture.md`.
- All I/O is non-blocking.
- Services are stateless, so any instance can serve any request.
- Clients render what the service computes. Business rules live on the service.

### Testing

- Service tests live in `tests/unit/` and `tests/integration/`.
- Mobile tests follow `.claude/rules/009-mobile.md`.
- Each test is independent. External dependencies are faked in unit tests.
- Line coverage stays at 80% or higher; CI enforces the gate.
- Every bug fix adds a regression test.
- See: `.claude/rules/003-testing.md`.

### Data and Migrations

- Every schema change is a migration.
- **Never modify a merged migration.** Add a new one.
- Migrations run before the application starts.

### API Design

- REST conventions, validated request and response models, correct status codes.
- Every endpoint appears in the generated OpenAPI document.
- One error envelope on every endpoint.

### Error Handling (Non-negotiable)

Every failure serves three audiences and each gets only its own content: the user gets a two-clause
message (what happened, what to do next); agents and automation get a stable `code`, a documented
`debug_info` schema, and `recovery` guidance; engineers get a `reference_id` that resolves to exactly
one sanitized record in centralized logging and monitoring.

- Normalize every failure at the boundary that handles or exposes it; unexpected failures use a
  registered fallback code and a safe, actionable default message.
- Translate inconsistent third-party errors through one resolver per integration point; preserve the cause.
- Never put status codes, class names, provider jargon, debug data, or secrets in a user message or API response.
- Sanitize before anything reaches `debug_info`, logs, traces, or monitoring.
- External clients get one versioned envelope `{error: {code, message, request_id, recovery}}`
  mapped from internal codes in one place.
- Every public error states `recovery.retryable`; retryable errors state wait time and max attempts.
- A failure inside error handling must never hide the original error.
- Failure paths are tested end to end (message, code, response, reference ID, record, privacy with
  fake secrets, recovery); release only with that evidence or an approved PR exception.

Full rules: `.specify/memory/error-handling.md` (EH-01 to EH-13). Daily rule: `.claude/rules/008-error-handling.md`.

### Security

- Validate and sanitize all input at trust boundaries.
- Never log secrets, tokens, or personal data.
- Containers run as a non-root user.
- CI scans dependencies and images. Known high-severity findings block release.

### Configuration

- Settings come from environment variables, validated at startup.
- Every setting appears in `.env.example` with a safe value.
- Values that change between environments are never hardcoded.

### Dependencies

- `uv` manages Python dependencies; `uv.lock` is committed.
- `npm` manages TypeScript dependencies; `package-lock.json` is committed. Expo packages are added with `npx expo install`.
- Every new dependency is justified in its PR. Prefer the standard library and what is already installed.

### Deprecation

- Mark deprecated before removal, with a warning and a migration path.
- Published API fields and error codes are never repurposed.

### Git

- `main` is always releasable. Work happens on short-lived branches, squash-merged.
- Conventional Commits for commits and PR titles.
- See: `.claude/rules/007-git-workflow.md`.

## Prohibited Practices

1. **NEVER** commit secrets, keys, or tokens.
2. **NEVER** modify a merged migration.
3. **NEVER** skip tests or bypass linting to merge.
4. **NEVER** use blocking I/O in async code.
5. **NEVER** hardcode environment-specific values.
6. **NEVER** swallow an error or return a misleading success.
7. **NEVER** claim work is done without running its validation.
8. **NEVER** add an actuation route, relay command, or control credential.
9. **NEVER** render missing data as zero, fill a gap, or show a combined total for overlapping loads.
10. **NEVER** state a diagnosis, verified waste, verified savings, or an unqualified live connection.

## Review and Merge

- A change is mergeable only when its validation path has been run and passes.
- Security, data-loss, and contract-breaking issues block merge.
- A human reviewer stays accountable, whoever or whatever wrote the code.

## Amending This Document

Amend when a recurring decision should bind future work. Keep principles here and detail in rules.

- Bump the version in the Sync Impact Report: MAJOR removes or redefines a principle, MINOR adds one, PATCH rewords.
- Update affected rules and templates in the same PR.
- Record the change in the Sync Impact Report.
