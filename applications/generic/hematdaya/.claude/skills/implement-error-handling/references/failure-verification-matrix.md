# Failure Verification Matrix

Select rows by actual component/protocol and explain non-applicability. Do not create artificial infrastructure solely to satisfy a test row. Use the project's existing test runner, controlled clock, local dependency doubles, and captured sinks. The constitution remains normative.

## Required lifecycle assertions

For every applicable system failure, verify reviewed message; stable internal and public code/mapping; actual protocol status/shape/headers; nonempty preserved occurrence ID; exactly one canonical sanitized diagnostic record; sensitive-value absence across all configured captured surfaces; recovery/retry termination and escalation. Expected domain rejections use the documented contract and suitable record/severity policy. For sink outages, explicitly assert original-error preservation and degraded or restored correlation instead of asserting a nonexistent record.

## Scenario matrix

| Scenario | Injection / trigger | Specific acceptance evidence |
| --- | --- | --- |
| Known dependency failure | Controlled auth/rate-limit/timeout/unavailable error | Correct contextual mapping; provider details private; full lifecycle assertions |
| Unknown failure | Unrecognized exception or unknown upstream response shape | Registered nonempty fallback; safe actionable message; nonretryable unless replay safety proven |
| Framework rejection | Validation/auth/permission failure through actual entry point | Same protocol contract; correct transport semantics; safe security logging where relevant |
| Sensitive payload | Fake token/key/email/prompt embedded in nested upstream text/causes | Literal fake values absent from responses, rendering, diagnostics, logs, traces, exporters, emergency sink |
| Log injection | Untrusted CR/LF and format delimiters in diagnostic input | Encoded structured field; no forged log event or altered record shape |
| Diagnostic resource abuse | Oversized, recursive, malformed, or unserializable input | Bounded safe serialization; original safe failure survives |
| Wrapping | SDK -> application -> API/client | Origin code/type/provenance and same occurrence ID preserved; public code separate |
| Reference lookup | Fail through public entry point and query captured store | Returned ID matches one canonical record with accurate timestamp/component/operation |
| Duplicate reporting | Multiple wrappers and replayed sink delivery | One canonical key/record; related attempt/trace events explicitly separate |
| Sink acknowledgment ambiguity | Sink stores record then reports failure | Safe fallback/replay does not create duplicate canonical occurrences |
| Handler/storage outage | Logger, sanitizer, serializer, or store raises | Primary code/message/status/reference survives; fallback is safe and nonrecursive |
| Emergency outage | Primary and emergency paths unavailable | Safe response remains; missing traceability reported; no false success or secret dump |
| Safe transient retry | Replay-safe operation plus valid/invalid Retry-After | Delay/date parsed safely; headers consistent; bounded attempts and deadline; cancellation respected |
| Timeout after commit | Side effect completes before response is lost | No blind replay; outcome reconciliation or stable idempotency key produces one effect |
| Concurrent duplicate write | Same idempotency key racing across requests | Atomic deduplication; same intended result; no double side effect; different intent rejected appropriately |
| Client handling | Contract error, malformed body, non-JSON gateway failure | Safe message/reference; no raw body rendering; no unsafe automatic resubmission |
| Cancellation/cleanup | Cancel or interrupt in-flight operation | Resources released; control flow preserved; no retry loop; cleanup failure does not replace primary |
| Committed stream | Failure after headers/partial output | Documented safe terminal event/close; no second HTTP response; correlated diagnostics |
| Queue terminal failure | Exhausted attempts or permanent failure | Correct acknowledgment policy; durable terminal handling/dead-letter where appropriate |
| Existing contract | Existing RFC 9457 or GraphQL partial-error response | No accidental breaking changes; stable extensions and media type/protocol fields preserved |

## Evidence levels

- Source inspection shows implementation intent and reachable paths, not execution success.
- A local full-chain test proves behavior under its fixture and captured sinks, not production export or retention.
- Actual CI/PR/operational evidence may establish required-check enforcement and production correlation; inaccessible evidence remains unverified.
- Suggested tests are proposed acceptance conditions until actually run. Record exact safe commands or include the reproducible probe script and its invocation; do not report an ellipsis as an executed command.
