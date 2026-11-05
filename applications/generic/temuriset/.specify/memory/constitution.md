<!--
Sync Impact Report
Version: 1.2.0
Ratified: 2026-11-05
Changes: 1.2.0 adds the TemuRiset product principles and a TypeScript web application; 1.1.0 adds TypeScript client applications; 1.0.0 is the initial constitution from the starter template.
-->

# Constitution

Authoritative engineering standards for `temuriset`. This document says WHAT applies. `.claude/rules/` says HOW. When guidance conflicts, resolve it in this order:

1. `.specify/memory/constitution.md` (this file)
2. `.specify/memory/error-handling.md`
3. `AGENTS.md`
4. `.claude/rules/`
5. `.claude/skills/`

## Project Overview

**Product:** TemuRiset helps inventors find investors and partners who can advance their inventions, then carries a deliberate pitch through review, itemized revisions, meetings and a relationship both parties confirm. Independent individuals, startups, corporate teams, nonprofits, communities and researchers use the same product, on a responsive web client with an Indonesian interface.

**Main features:**

- Versioned invention portfolios with current versus planned facts, deliberate disclosure, private documents and per-recipient, per-version grants.
- Project support requests and company funding requests kept distinct, with money that always states subject, currency, basis and period.
- Partner profiles and versioned opportunities with typed, visible requirements; explainable matching that separates eligibility, readiness and fit.
- Pitch submission with preflight and frozen snapshots, three recipient decisions, itemized revision rounds, shared discussion and race-safe scheduling.
- Relationship records confirmed by both parties on the same version, with a public projection limited to the intersection of their consent.

**Out of scope:** holding or transferring money, issuing shares, securities offerings, crowdfunding, automated valuation, investment advice, guaranteed introductions, cap tables, legal ownership determination, patentability assessment, mass outreach and public inventor ratings. See PRD section 2 in `docs/generic/temuriset/01_PRD_TemuRiset_Generic_EN.md` at the repository root.

## Core Principles

1. **Simple designs (KISS/YAGNI).** Build the smallest design that satisfies the requirement. Add nothing speculative.
2. **Test-first reliability.** Establish a failing test or concrete validation path before implementing. Keep the suite green.
3. **Smallest justified diff.** Change only what the task requires. Report unrelated gaps instead of fixing them in passing.
4. **Evidence over assertion.** Ground every claim in a command that was run and its output.
5. **No secrets in tracked files.** Credentials live in the environment, never in the repository.
6. **Deny by default.** Every read, write, preview, search projection, job result and download is authorized on the server for the acting party. An object the actor may not see answers `NOT_FOUND`, so its existence never leaks.
7. **Unknown is never zero or failure.** Missing, conflicting or unreviewed facts are `UNKNOWN` with a reason. A null amount is "Belum ditentukan", never Rp0 or USD 0.
8. **Money keeps its meaning.** Amounts are decimal strings with currency, subject, basis and period. Unlike amounts are never compared, converted, summed into valuations or turned into ownership.
9. **Deliberate disclosure.** Documents are private by default. Sharing names one recipient and one version, revocation blocks new retrieval, and the product says plainly that copies already downloaded cannot be recalled.
10. **Same version, both parties.** A pitch approval opens discussion only. A relationship exists only when both authorized parties confirm the same version, and public fields are the intersection of their consent minus live restrictions.
11. **Retries never duplicate.** Consequential mutations carry an idempotency key and an expected version. Stale intent never overwrites current state.
12. **One authority.** The API owns rules, matching, permissions, money semantics and consent. The web client renders what it receives and never re-implements a rule.
13. **Natural Indonesian product interface.** Product copy is Indonesian. Code, specs and documentation are English.

## Standards

### Code Quality

- All code passes `make check` (lint, format, tests) before merge.
- Pre-commit hooks stay installed and passing.
- Comments explain why, not what. Public APIs have docstrings.
- See: `.claude/rules/001-code-standards.md`, `.claude/rules/002-documentation.md`.
- Web: `.claude/rules/009-web.md`.

### Architecture

- Applications live in `applications/<app>/`, each with its own dependencies and Makefile.
- Features follow one module shape. See: `.claude/rules/005-module-structure.md`.
- Business logic stays independent of transport and storage. See: `.claude/rules/006-architecture.md`.
- All I/O is non-blocking.
- Services are stateless, so any instance can serve any request.

### Testing

- Service tests live in `tests/unit/` and `tests/integration/`.
- Web tests follow `.claude/rules/009-web.md`.
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

## Review and Merge

- A change is mergeable only when its validation path has been run and passes.
- Security, data-loss, and contract-breaking issues block merge.
- A human reviewer stays accountable, whoever or whatever wrote the code.

## Amending This Document

Amend when a recurring decision should bind future work. Keep principles here and detail in rules.

- Bump the version in the Sync Impact Report: MAJOR removes or redefines a principle, MINOR adds one, PATCH rewords.
- Update affected rules and templates in the same PR.
- Record the change in the Sync Impact Report.
