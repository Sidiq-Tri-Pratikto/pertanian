---
name: implement-error-handling
description: >-
  Builds or fixes failure behavior following the project error-handling
  constitution (EH-01 to EH-13): typed errors with stable codes, two-clause
  messages, sanitized debug_info, recovery and retry guidance, a public error
  envelope, one centralized record per reference ID, a handler that survives
  its own failure, and full-chain failure-path tests. Use when implementing or
  changing APIs, clients, SDKs, workers, integrations, or UI error states, when
  adding error codes or exception handlers, or when executing an EH-Tnn
  subtask from a robust-error-handling audit plan.
---

# Implement Error Handling

`references/error-handling-constitution.md` is a symlink to `.specify/memory/error-handling.md`; edit only that file. Read `docs/error-handling/deviation.md` for this project's base error, code prefix, envelope, and sanitizer.

## 1. Load the contract

1. Read [references/error-handling-constitution.md](references/error-handling-constitution.md) and [references/failure-verification-matrix.md](references/failure-verification-matrix.md). For idiomatic Python, read `references/python.md` in the `robust-error-handling` skill.
2. Read the project's instructions, constitution amendments, error catalog, API schema, framework handlers, clients, telemetry setup, tests, PR template, and CI config. Reuse the existing base error, code registry, envelope, sanitizer, logger, and tracker. Never add a second base class, envelope, or code style.
3. Keep compatible published contracts (an existing envelope, RFC 9457 Problem Details, GraphQL `errors`). Document deviations and the evidence that each mandatory outcome still holds.

## 2. Pin the scope

- **Feature or fix:** implement failure behavior for the feature and the shared boundaries it touches. Report other legacy gaps you notice with a P0/P1/P2 priority (rubric in `robust-error-handling/references/rules.md`); do not fix them in this change.
- **Plan subtask (`EH-Tnn`):** open the latest `docs/error-handling/audit-*.md`, read the subtask block, and confirm its dependencies are `done`. Implement only its scope; respect its out-of-scope list. If the change grows past about 400 production lines or 10 production files, stop, propose a split in the plan, and implement only the first part.

Before editing, map the lifecycle for each failure: origin, normalization or resolver, wrapping, terminal handler and record, public serializer, client display and recovery. Note sensitive values, side effects, retry safety (could a timeout follow a committed write?), cancellation, and whether a response or stream is already committed.

## 3. Implement

1. **Codes and messages.** Register a stable internal code per failure type (fallback included) with a two-clause default message (what happened, what to do next) and a documented trigger. Add each to the error catalog.
2. **Translation.** Route inconsistent third-party errors through one resolver per integration point; prefer structured signals over message text; fall back safely. `raise resolve(raw) from raw`. Own-logic failures raise typed errors directly.
3. **Diagnostics.** Build `debug_info` (`error_type`, sanitized `original_message`, optional sanitized `traceback`) through the shared sanitizer before it is attached or emitted. Prefer allowlisted fields over redacting raw bodies. Default rendering is the message only.
4. **Wrapping.** App errors that wrap library errors keep the original type (chained cause), code, `debug_info`, and `reference_id`. Do not generate a new reference ID on each wrapper.
5. **Public contract.** Map internal codes to one public definition (code, HTTP status, message, recovery) in one place with an `INTERNAL_ERROR` fallback. Cover framework validation and auth errors too. Never send internal codes, class names, `debug_info`, or `escalate_when`.
6. **Recording.** Assign `reference_id` once, on construction. Record each system failure once, at the terminal boundary, to centralized logging and the error tracker, with code, service, operation (route template), timestamp, and sanitized `debug_info`. Return the same ID as `error.request_id`.
7. **Recovery.** Set `recovery.retryable` from operation safety, not status alone; unknown failures are not retryable. Document `retry_after_seconds` (and send `Retry-After`) and `max_attempts`. Retry side effects only with idempotency keys or deduplication; retry in one layer, bounded, with jitter.
8. **Resilience of the handler.** Wrap the recorder, tracker, and serializer so their failure keeps the original status, code, message, and reference ID; use a bounded, non-recursive emergency log.
9. **Cancellation and cleanup.** Propagate cancellation and shutdown signals after cleanup; cleanup errors never replace the primary failure. Queue jobs separate retry from terminal failure and never acknowledge failed work. Committed streams end with a documented error event or close.
10. **Consumers.** Frontends and SDK clients render `error.message` and `error.request_id`, branch on `error.code`, follow `recovery`, never auto-resubmit unsafe writes, and handle non-JSON or malformed responses without showing raw bodies.
11. **Internal services (X-07).** A client for a sibling service resolves the upstream envelope into a typed error, parses both the legacy and the new shape until the producer's migration is done, never copies `response.text` into messages or logs, sends `X-Request-ID`, and stores the upstream `request_id` as `debug_info.upstream_request_id`. A producer-side envelope change waits until the consumer subtask is `done`. For FastAPI wiring and the client pattern, see `robust-error-handling/references/python.md` sections 1a and 1b.

## 4. Verify before calling it done

1. Pick the applicable rows from the verification matrix; write the failing tests first.
2. Full-chain tests call the public entry point and read the captured record. Assert message, internal and public code, status and headers, `request_id`, exactly one record found by that ID, recovery, and that injected fake secret values (API key, bearer token, email, prompt text) appear in no response, log, or record. A resolver-only or `assert raises` test is not enough.
3. Test the unknown-failure fallback and a failing recorder or logger.
4. Run the project's lint and test commands (inspect scripts first; never target production). Do not install tools or change dependencies just to make a check pass; report checks you could not run.
5. Update the error catalog, public contract docs, and the PR description with the four EH-13 checklist lines.

## 5. Report

State the files changed, the failure behavior before and after, the exact test commands and results, and anything not verified. For a plan subtask, update its status in the audit file: `done` with `Verified by: <test names> · <command> → <result>`, or `in-progress` with what remains; update the findings it closes; suggest the PR title from the subtask. Never claim manager confirmation, release approval, required-check enforcement, or production traceability you have not seen. Leave commits and PRs to the user unless asked.
