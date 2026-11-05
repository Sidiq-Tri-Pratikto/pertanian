# Feature Specification: Platform core

**Feature Branch**: `005-platform-core`
**Created**: 2026-11-05
**Status**: Seeded, not started
**Milestone**: M0 Foundations
**Depends on**: 004
**Size**: L
**Covers**: FR16, AC46
**Flips**: none

## User Scenarios & Testing

### User Story 1 - A retried request never duplicates its effect (Priority: P1)

Every consequential POST from 023 onward needs the same idempotency, version and operation behaviour. It is built once here and used by each feature.

**Why this priority**: PRD section 11 requires retries without duplicates and stale intent without overwrites, and every mutation spec depends on it.

**Independent Test**: A test-only mutation route exercised with repeated and conflicting keys.

**Acceptance Scenarios**:

1. **Given** a consequential POST with `Idempotency-Key: k`, **When** it is repeated with the same body, **Then** the stored response is returned with `Idempotent-Replayed: true` and the effect happens once.
2. **Given** the same key with a different body, **When** it is sent, **Then** the response is `IDEMPOTENCY_CONFLICT` and nothing changes.
3. **Given** a mutation with `expected_version` older than the stored version, **When** it is sent, **Then** the response is `STALE_VERSION` with the current version.
4. **Given** a committed operation whose response was lost, **When** `GET /api/v1/operations/{id}` is called by the same actor, **Then** it returns `COMMITTED` with a result reference; for another actor it returns `NOT_FOUND`; for an unknown id it returns `UNKNOWN`.
5. **Given** a POST without `Idempotency-Key` on an operation that requires one, **When** it is sent, **Then** it is refused with `BAD_REQUEST` and an Indonesian field message.

### User Story 2 - Decisions commit once; side effects retry (Priority: P1)

**Acceptance Scenarios**:

1. **Given** a state change, **When** it commits, **Then** its audit event and outbox event commit in the same transaction, and none exist if the request fails.
2. **Given** a consumer that fails, **When** the worker retries, **Then** the underlying state is unchanged and the consumer runs again with backoff until it succeeds or reaches its attempt limit (AC46).
3. **Given** a consumer that already handled an event, **When** the event is delivered again, **Then** the consumer does nothing.
4. **Given** two workers, **When** they poll at once, **Then** each event is claimed by one of them.

### Edge Cases

- Idempotency records expire after seven days (policy `idempotency-retention` v1); after expiry the operation status remains readable.
- A request that fails before commit leaves a `pending` record that the next identical request completes.
- Product time comes only from `app.core.clock.now()`; tests freeze it.

## Requirements

### Functional Requirements

- **FR-001**: The platform MUST provide `Money` (decimal string type), `Version` handling, cursor pagination (`limit` ≤ 100), and a clock dependency.
- **FR-002**: The platform MUST provide an idempotency dependency storing actor, operation, key, request digest, response and operation id.
- **FR-003**: The platform MUST provide `GET /api/v1/operations/{id}` scoped to the acting party.
- **FR-004**: Audit and outbox writes MUST share the request transaction.
- **FR-005**: `python -m app.worker` MUST dispatch outbox events and jobs with `FOR UPDATE SKIP LOCKED`, per-consumer deduplication, backoff and an attempt limit.
- **FR-006**: New codes `STALE_VERSION`, `IDEMPOTENCY_CONFLICT` MUST be registered with Indonesian messages.

### Key Entities

- **IdempotencyRecord**, **Operation**, **AuditEvent**, **OutboxEvent**, **OutboxDelivery**, **Job**.

## Success Criteria

### Measurable Outcomes

- **SC-001**: A concurrency test sends the same key 20 times in parallel and observes one effect.
- **SC-002**: A worker test kills a consumer midway and observes exactly one completed delivery after restart.
